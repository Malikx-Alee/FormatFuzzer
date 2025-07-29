"""
Learning Constraints Package

A modular system for file format fuzzing and learning through constraint discovery.
This package provides tools for parsing file structures, performing abstractions,
and discovering new format attributes through systematic analysis.

Main Components:
- config: Configuration and global state management
- validators: File validation for different formats
- parsers: File structure parsing and byte extraction
- mutators: File mutation through smart abstraction and random overwrites
- transformers: Result transformation and JSON flattening
- utils: Utility functions and helpers
- main: Main orchestrator for the complete process

Usage:
    from learning_constraints import LearningConstraintsOrchestrator

    # Create orchestrator for GIF files
    orchestrator = LearningConstraintsOrchestrator(file_type="gif")

    # Run the complete process
    results = orchestrator.run_complete_process()

    # Or process individual files/directories
    orchestrator.process_file("path/to/file.gif")
    orchestrator.process_directory("path/to/directory")

    # Use individual components
    from learning_constraints import FileParser, FileMutator, ResultTransformer, GlobalState

    state = GlobalState()
    parser = FileParser(state)
    mutator = FileMutator(state)
    transformer = ResultTransformer()
"""

from .config import Config, GlobalState
from .validators import FileValidator
from .parsers import FileParser
from .mutators import FileMutator
from .transformers import ResultTransformer
from .main import LearningConstraintsOrchestrator, main
from .utils import (
    convert_sets_to_lists,
    clean_attribute_key,
    insert_nested_dict,
    overwrite_bytes_randomly,
    extract_byte_values,
    validate_byte_range
)

__version__ = "1.0.0"
__author__ = "Learning Constraints Team"
__description__ = "A modular system for file format fuzzing and learning through constraint discovery"

# Package-level convenience functions
def set_file_type(file_type):
    """
    Set the file type for the entire package.
    
    Args:
        file_type (str): The file type to set (e.g., 'gif', 'jpg', 'png')
    """
    Config.set_file_type(file_type)

def get_supported_file_types():
    """
    Get the list of supported file types.
    
    Returns:
        list: List of supported file type strings
    """
    return Config.SUPPORTED_FILE_TYPES.copy()

def create_orchestrator(file_type=None, log_level=None, max_files=None):
    """
    Create a new LearningConstraintsOrchestrator instance.

    Args:
        file_type (str, optional): File type to process
        log_level (optional): Logging level
        max_files (int, optional): Maximum number of files to process

    Returns:
        LearningConstraintsOrchestrator: New orchestrator instance
    """
    return LearningConstraintsOrchestrator(file_type=file_type, log_level=log_level, max_files=max_files)

# Export main classes and functions
__all__ = [
    # Main classes
    'LearningConstraintsOrchestrator',
    'Config',
    'GlobalState',
    'FileValidator',
    'FileParser',
    'FileMutator',
    'ResultTransformer',
    
    # Convenience functions
    'main',
    'set_file_type',
    'get_supported_file_types',
    'create_orchestrator',
    
    # Utility functions
    'convert_sets_to_lists',
    'clean_attribute_key',
    'insert_nested_dict',
    'overwrite_bytes_randomly',
    'extract_byte_values',
    'validate_byte_range',
]
