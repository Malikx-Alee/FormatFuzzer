"""
File parsing module for the learning constraints system.
Contains functions for parsing files and extracting byte ranges.
"""
import subprocess
import re
import json
import collections
import binascii
import zlib
import logging
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
        self.logger = logging.getLogger(__name__)

    def parse_file_structure(self, file_path):
        """
        Parse a file and extract attributes with byte ranges.

        Args:
            file_path (str): Path to the file to parse

        Returns:
            tuple: (original_byte_ranges, filtered_byte_ranges)
                - original_byte_ranges: List of all byte ranges including those > MAX_ATTRIBUTE_SIZE_BYTES
                - filtered_byte_ranges: List of byte ranges after filtering (current implementation)
        """
        byte_ranges = []
        original_byte_ranges = []

        try:
            result = subprocess.run(
                [Config.get_fuzzer_executable(), "parse", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )

            current_parent_end = -1
            original_current_parent_end = -1
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

            # Step 3: Build original_byte_ranges (without size filtering, but with overlap filtering)
            for start, end, attribute, line in entries:
                # Skip if start == end and attribute has underscore followed by a number (e.g., "field_0", "item_123")
                if start == end and "_" in attribute:
                    # Check if underscore is followed by a number
                    parts = attribute.split("_")
                    if len(parts) > 1 and parts[-1].isdigit():
                        continue

                # Check for overlap with previous parent (no size constraint)
                if start > original_current_parent_end or end < original_current_parent_end:
                    # No overlap with previous parent
                    original_byte_ranges.append((start, end, attribute))
                    original_current_parent_end = end

            # Step 4: Filter overlapping ranges and blacklisted attributes for filtered_byte_ranges
            for start, end, attribute, line in entries:
                # Skip if start == end and attribute has underscore followed by a number (e.g., "field_0", "item_123")
                if start == end and "_" in attribute:
                    # Check if underscore is followed by a number
                    parts = attribute.split("_")
                    if len(parts) > 1 and parts[-1].isdigit():
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

        return original_byte_ranges, byte_ranges

    def extract_bytes_from_file(self, file_path, byte_ranges, original_byte_ranges=None):
        """
        Extract byte values from a file based on the provided byte ranges.

        Args:
            file_path (str): Path to the file to extract bytes from
            byte_ranges (list): List of tuples (start, end, attribute) - filtered ranges
            original_byte_ranges (list): List of all byte ranges including large ones (optional)
        """
        # If original_byte_ranges is not provided, use byte_ranges as fallback
        if original_byte_ranges is None:
            original_byte_ranges = byte_ranges
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

                            # Check if attribute now has too many unique values
                            cleaned_key = clean_attribute_key(attribute)
                            if cleaned_key not in self.global_state.blacklisted_attributes:
                                # Navigate to the leaf set to count unique values
                                current = self.global_state.nested_values_hex
                                for key in attribute_keys:
                                    if key in current:
                                        current = current[key]
                                    else:
                                        current = None
                                        break

                                if current is not None and isinstance(current, set):
                                    if len(current) > Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE:
                                        self.global_state.blacklisted_attributes.add(cleaned_key)
                                        remove_attribute_from_nested_dict(self.global_state.nested_values_hex, attribute)
                                        self.logger.debug(f"Blacklisted attribute '{cleaned_key}' - exceeded {Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE} unique values")

                            # Detect PNG compression method from IHDR chunk
                            # PNG IHDR structure: width(4) + height(4) + bit_depth(1) + color_type(1) + compression(1) + filter(1) + interlace(1)
                            if Config.FILE_TYPE == "png":
                                last_key = attribute_keys[-1]
                                # Check if we're in the IHDR chunk and just parsed the bits field
                                if last_key == "compr_method" and len(attribute_keys) >= 3 and "ihdr" in attribute_keys:
                                    # The compression method is 2 bytes after bits: bits(1) + color_type(1) + compression(1)
                                    # So compression is at position: end + 1 + 1 + 1 = end + 3
                                    # compr_offset = end + 3
                                    # if compr_offset < len(file_data):
                                    compr_method_value = file_data[end]
                                    method_name = self._get_png_compression_method_name(compr_method_value)
                                    # Only log if this compression method hasn't been detected yet
                                    if str(compr_method_value) not in self.global_state.checksum_algorithms["compression_methods"]:
                                        self.global_state.checksum_algorithms["compression_methods"][str(compr_method_value)] = method_name
                                        self.logger.info(f"[PNG] Detected compression method: {compr_method_value} ({method_name})")
                                    else:
                                        # Still update the dict in case it was set to a different name
                                        self.global_state.checksum_algorithms["compression_methods"][str(compr_method_value)] = method_name

                            # Detect BMP compression method from BITMAPINFOHEADER
                            if Config.FILE_TYPE == "bmp":
                                last_key = attribute_keys[-1]
                                if last_key == "biCompression" and len(attribute_keys) >= 2:
                                    # Extract compression method value (4 bytes, little-endian)
                                    compr_method_value = int.from_bytes(file_data[start:end + 1], "little")
                                    method_name = self._get_bmp_compression_method_name(compr_method_value)
                                    # Only log if this compression method hasn't been detected yet
                                    if str(compr_method_value) not in self.global_state.checksum_algorithms["compression_methods"]:
                                        self.global_state.checksum_algorithms["compression_methods"][str(compr_method_value)] = method_name
                                        self.logger.info(f"[BMP] Detected compression method: {compr_method_value} ({method_name})")
                                    else:
                                        # Still update the dict in case it was set to a different name
                                        self.global_state.checksum_algorithms["compression_methods"][str(compr_method_value)] = method_name

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
                                        # ZIP: compute for each record/dirEntry element and aggregate under recordCrc/dirEntryCrc
                                        # Only process frCrc once and deCrc once per file
                                        try:
                                            expected_crc_bytes = bytes.fromhex(byte_values['hex'])
                                            if last_key == "frCrc":
                                                # Use a unified key "recordCrc" for all record elements
                                                unified_key = "recordCrc"

                                                # Only process frCrc once per file
                                                if "frCrc" not in seen_chunk_types_for_file:
                                                    # Extract the record element identifier from the current attribute
                                                    # attribute_keys is like ['file', 'record', 'frCrc'] or ['file', 'record_1', 'frCrc']
                                                    record_element = attribute_keys[1] if len(attribute_keys) > 1 else "record"
                                                    chunk_label = record_element  # e.g., "record", "record_1", "record_2"
                                                    first_match = None

                                                    # Always extract compression method to track it
                                                    record_prefix = f"file~{record_element}"
                                                    frdata_prefix = f"{record_prefix}~frData"
                                                    frmethod_prefix = f"{record_prefix}~frCompression"

                                                    frdata_start = None
                                                    frdata_end = None
                                                    frmethod_value = None

                                                    # Find frData and frCompression in original_byte_ranges
                                                    for s2, e2, attr2 in original_byte_ranges:
                                                        if attr2.startswith(frdata_prefix):
                                                            frdata_start, frdata_end = s2, e2
                                                        elif attr2.startswith(frmethod_prefix):
                                                            # Extract compression method (2 bytes, little-endian)
                                                            method_bytes = file_data[s2:e2 + 1]
                                                            if len(method_bytes) == 2:
                                                                frmethod_value = int.from_bytes(method_bytes, "little")

                                                        # Exit early if we have both values
                                                        if frdata_start is not None and frmethod_value is not None:
                                                            break

                                                    # Track compression method in global state
                                                    if frmethod_value is not None:
                                                        method_name = self._get_compression_method_name(frmethod_value)
                                                        # Only log if this compression method hasn't been detected yet
                                                        if str(frmethod_value) not in self.global_state.checksum_algorithms["compression_methods"]:
                                                            self.global_state.checksum_algorithms["compression_methods"][str(frmethod_value)] = method_name
                                                            self.logger.info(f"[ZIP] Detected compression method: {frmethod_value} ({method_name})")
                                                        else:
                                                            # Still update the dict in case it was set to a different name
                                                            self.global_state.checksum_algorithms["compression_methods"][str(frmethod_value)] = method_name

                                                    # Check if we should validate by decompressing
                                                    if getattr(Config, "ZIP_VALIDATE_CHECKSUM_WITH_DECOMPRESSION", False):
                                                        if frdata_start is not None and frdata_end is not None and frmethod_value is not None:
                                                            compressed_data = file_data[frdata_start:frdata_end + 1]

                                                            try:
                                                                # Decompress based on compression method
                                                                uncompressed_data = self._decompress_zip_data(compressed_data, frmethod_value)

                                                                if uncompressed_data is not None:
                                                                    # Validate checksum on uncompressed data
                                                                    # Try both big-endian and little-endian
                                                                    expected_bytes = expected_crc_bytes
                                                                    if len(expected_bytes) == 4:
                                                                        be = expected_bytes
                                                                        le = expected_bytes[::-1]
                                                                    else:
                                                                        be = expected_bytes
                                                                        le = expected_bytes

                                                                    # Try BE first, then LE
                                                                    first_match = detect_checksum_algorithm_first(uncompressed_data, be)
                                                                    if not first_match and len(expected_bytes) == 4:
                                                                        first_match = detect_checksum_algorithm_first(uncompressed_data, le)

                                                                    method_name = self._get_compression_method_name(frmethod_value)
                                                                    print(f"[ChecksumDetect][ZIP] element={chunk_label} method={frmethod_value}({method_name}) validated={first_match}")
                                                                else:
                                                                    print(f"[ChecksumDetect][ZIP] element={chunk_label} method={frmethod_value} unsupported")
                                                            except Exception as decomp_err:
                                                                print(f"[ChecksumDetect][ZIP] element={chunk_label} decompression failed: {decomp_err}")

                                                    # If decompression is disabled or failed, assume CRC-32 per ZIP spec
                                                    if first_match is None:
                                                        # NOTE: In ZIP files, frCrc is the CRC32 of the UNCOMPRESSED data.
                                                        # According to ZIP specification, CRC-32 is always used for file data.
                                                        first_match = "CRC-32"
                                                        if frmethod_value is not None:
                                                            method_name = self._get_compression_method_name(frmethod_value)
                                                            print(f"[ChecksumDetect][ZIP] element={chunk_label} method={frmethod_value}({method_name}) assumed=CRC-32 (ZIP spec)")
                                                        else:
                                                            print(f"[ChecksumDetect][ZIP] element={chunk_label} assumed=CRC-32 (ZIP spec: CRC over uncompressed data)")

                                                    # Aggregate under unified key "recordCrc"
                                                    if first_match:
                                                        existing = self.global_state.checksum_algorithms["by_chunk_type"].get(unified_key, [])
                                                        merged = sorted(set(existing + [first_match]))
                                                        self.global_state.checksum_algorithms["by_chunk_type"][unified_key] = merged

                                                    # Mark frCrc as processed for this file
                                                    seen_chunk_types_for_file.add("frCrc")
                                            else:  # deCrc in central directory
                                                # Use a unified key "dirEntryCrc" for all dirEntry elements
                                                unified_key = "dirEntryCrc"

                                                # Only process deCrc once per file
                                                if "deCrc" not in seen_chunk_types_for_file:
                                                    # Extract the dirEntry element identifier
                                                    direntry_element = attribute_keys[1] if len(attribute_keys) > 1 else "dirEntry"
                                                    chunk_label = direntry_element  # e.g., "dirEntry", "dirEntry_1"

                                                    # Mirror from recordCrc (all records use the same algorithm set)
                                                    record_algos = self.global_state.checksum_algorithms["by_chunk_type"].get("recordCrc")
                                                    if record_algos:
                                                        self.global_state.checksum_algorithms["by_chunk_type"][unified_key] = list(record_algos)
                                                        print(f"[ChecksumDetect][ZIP] element={chunk_label} mirrored to {unified_key}: {record_algos}")

                                                    # Mark deCrc as processed for this file
                                                    seen_chunk_types_for_file.add("deCrc")
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

    def _get_compression_method_name(self, method_value):
        """
        Get the name of a ZIP compression method.

        Args:
            method_value (int): The compression method value

        Returns:
            str: The name of the compression method
        """
        compression_methods = {
            0: "STORED",
            1: "SHRUNK",
            2: "REDUCED_1",
            3: "REDUCED_2",
            4: "REDUCED_3",
            5: "REDUCED_4",
            6: "IMPLODED",
            7: "RESERVED",
            8: "DEFLATE",
            9: "DEFLATE64",
            10: "PKWARE_IMPLODE",
            11: "RESERVED",
            12: "BZIP2",
            13: "RESERVED",
            14: "LZMA",
            15: "RESERVED",
            16: "RESERVED",
            17: "RESERVED",
            18: "IBM_TERSE",
            19: "IBM_LZ77",
            20: "ZSTD_DEPRECATED",
            93: "ZSTD",
            94: "MP3",
            95: "XZ",
            96: "JPEG",
            97: "WAVPACK",
            98: "PPMD",
            99: "AE-x"
        }
        return compression_methods.get(method_value, f"UNKNOWN_{method_value}")

    def _get_png_compression_method_name(self, method_value):
        """
        Get the name of a PNG compression method.

        Args:
            method_value (int): The compression method value

        Returns:
            str: The name of the compression method
        """
        compression_methods = {
            0: "DEFLATE"
        }
        return compression_methods.get(method_value, f"UNKNOWN_{method_value}")

    def _get_bmp_compression_method_name(self, method_value):
        """
        Get the name of a BMP compression method.

        Args:
            method_value (int): The compression method value

        Returns:
            str: The name of the compression method
        """
        compression_methods = {
            0: "BI_RGB",
            1: "BI_RLE8",
            2: "BI_RLE4",
            3: "BI_BITFIELDS",
            4: "BI_JPEG",
            5: "BI_PNG",
            6: "BI_ALPHABITFIELDS",
            11: "BI_CMYK",
            12: "BI_CMYKRLE8",
            13: "BI_CMYKRLE4"
        }
        return compression_methods.get(method_value, f"UNKNOWN_{method_value}")

    def _decompress_zip_data(self, compressed_data, method_value):
        """
        Decompress ZIP data based on compression method.

        Args:
            compressed_data (bytes): The compressed data
            method_value (int): The compression method value

        Returns:
            bytes or None: The uncompressed data, or None if unsupported/failed
        """
        try:
            if method_value == 0:
                # STORED (no compression)
                return compressed_data
            elif method_value == 8:
                # DEFLATE
                return zlib.decompress(compressed_data, -zlib.MAX_WBITS)
            elif method_value == 12:
                # BZIP2
                try:
                    import bz2
                    return bz2.decompress(compressed_data)
                except ImportError:
                    print(f"[ZIP] BZIP2 decompression not available (bz2 module not found)")
                    return None
            elif method_value == 14:
                # LZMA
                try:
                    import lzma
                    return lzma.decompress(compressed_data)
                except ImportError:
                    print(f"[ZIP] LZMA decompression not available (lzma module not found)")
                    return None
            else:
                # Unsupported compression method
                return None
        except Exception as e:
            print(f"[ZIP] Decompression failed for method {method_value}: {e}")
            return None


