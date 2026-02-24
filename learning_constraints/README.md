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

## Module Architecture

```
learning_constraints/
├── main.py              # Orchestrator - coordinates entire process
├── config.py            # Configuration and GlobalState
├── parsers.py           # File parsing and value extraction
├── mutators.py          # File mutation (abstraction & overwrite)
├── validators.py        # File format validation
├── parallel.py          # Multi-process parallel execution
├── checkpoint.py        # Progress saving/resuming
├── transformers.py      # Result JSON transformation
├── result_saver.py      # Result file saving
├── statistics.py        # Statistics reporting
├── checksum_detector.py # CRC/checksum detection
└── utils.py             # Shared utility functions
```

## Processing Flow

### Complete Process Flow

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. INITIALIZATION                                               │
│    Orchestrator → GlobalState → CheckpointManager               │
│    (Load checkpoint if resuming)                                │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. TEMPLATE MINING                                              │
│    FileParser.mine_interesting_values_from_template()           │
│    Template (png.bt) → ffcompile → Extract predefined values    │
│    → Save template_values.json                                  │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. FILE PROCESSING (for each file in directory)                 │
│                                                                 │
│    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │
│    │  Worker 1   │     │  Worker 2   │     │  Worker N   │     │
│    │ (parallel)  │     │ (parallel)  │ ... │ (parallel)  │     │
│    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘     │
│           │                   │                   │             │
│           └───────────────────┴───────────────────┘             │
│                               │                                 │
│                               ▼                                 │
│                      Merge Worker States                        │
│                      Enforce Blacklist Limits                   │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SAVE RESULTS                                                 │
│    Filter blacklisted → Save JSON files → Transform/flatten     │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
END (Print statistics)
```

### Single File Processing

```
INPUT FILE (e.g., image.png)
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ PARSE: FileParser.parse_file_structure()                        │
│                                                                 │
│   Run fuzzer → Get byte ranges with attributes                  │
│        │                                                        │
│        ▼                                                        │
│   For each attribute:                                           │
│        │                                                        │
│        ├── Size > 8 bytes? ──YES──► Add to blacklisted_by_size  │
│        │                           (skip this attribute)        │
│        │                                                        │
│        └── NO ─► Extract hex value                              │
│                       │                                         │
│                       ▼                                         │
│                  Store in nested_values_hex                     │
│                       │                                         │
│                       ▼                                         │
│                  Count > 30? ──YES──► Add to blacklisted_by_count│
│                       │              (remove values)            │
│                       │                                         │
│                       └── NO ─► Keep values                     │
│                                                                 │
│   Also: Detect checksums/CRCs (ChecksumDetector)                │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ MUTATE: FileMutator.mutate_file_completely()                    │
│                                                                 │
│   For each byte range (not blacklisted):                        │
│        │                                                        │
│        ├── Smart Abstraction Mutation                           │
│        │        │                                               │
│        │        ▼                                               │
│        │   Modify bytes → Validate (FileValidator)              │
│        │        │                                               │
│        │        ├── VALID ──► Save special file                 │
│        │        │             Parse for new attributes          │
│        │        │             Increment valid_abstractions      │
│        │        │                                               │
│        │        └── INVALID ─► Discard                          │
│        │                                                        │
│        └── Random Overwrite Mutation                            │
│                 │                                               │
│                 ▼                                               │
│            Overwrite with random bytes → Validate               │
│                 │                                               │
│                 ├── VALID ──► Increment valid_overwrites        │
│                 │                                               │
│                 └── INVALID ─► Discard                          │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
NEXT FILE (or END if no more files)
```

### Blacklisting Flow

```
Attribute parsed
      │
      ▼
 Size > 8 bytes? ───YES───► blacklisted_by_size
      │                            │
      NO                           ▼
      │                     Remove from values
      ▼                     Skip in mutations
 Add value to set
      │
      ▼
 Count > 30? ───────YES───► blacklisted_by_count
      │                            │
      NO                           ▼
      │                     Remove all values
      ▼                     Skip in mutations
 Keep value
      │
      ▼
 [During parallel merge]
      │
 Already blacklisted? ─YES─► Skip merge (don't add new values)
      │
      NO
      │
      ▼
 Merge worker values
      │
      ▼
 Count > 30 now? ───YES───► blacklisted_by_count
      │
      NO
      │
      ▼
 Keep merged values
```

## Key Data Structures

### GlobalState

Holds all collected data during processing:

| Field                      | Type          | Description                                       |
| -------------------------- | ------------- | ------------------------------------------------- |
| `nested_values_hex`        | `defaultdict` | Hierarchical dict → set of hex values             |
| `blacklisted_by_size`      | `set`         | Attributes > MAX_ATTRIBUTE_SIZE_BYTES (8)         |
| `blacklisted_by_count`     | `set`         | Attributes > MAX_UNIQUE_VALUES_PER_ATTRIBUTE (30) |
| `checksum_algorithms`      | `dict`        | Detected CRC types per chunk                      |
| `valid_abstractions_count` | `int`         | Successful abstraction mutations                  |
| `valid_overwrites_count`   | `int`         | Successful overwrite mutations                    |

### ByteRange (dataclass)

Represents a parsed attribute with byte positions:

```python
@dataclass
class ByteRange:
    start: int        # Start byte offset
    end: int          # End byte offset
    attribute: str    # Full attribute path (e.g., "file~chunk~data")

    @property
    def size(self) -> int
    @property
    def cleaned_key(self) -> str
    def is_within_size_limit(self) -> bool
```

## Module Responsibilities

| Module                   | Responsibility                                          |
| ------------------------ | ------------------------------------------------------- |
| **main.py**              | High-level orchestration, coordinates workflow          |
| **config.py**            | Configuration constants, GlobalState class              |
| **parsers.py**           | Parse files with fuzzer, extract byte ranges and values |
| **mutators.py**          | Mutation strategies (abstraction, overwrite)            |
| **validators.py**        | Validate files using external tools (ImageMagick, etc.) |
| **parallel.py**          | Multi-process execution, state merging                  |
| **checkpoint.py**        | Save/restore progress for resumability                  |
| **transformers.py**      | Flatten nested JSON results                             |
| **result_saver.py**      | Write all result files to disk                          |
| **statistics.py**        | Print processing statistics                             |
| **checksum_detector.py** | Detect CRC algorithms in file chunks                    |
| **utils.py**             | Shared helpers (key cleaning, byte operations)          |

## Configuration

Key settings in `config.py`:

| Setting                           | Default | Description                           |
| --------------------------------- | ------- | ------------------------------------- |
| `MAX_ATTRIBUTE_SIZE_BYTES`        | 8       | Blacklist attributes larger than this |
| `MAX_UNIQUE_VALUES_PER_ATTRIBUTE` | 30      | Blacklist attributes with more values |
| `PARALLEL_WORKERS`                | 10      | Number of parallel workers            |
| `CHECKPOINT_SAVE_INTERVAL`        | 10      | Save checkpoint every N files         |
| `ENABLE_CHECKSUM_DETECTION`       | True    | Detect CRC algorithms                 |

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

## Detailed Flow Diagrams (Mermaid)

For interactive visualization, these Mermaid diagrams provide detailed views of each process.

### Execution Flow Overview

```mermaid
flowchart TD
    subgraph Init["1. Initialization"]
        A[Start] --> B[Create Orchestrator]
        B --> C[Initialize GlobalState]
        C --> D[Load Checkpoint if resuming]
    end

    subgraph Template["2. Template Mining"]
        D --> E[Mine template values]
        E --> F[Save template_values.json]
    end

    subgraph Process["3. File Processing"]
        F --> G[Process source directory]
        G --> H{Parallel?}
        H -->|Yes| I[Parallel Workers]
        H -->|No| J[Sequential Processing]
        I --> K[Merge Worker States]
        J --> K
    end

    subgraph Save["4. Save Results"]
        K --> L[Filter blacklisted attributes]
        L --> M[Save parsed_values_hex.json]
        M --> N[Save blacklist files]
        N --> O[Transform/flatten results]
    end

    subgraph Report["5. Report"]
        O --> P[Print statistics]
        P --> Q[End]
    end
```

### Data Flow Diagram

```mermaid
flowchart LR
    subgraph Input
        F1[Input Files<br>e.g., image.png]
        T1[Template File<br>e.g., png.bt]
    end

    subgraph Parsing
        P1[FileParser]
        CD[ChecksumDetector]
    end

    subgraph State["GlobalState"]
        NV[nested_values_hex<br>Hierarchical dict of sets]
        BS[blacklisted_by_size<br>Attributes > 8 bytes]
        BC[blacklisted_by_count<br>Attributes > 30 values]
        CA[checksum_algorithms<br>Detected CRCs]
    end

    subgraph Mutation
        M1[FileMutator]
        V1[FileValidator]
    end

    subgraph Output
        O1[parsed_values_hex_original.json]
        O2[blacklisted_by_size.json]
        O3[blacklisted_by_count.json]
        O4[*_flattened.json]
    end

    F1 --> P1
    T1 --> P1
    P1 --> NV
    P1 --> BS
    P1 --> BC
    P1 --> CD
    CD --> CA
    P1 --> M1
    M1 --> V1
    V1 -->|Valid?| NV
    NV --> O1
    BS --> O2
    BC --> O3
    O1 --> O4
```

### Single File Processing Flow

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant P as FileParser
    participant M as FileMutator
    participant V as FileValidator
    participant G as GlobalState

    O->>P: parse_file_structure(file_path)
    P->>P: Run fuzzer to get byte ranges
    P->>P: Filter by size (>8 bytes → blacklist)
    P->>P: Extract hex values
    P->>G: Store in nested_values_hex
    P->>G: Check value count (>30 → blacklist)
    P-->>O: Return (original_ranges, filtered_ranges)

    O->>M: mutate_file_completely(file, ranges)

    loop For each byte range
        M->>M: Smart abstraction mutation
        M->>V: Validate mutated file
        V-->>M: Valid/Invalid
        alt Valid abstraction
            M->>G: Increment valid_abstractions
            M->>P: Parse new attributes
        end

        M->>M: Random overwrite mutation
        M->>V: Validate mutated file
        V-->>M: Valid/Invalid
        alt Valid overwrite
            M->>G: Increment valid_overwrites
        end
    end
```

### Parallel Processing Flow

```mermaid
flowchart TD
    subgraph Main["Main Process"]
        A[File List] --> B[Split into batches]
        B --> C[Create Worker Pool]
        K[Merge Results] --> L[Save Checkpoint]
    end

    subgraph Workers["Worker Processes"]
        C --> W1[Worker 1<br>Own GlobalState]
        C --> W2[Worker 2<br>Own GlobalState]
        C --> W3[Worker N<br>Own GlobalState]
        W1 --> D1[Process Files]
        W2 --> D2[Process Files]
        W3 --> D3[Process Files]
        D1 --> R1[Return Serialized State]
        D2 --> R2[Return Serialized State]
        D3 --> R3[Return Serialized State]
    end

    R1 --> K
    R2 --> K
    R3 --> K
```

### Blacklisting Logic

```mermaid
flowchart TD
    A[Parse Attribute] --> B{Size > 8 bytes?}
    B -->|Yes| C[Add to blacklisted_by_size]
    C --> D[Remove from nested_values_hex]
    B -->|No| E[Extract hex value]
    E --> F[Add to nested_values_hex]
    F --> G{Value count > 30?}
    G -->|Yes| H[Add to blacklisted_by_count]
    H --> I[Remove from nested_values_hex]
    G -->|No| J[Continue]

    subgraph Parallel["During Parallel Merge"]
        K[Worker returns values] --> L{Attribute blacklisted?}
        L -->|Yes| M[Skip merge]
        L -->|No| N[Merge values]
        N --> O{Count > 30 after merge?}
        O -->|Yes| H
        O -->|No| P[Keep values]
    end

    subgraph Save["Before Saving"]
        Q[Final nested_values_hex] --> R[Filter blacklisted keys]
        R --> S[Write to JSON]
    end
```

## Documentation

For comprehensive documentation, usage examples, and detailed explanations, see:
**[README_LEARNING_CONSTRAINTS_COMPREHENSIVE.md](../README_LEARNING_CONSTRAINTS_COMPREHENSIVE.md)**
