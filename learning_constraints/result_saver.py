"""
Result saving module for the learning constraints system.
Writes parsed values, blacklists, dropped arrays, template values and a run summary to the
results directory.
"""
import os
import json
import logging

from .config import Config
from .utils import convert_sets_to_lists, filter_blacklisted_attributes


class ResultSaver:
    """Handles saving all result files for the learning constraints system."""

    def __init__(self, global_state, transformer=None):
        self.global_state = global_state
        self.transformer = transformer
        self.logger = logging.getLogger(__name__)

    def _results_path(self, name):
        return os.path.join(Config.CURRENT_RESULTS_DIR, f"{Config.FILE_TYPE}_{name}")

    def save_all_results(self):
        """Save parsed values, blacklists and dropped arrays."""
        self.save_parsed_values()
        self.save_blacklisted_attributes()
        self.save_dropped_arrays()

    def save_parsed_values(self):
        """Save the learned hex values (minus blacklisted leaves) to JSON."""
        if not Config.CURRENT_RESULTS_DIR:
            self.logger.warning("Log directory not initialized, results not saved!")
            return
        try:
            final_stats_hex = convert_sets_to_lists(self.global_state.nested_values_hex)

            blacklisted = self.global_state.blacklisted_by_size | self.global_state.blacklisted_by_count
            legacy = self.global_state.legacy_blacklisted_names
            if blacklisted or legacy:
                self.logger.info(f"Filtering {len(blacklisted) + len(legacy)} blacklisted attributes from results")
                final_stats_hex = filter_blacklisted_attributes(final_stats_hex, blacklisted, legacy)

            if Config.ENABLE_CHECKSUM_DETECTION and self.global_state.checksum_algorithms:
                final_stats_hex["checksum_algorithms"] = self.global_state.checksum_algorithms

            path = self._results_path("parsed_values_hex_original.json")
            with open(path, "w") as f:
                json.dump(final_stats_hex, f, indent=4)
            self.logger.info(f"Hex results saved to {path}")
        except Exception as e:
            self.logger.error(f"Error saving parsed values: {e}")

    def save_blacklisted_attributes(self):
        """Save both blacklists (cleaned full paths) to JSON files."""
        if not Config.CURRENT_RESULTS_DIR:
            self.logger.warning("Log directory not initialized, blacklisted attributes not saved!")
            return
        try:
            self._save_blacklist_file(
                attributes=self.global_state.blacklisted_by_size,
                filename="blacklisted_by_size.json",
                threshold_key="threshold_bytes",
                threshold_value=Config.MAX_ATTRIBUTE_SIZE_BYTES,
                description=f"Fields blacklisted because their size exceeds {Config.MAX_ATTRIBUTE_SIZE_BYTES} bytes"
            )
            self._save_blacklist_file(
                attributes=self.global_state.blacklisted_by_count,
                filename="blacklisted_by_count.json",
                threshold_key="threshold_count",
                threshold_value=Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE,
                description=f"Fields blacklisted because they have more than {Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE} unique values"
            )
        except Exception as e:
            self.logger.error(f"Error saving blacklisted attributes: {e}")

    def _save_blacklist_file(self, attributes, filename, threshold_key, threshold_value, description):
        data = {
            "blacklisted_attributes": sorted(attributes),
            "total_count": len(attributes),
            "key_type": "cleaned_path",
            "file_type": Config.FILE_TYPE,
            threshold_key: threshold_value,
            "description": description
        }
        if self.global_state.legacy_blacklisted_names:
            data["legacy_leaf_names"] = sorted(self.global_state.legacy_blacklisted_names)
        path = self._results_path(filename)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        self.logger.info(f"Blacklist saved to {path}")

    def save_dropped_arrays(self):
        """Save the leaf arrays that were skipped for having too many elements."""
        if not Config.CURRENT_RESULTS_DIR:
            return
        try:
            data = {
                "dropped_arrays": dict(sorted(self.global_state.dropped_arrays.items())),
                "threshold_elements": Config.MAX_ARRAY_ELEMENTS_LEARNED,
                "description": "Leaf arrays with more elements than the threshold are neither learned nor mutated",
            }
            with open(self._results_path("dropped_arrays.json"), "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving dropped arrays: {e}")

    def save_run_summary(self, summary):
        """Save the run summary (counts, failures, timing) as JSON."""
        if not Config.CURRENT_RESULTS_DIR:
            return
        try:
            with open(self._results_path("run_summary.json"), "w") as f:
                json.dump(summary, f, indent=4, default=str)
        except Exception as e:
            self.logger.error(f"Error saving run summary: {e}")

    def save_template_values(self, template_values):
        """Save the mined template values (and their flattened form)."""
        if not Config.CURRENT_RESULTS_DIR:
            self.logger.warning("Log directory not initialized, template values not saved!")
            return
        try:
            path = self._results_path("template_values.json")
            with open(path, "w") as f:
                json.dump(convert_sets_to_lists(template_values), f, indent=4)
            self.logger.info(f"Template values saved to {path}")

            if self.transformer:
                flattened_count, _ = self.transformer.transform_specific_files([path], output_suffix="_flattened")
                if flattened_count == 0:
                    self.logger.warning("Failed to transform template values")
        except Exception as e:
            self.logger.error(f"Error saving template results: {e}")
