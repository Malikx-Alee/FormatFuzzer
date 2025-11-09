# Learning Constraints Module

A modular system for file format fuzzing and constraint discovery through systematic analysis. This module provides tools for parsing file structures, performing mutations, and discovering format constraints.

## Quick Start

```python
from learning_constraints import LearningConstraintsOrchestrator

# Process PNG files
orchestrator = LearningConstraintsOrchestrator(file_type="png")
results = orchestrator.run_complete_process()
```

## Command Line Usage

```bash
# Process BMP files
python run_learning_constraints.py bmp

# Process 10 PNG files
python run_learning_constraints.py png 10
```

## Documentation

For comprehensive documentation, usage examples, and detailed explanations, see:
**[README_LEARNING_CONSTRAINTS_COMPREHENSIVE.md](../README_LEARNING_CONSTRAINTS_COMPREHENSIVE.md)**

## Supported File Types

- **Images**: GIF, JPG, PNG, BMP
- **Audio**: MP3, WAV
- **Video**: MP4, AVI
- **Archives**: ZIP
- **Network**: PCAP
- **Music**: MIDI

## Requirements

- **ImageMagick**: For image validation
- **FFmpeg**: For audio/video validation
- **Wireshark**: For PCAP validation
- **TiMidity**: For MIDI validation
- **Format-specific fuzzers**: `{file_type}-fuzzer` executables
