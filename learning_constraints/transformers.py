"""
Result transformation module for the learning constraints system.
Flattens the nested result JSON into the key/value shape downstream tools read.

Two flattenings are produced:

* ``*_flattened.json``       keyed by cleaned *leaf name* (``width``), values pooled across all
                              paths that end in that name (historical shape);
* ``*_flattened_paths.json`` keyed by cleaned *full path* (``file~chunk~ihdr~width``), so fields
                              that share a name under different parents stay apart.
"""
import os
import json
import logging
from .config import Config
from .utils import strip_index


class ResultTransformer:
    """Result transformer class for processing and flattening JSON results."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def flatten_json(self, data, out=None, key_mode="leaf"):
        """
        Flatten nested JSON into ``{key: value | [values] | marker}``.

        Args:
            data: nested dict with lists at the leaves
            out: optional dict to accumulate into
            key_mode: ``"leaf"`` (cleaned last key) or ``"path"`` (cleaned full path)
        """
        if out is None:
            out = {}

        def _add(key, value):
            if key in out:
                if isinstance(out[key], list):
                    if value not in out[key]:
                        out[key].append(value)
                elif out[key] != value:
                    out[key] = [out[key], value]
            else:
                out[key] = value

        def _flatten(obj, path):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    k = strip_index(k)
                    _flatten(v, f"{path}~{k}" if path else k)
            elif isinstance(obj, list):
                for item in obj:
                    _flatten(item, path)
            else:
                key = path if key_mode == "path" else path.split("~")[-1]
                _add(key, obj)

        _flatten(data, "")

        limit = Config.FLATTEN_MAX_VALUES
        for k in list(out.keys()):
            if isinstance(out[k], list) and len(out[k]) > limit:
                out[k] = f"More than {limit} values"

        return out

    def transform_json_file(self, input_path, output_path, key_mode="leaf"):
        """Flatten one result JSON file into ``output_path``."""
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)

            checksum_algorithms = data.pop("checksum_algorithms", None)
            flattened_data = self.flatten_json(data, key_mode=key_mode)

            if checksum_algorithms:
                for chunk_type, algorithms in checksum_algorithms.get("by_chunk_type", {}).items():
                    if isinstance(algorithms, list) and len(algorithms) == 1:
                        flattened_data[chunk_type] = algorithms[0]
                    else:
                        flattened_data[chunk_type] = algorithms
                compression_methods = checksum_algorithms.get("compression_methods") or {}
                if compression_methods:
                    flattened_data["compressionMethods"] = sorted(set(compression_methods.values()))
                    flattened_data["compressionMethodsValues"] = sorted(int(k) for k in compression_methods.keys())

            with open(output_path, 'w') as f:
                json.dump(flattened_data, f, indent=4)

            self.logger.info(f"Transformed {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            return True
        except Exception as e:
            self.logger.error(f"Error transforming {input_path}: {e}")
            return False

    def transform_results_directory(self, results_dir=None, output_suffix="_flattened"):
        """
        Flatten the hex values file in the results directory (leaf-keyed and path-keyed).

        Returns:
            tuple: (successful_count, total_count)
        """
        if results_dir is None:
            results_dir = Config.CURRENT_RESULTS_DIR

        if results_dir is None or not os.path.exists(results_dir):
            self.logger.warning(f"Results directory does not exist: {results_dir}")
            return 0, 0

        hex_file = os.path.join(results_dir, f"{Config.FILE_TYPE}_parsed_values_hex_original.json")
        if not os.path.exists(hex_file):
            self.logger.warning(f"Hex values file does not exist: {hex_file}")
            return 0, 0

        stem = os.path.splitext(os.path.basename(hex_file))[0]
        jobs = [
            (os.path.join(results_dir, f"{stem}{output_suffix}.json"), "leaf"),
            (os.path.join(results_dir, f"{stem}{output_suffix}_paths.json"), "path"),
        ]
        successful = sum(1 for out, mode in jobs if self.transform_json_file(hex_file, out, key_mode=mode))
        self.logger.info(f"Transformation complete! Produced {successful}/{len(jobs)} flattened files")
        return successful, len(jobs)

    def transform_specific_files(self, file_patterns, output_suffix="_flattened", key_mode="leaf"):
        """Flatten specific JSON files next to themselves."""
        successful_count = 0
        total_count = 0
        for file_path in file_patterns:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                continue
            total_count += 1
            output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}{output_suffix}.json"
            output_path = os.path.join(os.path.dirname(file_path), output_filename)
            if self.transform_json_file(file_path, output_path, key_mode=key_mode):
                successful_count += 1
        return successful_count, total_count
