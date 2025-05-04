import os
import shutil
import subprocess
import collections
import json
import random

# Paths
file_type = "png"
OUTPUT_DIR = f"./learning-data/{file_type}-data/"
PASSED_DIR = os.path.join(OUTPUT_DIR, "passed/")
ABSTRACTED_DIR = os.path.join(OUTPUT_DIR, "abstracted/")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed/")
GIF_FUZZER_CMD = f"./{file_type}-fuzzer fuzz"
GIF_ABSTACT_CMD = f"./{file_type}-fuzzer abstract"
STATS_FILE_HEX = os.path.join(OUTPUT_DIR, f"{file_type}_parsed_values_hex.json")  # File for hex values
STATS_FILE_BASE10 = os.path.join(OUTPUT_DIR, f"{file_type}_parsed_values_base10.json")  # File for base 10 values
STATS_FILE_ASCII = os.path.join(OUTPUT_DIR, f"{file_type}_parsed_values_ascii.json")  # File for ASCII values

# Nested dictionaries to store extracted values in different formats
nested_values_hex = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
nested_values_base10 = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
nested_values_ascii = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

# Ensure output directories exist
os.makedirs(PASSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

# Validate GIFs
def is_valid_gif(file_path):
    try:
        result = subprocess.run(
            ["identify", "-verbose", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return "Elapsed" in result.stdout
    except Exception:
        return False
    
# Function to parse GIF and extract attributes with byte ranges
def parse_gif(file_path):
    byte_ranges = []
    try:
        result = subprocess.run(
            [f"./{file_type}-fuzzer", "parse", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )

        for line in result.stdout.splitlines():
            parts = line.split(",")
            if len(parts) == 3:
                start, end, attribute = int(parts[0]), int(parts[1]), parts[2]

                # Split attribute into hierarchical keys
                attribute_keys = attribute.split("~")

                # Skip if the attribute path has only two levels (e.g., "file~GifHeader")
                # if len(attribute_keys) <= 2:
                #     continue

                # Only consider attributes where byte size is <= 8
                if (end - start + 1) <= 8:
                    byte_ranges.append((start, end, attribute))

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return byte_ranges


def parse_gif_new(file_path):
    byte_ranges = []
    try:
        result = subprocess.run(
            [f"./{file_type}-fuzzer", "parse", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        # print("result")
        # print(result.stdout)

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

        # Step 2: Sort entries by start byte
        # Step 2: Sort by start ASCENDING and end DESCENDING
        entries.sort(key=lambda x: (x[0], -x[1]))


        for start, end, attribute, line in entries:
            # parts = line.split(",")
            # if len(parts) == 3:
            #     start, end, attribute = int(parts[0]), int(parts[1]), parts[2]

                # Split attribute into hierarchical keys
                # attribute_keys = attribute.split("~")

                # Skip if the attribute path has only two levels (e.g., "file~GifHeader")
                # if len(attribute_keys) <= 2:
                #     continue

                # Only consider attributes where byte size is <= 8
                # if (end - start + 1) <= 8:
                #     byte_ranges.append((start, end, attribute))

            if start == end and "_" in attribute:
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

    if "GifHeader" in originalKeys:
        pass

    keys = []
    for key in originalKeys:
        if "_" in key:
            # If the key contains an underscore, split it
            key = key.split("_")[0]
        keys.append(key)


    for key in keys[:-1]:  # Traverse and create intermediate levels
        if key not in current:
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], set):
            # If the current level is a set, convert it to a defaultdict
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], list):
            print(f"Error: Attempting to access a list with a string key '{key}'")
            raise TypeError(f"Invalid access: {key} is a list, not a dictionary.")
        current = current[key]

    last_key = keys[-1]  # Final key where value should be stored

    # Check if the current key is empty or null before replacing/assigning
    if last_key not in current or not current[last_key]:
        current[last_key] = []  # Initialize as a list if it doesn't exist or is empty

    if isinstance(current[last_key], collections.defaultdict) and not current[last_key]:
        # If it's a defaultdict, convert it to a set
        current[last_key] = set()
    elif isinstance(current[last_key], list):
        # Use a set to ensure uniqueness, then convert back to a list
        current[last_key] = list(set(current[last_key] + [value]))
    

# Function to extract byte values from GIF file and store in nested structures
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
                    # print(f"{file_path}: {attribute_keys} = {byte_values_hex} (hex) -> {byte_values_base10} (base 10) -> {byte_values_ascii} (ASCII)")
                    
                    # Insert into respective dictionaries
                    insert_nested_dict(nested_values_hex, attribute_keys, byte_values_hex)
                    insert_nested_dict(nested_values_base10, attribute_keys, byte_values_base10)
                    insert_nested_dict(nested_values_ascii, attribute_keys, byte_values_ascii)

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

def abstract_gif(file_path, byte_ranges):
    for start, end, attribute in byte_ranges:
        print(f"Abstracting {file_path} from {start} to {end}...")
        try:
            abstract_attempt = 1
            while abstract_attempt <= 10:
                try: 
                    outputfile = os.path.join(ABSTRACTED_DIR, f"abstracted.{file_type}")
                    # print(f"Abstracting {file_path} from {start} to {end}...")
                    # print(f"Output file: {outputfile}")
                    result = subprocess.run(
                        [f"./{file_type}-fuzzer", "abstract", "--targetfile", file_path, "--targetstart", str(start), "--targetend", str(end), outputfile ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )

                    if is_valid_gif(outputfile):
                        print(f"Valid Abstracted GIF")
                        abstract_byte_ranges = parse_gif_new(outputfile)
                        extract_bytes(outputfile, abstract_byte_ranges)
                        break
                    else:
                        print(f"Invalid Abstracted GIF")
                except Exception as e:
                    print(f"Error abstracting {file_path}: {e}")
                    
                abstract_attempt += 1
            # break
        except Exception as e:
            print(f"Error abstract main {file_path}: {e}")

        try:
            random_overwrite_attempt = 1
            while random_overwrite_attempt <= 10:
                outputfile = os.path.join(ABSTRACTED_DIR, f"overwrite.{file_type}")
                try: 
                    shutil.copy(file_path, outputfile)
                    overwrite_bytes(outputfile, start, end)

                    if is_valid_gif(outputfile):
                        print(f"Valid Overwrite GIF")
                        abstract_byte_ranges = parse_gif_new(outputfile)
                        extract_bytes(outputfile, abstract_byte_ranges)
                    else:
                        print(f"Invalid Overwrite GIF")
                except Exception as e:
                    print(f"Overwrite failed {file_path}: {e}")
                
                os.remove(outputfile)
                random_overwrite_attempt += 1
        except Exception as e:
            print(f"Error overwriting main {file_path}: {e}")

    return byte_ranges

valid_count = 0
attempt = 1  # Track total attempts to generate valid GIFs


# List all files in the directory
file_names = [f for f in os.listdir(PASSED_DIR) if os.path.isfile(os.path.join(PASSED_DIR, f))]

# Print the file names
for name in file_names:
    gif_path = os.path.join(PASSED_DIR, f"{name}")
    byte_ranges = parse_gif_new(gif_path)
    abstract_gif(gif_path, byte_ranges)


# Convert sets to lists for JSON serialization
def convert_sets_to_lists(obj):
    """ Recursively converts sets to lists in a nested dictionary. """
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        return list(obj)
    return obj

# Convert nested dictionaries to final stats
final_stats_hex = convert_sets_to_lists(nested_values_hex)
final_stats_base10 = convert_sets_to_lists(nested_values_base10)
final_stats_ascii = convert_sets_to_lists(nested_values_ascii)

# Save results to JSON files
with open(STATS_FILE_HEX, "w") as f:
    json.dump(final_stats_hex, f, indent=4)

with open(STATS_FILE_BASE10, "w") as f:
    json.dump(final_stats_base10, f, indent=4)

with open(STATS_FILE_ASCII, "w") as f:
    json.dump(final_stats_ascii, f, indent=4)

print("Processing complete!")
