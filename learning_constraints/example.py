#!/usr/bin/env python3
"""
Example script demonstrating the usage of the Learning Constraints module.

This script shows various ways to use the refactored learning constraints system,
from basic usage to advanced configuration and individual component usage.
"""

import logging
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning_constraints import (
    LearningConstraintsOrchestrator,
    Config,
    GlobalState,
    FileParser,
    FileValidator,
    set_file_type,
    get_supported_file_types
)


def example_basic_usage():
    """Example 1: Basic usage with the orchestrator."""
    print("="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)
    
    # Create orchestrator for GIF files
    orchestrator = LearningConstraintsOrchestrator(file_type="gif")

    # Run the complete process
    print("Running complete learning constraints process...")
    results = orchestrator.run_complete_process()
    
    if results:
        print("Process completed successfully!")
        print(f"Results: {results}")
    else:
        print("Process failed or was interrupted.")


def example_individual_file_processing():
    """Example 2: Processing individual files and directories."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Individual File Processing")
    print("="*60)
    
    orchestrator = LearningConstraintsOrchestrator(file_type="gif")
    
    # Check if the valid_files directory exists
    if os.path.exists(Config.PASSED_DIR):
        print(f"Processing files from: {Config.PASSED_DIR}")

        # Process all files in the valid_files directory
        successful, total = orchestrator.process_directory(Config.PASSED_DIR)
        print(f"Successfully processed {successful}/{total} files")

        # Save results
        orchestrator.save_results()
        orchestrator.print_statistics()
    else:
        print(f"Directory {Config.PASSED_DIR} does not exist.")
        print("Please ensure you have files in the valid_files directory before running this example.")


def example_component_usage():
    """Example 3: Using individual components."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Individual Component Usage")
    print("="*60)
    
    # Initialize global state
    state = GlobalState()
    
    # Create individual components
    parser = FileParser(state)
    validator = FileValidator()
    
    # Example file path (you may need to adjust this)
    example_file = os.path.join(Config.PASSED_DIR, "example.gif")
    
    if os.path.exists(example_file):
        print(f"Analyzing file: {example_file}")
        
        # Validate the file
        is_valid = validator.is_valid_file(example_file)
        print(f"File is valid: {is_valid}")
        
        if is_valid:
            # Parse the file structure
            byte_ranges = parser.parse_file_structure(example_file)
            print(f"Found {len(byte_ranges)} byte ranges")
            
            # Extract bytes
            parser.extract_bytes_from_file(example_file, byte_ranges)
            print("Byte extraction completed")
            
            # Get attributes
            attributes = parser.get_file_attributes(byte_ranges)
            print(f"File attributes: {attributes}")
    else:
        print(f"Example file {example_file} not found.")
        print("Please place a valid GIF file in the valid_files directory.")


def example_configuration():
    """Example 4: Configuration management."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Configuration Management")
    print("="*60)
    
    # Show supported file types
    print(f"Supported file types: {get_supported_file_types()}")
    
    # Show current configuration
    print(f"Current file type: {Config.FILE_TYPE}")
    print(f"Data directory: {Config.DATA_DIR}")
    print(f"Results directory: {Config.RESULTS_OUTPUT_DIR}")
    
    # Change file type
    print("\nChanging file type to 'png'...")
    set_file_type("png")
    
    print(f"New file type: {Config.FILE_TYPE}")
    print(f"New data directory: {Config.DATA_DIR}")
    
    # Ensure directories exist
    Config.ensure_directories_exist()
    print("Directories created/verified")
    
    # Change back to gif for other examples
    set_file_type("gif")


def example_with_logging():
    """Example 5: Using the system with detailed logging."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Detailed Logging")
    print("="*60)
    
    # Set up detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create orchestrator with debug logging
    orchestrator = LearningConstraintsOrchestrator(
        file_type="gif",
        log_level=logging.DEBUG
    )
    
    # Process a single file if available
    if os.path.exists(Config.PASSED_DIR):
        files = [f for f in os.listdir(Config.PASSED_DIR) 
                if os.path.isfile(os.path.join(Config.PASSED_DIR, f))]
        
        if files:
            example_file = os.path.join(Config.PASSED_DIR, files[0])
            print(f"Processing {example_file} with detailed logging...")
            orchestrator.process_file(example_file)
        else:
            print("No files found in valid_files directory for logging example.")
    else:
        print("Valid_files directory not found for logging example.")


def main():
    """Main function to run all examples."""
    print("Learning Constraints Module - Example Usage")
    print("This script demonstrates various ways to use the refactored module.")
    
    try:
        # Run examples
        example_configuration()
        example_component_usage()
        example_individual_file_processing()
        example_with_logging()
        
        # Note: Commented out the basic usage example as it runs the full process
        # Uncomment the line below if you want to run the complete process
        # example_basic_usage()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user.")
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
