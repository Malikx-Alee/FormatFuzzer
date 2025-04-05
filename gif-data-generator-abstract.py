import os
import shutil
import subprocess
import collections
import json

# Paths
OUTPUT_DIR = "./gif_data/"
PASSED_DIR = os.path.join(OUTPUT_DIR, "passed/")
ABSTRACTED_DIR = os.path.join(OUTPUT_DIR, "abstracted/")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed/")
GIF_FUZZER_CMD = "./gif-fuzzer fuzz"
GIF_ABSTACT_CMD = "./gif-fuzzer abstract"
STATS_FILE_HEX = os.path.join(OUTPUT_DIR, "gif_parsed_stats_hex.json")  # File for hex values
STATS_FILE_BASE10 = os.path.join(OUTPUT_DIR, "gif_parsed_stats_base10.json")  # File for base 10 values
STATS_FILE_ASCII = os.path.join(OUTPUT_DIR, "gif_parsed_stats_ascii.json")  # File for ASCII values

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
            ["./gif-fuzzer", "parse", file_path],
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
                if len(attribute_keys) <= 2:
                    continue

                # Only consider attributes where byte size is <= 8
                if (end - start + 1) <= 8:
                    byte_ranges.append((start, end, attribute))

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return byte_ranges

def parse_gif_reduced(file_path):
    byte_ranges = []
    try:
        result = subprocess.run(
            ["./gif-fuzzer", "parse", file_path],
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
                if (end - start + 1) >= 6:
                    byte_ranges.append((start, end, attribute))

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    return byte_ranges


# Function to insert values into a nested dictionary with special handling for arrays
def insert_nested_dict(root, keys, value):
    """ Recursively inserts values into a nested dictionary with special handling for hierarchical arrays. """
    current = root
    for key in keys[:-1]:  # Traverse and create intermediate levels
        if key not in current:
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], set):
            # If the current level is a set, convert it to a defaultdict
            current[key] = collections.defaultdict(lambda: set())
        current = current[key]

    last_key = keys[-1]  # Final key where value should be stored

    # Special handling for hierarchical keys like rgb~R, rgb~R_1, etc.
    if "_" in last_key:
        base_key, index = last_key.rsplit("_", 1)
        if base_key not in current:
            current[base_key] = []
        # Ensure the list is large enough to accommodate the index
        while len(current[base_key]) <= int(index):
            current[base_key].append(None)
        if current[base_key][int(index)] != value:  # Ensure uniqueness
            current[base_key][int(index)] = value
    else:
        if isinstance(current[last_key], collections.defaultdict):
            # If it's a defaultdict, convert it to a set
            current[last_key] = set()
        if isinstance(current[last_key], list):
            if value not in current[last_key]:  # Ensure uniqueness
                current[last_key].append(value)
        else:
            current[last_key] = [value] if current[last_key] != value else current[last_key]


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
                    print(f"{file_path}: {attribute_keys} = {byte_values_hex} (hex) -> {byte_values_base10} (base 10) -> {byte_values_ascii} (ASCII)")
                    
                    # Insert into respective dictionaries
                    insert_nested_dict(nested_values_hex, attribute_keys, byte_values_hex)
                    insert_nested_dict(nested_values_base10, attribute_keys, byte_values_base10)
                    insert_nested_dict(nested_values_ascii, attribute_keys, byte_values_ascii)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")


def abstract_gif(file_path, byte_ranges):
    for start, end, attribute in byte_ranges:
        try:
            abstract_attempt = 1
            while abstract_attempt <= 1:
                try: 
                    outputfile = os.path.join(ABSTRACTED_DIR, "abstracted.gif")
                    # print(f"Abstracting {file_path} from {start} to {end}...")
                    # print(f"Output file: {outputfile}")
                    result = subprocess.run(
                        ["./gif-fuzzer", "abstract", "--targetfile", file_path, "--targetstart", str(start), "--targetend", str(end), outputfile ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        text=True
                    )

                    if is_valid_gif(outputfile):
                        print(f"Valid Abstracted GIF")
                        abstract_byte_ranges = parse_gif(outputfile)
                        extract_bytes(outputfile, abstract_byte_ranges)
                    else:
                        print(f"Invalid Abstracted GIF")
                except Exception as e:
                    print(f"Error abstracting {file_path}: {e}")
                    
                abstract_attempt += 1
            # break
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    return byte_ranges

valid_count = 0
attempt = 1  # Track total attempts to generate valid GIFs

while valid_count <= 2:
    # gif_path = os.path.join(OUTPUT_DIR, f"out{attempt}.gif")
    gif_path = os.path.join(PASSED_DIR, f"out.gif")
    # cmd = f"{GIF_FUZZER_CMD} {gif_path}"
    # subprocess.run(cmd, shell=True, check=True)
    # print(f"Generated: {gif_path}")

    byte_ranges = parse_gif_reduced(gif_path)
    abstract_gif(gif_path, byte_ranges)
    
    # if is_valid_gif(gif_path):
    #     shutil.move(gif_path, os.path.join(PASSED_DIR, f"out{valid_count + 1}.gif"))
    #     print(f"Valid GIF: Moved to {PASSED_DIR} as out{valid_count + 1}.gif")
    #     valid_count += 1
    # else:
    #     shutil.move(gif_path, os.path.join(FAILED_DIR, f"out{attempt}.gif"))
    #     print(f"Invalid GIF: Moved to {FAILED_DIR}")
    valid_count += 1
    attempt += 1

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
