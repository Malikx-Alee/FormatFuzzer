import os
import subprocess
import json
import collections

# Paths
OUTPUT_DIR = "./gif_data/"
PASSED_DIR = os.path.join(OUTPUT_DIR, "passed/")
GIF_FUZZER_CMD = "./gif-fuzzer"
STATS_FILE_HEX = os.path.join(OUTPUT_DIR, "gif_parsed_stats_hex.json")  # File for hex values
STATS_FILE_BASE10 = os.path.join(OUTPUT_DIR, "gif_parsed_stats_base10.json")  # File for base 10 values
STATS_FILE_ASCII = os.path.join(OUTPUT_DIR, "gif_parsed_stats_ascii.json")  # File for ASCII values

# Nested dictionaries to store extracted values in different formats
nested_values_hex = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
nested_values_base10 = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
nested_values_ascii = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

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

# Function to insert values into a nested dictionary
def insert_nested_dict(root, keys, value):
    """ Recursively inserts values into a nested dictionary. """
    current = root
    for key in keys[:-1]:  # Traverse and create intermediate levels
        if key not in current:
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], set):
            # If the current level is a set, convert it to a defaultdict
            current[key] = collections.defaultdict(lambda: set())
        current = current[key]

    last_key = keys[-1]  # Final key where value should be stored

    # Ensure it's a set to allow for unique values
    if isinstance(current[last_key], collections.defaultdict):
        # If it's a defaultdict, convert it to a set
        current[last_key] = set()
    current[last_key].add(value)

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

# Iterate over all passed GIFs and extract data
for filename in os.listdir(PASSED_DIR):
    if filename.endswith("2.gif"):
        gif_path = os.path.join(PASSED_DIR, filename)
        byte_ranges = parse_gif(gif_path)
        extract_bytes(gif_path, byte_ranges)

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

print(f"Parsing complete! Files saved:")
print(f"- Hex values: {STATS_FILE_HEX}")
print(f"- Base 10 values: {STATS_FILE_BASE10}")
print(f"- ASCII values: {STATS_FILE_ASCII}")