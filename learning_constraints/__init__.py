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
- parallel: Multi-process execution and state merging
- checkpoint: Progress saving/resuming
- transformers: Result transformation and JSON flattening
- utils: Utility functions and helpers
- main: Main orchestrator for the complete process

Usage (the ``__main__`` guard is required: worker processes re-import the calling module
on platforms that use the "spawn" start method, such as macOS and Windows):

    from learning_constraints import LearningConstraintsOrchestrator

    def main():
        orchestrator = LearningConstraintsOrchestrator(file_type="gif", source_dir="path/to/gifs")
        results = orchestrator.run_complete_process()
        return 0 if results["ok"] else 2

    if __name__ == "__main__":
        raise SystemExit(main())
"""

from .config import Config, GlobalState
from .validators import FileValidator
from .parsers import FileParser
from .mutators import FileMutator
from .transformers import ResultTransformer
from .checkpoint import CheckpointManager
from .parallel import process_files_parallel, merge_global_states, get_worker_count, FileResultLogger
from .main import LearningConstraintsOrchestrator, main
from .utils import (
    ByteRange,
    convert_sets_to_lists,
    strip_index,
    split_index,
    clean_attribute_key,
    clean_attribute_path,
    insert_nested_dict,
    iter_leaf_paths,
    overwrite_bytes_randomly,
    extract_byte_values,
    validate_byte_range,
)

__version__ = "1.1.0"
__author__ = "Learning Constraints Team"
__description__ = "A modular system for file format fuzzing and learning through constraint discovery"


def set_file_type(file_type):
    """Set the file type for the entire package."""
    Config.set_file_type(file_type)


def get_supported_file_types():
    """Return the list of supported file types."""
    return Config.SUPPORTED_FILE_TYPES.copy()


def create_orchestrator(file_type=None, log_level=None, max_files=None, **kwargs):
    """Create a new LearningConstraintsOrchestrator instance."""
    if log_level is None:
        import logging
        log_level = logging.INFO
    return LearningConstraintsOrchestrator(file_type=file_type, log_level=log_level, max_files=max_files, **kwargs)


__all__ = [
    'LearningConstraintsOrchestrator',
    'Config',
    'GlobalState',
    'FileValidator',
    'FileParser',
    'FileMutator',
    'ResultTransformer',
    'CheckpointManager',
    'FileResultLogger',
    'ByteRange',
    'main',
    'set_file_type',
    'get_supported_file_types',
    'create_orchestrator',
    'process_files_parallel',
    'merge_global_states',
    'get_worker_count',
    'convert_sets_to_lists',
    'strip_index',
    'split_index',
    'clean_attribute_key',
    'clean_attribute_path',
    'insert_nested_dict',
    'iter_leaf_paths',
    'overwrite_bytes_randomly',
    'extract_byte_values',
    'validate_byte_range',
]
