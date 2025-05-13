import os
import json
import collections

# Directory containing the JSON files
RESULTS_DIR = "./learning-data/results/original"
TRANSFORMED_RESULTS_DIR = "./learning-data/results/transformed/"


def transform_json(json_data):
    """Transform JSON data: if a key has more than 10 values, replace with message."""
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, list) and len(value) > 10:
                json_data[key] = "Had more than 10 values"
            elif isinstance(value, (dict, list)):
                transform_json(value)
    elif isinstance(json_data, list):
        for i, item in enumerate(json_data):
            if isinstance(item, (dict, list)):
                transform_json(item)
    return json_data

# Process all JSON files in the directory
for filename in os.listdir(RESULTS_DIR):
    if filename.endswith(".json"):
        file_path = os.path.join(RESULTS_DIR, filename)
        output_path = os.path.join(TRANSFORMED_RESULTS_DIR, f"{os.path.splitext(filename)[0]}_transformed.json")
        
        try:
            # Read the JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Transform the data
            transformed_data = transform_json(data)
            
            # Write the transformed data to a new file
            with open(output_path, 'w') as f:
                json.dump(transformed_data, f, indent=4)
                
            print(f"Transformed {filename} -> {os.path.basename(output_path)}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Transformation complete!")