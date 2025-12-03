"""
Configuration module for learning constraints system.
Contains all constants, paths, and configuration settings.
"""
import os
import collections
from datetime import datetime

class Config:
    """Configuration class containing all settings and paths."""

    # Supported file types
    SUPPORTED_FILE_TYPES = [
        "avi", "bmp", "gif", "jpg", "png", "midi", "pcap", "wav", "mp4", "zip"
    ]

    # Current file type (can be changed as needed)
    FILE_TYPE = "gif"

    # Base directories
    DATA_DIR = f"./testcases_4_learn/{FILE_TYPE}/"
    RESULTS_OUTPUT_DIR = f"./testcases_4_learn/results/{FILE_TYPE}"

    # Logging directories (will be set dynamically with timestamp)
    LOGS_BASE_DIR = "./logs"
    CURRENT_LOG_DIR = None  # Will be set when logging is initialized
    CURRENT_RESULTS_DIR = None  # Will be set when logging is initialized
    CURRENT_ABSTRACTED_DIR = None  # Will be set when logging is initialized
    CURRENT_ABSTRACTED_SPECIAL_DIR = None  # Will be set when logging is initialized
    LOG_FILE = None  # Will be set when logging is initialized

    # Subdirectories
    PASSED_DIR = os.path.join(DATA_DIR, "valid_files/")
    FAILED_DIR = os.path.join(DATA_DIR, "failed/")

    # Output files
    STATS_FILE_HEX = os.path.join(RESULTS_OUTPUT_DIR, f"{FILE_TYPE}_parsed_values_hex_original.json")
    BLACKLISTED_ATTRIBUTES_FILE = os.path.join(RESULTS_OUTPUT_DIR, f"{FILE_TYPE}_blacklisted_attributes.json")
    # Checksum detection output
    CHECKSUM_ALGO_FILE = os.path.join(RESULTS_OUTPUT_DIR, f"{FILE_TYPE}_checksum_algorithms.json")

    # Processing limits
    MAX_ATTRIBUTE_SIZE_BYTES = 8
    MAX_ABSTRACTION_ATTEMPTS = 10
    MAX_OVERWRITE_ATTEMPTS = 10

    # Feature toggles
    ENABLE_CHECKSUM_DETECTION = True

    # ZIP-specific checksum validation:
    # If True: Decompress frData (using frCompression method) and validate frCrc checksum
    #          Supports STORED (method 0) and DEFLATE (method 8) compression
    #          This provides actual validation but is slower
    # If False: Assume CRC-32 based on ZIP specification (default)
    #           This is faster but doesn't validate the actual checksum
    ZIP_VALIDATE_CHECKSUM_WITH_DECOMPRESSION = True

    # Validation tools configuration
    VALIDATION_TOOLS = {
        "images": ["gif", "jpg", "png", "bmp"],
        "audio": ["mp3", "wav"],
        "video": ["mp4", "avi"],
        "archive": ["zip"],
        "network": ["pcap"],
        "music": ["midi"]
    }

    @classmethod
    def get_fuzzer_executable(cls):
        """Get the fuzzer executable name for current file type."""
        return f"./{cls.FILE_TYPE}-fuzzer"

    @classmethod
    def initialize_logging(cls, file_type=None):
        """
        Initialize logging directories with timestamp.

        Args:
            file_type (str, optional): The file type to use in directory name. If None, uses cls.FILE_TYPE

        Returns:
            str: Path to the log file
        """
        if file_type is None:
            file_type = cls.FILE_TYPE

        # Create timestamp-based directory name: YYYYMMDD_HHMMSS_filetype
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir_name = f"{timestamp}_{file_type}"

        # Set up directory paths
        cls.CURRENT_LOG_DIR = os.path.join(cls.LOGS_BASE_DIR, log_dir_name)
        cls.CURRENT_RESULTS_DIR = os.path.join(cls.CURRENT_LOG_DIR, "results")
        cls.CURRENT_ABSTRACTED_DIR = os.path.join(cls.CURRENT_LOG_DIR, "abstracted")
        cls.CURRENT_ABSTRACTED_SPECIAL_DIR = os.path.join(cls.CURRENT_LOG_DIR, "abstracted_special")
        cls.LOG_FILE = os.path.join(cls.CURRENT_LOG_DIR, "learning_constraints.log")

        # Create directories
        os.makedirs(cls.CURRENT_LOG_DIR, exist_ok=True)
        os.makedirs(cls.CURRENT_RESULTS_DIR, exist_ok=True)
        os.makedirs(cls.CURRENT_ABSTRACTED_DIR, exist_ok=True)
        os.makedirs(cls.CURRENT_ABSTRACTED_SPECIAL_DIR, exist_ok=True)

        return cls.LOG_FILE

    @classmethod
    def ensure_directories_exist(cls):
        """Create all necessary directories if they don't exist."""
        directories = [
            cls.PASSED_DIR,
            cls.FAILED_DIR,
            cls.RESULTS_OUTPUT_DIR
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    @classmethod
    def set_file_type(cls, file_type):
        """Change the current file type and update all related paths."""
        if file_type not in cls.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_type}")

        cls.FILE_TYPE = file_type
        cls.DATA_DIR = f"./testcases_4_learn/{file_type}/"
        cls.RESULTS_OUTPUT_DIR = f"./testcases_4_learn/results/{file_type}"
        cls.PASSED_DIR = os.path.join(cls.DATA_DIR, "valid_files/")
        cls.FAILED_DIR = os.path.join(cls.DATA_DIR, "failed/")
        cls.STATS_FILE_HEX = os.path.join(cls.RESULTS_OUTPUT_DIR, f"{file_type}_parsed_values_hex_original.json")
        cls.BLACKLISTED_ATTRIBUTES_FILE = os.path.join(cls.RESULTS_OUTPUT_DIR, f"{file_type}_blacklisted_attributes.json")
        cls.CHECKSUM_ALGO_FILE = os.path.join(cls.RESULTS_OUTPUT_DIR, f"{file_type}_checksum_algorithms.json")


class GlobalState:
    """Global state management for the learning constraints process."""

    def __init__(self):
        # Nested dictionaries to store extracted values
        self.nested_values_hex = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

        # Blacklist for attributes that have been found to be larger than max size
        self.blacklisted_attributes = set()

        # Detected checksum algorithms and metadata
        # Structure:
        # {
        #   "by_chunk_type": { "IHDR": ["CRC-32"], ... },
        #   "compression_methods": { "0": "STORED", "8": "DEFLATE", ... }  # ZIP only
        # }
        self.checksum_algorithms = {"by_chunk_type": {}, "compression_methods": {}}

        # Output counts
        self.valid_abstractions_count = 0
        self.valid_abstractions_special_count = 0
        self.valid_overwrites_count = 0

    def reset(self):
        """Reset all state variables."""
        self.nested_values_hex.clear()
        self.blacklisted_attributes.clear()
        self.checksum_algorithms = {"by_chunk_type": {}, "compression_methods": {}}
        self.valid_abstractions_count = 0
        self.valid_abstractions_special_count = 0
        self.valid_overwrites_count = 0

    def get_stats(self):
        """Get current statistics."""
        return {
            "valid_abstractions": self.valid_abstractions_count,
            "valid_abstractions_special": self.valid_abstractions_special_count,
            "valid_overwrites": self.valid_overwrites_count,
            "blacklisted_attributes": len(self.blacklisted_attributes)
        }
