import os
import shutil
import subprocess
import collections
import json
import random

# Paths
# file_type = "avi"
file_type = "bmp"
# file_type = "gif"
# file_type = "jpg"
# file_type = "png"
# file_type = "midi"
# file_type = "pcap"
# file_type = "wav"
# file_type = "mp4"
# file_type = "zip"
DATA_DIR = f"./learning-data/{file_type}-data/"
RESULTS_OUTPUT_DIR = f"./learning-data/results/original"
PASSED_DIR = os.path.join(DATA_DIR, "passed/")
ABSTRACTED_DIR = os.path.join(DATA_DIR, "abstracted/")
ABSTRACTED_SPECIAL_DIR = os.path.join(DATA_DIR, "abstracted_special/")
FAILED_DIR = os.path.join(DATA_DIR, "failed/")
STATS_FILE_HEX = os.path.join(RESULTS_OUTPUT_DIR, f"{file_type}_parsed_values_hex.json")  # File for {file_type} hex values
# STATS_FILE_BASE10 = os.path.join(RESULTS_OUTPUT_DIR, f"{file_type}_parsed_values_base10.json")  # File for {file_type} base 10 values
# STATS_FILE_ASCII = os.path.join(RESULTS_OUTPUT_DIR, f"{file_type}_parsed_values_ascii.json")  # File for {file_type} ASCII values

# Nested dictionaries to store extracted values in different formats for {file_type}
nested_values_hex = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
# nested_values_base10 = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
# nested_values_ascii = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

# Blacklist for attributes that have been found to be larger than 8 bytes
BLACKLISTED_ATTRIBUTES = set()

# Output Counts
VALID_ABSTRACTIONS_COUNT = 0
VALID_ABSTRACTIONS_SPECIAL_COUNT = 0
VALID_OVERWRITES_COUNT = 0

# Ensure output directories exist for {file_type}
os.makedirs(PASSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)
os.makedirs(ABSTRACTED_DIR, exist_ok=True)
os.makedirs(ABSTRACTED_SPECIAL_DIR, exist_ok=True)

# Convert sets to lists for JSON serialization
def convert_sets_to_lists(obj):
    """ Recursively converts sets to lists in a nested dictionary. """
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
    """Extracts the last part after '~' and removes trailing _<number> if present."""
    key = attribute.split("~")[-1]
    if "_" in key:
        parts = key.split("_")
        if len(parts) > 1 and parts[1].isdigit():
            key = parts[0]
    return key

