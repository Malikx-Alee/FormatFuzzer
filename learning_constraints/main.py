"""
Main orchestrator module for the learning constraints system.
Coordinates the entire process of file parsing, abstraction, and analysis.
"""
import os
import json
import logging
import sys
import time

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .config import Config, GlobalState
    from .parsers import FileParser
    from .mutators import FileMutator
    from .transformers import ResultTransformer
    from .utils import convert_sets_to_lists
    from .checkpoint import CheckpointManager
except ImportError:
    # Fallback for direct execution
    from learning_constraints.config import Config, GlobalState
    from learning_constraints.parsers import FileParser
    from learning_constraints.mutators import FileMutator
    from learning_constraints.transformers import ResultTransformer
    from learning_constraints.utils import convert_sets_to_lists
    from learning_constraints.checkpoint import CheckpointManager


class LearningConstraintsOrchestrator:
    """Main orchestrator class for the learning constraints process."""

    def __init__(self, file_type=None, log_level=logging.INFO, max_files=None, source_dir=None,
                 resume_from_checkpoint=None):
        """
        Initialize the orchestrator.

        Args:
            file_type (str, optional): File type to process. If None, uses Config.FILE_TYPE
            log_level: Logging level
            max_files (int, optional): Maximum number of files to process. If None, process all files
            source_dir (str, optional): Custom source directory for reading files. If None, uses Config.DATA_DIR
            resume_from_checkpoint (str, optional): Path to checkpoint file to resume from.
                                                   If None and Config.RESUME_MODE is True,
                                                   will search for latest checkpoint.
        """
        # Set file type if provided
        if file_type:
            Config.set_file_type(file_type)

        # Check for resume mode
        self._is_resuming = False
        checkpoint_path = resume_from_checkpoint

        if Config.RESUME_MODE and checkpoint_path is None:
            # Search for latest checkpoint for this file type
            log_dir, checkpoint_path = Config.find_latest_checkpoint(file_type)
            if checkpoint_path:
                print(f"Found checkpoint to resume: {checkpoint_path}")

        if checkpoint_path and os.path.exists(checkpoint_path):
            # Resuming from checkpoint - restore the log directory
            self._is_resuming = True
            checkpoint_info = CheckpointManager.load_checkpoint_info(checkpoint_path)
            log_dir = checkpoint_info.get("log_dir")
            if log_dir and os.path.exists(log_dir):
                Config.restore_log_directory(log_dir)
                log_file = Config.LOG_FILE
            else:
                # Checkpoint exists but log dir is missing - start fresh
                self._is_resuming = False
                log_file = Config.initialize_logging(file_type)
        else:
            # Start fresh - initialize new logging directory
            log_file = Config.initialize_logging(file_type)

        # Set up logging to both file and console
        # Clear any existing handlers (for Python 3.7 compatibility - 'force' param added in 3.8)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Store max_files parameter
        self.max_files = max_files

        # Store source directory (use Config.DATA_DIR as default)
        self.source_dir = source_dir if source_dir else Config.DATA_DIR

        # Initialize global state and components
        self.global_state = GlobalState()
        self.parser = FileParser(self.global_state)
        self.mutator = FileMutator(self.global_state)
        self.transformer = ResultTransformer()

        # Initialize checkpoint manager
        self.checkpoint_manager = CheckpointManager(self.global_state)
        self.checkpoint_manager.set_run_info(self.source_dir, max_files)

        # Load checkpoint if resuming
        if self._is_resuming and checkpoint_path:
            self.checkpoint_manager.checkpoint_path = checkpoint_path
            if self.checkpoint_manager.load_checkpoint():
                self.logger.info(f"Resumed from checkpoint: {checkpoint_path}")
                self.logger.info(f"Previously processed {len(self.checkpoint_manager.processed_files)} files")
            else:
                self.logger.warning("Failed to load checkpoint, starting fresh")
                self._is_resuming = False

        files_info = f"all files" if max_files is None else f"up to {max_files} files"
        resume_info = " (RESUMING)" if self._is_resuming else ""
        self.logger.info(f"Initialized Learning Constraints Orchestrator for {Config.FILE_TYPE} files ({files_info}){resume_info}")
        self.logger.info(f"Source directory: {self.source_dir}")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info(f"Results will be saved to: {Config.CURRENT_RESULTS_DIR}")

    def process_file(self, file_path):
        """
        Process a single file through the complete abstraction pipeline.

        Args:
            file_path (str): Path to the file to process

        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # self.logger.info(f"Processing file: {file_path}")

            # Parse the file to get byte ranges
            original_byte_ranges, byte_ranges = self.parser.parse_file_structure(file_path)

            if not byte_ranges:
                self.logger.warning(f"No byte ranges found for {file_path}")
                return False

            self.logger.info(f"Found {len(original_byte_ranges)} original byte ranges")
            self.logger.info(f"Found {len(byte_ranges)} filtered byte ranges")

            # Perform mutation on the file
            self.mutator.mutate_file_completely(file_path, byte_ranges, original_byte_ranges)

            return True

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return False

    def process_directory(self, directory_path, max_files=None):
        """
        Process files in a directory.

        Args:
            directory_path (str): Path to the directory containing files to process
            max_files (int, optional): Maximum number of files to process. If None, uses self.max_files

        Returns:
            tuple: (successful_count, total_count, skipped_count)
        """
        if not os.path.exists(directory_path):
            self.logger.error(f"Directory does not exist: {directory_path}")
            return 0, 0, 0

        file_names = [f for f in os.listdir(directory_path)
                     if os.path.isfile(os.path.join(directory_path, f))]

        if not file_names:
            self.logger.warning(f"No files found in directory: {directory_path}")
            return 0, 0, 0

        # Determine how many files to process
        files_to_process = max_files if max_files is not None else self.max_files
        if files_to_process is not None:
            file_names = file_names[:files_to_process]
            self.logger.info(f"Processing {len(file_names)} files (limited to {files_to_process}) from {directory_path}")
        else:
            self.logger.info(f"Processing all {len(file_names)} files from {directory_path}")

        successful_count = 0
        skipped_count = 0

        for i, file_name in enumerate(file_names, 1):
            file_path = os.path.join(directory_path, file_name)

            # Check if file was already processed (resuming from checkpoint)
            if self.checkpoint_manager.is_file_processed(file_path):
                self.logger.info(f"Skipping already processed file {i}/{len(file_names)}: {file_path}")
                skipped_count += 1
                continue

            self.logger.info(f"Processing file {i}/{len(file_names)}: {file_path}")
            if self.process_file(file_path):
                successful_count += 1

            # Mark file as processed and save checkpoint
            self.checkpoint_manager.mark_file_processed(file_path)

        self.logger.info(f"Successfully processed {successful_count}/{len(file_names)} files (skipped {skipped_count} already processed)")
        return successful_count, len(file_names), skipped_count

    def save_results(self):
        """Save the collected results to JSON files in the log directory."""
        try:
            # Convert nested dictionaries to final stats
            final_stats_hex = convert_sets_to_lists(self.global_state.nested_values_hex)

            # Integrate checksum algorithms into the final hex results (no separate file)
            if getattr(Config, "ENABLE_CHECKSUM_DETECTION", False) and self.global_state.checksum_algorithms:
                try:
                    # Merge into final stats under a dedicated key BEFORE writing
                    final_stats_hex["checksum_algorithms"] = self.global_state.checksum_algorithms
                    self.logger.info("Checksum algorithms integrated into final hex results")
                except Exception as ce:
                    self.logger.warning(f"Integrating checksum algorithms failed: {ce}")

            # Save hex results to log directory
            if Config.CURRENT_RESULTS_DIR:
                log_hex_file = os.path.join(Config.CURRENT_RESULTS_DIR, f"{Config.FILE_TYPE}_parsed_values_hex_original.json")
                with open(log_hex_file, "w") as f:
                    json.dump(final_stats_hex, f, indent=4)
                self.logger.info(f"Hex results saved to {log_hex_file}")
            else:
                self.logger.warning("Log directory not initialized, results not saved!")

            # Save blacklisted attributes to JSON file
            blacklisted_data = {
                "blacklisted_attributes": list(self.global_state.blacklisted_attributes),
                "total_count": len(self.global_state.blacklisted_attributes),
                "file_type": Config.FILE_TYPE,
                "description": f"Attributes that were blacklisted due to size > {Config.MAX_ATTRIBUTE_SIZE_BYTES} bytes"
            }

            # Save to log directory
            if Config.CURRENT_RESULTS_DIR:
                log_blacklist_file = os.path.join(Config.CURRENT_RESULTS_DIR, f"{Config.FILE_TYPE}_blacklisted_attributes.json")
                with open(log_blacklist_file, "w") as f:
                    json.dump(blacklisted_data, f, indent=4)
                self.logger.info(f"Blacklisted attributes saved to {log_blacklist_file}")
            else:
                self.logger.warning("Log directory not initialized, blacklisted attributes not saved!")

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")

    def save_template_results(self, template_values):
        """Save the mined template values to a separate JSON file in the log directory."""
        try:
            # Convert sets to lists for JSON serialization
            final_template_values = convert_sets_to_lists(template_values)

            # Save to log directory
            if Config.CURRENT_RESULTS_DIR:
                log_template_file = os.path.join(Config.CURRENT_RESULTS_DIR, f"{Config.FILE_TYPE}_template_values.json")
                with open(log_template_file, "w") as f:
                    json.dump(final_template_values, f, indent=4)
                self.logger.info(f"Template values saved to {log_template_file}")

                # Also create a flattened version using the transformer
                self.transform_template_results(log_template_file)
            else:
                self.logger.warning("Log directory not initialized, template values not saved!")

        except Exception as e:
            self.logger.error(f"Error saving template results: {e}")

    def transform_template_results(self, template_file_path):
        """Transform the template results to flattened format."""
        try:
            # Use the existing transformer to flatten the template results
            flattened_count, _ = self.transformer.transform_specific_files(
                file_patterns=[template_file_path],
                output_suffix="_flattened"
            )

            if flattened_count > 0:
                self.logger.info(f"Template values transformed and flattened successfully")
            else:
                self.logger.warning(f"Failed to transform template values")

        except Exception as e:
            self.logger.error(f"Error transforming template results: {e}")

    def transform_results(self, output_suffix="_flattened"):
        """
        Transform the saved results by flattening JSON structures in the log directory.

        Args:
            output_suffix (str): Suffix to add to transformed file names

        Returns:
            tuple: (successful_count, total_count)
        """
        try:
            self.logger.info("Transforming results...")

            # Transform in log directory
            if Config.CURRENT_RESULTS_DIR:
                successful, total = self.transformer.transform_results_directory(
                    results_dir=Config.CURRENT_RESULTS_DIR,
                    output_suffix=output_suffix
                )
                if successful > 0:
                    self.logger.info(f"Successfully transformed {successful}/{total} result files")
                else:
                    self.logger.warning("No files were transformed")
                return successful, total
            else:
                self.logger.warning("Log directory not initialized, results not transformed!")
                return 0, 0

        except Exception as e:
            self.logger.error(f"Error transforming results: {e}")
            return 0, 0

    def log_crc_values(self):
        """Log detected checksum algorithms (by chunk type) before printing statistics."""
        try:
            if getattr(Config, "ENABLE_CHECKSUM_DETECTION", False):
                algos = self.global_state.checksum_algorithms or {}
                by_type = algos.get("by_chunk_type", {}) if isinstance(algos, dict) else {}

                if Config.FILE_TYPE == "zip":
                    print("\n----- ZIP checksum algorithms (by_chunk_type) -----")
                    print(f"recordCrc: {by_type.get('recordCrc')}")
                    print(f"dirEntryCrc: {by_type.get('dirEntryCrc')}")

                    # Show compression methods found
                    compression_methods = algos.get("compression_methods", {})
                    if compression_methods:
                        print("\n----- ZIP compression methods found -----")
                        for method_id, method_name in sorted(compression_methods.items(), key=lambda x: int(x[0])):
                            print(f"  {method_id}: {method_name}")
                else:
                    print("\n----- Checksum algorithms (by_chunk_type) -----")
                    if isinstance(by_type, dict) and by_type:
                        for k, v in by_type.items():
                            print(f"{k}: {v}")
                    else:
                        print("<none>")
        except Exception as e:
            print(f"[ChecksumAlgo LOG][ERROR] {e}")

    def print_statistics(self):
        """Print processing statistics."""
        stats = self.global_state.get_stats()

        print("\n" + "="*50)
        print("PROCESSING STATISTICS")
        print("="*50)
        print(f"File Type: {Config.FILE_TYPE}")
        print(f"Valid Abstractions: {stats['valid_abstractions']}")
        print(f"Valid Abstractions (Special): {stats['valid_abstractions_special']}")
        print(f"Valid Overwrites: {stats['valid_overwrites']}")
        print(f"Blacklisted Attributes: {stats['blacklisted_attributes']}")
        print("="*50)

    def run_complete_process(self):
        """
        Run the complete learning abstraction process.

        This mines interesting values from template first, then processes files from the
        passed directory, then processes any special files that were generated, and finally saves the results.
        """
        # Start timing
        start_time = time.time()
        self.logger.info("Starting complete learning constraints process")

        # Mine interesting values from template first
        self.logger.info("Mining interesting values from template")
        template_mining_success, template_values = self.parser.mine_interesting_values_from_template()
        if template_mining_success:
            self.logger.info("Successfully mined interesting values from template")
            # Save template values to a separate file
            self.save_template_results(template_values)
        else:
            self.logger.warning("Failed to mine interesting values from template, continuing with file processing")

        # Process files from the source directory
        self.logger.info(f"Processing files from source directory: {self.source_dir}")
        passed_successful, passed_total, passed_skipped = self.process_directory(self.source_dir)

        # Process files from the abstracted special directory (use remaining quota if any)
        abstracted_special_dir = Config.CURRENT_ABSTRACTED_SPECIAL_DIR

        remaining_files = None
        if self.max_files is not None:
            remaining_files = max(0, self.max_files - passed_total)
            if remaining_files > 0:
                self.logger.info(f"Processing files from abstracted special directory (up to {remaining_files} files)")
                special_successful, special_total, special_skipped = self.process_directory(abstracted_special_dir, remaining_files)
            else:
                self.logger.info("Skipping abstracted special directory - file limit reached")
                special_successful, special_total, special_skipped = 0, 0, 0
        else:
            self.logger.info("Processing files from abstracted special directory")
            special_successful, special_total, special_skipped = self.process_directory(abstracted_special_dir)

        # Save final checkpoint
        self.checkpoint_manager.mark_complete()
        self.logger.info("Checkpoint saved")

        # Save results
        self.save_results()

        # Transform results
        transform_successful, transform_total = self.transform_results()

        # Log CRCs (e.g., for ZIP) before printing statistics
        try:
            self.log_crc_values()
        except Exception:
            pass

        # Print statistics
        self.print_statistics()

        # Calculate and log total time
        end_time = time.time()
        total_time = end_time - start_time

        # Format time in a human-readable way
        if total_time < 60:
            time_str = f"{total_time:.2f} seconds"
        elif total_time < 3600:
            minutes = int(total_time // 60)
            seconds = total_time % 60
            time_str = f"{minutes} minutes {seconds:.2f} seconds"
        else:
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = total_time % 60
            time_str = f"{hours} hours {minutes} minutes {seconds:.2f} seconds"

        self.logger.info(f"Learning constraints process completed in {time_str}")
        print(f"\nTotal processing time: {time_str}")

        return {
            'passed_files': {'successful': passed_successful, 'total': passed_total, 'skipped': passed_skipped},
            'special_files': {'successful': special_successful, 'total': special_total, 'skipped': special_skipped},
            'transformed_files': {'successful': transform_successful, 'total': transform_total},
            'stats': self.global_state.get_stats(),
            'total_time': total_time,
            'total_time_formatted': time_str,
            'resumed': self._is_resuming
        }


def main(max_files=None):
    """Main entry point for the learning constraints system."""
    try:
        # Create orchestrator and run the complete process
        orchestrator = LearningConstraintsOrchestrator(file_type="png", max_files=max_files)
        results = orchestrator.run_complete_process()

        print("\nProcessing complete!")
        return results

    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return None
    except Exception as e:
        print(f"Error in main process: {e}")
        return None


if __name__ == "__main__":
    main()
