"""
File parsing module for the learning constraints system.
Contains functions for parsing files and extracting byte ranges.
"""
import subprocess
from .config import Config, GlobalState
from .utils import clean_attribute_key, insert_nested_dict, extract_byte_values


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
                        self.global_state.blacklisted_attributes.add(blocked_key)
                        
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



