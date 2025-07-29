# Learning Constraints - Comprehensive Guide

## Overview

Learning Constraints is a modular system for file format fuzzing and constraint discovery through systematic analysis. The system parses file structures, performs intelligent mutations, and discovers format constraints by analyzing the results.

## Architecture

### Module Structure
```
learning_constraints/
├── __init__.py          # Package initialization and exports
├── config.py            # Configuration and global state management
├── validators.py        # File validation for different formats
├── parsers.py          # File structure parsing and byte extraction
├── mutators.py         # File mutation through smart abstraction and random overwrites
├── transformers.py     # Result transformation and JSON flattening
├── utils.py            # Utility functions and helpers
├── main.py             # Main orchestrator for the complete process
└── README.md           # Basic module documentation
```

### Data Directory Structure
```
testcases_4_learn/
└── {file_type}/
    ├── valid_files/         # Valid input files for processing
    ├── abstracted/          # Temporary mutated files
    ├── abstracted_special/  # Files that revealed new attributes
    ├── failed/              # Invalid files
    └── results/             # JSON output files and transformed results
```

## Core Components

### 1. Configuration Management (`config.py`)
- **Config class**: Centralized configuration with file type management
- **GlobalState class**: Tracks processing statistics and blacklisted attributes
- **Dynamic paths**: Automatically updates paths when file type changes
- **Directory management**: Creates required directories automatically

### 2. File Validation (`validators.py`)
- **FileValidator class**: Format-specific validation using external tools
- **Supported formats**: Images (ImageMagick), Audio/Video (FFmpeg), Archives (zipfile), Network (tshark), MIDI (timidity)
- **Validation strategies**: Each file type uses appropriate validation tools

### 3. File Parsing (`parsers.py`)
- **FileParser class**: Extracts file structure and byte ranges using format-specific fuzzers
- **Attribute extraction**: Identifies file format attributes and their byte positions
- **Blacklist management**: Filters out attributes larger than 8 bytes
- **Hierarchical processing**: Handles nested file structures

### 4. File Mutation (`mutators.py`)
- **FileMutator class**: Performs two types of mutations:
  - **Smart Abstraction Mutation**: Uses fuzzer's abstract command for intelligent mutations
  - **Random Overwrite Mutation**: Performs random byte overwrites for chaos testing
- **New attribute discovery**: Identifies when mutations reveal new format attributes
- **Validation integration**: Ensures mutated files remain valid

### 5. Result Transformation (`transformers.py`)
- **ResultTransformer class**: Flattens nested JSON structures for easier analysis
- **JSON flattening**: Converts nested structures to flat key-value pairs
- **Duplicate key merging**: Combines values from duplicate keys into arrays
- **Large value handling**: Replaces arrays >10 items with "More than 10 values"
- **Selective processing**: Only transforms hex values files, preserves blacklist files

### 6. Main Orchestrator (`main.py`)
- **LearningConstraintsOrchestrator class**: Coordinates the complete workflow
- **File processing**: Handles individual files and batch directory processing
- **Result management**: Saves results and transforms them automatically
- **Statistics tracking**: Provides comprehensive processing statistics
- **Configurable limits**: Supports limiting the number of files to process

## Supported File Types

- **Images**: GIF, JPG, PNG, BMP
- **Audio**: MP3, WAV  
- **Video**: MP4, AVI
- **Archives**: ZIP
- **Network**: PCAP
- **Music**: MIDI

## Processing Workflow

1. **File Parsing**: Extract file structure and identify byte ranges
2. **Mutation**: Perform smart abstraction and random overwrite mutations
3. **Validation**: Verify mutated files remain valid
4. **Attribute Discovery**: Identify new format attributes revealed by mutations
5. **Result Saving**: Save hex values and blacklisted attributes to JSON files
6. **Result Transformation**: Flatten hex values JSON for easier analysis
7. **Statistics**: Generate comprehensive processing statistics

## Output Files

### Generated Results
```
testcases_4_learn/results/{file_type}/
├── {file_type}_parsed_values_hex_original.json           # Raw hex values (nested)
├── {file_type}_parsed_values_hex_original_flattened.json # Flattened hex values
└── {file_type}_blacklisted_attributes.json              # Blacklisted attributes info
```

### File Contents