# Validate {file_type} files
def is_valid_file(file_path):
    """
    Validates a file based on its type.

    :param file_path: Path to the file to validate.
    :param file_type: The type of the file (e.g., 'gif', 'zip', 'mp3').
    :return: True if the file is valid, False otherwise.
    """
    try:
        if file_type in ["gif", "jpg", "png", "bmp"]:
            # Use ImageMagick's identify command for image files
            result = subprocess.run(
                ["identify", "-verbose", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "Elapsed" in result.stdout

        elif file_type == "zip":
            # Validate zip files by checking if the file can be opened
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                return zip_ref.testzip() is None  # Returns None if no errors are found

        elif file_type in ["mp3", "wav"]:
            # Validate audio files using ffprobe (part of FFmpeg)
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "format_name" in result.stdout

        elif file_type == "mp4":
            # Validate video files using ffprobe
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "format_name" in result.stdout
        
        elif file_type == "avi":
            # Validate AVI files using ffprobe
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "format_name=avi" in result.stdout  # Check if the format is AVI

        elif file_type == "pcap":
            # Validate pcap files using tshark
            result = subprocess.run(
                ["tshark", "-r", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return result.returncode == 0

        elif file_type == "midi":
            # Validate MIDI files using timidity (matching the checker script)
            with open(file_path, 'rb') as f:
                result = subprocess.run(
                    ["timidity", "-", "-Ol", "-o", "/dev/null"],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            # Check that there are no error messages starting with "-:"
            return not any(line.startswith("-:") for line in result.stdout.splitlines())

        else:
            print(f"Validation for file type '{file_type}' is not implemented.")
            return False

    except Exception as e:
        print(f"Error validating {file_type} file: {e}")
        return False

def remove_nested_key_by_label(nested_dict, label):
    """
    Remove a key from nested_dict following the path described by label.
    The label is a '~'-separated path, and the last part is the key to remove.
    """
    keys = label.split("~")
    d = nested_dict
    for k in keys[:-1]:
        if k in d and isinstance(d[k], dict):
            d = d[k]
        else:
            return  # Path does not exist, nothing to remove
    d.pop(keys[-1], None)  # Remove the last key if present


# Function to parse {file_type} files and extract attributes with byte ranges
def parse_file_new(file_path):
    byte_ranges = []
    try:
        result = subprocess.run(
            [f"./{file_type}-fuzzer", "parse", file_path],
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
            start, end, label = int(parts[0]), int(parts[1]), parts[2]
            entries.append((start, end, label, line))
            
            # Add to blacklist if size > 8 bytes
            if end - start > 8:
                blocked_key = clean_attribute_key(label)
                BLACKLISTED_ATTRIBUTES.add(blocked_key)
                # Remove from nested_values_hex using the label path
                remove_nested_key_by_label(nested_values_hex, label)

                

        # Step 2: Sort entries by start byte
        # Step 2: Sort by start ASCENDING and end DESCENDING
        entries.sort(key=lambda x: (x[0], -x[1]))

        for start, end, attribute, line in entries:
            if start == end and "_" in attribute:
                continue
            # Skip if attribute is in blacklist
            if clean_attribute_key(attribute) in BLACKLISTED_ATTRIBUTES:
                continue
            if (start > current_parent_end or end < current_parent_end) and end - start <= 8:
                # No overlap with previous parent
                byte_ranges.append((start, end, attribute))
                current_parent_end = end
            else:
                # This entry is inside an earlier parent, so skip
                continue

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return byte_ranges


# Function to insert values into a nested dictionary with special handling for arrays
def insert_nested_dict(root, originalKeys, value):
    """ Recursively inserts values into a nested dictionary with special handling for hierarchical arrays. """
    current = root

    # Clean keys by removing array indices if present
    keys = []
    for key in originalKeys:
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
            # if not current[key]:  # Check if list is empty
            #     current[key] = collections.defaultdict(lambda: set())  # Convert to dict with set
            # else:
            #     print(f"Error: Attempting to access a list with a string key '{key}'")
        # Move to the next level
        current = current[key]

    last_key = keys[-1]  # Final key where value should be stored

    # Handle the final key insertion
    if last_key not in current:
        # Initialize as a list if it doesn't exist
        current[last_key] = set()
    # if isinstance(current[last_key], collections.defaultdict) and not current[last_key]:
    #     # If it's an empty defaultdict, convert it to a list with the value
    #     current[last_key] = [value]
    # if isinstance(current[last_key], list):
    #     # If it's already a list, add the value ensuring uniqueness
    #     if value not in current[last_key]:
    #         current[last_key].append(value)
    if isinstance(current[last_key], set):
        # If it's a set, add the value
        current[last_key].add(value)
    # else:
    #     # For any other case, convert to list and add
    #     current[last_key] = [current[last_key], value]


# Function to extract byte values from {file_type} file and store in nested structures
def extract_bytes(file_path, byte_ranges):
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()  # Read entire file into memory

            for start, end, attribute in byte_ranges:
                if end < len(file_data):  # Ensure within file size
                    # Extract the byte range
                    byte_range = file_data[start:end + 1]
                    
                    # Convert to hex, base 10, and ASCII
                    byte_values_hex = byte_range.hex()  # Hex representation
                    byte_values_base10 = [str(byte) for byte in byte_range]  # Base 10 values
                    byte_values_base10 = "".join(byte_values_base10)
                    byte_values_ascii = [chr(byte) if 32 <= byte <= 126 else '.' for byte in byte_range]  # ASCII values (non-printable as '.')
                    byte_values_ascii = "".join(byte_values_ascii)

                    attribute_keys = attribute.split("~")  # Split into hierarchical keys
                    
                    # Insert into respective dictionaries
                    insert_nested_dict(nested_values_hex, attribute_keys, byte_values_hex)
                    # insert_nested_dict(nested_values_base10, attribute_keys, byte_values_base10)
                    # insert_nested_dict(nested_values_ascii, attribute_keys, byte_values_ascii)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")


def overwrite_bytes(file_path, start, end):
    """
    Randomly overwrites bytes in a file between the given start and end positions.

    :param file_path: Path to the file to modify.
    :param start: Start position (inclusive) of the range to overwrite.
    :param end: End position (inclusive) of the range to overwrite.
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

def abstract_file(file_path, byte_ranges):
    global VALID_ABSTRACTIONS_COUNT, VALID_ABSTRACTIONS_SPECIAL_COUNT, VALID_OVERWRITES_COUNT
    
    # Get original attributes before abstraction
    original_attributes = set()
    for _, _, attribute in byte_ranges:
        original_attributes.add(clean_attribute_key(attribute))
    
    
    for start, end, attribute in byte_ranges:
        print(f"Abstracting {file_path} from {start} to {end}...")
        try:
            abstract_attempt = 1
            while abstract_attempt <= 10:
                try: 
                    outputfile = os.path.join(ABSTRACTED_DIR, f"abstracted.{file_type}")
                    result = subprocess.run(
                        [f"./{file_type}-fuzzer", "abstract", "--targetfile", file_path, "--targetstart", str(start), "--targetend", str(end), outputfile ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )

                    if is_valid_file(outputfile):
                        print(f"Valid Abstracted {file_type}")
                        abstract_byte_ranges = parse_file_new(outputfile)
                        
                        # Check for new attributes
                        new_attributes_found = False
                        for _, _, new_attr in abstract_byte_ranges:
                            cleaned_attr = clean_attribute_key(new_attr)
                            if cleaned_attr not in original_attributes:
                                new_attributes_found = True
                                break
                        
                        # If new attributes found, save to special directory
                        if new_attributes_found:
                            special_file = os.path.join(ABSTRACTED_SPECIAL_DIR, f"special_{new_attr}_{start}_{end}.{file_type}")
                            shutil.copy(outputfile, special_file)
                            VALID_ABSTRACTIONS_SPECIAL_COUNT += 1
                            print(f"New attributes found! Saved to {special_file}")
                        
                        extract_bytes(outputfile, abstract_byte_ranges)
                        VALID_ABSTRACTIONS_COUNT += 1
                        break
                    else:
                        print(f"Invalid Abstracted {file_type}")
                except Exception as e:
                    print(f"Error abstracting {file_path}: {e}")
                    
                abstract_attempt += 1
        except Exception as e:
            print(f"Error abstract main {file_path}: {e}")

        try:
            random_overwrite_attempt = 1
            while random_overwrite_attempt <= 10:
                outputfile = os.path.join(ABSTRACTED_DIR, f"overwrite.{file_type}")
                try: 
                    shutil.copy(file_path, outputfile)
                    overwrite_bytes(outputfile, start, end)

                    if is_valid_file(outputfile):
                        print(f"Valid Overwrite {file_type}")
                        abstract_byte_ranges = parse_file_new(outputfile)
                        
                        # Check for new attributes
                        new_attributes_found = False
                        for _, _, new_attr in abstract_byte_ranges:
                            cleaned_attr = clean_attribute_key(new_attr)
                            if cleaned_attr not in original_attributes:
                                new_attributes_found = True
                                break
                        
                        # If new attributes found, save to special directory
                        if new_attributes_found:
                            special_file = os.path.join(ABSTRACTED_SPECIAL_DIR, f"special_overwrite_{new_attr}_{start}_{end}.{file_type}")
                            shutil.copy(outputfile, special_file)
                            print(f"New attributes found in overwrite! Saved to {special_file}")
                            
                        extract_bytes(outputfile, abstract_byte_ranges)
                        VALID_OVERWRITES_COUNT += 1
                    else:
                        print(f"Invalid Overwrite {file_type}")
                except Exception as e:
                    print(f"Overwrite failed {file_path}: {e}")
                
                os.remove(outputfile)
                random_overwrite_attempt += 1
        except Exception as e:
            print(f"Error overwriting main {file_path}: {e}")

    return byte_ranges


def main():
    # List all files in the directory
    file_names = [f for f in os.listdir(PASSED_DIR) if os.path.isfile(os.path.join(PASSED_DIR, f))]

    # Print the file names
    for name in file_names:
        file_path = os.path.join(PASSED_DIR, f"{name}")
        byte_ranges = parse_file_new(file_path)
        abstract_file(file_path, byte_ranges)


    # List all files in the directory
    file_names = [f for f in os.listdir(ABSTRACTED_SPECIAL_DIR) if os.path.isfile(os.path.join(ABSTRACTED_SPECIAL_DIR, f))]

    # Print the file names
    for name in file_names:
        file_path = os.path.join(ABSTRACTED_SPECIAL_DIR, f"{name}")
        byte_ranges = parse_file_new(file_path)
        abstract_file(file_path, byte_ranges)

    # Convert nested dictionaries to final stats
    final_stats_hex = convert_sets_to_lists(nested_values_hex)
    # final_stats_base10 = convert_sets_to_lists(nested_values_base10)
    # final_stats_ascii = convert_sets_to_lists(nested_values_ascii)

    # Save results to JSON files
    with open(STATS_FILE_HEX, "w") as f:
        json.dump(final_stats_hex, f, indent=4)

    # with open(STATS_FILE_BASE10, "w") as f:
    #     json.dump(final_stats_base10, f, indent=4)

    # with open(STATS_FILE_ASCII, "w") as f:
    #     json.dump(final_stats_ascii, f, indent=4)

    print("Processing complete!")
    print(f"Valid Abstractions: {VALID_ABSTRACTIONS_COUNT}")
    print(f"VALID_ABSTRACTIONS_SPECIAL_COUNT: {VALID_ABSTRACTIONS_SPECIAL_COUNT}")
    print(f"Valid Overwrites: {VALID_OVERWRITES_COUNT}")


if __name__ == "__main__":
    main()