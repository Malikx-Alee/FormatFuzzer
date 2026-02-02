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
    FILE_TYPE = "jpg"

    # Base directories
    # DATA_DIR = f"./testcases_4_learn/valid_files/{FILE_TYPE}/"
    DATA_DIR = f"../Dataset/{FILE_TYPE}/"

    # Logging directories (will be set dynamically with timestamp)
    LOGS_BASE_DIR = "./logs"
    CURRENT_LOG_DIR = None  # Will be set when logging is initialized
    CURRENT_RESULTS_DIR = None  # Will be set when logging is initialized
    CURRENT_ABSTRACTED_DIR = None  # Will be set when logging is initialized
    CURRENT_ABSTRACTED_SPECIAL_DIR = None  # Will be set when logging is initialized
    LOG_FILE = None  # Will be set when logging is initialized

    # Processing limits
    MAX_ATTRIBUTE_SIZE_BYTES = 8
    MAX_UNIQUE_VALUES_PER_ATTRIBUTE = 30  # Blacklist attributes with more unique values
    MAX_ABSTRACTION_ATTEMPTS = 10
    MAX_OVERWRITE_ATTEMPTS = 10

    # Feature toggles
    ENABLE_CHECKSUM_DETECTION = True

    # Resume/Checkpoint settings
    # Set to True to resume from the last checkpoint, False to start fresh
    # Can also be set via environment variable: RESUME_RUN=true
    RESUME_MODE = False

    # Checkpoint settings
    CHECKPOINT_FILENAME = "checkpoint.json"  # Name of checkpoint file in log directory
    CHECKPOINT_SAVE_INTERVAL = 10  # Save checkpoint after every N files (1 = after each file)

    # ZIP-specific checksum validation:
    # If True: Decompress frData (using frCompression method) and validate frCrc checksum
    #          Supports STORED (method 0) and DEFLATE (method 8) compression
    #          This provides actual validation but is slower
    # If False: Assume CRC-32 based on ZIP specification (default)
    #           This is faster but doesn't validate the actual checksum
    ZIP_VALIDATE_CHECKSUM_WITH_DECOMPRESSION = True

    # Parallel processing settings
    # Number of worker processes for parallel file processing
    # Set to None to use all available CPU cores, or specify a number
    # Set to 1 to disable parallel processing
    PARALLEL_WORKERS = 10  # None = use all available CPU cores

    # Batch size for parallel processing (number of files to process in each batch)
    # Smaller batches mean more frequent checkpoint saves but more overhead
    PARALLEL_BATCH_SIZE = 100

    # Per-file timeout in seconds for parallel processing
    # If a file takes longer than this, it will be skipped and logged
    # Set to None to disable timeout (not recommended)
    PARALLEL_FILE_TIMEOUT = 300  # 5 minutes per file

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
    def set_file_type(cls, file_type):
        """Change the current file type and update all related paths."""
        if file_type not in cls.SUPPORTED_FILE_TYPES:
            raise ValueError(f"Unsupported file type: {file_type}")

        cls.FILE_TYPE = file_type
        # cls.DATA_DIR = f"./testcases_4_learn/valid_files/{file_type}/"
        cls.DATA_DIR = f"../Dataset/{file_type}/"

    @classmethod
    def set_resume_mode(cls, resume_mode):
        """
        Set the resume mode.

        Args:
            resume_mode (bool): True to resume from checkpoint, False to start fresh
        """
        cls.RESUME_MODE = resume_mode

    @classmethod
    def get_checkpoint_path(cls):
        """
        Get the path to the checkpoint file in the current log directory.

        Returns:
            str or None: Path to checkpoint file, or None if log directory not initialized
        """
        if cls.CURRENT_LOG_DIR:
            return os.path.join(cls.CURRENT_LOG_DIR, cls.CHECKPOINT_FILENAME)
        return None

    @classmethod
    def find_latest_checkpoint(cls, file_type=None):
        """
        Find the most recent checkpoint for the given file type.

        Args:
            file_type (str, optional): File type to search for. Uses cls.FILE_TYPE if None.

        Returns:
            tuple: (log_dir_path, checkpoint_path) or (None, None) if not found
        """
        if file_type is None:
            file_type = cls.FILE_TYPE

        if not os.path.exists(cls.LOGS_BASE_DIR):
            return None, None

        # Find directories matching pattern: YYYYMMDD_HHMMSS_filetype
        matching_dirs = []
        for dir_name in os.listdir(cls.LOGS_BASE_DIR):
            if dir_name.endswith(f"_{file_type}"):
                dir_path = os.path.join(cls.LOGS_BASE_DIR, dir_name)
                checkpoint_path = os.path.join(dir_path, cls.CHECKPOINT_FILENAME)
                if os.path.exists(checkpoint_path):
                    matching_dirs.append((dir_name, dir_path, checkpoint_path))

        if not matching_dirs:
            return None, None

        # Sort by directory name (which contains timestamp) to get the most recent
        matching_dirs.sort(reverse=True, key=lambda x: x[0])
        _, log_dir_path, checkpoint_path = matching_dirs[0]
        return log_dir_path, checkpoint_path

    @classmethod
    def restore_log_directory(cls, log_dir_path):
        """
        Restore the log directory paths from a previous run.

        Args:
            log_dir_path (str): Path to the log directory to restore
        """
        cls.CURRENT_LOG_DIR = log_dir_path
        cls.CURRENT_RESULTS_DIR = os.path.join(log_dir_path, "results")
        cls.CURRENT_ABSTRACTED_DIR = os.path.join(log_dir_path, "abstracted")
        cls.CURRENT_ABSTRACTED_SPECIAL_DIR = os.path.join(log_dir_path, "abstracted_special")
        cls.LOG_FILE = os.path.join(log_dir_path, "learning_constraints.log")


