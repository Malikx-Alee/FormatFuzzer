# Learning Constraints Module

A modular and well-organized system for file format fuzzing and learning through constraint discovery. This module provides tools for parsing file structures, performing abstractions, and discovering new format attributes through systematic analysis.

## Overview

The Learning Constraints module has been refactored from a monolithic script into a well-structured Python package with clear separation of concerns. It supports multiple file formats and provides a comprehensive framework for format analysis.

## Module Structure

```
learning_constraints/
├── __init__.py          # Package initialization and exports
├── config.py            # Configuration and global state management
├── validators.py        # File validation for different formats
├── parsers.py          # File structure parsing and byte extraction
├── mutators.py         # File mutation through smart abstraction and random overwrites
├── utils.py            # Utility functions and helpers
├── main.py             # Main orchestrator for the complete process
└── README.md           # This documentation file
```

## Components

### 1. Configuration (`config.py`)

- **Config**: Centralized configuration management
- **GlobalState**: Global state tracking for the learning process
- Manages file types, paths, and processing parameters

### 2. Validators (`validators.py`)

- **FileValidator**: File validation for different formats
- Supports images, audio, video, archives, network captures, and MIDI files
- Uses appropriate external tools for validation

### 3. Parsers (`parsers.py`)

- **FileParser**: File structure parsing and byte range extraction
- Interfaces with format-specific fuzzers
- Manages attribute extraction and blacklisting

### 4. Mutators (`mutators.py`)

- **FileMutator**: File mutation operations through two strategies
- Performs smart abstraction-based mutations and random overwrite mutations
- Tracks new attribute discovery

### 5. Utilities (`utils.py`)

- Helper functions for data conversion and manipulation
- Byte extraction and validation utilities
- Nested dictionary management

### 6. Main Orchestrator (`main.py`)

- **LearningAbstractionOrchestrator**: Main coordination class
- Manages the complete processing pipeline
- Provides logging and statistics

## Supported File Types

- **Images**: GIF, JPG, PNG, BMP
- **Audio**: MP3, WAV
- **Video**: MP4, AVI
- **Archives**: ZIP
- **Network**: PCAP
- **Music**: MIDI

## Usage

### Basic Usage

```python
from learning_constraints import LearningConstraintsOrchestrator

# Create orchestrator for GIF files (process all files)
orchestrator = LearningConstraintsOrchestrator(file_type="gif")

# Create orchestrator with file limit (process only 10 files)
orchestrator = LearningConstraintsOrchestrator(file_type="gif", max_files=10)

# Run the complete process
results = orchestrator.run_complete_process()
```

### Processing Individual Files

```python
from learning_constraints import LearningConstraintsOrchestrator

orchestrator = LearningConstraintsOrchestrator(file_type="png")

# Process a single file
success = orchestrator.process_file("path/to/image.png")

# Process all files in a directory
successful, total = orchestrator.process_directory("path/to/images/")

# Process only first 5 files in a directory
successful, total = orchestrator.process_directory("path/to/images/", max_files=5)
```

### Using Individual Components

```python
from learning_constraints import FileParser, FileValidator, FileMutator, GlobalState

# Initialize global state
state = GlobalState()

# Parse a file
parser = FileParser(state)
byte_ranges = parser.parse_file_structure("file.gif")

# Validate a file
validator = FileValidator()
is_valid = validator.is_valid_file("file.gif", "gif")

# Mutate a file
mutator = FileMutator(state)
mutator.mutate_file_completely("file.gif", byte_ranges)
```

### Configuration Management

```python
from learning_constraints import Config, set_file_type

# Change file type globally
set_file_type("jpg")

# Access configuration
print(Config.FILE_TYPE)
print(Config.SUPPORTED_FILE_TYPES)

# Ensure directories exist
Config.ensure_directories_exist()
```

## Migration from Original Script

The refactored module maintains backward compatibility through convenience functions:

```python
# Old style (still works)
from learning_constraints import parse_file_new, abstract_file, is_valid_file

byte_ranges = parse_file_new("file.gif")
abstract_file("file.gif", byte_ranges)
valid = is_valid_file("file.gif")

# New style (recommended)
from learning_constraints import LearningConstraintsOrchestrator

orchestrator = LearningConstraintsOrchestrator()
orchestrator.process_file("file.gif")
```

## Directory Structure

The module expects the following directory structure:

```
testcases_4_learn/
└── {file_type}/
    ├── passed/              # Valid input files
    ├── abstracted/          # Temporary abstracted files
    ├── abstracted_special/  # Files with new attributes
    ├── failed/              # Invalid files
    └── results/             # JSON statistics files
```

## Features

### Improved Code Organization

- Clear separation of concerns
- Modular design for easy maintenance
- Proper error handling and logging
- Type hints and documentation

### Enhanced Functionality

- Configurable file type processing
- Comprehensive logging system
- Statistics tracking and reporting
- Batch processing capabilities

### Better Error Handling

- Graceful error recovery
- Detailed error messages
- Logging of all operations

## Requirements

The module requires the following external tools based on file types:

- **ImageMagick**: For image validation (`identify` command)
- **FFmpeg**: For audio/video validation (`ffprobe` command)
- **Wireshark**: For PCAP validation (`tshark` command)
- **TiMidity**: For MIDI validation (`timidity` command)
- **Format-specific fuzzers**: `{file_type}-fuzzer` executables

## Example: Complete Workflow

```python
import logging
from learning_constraints import LearningConstraintsOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create orchestrator
orchestrator = LearningConstraintsOrchestrator(
    file_type="gif",
    log_level=logging.INFO
)

# Run complete process
results = orchestrator.run_complete_process()

# Print results
print(f"Processed {results['passed_files']['total']} files")
print(f"Found {results['stats']['valid_abstractions']} valid abstractions")
```

This refactored module provides a much more maintainable, extensible, and user-friendly interface for file format learning and abstraction.
