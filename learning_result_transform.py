import os
import json

RESULTS_DIR = "./learning-data/results/original"
TRANSFORMED_RESULTS_DIR = "./learning-data/results/flattened/"
os.makedirs(TRANSFORMED_RESULTS_DIR, exist_ok=True)

def flatten_json(y, out=None):
    """Flatten nested JSON, use last nested key, merge duplicate keys, keep unique values, and handle >10 values."""
    if out is None:
        out = {}
    def _flatten(obj, prefix=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _flatten(v, k)  # Only use the last key
        elif isinstance(obj, list):
            for item in obj:
                _flatten(item, prefix)
        else:
            # Merge duplicate keys and keep unique values
            if prefix in out:
                if isinstance(out[prefix], list):
                    if obj not in out[prefix]:
                        out[prefix].append(obj)
                else:
                    if out[prefix] != obj:
                        out[prefix] = [out[prefix], obj]
            else:
                out[prefix] = obj
    _flatten(y)
    # Post-process: if any key has more than 10 values, set to "More than 10 values"
    for k in list(out.keys()):
        if isinstance(out[k], list) and len(out[k]) > 10:
            out[k] = "More than 10 values"
    return out

# Process all JSON files in the directory
for filename in os.listdir(RESULTS_DIR):
    if filename.endswith(".json"):
        file_path = os.path.join(RESULTS_DIR, filename)
        output_path = os.path.join(TRANSFORMED_RESULTS_DIR, f"{os.path.splitext(filename)[0]}_flattened.json")
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Flatten and merge
            flattened_data = flatten_json(data)
            
            # Write the flattened data to a new file
            with open(output_path, 'w') as f:
                json.dump(flattened_data, f, indent=4)
                
            print(f"Flattened {filename} -> {os.path.basename(output_path)}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Flattening complete!")