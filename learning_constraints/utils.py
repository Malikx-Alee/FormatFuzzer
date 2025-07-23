"""
Utility functions for the learning constraints system.
Contains helper functions used across multiple modules.
"""
import collections
import random
import os


def convert_sets_to_lists(obj):
    """
    Recursively converts sets to lists in a nested dictionary.
    
    Args:
        obj: The object to convert (dict, set, list, or other)
        
    Returns:
        The converted object with sets replaced by lists
    """
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    elif isinstance(obj, collections.defaultdict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    return obj


def clean_attribute_key(attribute):
    """
    Extracts the last part after '~' and removes trailing _<number> if present.
    
    Args:
        attribute (str): The attribute string to clean
        
    Returns:
        str: The cleaned attribute key
    """
    key = attribute.split("~")[-1]
    if "_" in key:
        parts = key.split("_")
        if len(parts) > 1 and parts[1].isdigit():
            key = parts[0]
    return key


def insert_nested_dict(root, original_keys, value):
    """
    Recursively inserts values into a nested dictionary with special handling for hierarchical arrays.
    
    Args:
        root: The root dictionary to insert into
        original_keys (list): List of keys representing the path
        value: The value to insert
    """
    current = root

    # Clean keys by removing array indices if present
    keys = []
    for key in original_keys:
        if "_" in key:
            # If the key contains an underscore, split it
            parts = key.split("_")
            # Check if the second part is a number
            if parts[1].isdigit():
                # If it's a number, only keep the first part
                key = parts[0]
            # If it's not a number, keep the whole key
        keys.append(key)

    # Navigate through all keys except the last one
    for key in keys[:-1]:  # Traverse and create intermediate levels
        if key not in current:
            # Create new nested defaultdict if key doesn't exist
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], set):
            # If the current level is a set, convert it to a defaultdict for deeper nesting
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], list):
            current[key] = collections.defaultdict(lambda: set())
        # Move to the next level
        current = current[key]

    last_key = keys[-1]  # Final key where value should be stored

    # Handle the final key insertion
    if last_key not in current:
        # Initialize as a set if it doesn't exist
        current[last_key] = set()
    
    if isinstance(current[last_key], set):
        # If it's a set, add the value
        current[last_key].add(value)


def overwrite_bytes_randomly(file_path, start, end):
    """
    Randomly overwrites bytes in a file between the given start and end positions.

    Args:
        file_path (str): Path to the file to modify
        start (int): Start position (inclusive) of the range to overwrite
        end (int): End position (inclusive) of the range to overwrite
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If start > end or positions are out of bounds
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if start > end:
        raise ValueError("Start position must be less than or equal to the end position.")

    try:
        with open(file_path, "r+b") as f:  # Open file in read/write binary mode
            file_size = os.path.getsize(file_path)
            
            if start < 0 or end >= file_size:
                raise ValueError(f"Start and end positions must be within the file size (0 to {file_size - 1}).")

            # Seek to the start position
            f.seek(start)

            # Overwrite bytes with random values
            for position in range(start, end + 1):
                random_byte = random.randint(0, 255)  # Generate a random byte (0-255)
                f.write(bytes([random_byte]))  # Write the random byte

            print(f"Successfully overwrote bytes from position {start} to {end} in {file_path}.")

    except Exception as e:
        print(f"Error overwriting bytes in {file_path}: {e}")
        raise


def extract_byte_values(file_data, start, end):
    """
    Extract byte values from file data and convert to different formats.
    
    Args:
        file_data (bytes): The file data
        start (int): Start position
        end (int): End position
        
    Returns:
        dict: Dictionary containing hex, base10, and ascii representations
    """
    if end >= len(file_data):
        raise ValueError(f"End position {end} exceeds file size {len(file_data)}")
    
    # Extract the byte range
    byte_range = file_data[start:end + 1]
    
    return {
        'hex': byte_range.hex(),
        'base10': "".join(str(byte) for byte in byte_range),
        'ascii': "".join(chr(byte) if 32 <= byte <= 126 else '.' for byte in byte_range)
    }


def validate_byte_range(start, end, file_size, max_size=8):
    """
    Validate that a byte range is within acceptable bounds.
    
    Args:
        start (int): Start position
        end (int): End position
        file_size (int): Size of the file
        max_size (int): Maximum allowed range size
        
    Returns:
        bool: True if valid, False otherwise
    """
    if start < 0 or end >= file_size:
        return False
    if start > end:
        return False
    if end - start > max_size:
        return False
    return True
