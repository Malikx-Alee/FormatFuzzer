"""
Result transformation module for the learning constraints system.
Contains functions for transforming and flattening JSON results.
"""
import os
import json
import logging
from .config import Config


class ResultTransformer:
    """Result transformer class for processing and flattening JSON results."""
    
    def __init__(self):
        """Initialize the result transformer."""
        self.logger = logging.getLogger(__name__)
    
    def flatten_json(self, data, out=None):
        """
        Flatten nested JSON, use last nested key, merge duplicate keys, keep unique values, and handle >10 values.
        
        Args:
            data: The JSON data to flatten
            out (dict, optional): Output dictionary to accumulate results
            
        Returns:
            dict: Flattened JSON data
        """
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
        
        _flatten(data)
        
        # Post-process: if any key has more than 10 values, set to "More than 10 values"
        for k in list(out.keys()):
            if isinstance(out[k], list) and len(out[k]) > 10:
                out[k] = "More than 10 values"
        
        return out
    
    def transform_json_file(self, input_path, output_path):
        """
        Transform a single JSON file by flattening its structure.
        
        Args:
            input_path (str): Path to the input JSON file
            output_path (str): Path to save the transformed JSON file
            
        Returns:
            bool: True if transformation was successful, False otherwise
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Flatten and merge
            flattened_data = self.flatten_json(data)
            
            # Write the flattened data to a new file
            with open(output_path, 'w') as f:
                json.dump(flattened_data, f, indent=4)
            
            self.logger.info(f"Transformed {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error transforming {input_path}: {e}")
            return False
    
    def transform_results_directory(self, results_dir=None, output_suffix="_flattened"):
        """
        Transform the hex values JSON file in the results directory.

        Args:
            results_dir (str, optional): Directory containing JSON files. If None, uses Config.RESULTS_OUTPUT_DIR
            output_suffix (str): Suffix to add to transformed file names

        Returns:
            tuple: (successful_count, total_count)
        """
        if results_dir is None:
            results_dir = Config.RESULTS_OUTPUT_DIR

        if not os.path.exists(results_dir):
            self.logger.warning(f"Results directory does not exist: {results_dir}")
            return 0, 0

        # Only process the hex values file
        hex_file = Config.STATS_FILE_HEX

        if not os.path.exists(hex_file):
            self.logger.warning(f"Hex values file does not exist: {hex_file}")
            return 0, 0

        # Transform the hex values file
        filename = os.path.basename(hex_file)
        output_filename = f"{os.path.splitext(filename)[0]}{output_suffix}.json"
        output_path = os.path.join(results_dir, output_filename)

        successful_count = 0
        if self.transform_json_file(hex_file, output_path):
            successful_count = 1

        self.logger.info(f"Transformation complete! Processed {successful_count}/1 hex values file")
        return successful_count, 1
    
    def transform_specific_files(self, file_patterns=None, output_suffix="_flattened"):
        """
        Transform specific JSON files based on patterns.

        Args:
            file_patterns (list, optional): List of file patterns to transform.
                                          If None, transforms only the hex values file
            output_suffix (str): Suffix to add to transformed file names

        Returns:
            tuple: (successful_count, total_count)
        """
        if file_patterns is None:
            file_patterns = [
                Config.STATS_FILE_HEX
            ]
        
        successful_count = 0
        total_count = 0
        
        for file_path in file_patterns:
            if os.path.exists(file_path):
                total_count += 1
                output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}{output_suffix}.json"
                output_path = os.path.join(os.path.dirname(file_path), output_filename)
                
                if self.transform_json_file(file_path, output_path):
                    successful_count += 1
            else:
                self.logger.warning(f"File not found: {file_path}")
        
        return successful_count, total_count



