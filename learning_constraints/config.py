"""
Configuration module for learning constraints system.
Contains all constants, paths, and configuration settings.
"""
import os
import collections

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
    
    # Subdirectories
    PASSED_DIR = os.path.join(DATA_DIR, "passed/")
    ABSTRACTED_DIR = os.path.join(DATA_DIR, "abstracted/")
    ABSTRACTED_SPECIAL_DIR = os.path.join(DATA_DIR, "abstracted_special/")
    FAILED_DIR = os.path.join(DATA_DIR, "failed/")
    
    # Output files
    STATS_FILE_HEX = os.path.join(RESULTS_OUTPUT_DIR, f"{FILE_TYPE}_parsed_values_hex_original.json")
    BLACKLISTED_ATTRIBUTES_FILE = os.path.join(RESULTS_OUTPUT_DIR, f"{FILE_TYPE}_blacklisted_attributes.json")
    
    # Processing limits
    MAX_ATTRIBUTE_SIZE_BYTES = 8
    MAX_ABSTRACTION_ATTEMPTS = 10
    MAX_OVERWRITE_ATTEMPTS = 10
    
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
    def ensure_directories_exist(cls):
        """Create all necessary directories if they don't exist."""
        directories = [
            cls.PASSED_DIR,
            cls.FAILED_DIR,
            cls.ABSTRACTED_DIR,
            cls.ABSTRACTED_SPECIAL_DIR,
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
        cls.PASSED_DIR = os.path.join(cls.DATA_DIR, "passed/")
        cls.ABSTRACTED_DIR = os.path.join(cls.DATA_DIR, "abstracted/")
        cls.ABSTRACTED_SPECIAL_DIR = os.path.join(cls.DATA_DIR, "abstracted_special/")
        cls.FAILED_DIR = os.path.join(cls.DATA_DIR, "failed/")
        cls.STATS_FILE_HEX = os.path.join(cls.RESULTS_OUTPUT_DIR, f"{file_type}_parsed_values_hex_original.json")
        cls.BLACKLISTED_ATTRIBUTES_FILE = os.path.join(cls.RESULTS_OUTPUT_DIR, f"{file_type}_blacklisted_attributes.json")


class GlobalState:
    """Global state management for the learning constraints process."""
    
    def __init__(self):
        # Nested dictionaries to store extracted values
        self.nested_values_hex = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
        
        # Blacklist for attributes that have been found to be larger than max size
        self.blacklisted_attributes = set()
        
        # Output counts
        self.valid_abstractions_count = 0
        self.valid_abstractions_special_count = 0
        self.valid_overwrites_count = 0
    
    def reset(self):
        """Reset all state variables."""
        self.nested_values_hex.clear()
        self.blacklisted_attributes.clear()
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
