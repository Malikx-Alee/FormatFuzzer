"""
File parsing module for the learning constraints system.
Contains functions for parsing files and extracting byte ranges.
"""
import subprocess
import re
import json
import collections
from .config import Config, GlobalState
from .utils import clean_attribute_key, insert_nested_dict, extract_byte_values, remove_attribute_from_nested_dict, detect_checksum_algorithm_first


class FileParser:
    """File parser class for extracting structure and byte ranges from files."""

    def __init__(self, global_state: GlobalState):
        """
        Initialize the parser with global state.

        Args:
            global_state (GlobalState): The global state object
        """
        self.global_state = global_state

    def parse_file_structure(self, file_path):
        """
        Parse a file and extract attributes with byte ranges.

        Args:
            file_path (str): Path to the file to parse

        Returns:
            list: List of tuples (start, end, attribute) representing byte ranges
        """
        byte_ranges = []

        try:
            result = subprocess.run(
                [Config.get_fuzzer_executable(), "parse", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )

            current_parent_end = -1
            lines = result.stdout.splitlines()
            entries = []

            # Step 1: Parse all lines into structured format
            for line in lines:
                parts = line.split(',')
                if len(parts) < 3:
                    continue  # Skip bad lines

                try:
                    start, end, label = int(parts[0]), int(parts[1]), parts[2]
                    entries.append((start, end, label, line))

                    # Add to blacklist if size > max allowed bytes
                    if end - start > Config.MAX_ATTRIBUTE_SIZE_BYTES:
                        blocked_key = clean_attribute_key(label)
                        # Check if this is a new attribute being blacklisted
                        if blocked_key not in self.global_state.blacklisted_attributes:
                            self.global_state.blacklisted_attributes.add(blocked_key)
                            # Remove any previously added values for this attribute from nested_values_hex
                            remove_attribute_from_nested_dict(self.global_state.nested_values_hex, label)

                except ValueError:
                    # Skip lines with invalid integer values
                    continue

            # Step 2: Sort entries by start byte (ascending) and end byte (descending)
            entries.sort(key=lambda x: (x[0], -x[1]))

            # Step 3: Filter overlapping ranges and blacklisted attributes
            for start, end, attribute, line in entries:
                if start == end and "_" in attribute:
                    continue

                # Skip if attribute is in blacklist
                if clean_attribute_key(attribute) in self.global_state.blacklisted_attributes:
                    continue

                # Check for overlap with previous parent and size constraint
                if ((start > current_parent_end or end < current_parent_end) and
                    end - start <= Config.MAX_ATTRIBUTE_SIZE_BYTES):
                    # No overlap with previous parent
                    byte_ranges.append((start, end, attribute))
                    current_parent_end = end

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return byte_ranges

    def extract_bytes_from_file(self, file_path, byte_ranges):
        """
        Extract byte values from a file based on the provided byte ranges.

        Args:
            file_path (str): Path to the file to extract bytes from
            byte_ranges (list): List of tuples (start, end, attribute)
        """
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()  # Read entire file into memory


                # Track which chunk types have had checksum detection in this file
                seen_chunk_types_for_file = set()

                for start, end, attribute in byte_ranges:
                    if end < len(file_data):  # Ensure within file size
                        try:
                            # Extract byte values in different formats
                            byte_values = extract_byte_values(file_data, start, end)

                            # Split attribute into hierarchical keys
                            attribute_keys = attribute.split("~")

                            # Insert into nested dictionary (currently only hex)
                            insert_nested_dict(
                                self.global_state.nested_values_hex,
                                attribute_keys,
                                byte_values['hex']
                            )

                            # If checksum detection is enabled, verify algorithms during parsing (PNG focus)
                            if getattr(Config, "ENABLE_CHECKSUM_DETECTION", False):
                                try:
                                    last_key = attribute_keys[-1]
                                    if last_key == "crc" and Config.FILE_TYPE == "png":
                                        # Use the attribute prefix (handles first chunk 'file~chunk' and indexed 'file~chunk_N')
                                        prefix = "~".join(attribute_keys[:-1])  # drop trailing 'crc'

                                        # Expected CRC value (bytes) from the file
                                        expected_crc_bytes = bytes.fromhex(byte_values['hex'])

                                        # Reconstruct checksum input range: type (4 bytes) + data (length bytes)
                                        type_start = None
                                        type_end = None

                                        # Try to find explicit type range in byte_ranges (match both '~type' and '~type~cname')
                                        type_prefix = prefix + "~type"
                                        for s2, e2, attr2 in byte_ranges:
                                            if attr2.startswith(type_prefix):
                                                type_start, type_end = s2, e2
                                                break

                                        # If not found, infer type immediately after length
                                        if type_start is None:
                                            length_prefix = prefix + "~length"
                                            length_end = None
                                            for s2, e2, attr2 in byte_ranges:
                                                if attr2.startswith(length_prefix):
                                                    length_end = e2
                                                    break
                                            if length_end is not None:
                                                type_start = length_end + 1
                                                type_end = type_start + 3

                                        crc_start = start
                                        if type_start is not None and type_end is not None:
                                            checksum_start = type_start
                                            checksum_end = crc_start - 1
                                            if checksum_end >= checksum_start:
                                                checksum_input = file_data[checksum_start:checksum_end + 1]

                                                # DEBUG LOGS FOR CHECKSUM DETECTION
                                                print(f"[ChecksumDetect] prefix={prefix} type_range=({type_start},{type_end}) crc_start={crc_start} checksum_span=({checksum_start},{checksum_end}) expected={byte_values['hex']}")

                                                first_match = detect_checksum_algorithm_first(checksum_input, expected_crc_bytes)
                                                matches = [first_match] if first_match else []

                                                print(f"[ChecksumDetect] match={first_match}")

                                                # Record by chunk type (read the 4-byte type) and only compute once per type per file
                                                try:
                                                    chunk_type = file_data[type_start:type_end + 1]
                                                    chunk_type_str = chunk_type.decode("ascii", errors="ignore")
                                                    if chunk_type_str and chunk_type_str not in seen_chunk_types_for_file:
                                                        existing = self.global_state.checksum_algorithms["by_chunk_type"].get(chunk_type_str, [])
                                                        merged = sorted(set(existing + matches))
                                                        self.global_state.checksum_algorithms["by_chunk_type"][chunk_type_str] = merged
                                                        seen_chunk_types_for_file.add(chunk_type_str)
                                                except Exception:
                                                    pass

                                    elif Config.FILE_TYPE == "zip" and last_key in ("frCrc", "deCrc"):
                                        # ZIP: compute once per type per file. Types: 'record' (local file header) and 'dirEntry' (central directory)
                                        try:
                                            expected_crc_bytes = bytes.fromhex(byte_values['hex'])
                                            if last_key == "frCrc":
                                                chunk_label = "record"
                                                if chunk_label not in seen_chunk_types_for_file:
                                                    # Find data span for this record
                                                    data_start = None
                                                    data_end = None
                                                    for s2, e2, attr2 in byte_ranges:
                                                        if attr2.startswith("file~record~frData"):
                                                            data_start, data_end = s2, e2
                                                            break
                                                    if data_start is not None and data_end is not None and data_end >= data_start:
                                                        checksum_input = file_data[data_start:data_end + 1]
                                                        print(f"[ChecksumDetect][ZIP] type={chunk_label} data_range=({data_start},{data_end}) expected={byte_values['hex']}")
                                                        first_match = detect_checksum_algorithm_first(checksum_input, expected_crc_bytes)
                                                        print(f"[ChecksumDetect][ZIP] match={first_match}")
                                                        matches = [first_match] if first_match else []
                                                        existing = self.global_state.checksum_algorithms["by_chunk_type"].get(chunk_label, [])
                                                        merged = sorted(set(existing + matches))
                                                        self.global_state.checksum_algorithms["by_chunk_type"][chunk_label] = merged
                                                        seen_chunk_types_for_file.add(chunk_label)
                                            else:  # deCrc in central directory
                                                chunk_label = "dirEntry"
                                                if chunk_label not in seen_chunk_types_for_file:
                                                    # Prefer to mirror the local record's algorithm for this file if already known
                                                    record_algos = self.global_state.checksum_algorithms["by_chunk_type"].get("record")
                                                    if record_algos:
                                                        self.global_state.checksum_algorithms["by_chunk_type"][chunk_label] = list(record_algos)
                                                        seen_chunk_types_for_file.add(chunk_label)
                                        except Exception as zde:
                                            print(f"[ChecksumDetect][ZIP][ERROR] {zde}")
                                            pass
                                except Exception as de:
                                    # Best-effort detection; continue
                                    print(f"[ChecksumDetect][ERROR] {de}")
                                    pass

                        except ValueError as e:
                            print(f"Error extracting bytes for attribute {attribute}: {e}")
                            continue

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def get_file_attributes(self, byte_ranges):
        """
        Extract unique attributes from byte ranges.

        Args:
            byte_ranges (list): List of tuples (start, end, attribute)

        Returns:
            set: Set of cleaned attribute keys
        """
        attributes = set()
        for _, _, attribute in byte_ranges:
            attributes.add(clean_attribute_key(attribute))
        return attributes

    def check_for_new_attributes(self, byte_ranges, original_attributes):
        """
        Check if any new attributes are found in the byte ranges.

        Args:
            byte_ranges (list): List of tuples (start, end, attribute)
            original_attributes (set): Set of original attribute keys

        Returns:
            tuple: (bool, str) - (has_new_attributes, first_new_attribute_found)
        """
        for _, _, attribute in byte_ranges:
            cleaned_attr = clean_attribute_key(attribute)
            if cleaned_attr not in original_attributes:
                return True, cleaned_attr
        return False, None

    def mine_interesting_values_from_template(self):
        """
        Mine interesting values from the template using ffcompile command.
        This runs before processing valid files to populate nested_values_hex with template values.

        Returns:
            tuple: (success: bool, mined_values: dict) - success status and mined template values
        """
        try:
            # Construct the ffcompile command
            template_file = f"templates/{Config.FILE_TYPE}.bt"
            output_file = f"{Config.FILE_TYPE}.cpp"

            print(f"Mining interesting values from template: {template_file}")

            result = subprocess.run(
                ["./ffcompile", template_file, output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Parse the output to extract mined interesting values
            output_lines = result.stdout.splitlines()
            stderr_lines = result.stderr.splitlines()

            # Combine stdout and stderr for parsing (ffcompile might output to either)
            all_lines = output_lines + stderr_lines

            # Look for the "Mined interesting values:" section
            mining_started = False

            # Create a separate nested structure for template values only
            template_values = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

            for line in all_lines:
                line = line.strip()

                if "Mined interesting values:" in line:
                    mining_started = True
                    print("Found mined interesting values section")
                    continue

                if not mining_started:
                    continue

                # Stop parsing when we hit other sections
                if any(section in line for section in ["File stat functions found:", "Lookahead functions found:", "Finished creating"]):
                    break

                # Parse attribute lines - handle both object and array formats
                if ":" in line and (("{" in line) or ("[" in line)):
                    try:
                        # Split on the first colon to separate attribute name from values
                        attr_name, values_str = line.split(":", 1)
                        attr_name = attr_name.strip()
                        values_str = values_str.strip()

                        # Handle both dictionary format (objects) and list format (arrays)
                        if values_str.startswith("{"):
                            # Dictionary/Object format: {'0': ['0x8950'], '1': ['0x4E47']}
                            values_dict = eval(values_str)  # Safe since we control the input
                            for key, value_list in values_dict.items():
                                if isinstance(value_list, list):
                                    for value in value_list:
                                        # Clean the value (remove quotes and 0x prefix if present)
                                        clean_value = value.strip('"\'')
                                        if clean_value.startswith('0x'):
                                            clean_value = clean_value[2:]  # Remove 0x prefix

                                        # Create attribute path: attr_name~key (no "template" prefix for separate storage)
                                        attribute_keys = [attr_name, key]
                                        insert_nested_dict(
                                            template_values,
                                            attribute_keys,
                                            clean_value
                                        )
                                else:
                                    # Single value case
                                    clean_value = str(value_list).strip('"\'')
                                    if clean_value.startswith('0x'):
                                        clean_value = clean_value[2:]

                                    attribute_keys = [attr_name, key]
                                    insert_nested_dict(
                                        template_values,
                                        attribute_keys,
                                        clean_value
                                    )

                        elif values_str.startswith("["):
                            # List/Array format: ['"IHDR"', '"tEXt"', '"PLTE"']
                            values_list = eval(values_str)  # Safe since we control the input

                            # Clean all values in the array
                            cleaned_values = []
                            for value in values_list:
                                clean_value = value.strip('"\'')
                                if clean_value.startswith('0x'):
                                    clean_value = clean_value[2:]  # Remove 0x prefix
                                cleaned_values.append(clean_value)

                            # Store the entire array as a single entry in template_values
                            # Create attribute path: attr_name (no "template" prefix for separate storage)
                            final_key = attr_name

                            # For arrays, store as a set containing all array values
                            if final_key not in template_values:
                                template_values[final_key] = set()

                            # Add all cleaned values to the set
                            for clean_value in cleaned_values:
                                template_values[final_key].add(clean_value)

                        print(f"Mined values for {attr_name}")

                    except Exception as e:
                        print(f"Error parsing line '{line}': {e}")
                        continue

            print("Successfully mined interesting values from template")

            # Return the separate template values
            return True, dict(template_values)

        except Exception as e:
            print(f"Error mining interesting values from template: {e}")
            return False, {}



