"""
File parsing module for the learning constraints system.
Contains functions for parsing files and extracting byte ranges.
"""
import subprocess
import re
import json
import collections
from .config import Config, GlobalState
from .utils import clean_attribute_key, insert_nested_dict, extract_byte_values, remove_attribute_from_nested_dict


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



