#!/usr/bin/env python3
"""
Simple runner script for the Learning Constraints module.

Usage:
    python run_learning_constraints.py [file_type] [max_files]

Examples:
    python run_learning_constraints.py                # Uses default file type (gif), process all files
    python run_learning_constraints.py png            # Process all PNG files
    python run_learning_constraints.py jpg 5          # Process only 5 JPG files
    python run_learning_constraints.py gif 10         # Process only 10 GIF files
"""

import sys
import os
from learning_constraints import (
    LearningConstraintsOrchestrator,
    Config,
    set_file_type,
    get_supported_file_types
)


def main():
    """Simple main function that takes file type and max files as command line arguments."""

    # Default values
    file_type = "zip"
    max_files = None

    # Check if file type was provided as argument
    if len(sys.argv) > 1:
        file_type = sys.argv[1].lower()

    # Check if max_files was provided as argument
    if len(sys.argv) > 2:
        try:
            max_files = int(sys.argv[2])
            if max_files <= 0:
                print("Error: max_files must be a positive integer.")
                sys.exit(1)
        except ValueError:
            print("Error: max_files must be a valid integer.")
            sys.exit(1)

    # Validate file type
    supported_types = get_supported_file_types()
    if file_type not in supported_types:
        print(f"Error: '{file_type}' is not a supported file type.")
        print(f"Supported types: {', '.join(supported_types)}")
        sys.exit(1)

    # Set the file type
    set_file_type(file_type)

    files_info = f"all files" if max_files is None else f"up to {max_files} files"
    print(f"Learning Constraints - Processing {file_type.upper()} files ({files_info})")
    print("=" * 60)
    print(f"Data directory: {Config.DATA_DIR}")
    print(f"Results directory: {Config.RESULTS_OUTPUT_DIR}")
    if max_files is not None:
        print(f"File limit: {max_files} files")

    # Check if data directory exists
    if not os.path.exists(Config.PASSED_DIR):
        print(f"\nWarning: Data directory {Config.PASSED_DIR} does not exist.")
        print("Please ensure you have files in the valid_files directory before running.")
        print("\nCreating directories...")
        Config.ensure_directories_exist()
        print(f"Created: {Config.PASSED_DIR}")
        print("Please add some files to the valid_files directory and run again.")
        return

    try:
        # Create orchestrator and run
        orchestrator = LearningConstraintsOrchestrator(file_type=file_type, max_files=max_files)
        results = orchestrator.run_complete_process()

        if results:
            print("\n" + "=" * 60)
            print("PROCESSING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Valid files processed: {results['passed_files']['successful']}/{results['passed_files']['total']}")
            print(f"Special files processed: {results['special_files']['successful']}/{results['special_files']['total']}")
            print(f"Result files transformed: {results['transformed_files']['successful']}/{results['transformed_files']['total']}")
        else:
            print("Process failed or was interrupted.")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