class GlobalState:
    """Global state management for the learning constraints process."""

    def __init__(self):
        # Nested dictionaries to store extracted values
        self.nested_values_hex = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

        # Separate blacklists for different reasons
        # Attributes blacklisted because their byte size > MAX_ATTRIBUTE_SIZE_BYTES
        self.blacklisted_by_size = set()
        # Attributes blacklisted because unique values count > MAX_UNIQUE_VALUES_PER_ATTRIBUTE
        self.blacklisted_by_count = set()

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

    @property
    def blacklisted_attributes(self):
        """Combined blacklist for backward compatibility - union of both blacklists."""
        return self.blacklisted_by_size | self.blacklisted_by_count

    def reset(self):
        """Reset all state variables."""
        self.nested_values_hex.clear()
        self.blacklisted_by_size.clear()
        self.blacklisted_by_count.clear()
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
            "blacklisted_by_size": len(self.blacklisted_by_size),
            "blacklisted_by_count": len(self.blacklisted_by_count),
            "blacklisted_total": len(self.blacklisted_attributes)
        }

    def to_dict(self):
        """
        Serialize the global state to a dictionary for checkpointing.

        Returns:
            dict: Serialized state that can be saved to JSON
        """
        # Helper function to convert nested defaultdicts with sets to regular dicts with lists
        def convert_nested(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, (dict, collections.defaultdict)):
                return {k: convert_nested(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_nested(item) for item in obj]
            return obj

        return {
            "nested_values_hex": convert_nested(dict(self.nested_values_hex)),
            "blacklisted_by_size": list(self.blacklisted_by_size),
            "blacklisted_by_count": list(self.blacklisted_by_count),
            "checksum_algorithms": self.checksum_algorithms,
            "valid_abstractions_count": self.valid_abstractions_count,
            "valid_abstractions_special_count": self.valid_abstractions_special_count,
            "valid_overwrites_count": self.valid_overwrites_count,
        }

    def from_dict(self, data):
        """
        Restore the global state from a dictionary (loaded from checkpoint).

        Args:
            data (dict): The dictionary containing serialized state
        """
        # Helper function to convert lists back to sets at the leaf level
        def restore_nested(obj, depth=0):
            if isinstance(obj, dict):
                result = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
                for k, v in obj.items():
                    result[k] = restore_nested(v, depth + 1)
                return result
            elif isinstance(obj, list):
                # At leaf level, lists should be converted back to sets
                # Check if items are primitive (strings, numbers) - indicates it's a set of values
                if obj and all(isinstance(item, (str, int, float)) for item in obj):
                    return set(obj)
                return [restore_nested(item, depth + 1) for item in obj]
            return obj

        # Restore nested_values_hex
        if "nested_values_hex" in data:
            self.nested_values_hex = restore_nested(data["nested_values_hex"])

        # Restore blacklisted sets (with backward compatibility for old checkpoints)
        if "blacklisted_by_size" in data:
            self.blacklisted_by_size = set(data["blacklisted_by_size"])
        elif "blacklisted_attributes" in data:
            # Old checkpoint format - put all in blacklisted_by_size for backward compatibility
            self.blacklisted_by_size = set(data["blacklisted_attributes"])

        if "blacklisted_by_count" in data:
            self.blacklisted_by_count = set(data["blacklisted_by_count"])

        # Restore checksum_algorithms
        if "checksum_algorithms" in data:
            self.checksum_algorithms = data["checksum_algorithms"]

        # Restore counts
        self.valid_abstractions_count = data.get("valid_abstractions_count", 0)
        self.valid_abstractions_special_count = data.get("valid_abstractions_special_count", 0)
        self.valid_overwrites_count = data.get("valid_overwrites_count", 0)
