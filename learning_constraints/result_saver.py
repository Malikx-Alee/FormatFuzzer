"""
Result saving module for the learning constraints system.
Handles saving parsed values, blacklisted attributes, and template values to JSON files.
"""
import os
import json
import logging

try:
    from .config import Config
    from .utils import convert_sets_to_lists, filter_blacklisted_attributes
except ImportError:
    from learning_constraints.config import Config
    from learning_constraints.utils import convert_sets_to_lists, filter_blacklisted_attributes


class ResultSaver:
    """Handles saving all result files for the learning constraints system."""

    def __init__(self, global_state, transformer=None):
        """
        Initialize the result saver.

        Args:
            global_state: The GlobalState instance containing collected data
            transformer: Optional ResultTransformer for flattening results
        """
        self.global_state = global_state
        self.transformer = transformer
        self.logger = logging.getLogger(__name__)

    def save_all_results(self):
        """Save all results including parsed values and blacklisted attributes."""
        self.save_parsed_values()
        self.save_blacklisted_attributes()

    def save_parsed_values(self):
        """Save the parsed hex values to JSON file."""
        try:
            # Convert nested dictionaries to final stats
            final_stats_hex = convert_sets_to_lists(self.global_state.nested_values_hex)

            # Filter out blacklisted attributes from final results
            blacklisted = self.global_state.blacklisted_attributes
            if blacklisted:
                self.logger.info(f"Filtering {len(blacklisted)} blacklisted attributes from results")
                final_stats_hex = filter_blacklisted_attributes(final_stats_hex, blacklisted)

            # Integrate checksum algorithms into the final hex results
            if getattr(Config, "ENABLE_CHECKSUM_DETECTION", False) and self.global_state.checksum_algorithms:
                try:
                    final_stats_hex["checksum_algorithms"] = self.global_state.checksum_algorithms
                    self.logger.info("Checksum algorithms integrated into final hex results")
                except Exception as ce:
                    self.logger.warning(f"Integrating checksum algorithms failed: {ce}")

            # Save hex results to log directory
            if Config.CURRENT_RESULTS_DIR:
                log_hex_file = os.path.join(
                    Config.CURRENT_RESULTS_DIR,
                    f"{Config.FILE_TYPE}_parsed_values_hex_original.json"
                )
                with open(log_hex_file, "w") as f:
                    json.dump(final_stats_hex, f, indent=4)
                self.logger.info(f"Hex results saved to {log_hex_file}")
            else:
                self.logger.warning("Log directory not initialized, results not saved!")

        except Exception as e:
            self.logger.error(f"Error saving parsed values: {e}")

    def save_blacklisted_attributes(self):
        """Save blacklisted attributes to separate JSON files."""
        if not Config.CURRENT_RESULTS_DIR:
            self.logger.warning("Log directory not initialized, blacklisted attributes not saved!")
            return

        try:
            # Save blacklisted by size
            self._save_blacklist_file(
                attributes=self.global_state.blacklisted_by_size,
                filename=f"{Config.FILE_TYPE}_blacklisted_by_size.json",
                threshold_key="threshold_bytes",
                threshold_value=Config.MAX_ATTRIBUTE_SIZE_BYTES,
                description=f"Attributes blacklisted because their byte size exceeds {Config.MAX_ATTRIBUTE_SIZE_BYTES} bytes"
            )

            # Save blacklisted by count
            self._save_blacklist_file(
                attributes=self.global_state.blacklisted_by_count,
                filename=f"{Config.FILE_TYPE}_blacklisted_by_count.json",
                threshold_key="threshold_count",
                threshold_value=Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE,
                description=f"Attributes blacklisted because they have more than {Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE} unique values"
            )

        except Exception as e:
            self.logger.error(f"Error saving blacklisted attributes: {e}")

    def _save_blacklist_file(self, attributes, filename, threshold_key, threshold_value, description):
        """Helper to save a single blacklist file."""
        data = {
            "blacklisted_attributes": sorted(list(attributes)),
            "total_count": len(attributes),
            "file_type": Config.FILE_TYPE,
            threshold_key: threshold_value,
            "description": description
        }
        filepath = os.path.join(Config.CURRENT_RESULTS_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        self.logger.info(f"Blacklist saved to {filepath}")

    def save_template_values(self, template_values):
        """Save the mined template values to a separate JSON file."""
        try:
            final_template_values = convert_sets_to_lists(template_values)

            if Config.CURRENT_RESULTS_DIR:
                log_template_file = os.path.join(
                    Config.CURRENT_RESULTS_DIR,
                    f"{Config.FILE_TYPE}_template_values.json"
                )
                with open(log_template_file, "w") as f:
                    json.dump(final_template_values, f, indent=4)
                self.logger.info(f"Template values saved to {log_template_file}")

                # Transform template values if transformer is available
                if self.transformer:
                    self._transform_template(log_template_file)
            else:
                self.logger.warning("Log directory not initialized, template values not saved!")

        except Exception as e:
            self.logger.error(f"Error saving template results: {e}")

    def _transform_template(self, template_file_path):
        """Transform template results to flattened format."""
        try:
            flattened_count, _ = self.transformer.transform_specific_files(
                file_patterns=[template_file_path],
                output_suffix="_flattened"
            )
            if flattened_count > 0:
                self.logger.info("Template values transformed and flattened successfully")
            else:
                self.logger.warning("Failed to transform template values")
        except Exception as e:
            self.logger.error(f"Error transforming template results: {e}")

