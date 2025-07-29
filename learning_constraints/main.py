"""
Main orchestrator module for the learning constraints system.
Coordinates the entire process of file parsing, abstraction, and analysis.
"""
import os
import json
import logging
import sys

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .config import Config, GlobalState
    from .parsers import FileParser
    from .mutators import FileMutator
    from .transformers import ResultTransformer
    from .utils import convert_sets_to_lists
except ImportError:
    # Fallback for direct execution
    from learning_constraints.config import Config, GlobalState
    from learning_constraints.parsers import FileParser
    from learning_constraints.mutators import FileMutator
    from learning_constraints.transformers import ResultTransformer
    from learning_constraints.utils import convert_sets_to_lists


class LearningConstraintsOrchestrator:
    """Main orchestrator class for the learning constraints process."""

    def __init__(self, file_type=None, log_level=logging.INFO, max_files=None):
        """
        Initialize the orchestrator.

        Args:
            file_type (str, optional): File type to process. If None, uses Config.FILE_TYPE
            log_level: Logging level
            max_files (int, optional): Maximum number of files to process. If None, process all files
        """
        # Set up logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set file type if provided
        if file_type:
            Config.set_file_type(file_type)
        
        # Ensure directories exist
        Config.ensure_directories_exist()
        
        # Store max_files parameter
        self.max_files = max_files

        # Initialize global state and components
        self.global_state = GlobalState()
        self.parser = FileParser(self.global_state)
        self.mutator = FileMutator(self.global_state)
        self.transformer = ResultTransformer()

        files_info = f"all files" if max_files is None else f"up to {max_files} files"
        self.logger.info(f"Initialized Learning Constraints Orchestrator for {Config.FILE_TYPE} files ({files_info})")
    
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
            byte_ranges = self.parser.parse_file_structure(file_path)
            
            if not byte_ranges:
                self.logger.warning(f"No byte ranges found for {file_path}")
                return False
            
            self.logger.info(f"Found {len(byte_ranges)} byte ranges in {file_path}")
            
            # Perform mutation on the file
            self.mutator.mutate_file_completely(file_path, byte_ranges)
            
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
            tuple: (successful_count, total_count)
        """
        if not os.path.exists(directory_path):
            self.logger.error(f"Directory does not exist: {directory_path}")
            return 0, 0

        file_names = [f for f in os.listdir(directory_path)
                     if os.path.isfile(os.path.join(directory_path, f))]

        if not file_names:
            self.logger.warning(f"No files found in directory: {directory_path}")
            return 0, 0

        # Determine how many files to process
        files_to_process = max_files if max_files is not None else self.max_files
        if files_to_process is not None:
            file_names = file_names[:files_to_process]
            self.logger.info(f"Processing {len(file_names)} files (limited to {files_to_process}) from {directory_path}")
        else:
            self.logger.info(f"Processing all {len(file_names)} files from {directory_path}")

        successful_count = 0
        for i, file_name in enumerate(file_names, 1):
            file_path = os.path.join(directory_path, file_name)
            self.logger.info(f"Processing file {i}/{len(file_names)}: {file_path}")
            if self.process_file(file_path):
                successful_count += 1

        self.logger.info(f"Successfully processed {successful_count}/{len(file_names)} files")
        return successful_count, len(file_names)
    
    def save_results(self):
        """Save the collected results to JSON files."""
        try:
            # Convert nested dictionaries to final stats
            final_stats_hex = convert_sets_to_lists(self.global_state.nested_values_hex)

            # Save hex results to JSON file
            with open(Config.STATS_FILE_HEX, "w") as f:
                json.dump(final_stats_hex, f, indent=4)

            self.logger.info(f"Hex results saved to {Config.STATS_FILE_HEX}")

            # Save blacklisted attributes to JSON file
            blacklisted_data = {
                "blacklisted_attributes": list(self.global_state.blacklisted_attributes),
                "total_count": len(self.global_state.blacklisted_attributes),
                "file_type": Config.FILE_TYPE,
                "description": f"Attributes that were blacklisted due to size > {Config.MAX_ATTRIBUTE_SIZE_BYTES} bytes"
            }

            with open(Config.BLACKLISTED_ATTRIBUTES_FILE, "w") as f:
                json.dump(blacklisted_data, f, indent=4)

            self.logger.info(f"Blacklisted attributes saved to {Config.BLACKLISTED_ATTRIBUTES_FILE}")

        except Exception as e:
            self.logger.error(f"Error saving results: {e}")

    def transform_results(self, output_suffix="_flattened"):
        """
        Transform the saved results by flattening JSON structures.

        Args:
            output_suffix (str): Suffix to add to transformed file names

        Returns:
            tuple: (successful_count, total_count)
        """
        try:
            self.logger.info("Transforming results...")
            successful, total = self.transformer.transform_results_directory(output_suffix=output_suffix)

            if successful > 0:
                self.logger.info(f"Successfully transformed {successful}/{total} result files")
            else:
                self.logger.warning("No files were transformed")

            return successful, total

        except Exception as e:
            self.logger.error(f"Error transforming results: {e}")
            return 0, 0

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
        
        This processes files from the passed directory, then processes any special files
        that were generated, and finally saves the results.
        """
        self.logger.info("Starting complete learning constraints process")
        
        # Process files from the valid_files directory
        self.logger.info("Processing files from valid_files directory")
        passed_successful, passed_total = self.process_directory(Config.PASSED_DIR)

        # Process files from the abstracted special directory (use remaining quota if any)
        remaining_files = None
        if self.max_files is not None:
            remaining_files = max(0, self.max_files - passed_total)
            if remaining_files > 0:
                self.logger.info(f"Processing files from abstracted special directory (up to {remaining_files} files)")
                special_successful, special_total = self.process_directory(Config.ABSTRACTED_SPECIAL_DIR, remaining_files)
            else:
                self.logger.info("Skipping abstracted special directory - file limit reached")
                special_successful, special_total = 0, 0
        else:
            self.logger.info("Processing files from abstracted special directory")
            special_successful, special_total = self.process_directory(Config.ABSTRACTED_SPECIAL_DIR)
        
        # Save results
        self.save_results()

        # Transform results
        transform_successful, transform_total = self.transform_results()

        # Print statistics
        self.print_statistics()

        self.logger.info("Learning constraints process completed")
        
        return {
            'passed_files': {'successful': passed_successful, 'total': passed_total},
            'special_files': {'successful': special_successful, 'total': special_total},
            'transformed_files': {'successful': transform_successful, 'total': transform_total},
            'stats': self.global_state.get_stats()
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