#### Hex Values File (Flattened)
```json
{
  "attribute_name": ["value1", "value2"],
  "another_attribute": "single_value",
  "large_attribute": "More than 10 values"
}
```

#### Blacklisted Attributes File
```json
{
  "blacklisted_attributes": ["large_attr1", "large_attr2"],
  "total_count": 2,
  "file_type": "png",
  "description": "Attributes that were blacklisted due to size > 8 bytes"
}
```

## Usage Examples

### Basic Usage
```python
from learning_constraints import LearningConstraintsOrchestrator

# Process all files of a specific type
orchestrator = LearningConstraintsOrchestrator(file_type="png")
results = orchestrator.run_complete_process()

# Process limited number of files
orchestrator = LearningConstraintsOrchestrator(file_type="gif", max_files=5)
results = orchestrator.run_complete_process()
```

### Command Line Usage
```bash
# Process all BMP files
python run_learning_constraints.py bmp

# Process only 10 PNG files  
python run_learning_constraints.py png 10

# Process all files (default: gif)
python run_learning_constraints.py
```

### Individual Component Usage
```python
from learning_constraints import FileParser, FileMutator, ResultTransformer, GlobalState

# Initialize components
state = GlobalState()
parser = FileParser(state)
mutator = FileMutator(state)
transformer = ResultTransformer()

# Parse file structure
byte_ranges = parser.parse_file_structure("image.png")

# Perform mutations
mutator.mutate_file_completely("image.png", byte_ranges)

# Transform results
transformer.transform_results_directory()
```

### Configuration Management
```python
from learning_constraints import Config, set_file_type

# Change file type globally
set_file_type("jpg")

# Access configuration
print(f"Current type: {Config.FILE_TYPE}")
print(f"Data directory: {Config.DATA_DIR}")
print(f"Results directory: {Config.RESULTS_OUTPUT_DIR}")

# Create directories
Config.ensure_directories_exist()
```

## Advanced Features

### File Limit Control
```python
# Process specific number of files
orchestrator = LearningConstraintsOrchestrator(file_type="png", max_files=10)

# Process directory with limit
successful, total = orchestrator.process_directory("path/to/files", max_files=5)
```

### Manual Result Transformation
```python
from learning_constraints import ResultTransformer

transformer = ResultTransformer()

# Transform specific files
transformer.transform_specific_files(["path/to/hex_file.json"])

# Transform results directory
successful, total = transformer.transform_results_directory()
```

### Direct JSON Flattening
```python
from learning_constraints import flatten_json

nested_data = {
    "level1": {
        "level2": {
            "attribute": "value"
        }
    }
}

flattened = flatten_json(nested_data)
# Result: {"attribute": "value"}
```

## Requirements

### External Tools
- **ImageMagick**: For image validation (`identify` command)
- **FFmpeg**: For audio/video validation (`ffprobe` command)  
- **Wireshark**: For PCAP validation (`tshark` command)
- **TiMidity**: For MIDI validation (`timidity` command)

### Format-Specific Fuzzers
- Requires `{file_type}-fuzzer` executables (e.g., `gif-fuzzer`, `png-fuzzer`)
- Fuzzers must support `parse` and `abstract` commands

## Installation & Setup

1. **Place files**: Put valid files in `testcases_4_learn/{file_type}/valid_files/`
2. **Install tools**: Ensure external validation tools are installed
3. **Fuzzer setup**: Make sure format-specific fuzzers are available
4. **Run processing**: Use command line or Python API

## Statistics & Monitoring

The system provides comprehensive statistics:
- **Files processed**: Valid files and special files counts
- **Mutations**: Smart abstraction and random overwrite counts  
- **Discoveries**: New attributes found during processing
- **Transformations**: Result transformation success rates
- **Blacklisted items**: Attributes filtered due to size

## Error Handling

- **Graceful degradation**: Continues processing even if individual files fail
- **Comprehensive logging**: Detailed logs for debugging and monitoring
- **Validation checks**: Ensures files remain valid after mutations
- **Directory management**: Automatically creates required directories

## Performance Considerations

- **File limits**: Use `max_files` parameter for testing or time-limited runs
- **Batch processing**: Efficiently processes multiple files
- **Memory management**: Handles large files and result sets appropriately
- **Parallel potential**: Architecture supports future parallel processing

This comprehensive system provides a complete solution for file format constraint discovery through systematic mutation and analysis.
