#!/usr/bin/env python3
"""
Simple runner script for the Learning Constraints module.

Usage:
    python run_learning_constraints.py <file_type> [max_files] [source_dir]

Examples:
    python run_learning_constraints.py png                    # Process all PNG files from default directory
    python run_learning_constraints.py jpg 5                  # Process only 5 JPG files
    python run_learning_constraints.py gif /path/to/files     # Process all GIF files from custom directory
    python run_learning_constraints.py bmp 5 /path/to/files   # Process 5 BMP files from custom directory
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
    """Simple main function that takes file type, max files, and source directory as command line arguments."""

    # Check if file type was provided as argument (required)
    if len(sys.argv) < 2:
        print("Error: file_type argument is required.")
        print("Usage: python run_learning_constraints.py <file_type> [max_files] [source_dir]")
        print(f"Supported types: {', '.join(get_supported_file_types())}")
        sys.exit(1)

    file_type = sys.argv[1].lower()

    # Default values
    max_files = None
    source_dir = None

    # Parse optional arguments - detect if second arg is max_files (integer) or source_dir (path)
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        try:
            max_files = int(arg2)
            if max_files <= 0:
                print("Error: max_files must be a positive integer.")
                sys.exit(1)
        except ValueError:
            # Not an integer, treat as source_dir
            source_dir = arg2
            if not os.path.isdir(source_dir):
                print(f"Error: source_dir '{source_dir}' does not exist or is not a directory.")
                sys.exit(1)

    # Check if source_dir was provided as third argument
    if len(sys.argv) > 3:
        source_dir = sys.argv[3]
        if not os.path.isdir(source_dir):
            print(f"Error: source_dir '{source_dir}' does not exist or is not a directory.")
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
    effective_source_dir = source_dir if source_dir else Config.DATA_DIR
    print(f"Learning Constraints - Processing {file_type.upper()} files ({files_info})")
    print("=" * 60)
    print(f"Source directory: {effective_source_dir}")
    print(f"Results directory: ./logs/<timestamp>_{file_type}/results/")
    if max_files is not None:
        print(f"File limit: {max_files} files")

    # Check if source directory exists
    if not os.path.exists(effective_source_dir):
        print(f"\nWarning: Source directory {effective_source_dir} does not exist.")
        if source_dir is None:
            print("Please ensure you have files in the data directory before running.")
            print(f"Expected directory: {Config.DATA_DIR}")
        return

    try:
        # Create orchestrator and run
        orchestrator = LearningConstraintsOrchestrator(file_type=file_type, max_files=max_files, source_dir=source_dir)
        results = orchestrator.run_complete_process()

        if results:
            print("\n" + "=" * 60)
            print("PROCESSING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Valid files processed: {results['passed_files']['successful']}/{results['passed_files']['total']}")
            print(f"Special files processed: {results['special_files']['successful']}/{results['special_files']['total']}")
            print(f"Result files transformed: {results['transformed_files']['successful']}/{results['transformed_files']['total']}")
            if 'total_time_formatted' in results:
                print(f"Total time: {results['total_time_formatted']}")
        else:
            print("Process failed or was interrupted.")

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
