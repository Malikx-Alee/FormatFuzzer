"""
Configuration module for learning constraints system.
Contains all constants, paths, and configuration settings, plus the GlobalState that
accumulates everything learned during a run.
"""
import os
import collections
import logging
from datetime import datetime

from .utils import (
    new_nested_dict, insert_nested_dict, remove_path_from_nested_dict, iter_leaf_paths
)

logger = logging.getLogger(__name__)


class Config:
    """Configuration class containing all settings and paths."""

    # Supported file types (each needs templates/<type>.bt and a <type>-fuzzer binary)
    SUPPORTED_FILE_TYPES = [
        "avi", "bmp", "gif", "jpg", "png", "midi", "pcap", "wav", "mp4", "zip", "mp3"
    ]

    # Current file type (can be changed as needed)
    FILE_TYPE = "jpg"

    # Base directories
    DATA_DIR = f"../Dataset/{FILE_TYPE}/"

    # Where the fuzzer binaries, ffcompile and templates live (relative to the cwd by default,
    # which keeps the historical "run from the repo root" behaviour).
    FUZZER_DIR = "."
    FFCOMPILE_PATH = "./ffcompile"
    TEMPLATES_DIR = "templates"

    # Logging directories (will be set dynamically with timestamp)
    LOGS_BASE_DIR = "./logs"
    CURRENT_LOG_DIR = None
    CURRENT_RESULTS_DIR = None
    CURRENT_ABSTRACTED_DIR = None
    CURRENT_ABSTRACTED_SPECIAL_DIR = None
    LOG_FILE = None

    # Processing limits
    MAX_ATTRIBUTE_SIZE_BYTES = 8          # fields larger than this (size in bytes, inclusive) are blacklisted
    MAX_UNIQUE_VALUES_PER_ATTRIBUTE = 30  # blacklist a field once it has more unique values than this
    MAX_ABSTRACTION_ATTEMPTS = 10
    MAX_OVERWRITE_ATTEMPTS = 10

    # Arrays: a leaf array (fields named name, name_1, name_2, ...) with more elements than this
    # is not learned or mutated at all (entropy-coded data, pixel rows). Smaller arrays
    # (palettes, brand lists) are kept and pooled under the base name.
    MAX_ARRAY_ELEMENTS_LEARNED = 16

    # "Special" files (mutants that expose attribute paths never seen before in the run)
    MAX_SPECIAL_FILES_PER_FILE = 5   # per processed input file
    MAX_SPECIAL_FILES = 50           # processed in the second pass per run

    # Subprocess timeouts (seconds). None disables the timeout (not recommended).
    FUZZER_TIMEOUT = 60
    VALIDATOR_TIMEOUT = 60
    TEMPLATE_COMPILE_TIMEOUT = 300

    # Validator strictness. False keeps the historical lenient oracle (identify -verbose /
    # ffmpeg accept files that only produce warnings). True adds `identify -regard-warnings`
    # and `ffmpeg -xerror`, so any decoder warning makes the mutant invalid.
    VALIDATOR_STRICT = False

    # ImageMagick resource limits, mirroring scripts/fuzz_manager.py (see
    # docs_llm/identify_validator_resource_exhaustion.md).
    IDENTIFY_RESOURCE_LIMITS = [
        "-limit", "memory", "512MiB",
        "-limit", "map", "512MiB",
        "-limit", "disk", "2GiB",
        "-limit", "time", "10",
    ]

    # Feature toggles
    ENABLE_CHECKSUM_DETECTION = True
    CHECKSUM_DETECTION_SUPPORTED_TYPES = ["png", "zip", "bmp"]

    # Resume/Checkpoint settings
    RESUME_MODE = False
    CHECKPOINT_FILENAME = "checkpoint.json"
    CHECKPOINT_VERSION = 2
    CHECKPOINT_SAVE_INTERVAL = 10   # save after every N processed files ...
    CHECKPOINT_SAVE_SECONDS = 30    # ... or whenever this many seconds passed since the last save

    # ZIP-specific checksum validation (decompress frData and validate frCrc)
    ZIP_VALIDATE_CHECKSUM_WITH_DECOMPRESSION = True

    # Parallel processing settings
    PARALLEL_WORKERS = 10        # None = use all available CPU cores, 1 = sequential
    PARALLEL_BATCH_SIZE = 100    # files per batch (a checkpoint is saved after every batch)
    # Per-file time budget used to bound a whole batch:
    # batch timeout = PARALLEL_FILE_TIMEOUT * ceil(batch_size / workers). Files still running
    # when the batch times out are recorded as failed. None disables the batch timeout; the
    # per-subprocess timeouts above still bound a hang.
    PARALLEL_FILE_TIMEOUT = 900

    # Flattened output: a leaf with more unique values than this is replaced by a marker string
    FLATTEN_MAX_VALUES = 20

    # Validation tools configuration
    VALIDATION_TOOLS = {
        "images": ["gif", "jpg", "png", "bmp"],
        "audio": ["mp3", "wav"],
        "video": ["mp4", "avi"],
        "archive": ["zip"],
        "network": ["pcap"],
        "music": ["midi"]
    }

    # Settings that worker processes must inherit from the parent (spawned workers start from
    # the module defaults, so anything changed at runtime has to travel with the work item).
    _WORKER_SETTINGS = [
        "FILE_TYPE", "DATA_DIR", "FUZZER_DIR", "FFCOMPILE_PATH", "TEMPLATES_DIR",
        "CURRENT_LOG_DIR", "CURRENT_RESULTS_DIR", "CURRENT_ABSTRACTED_DIR",
        "CURRENT_ABSTRACTED_SPECIAL_DIR", "LOG_FILE",
        "MAX_ATTRIBUTE_SIZE_BYTES", "MAX_UNIQUE_VALUES_PER_ATTRIBUTE",
        "MAX_ABSTRACTION_ATTEMPTS", "MAX_OVERWRITE_ATTEMPTS", "MAX_ARRAY_ELEMENTS_LEARNED",
        "MAX_SPECIAL_FILES_PER_FILE", "MAX_SPECIAL_FILES",
        "FUZZER_TIMEOUT", "VALIDATOR_TIMEOUT", "VALIDATOR_STRICT", "IDENTIFY_RESOURCE_LIMITS",
        "ENABLE_CHECKSUM_DETECTION", "CHECKSUM_DETECTION_SUPPORTED_TYPES",
        "ZIP_VALIDATE_CHECKSUM_WITH_DECOMPRESSION",
    ]

    @classmethod
    def get_fuzzer_executable(cls):
        """Get the fuzzer executable path for the current file type."""
        return os.path.join(cls.FUZZER_DIR, f"{cls.FILE_TYPE}-fuzzer")

    @classmethod
    def get_template_path(cls):
        """Get the binary template path for the current file type."""
        return os.path.join(cls.TEMPLATES_DIR, f"{cls.FILE_TYPE}.bt")

    @classmethod
    def worker_snapshot(cls):
        """Collect the settings a worker process must inherit."""
        return {name: getattr(cls, name) for name in cls._WORKER_SETTINGS}

    @classmethod
    def apply_worker_snapshot(cls, snapshot):
        """Apply a snapshot produced by :meth:`worker_snapshot` in a worker process."""
        for name, value in snapshot.items():
            setattr(cls, name, value)

    @classmethod
    def initialize_logging(cls, file_type=None):
        """
        Initialize logging directories with timestamp.

        Returns:
            str: Path to the log file
        """
        if file_type is None:
            file_type = cls.FILE_TYPE

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir_name = f"{timestamp}_{file_type}"

        cls.restore_log_directory(os.path.join(cls.LOGS_BASE_DIR, log_dir_name))

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
        cls.DATA_DIR = f"../Dataset/{file_type}/"

    @classmethod
    def set_resume_mode(cls, resume_mode):
        """Set the resume mode."""
        cls.RESUME_MODE = resume_mode

    @classmethod
    def get_checkpoint_path(cls):
        """Path to the checkpoint file in the current log directory, or None."""
        if cls.CURRENT_LOG_DIR:
            return os.path.join(cls.CURRENT_LOG_DIR, cls.CHECKPOINT_FILENAME)
        return None

    @classmethod
    def find_latest_checkpoint(cls, file_type=None, include_completed=False):
        """
        Find the most recent checkpoint for the given file type.

        Args:
            file_type (str, optional): File type to search for. Uses cls.FILE_TYPE if None.
            include_completed (bool): also return checkpoints of runs that finished normally.

        Returns:
            tuple: (log_dir_path, checkpoint_path) or (None, None) if not found
        """
        import json

        if file_type is None:
            file_type = cls.FILE_TYPE

        if not os.path.exists(cls.LOGS_BASE_DIR):
            return None, None

        matching_dirs = []
        for dir_name in os.listdir(cls.LOGS_BASE_DIR):
            if not dir_name.endswith(f"_{file_type}"):
                continue
            dir_path = os.path.join(cls.LOGS_BASE_DIR, dir_name)
            checkpoint_path = os.path.join(dir_path, cls.CHECKPOINT_FILENAME)
            if not os.path.exists(checkpoint_path):
                continue
            if not include_completed:
                try:
                    with open(checkpoint_path) as f:
                        if json.load(f).get("completed", False):
                            continue
                except (OSError, ValueError):
                    continue
            matching_dirs.append((dir_name, dir_path, checkpoint_path))

        if not matching_dirs:
            return None, None

        matching_dirs.sort(reverse=True, key=lambda x: x[0])
        _, log_dir_path, checkpoint_path = matching_dirs[0]
        return log_dir_path, checkpoint_path

    @classmethod
    def restore_log_directory(cls, log_dir_path):
        """Point all log/result paths at an existing (or new) run directory."""
        cls.CURRENT_LOG_DIR = log_dir_path
        cls.CURRENT_RESULTS_DIR = os.path.join(log_dir_path, "results")
        cls.CURRENT_ABSTRACTED_DIR = os.path.join(log_dir_path, "abstracted")
        cls.CURRENT_ABSTRACTED_SPECIAL_DIR = os.path.join(log_dir_path, "abstracted_special")
        cls.LOG_FILE = os.path.join(log_dir_path, "learning_constraints.log")


class GlobalState:
    """
    Everything learned during a run.

    All attribute bookkeeping is keyed by *cleaned full path* (see utils.py): values live in
    ``nested_values_hex`` under those paths, and the blacklists and ``seen_attribute_paths``
    hold the same strings.
    """

    def __init__(self):
        # Nested dictionaries to store extracted values: path segments -> set of hex strings
        self.nested_values_hex = new_nested_dict()

        # Fields blacklisted because their byte size > MAX_ATTRIBUTE_SIZE_BYTES (cleaned paths)
        self.blacklisted_by_size = set()
        # Fields blacklisted because unique values count > MAX_UNIQUE_VALUES_PER_ATTRIBUTE (cleaned paths)
        self.blacklisted_by_count = set()
        # Leaf *names* loaded from a version-1 checkpoint (which stored names, not paths)
        self.legacy_blacklisted_names = set()

        # Every cleaned path encountered in any parsed file or valid mutant so far
        self.seen_attribute_paths = set()
        # Leaf arrays skipped because they had more than MAX_ARRAY_ELEMENTS_LEARNED elements
        self.dropped_arrays = {}  # cleaned path -> largest element count seen

        # Detected checksum algorithms and metadata
        self.checksum_algorithms = {"by_chunk_type": {}, "compression_methods": {}}

        # Output counts
        self.valid_abstractions_count = 0
        self.valid_abstractions_special_count = 0
        self.valid_overwrites_count = 0

    # -- blacklist helpers -------------------------------------------------

    @property
    def blacklisted_attributes(self):
        """Union of both blacklists (plus any legacy leaf names)."""
        return self.blacklisted_by_size | self.blacklisted_by_count | self.legacy_blacklisted_names

    def is_blacklisted(self, path):
        """True if a cleaned path is blacklisted (by size, by count, or by legacy leaf name)."""
        if path in self.blacklisted_by_size or path in self.blacklisted_by_count:
            return True
        if self.legacy_blacklisted_names and path.split("~")[-1] in self.legacy_blacklisted_names:
            return True
        return False

    def blacklist_by_size(self, path):
        """Blacklist a cleaned path for size; drop any values already stored. Returns True if new."""
        if path in self.blacklisted_by_size:
            return False
        self.blacklisted_by_size.add(path)
        remove_path_from_nested_dict(self.nested_values_hex, path)
        return True

    def blacklist_by_count(self, path):
        """Blacklist a cleaned path for too many unique values; drop its values. Returns True if new."""
        if path in self.blacklisted_by_count:
            return False
        self.blacklisted_by_count.add(path)
        remove_path_from_nested_dict(self.nested_values_hex, path)
        return True

    def register_attributes(self, paths):
        """Record cleaned paths as seen in this run."""
        self.seen_attribute_paths.update(paths)

    def record_dropped_array(self, path, count):
        """Record a leaf array that was skipped because it had too many elements."""
        if count > self.dropped_arrays.get(path, 0):
            self.dropped_arrays[path] = count

    def enforce_unique_value_limit(self, max_values=None):
        """
        Blacklist (by count) every leaf that holds more than ``max_values`` unique values.

        Returns:
            list: the cleaned paths that were newly blacklisted
        """
        if max_values is None:
            max_values = Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE
        offenders = [path for path, values in iter_leaf_paths(self.nested_values_hex) if len(values) > max_values]
        newly = []
        for path in offenders:
            if self.blacklist_by_count(path):
                newly.append(path)
        return newly

    # -- lifecycle ---------------------------------------------------------

    def reset(self):
        """Reset all state variables."""
        self.nested_values_hex = new_nested_dict()
        self.blacklisted_by_size.clear()
        self.blacklisted_by_count.clear()
        self.legacy_blacklisted_names.clear()
        self.seen_attribute_paths.clear()
        self.dropped_arrays = {}
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
            "blacklisted_total": len(self.blacklisted_attributes),
            "seen_attributes": len(self.seen_attribute_paths),
            "dropped_arrays": len(self.dropped_arrays),
            "learned_leaves": sum(1 for _ in iter_leaf_paths(self.nested_values_hex)),
            "learned_values": sum(len(v) for _, v in iter_leaf_paths(self.nested_values_hex)),
        }

    # -- (de)serialisation -------------------------------------------------

    def to_dict(self):
        """Serialize the global state to a JSON-compatible dictionary."""
        def convert_nested(obj):
            if isinstance(obj, set):
                return sorted(obj)
            elif isinstance(obj, dict):
                return {k: convert_nested(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_nested(item) for item in obj]
            return obj

        return {
            "version": Config.CHECKPOINT_VERSION,
            "nested_values_hex": convert_nested(dict(self.nested_values_hex)),
            "blacklisted_by_size": sorted(self.blacklisted_by_size),
            "blacklisted_by_count": sorted(self.blacklisted_by_count),
            "legacy_blacklisted_names": sorted(self.legacy_blacklisted_names),
            "seen_attribute_paths": sorted(self.seen_attribute_paths),
            "dropped_arrays": dict(self.dropped_arrays),
            "checksum_algorithms": self.checksum_algorithms,
            "valid_abstractions_count": self.valid_abstractions_count,
            "valid_abstractions_special_count": self.valid_abstractions_special_count,
            "valid_overwrites_count": self.valid_overwrites_count,
        }

    def from_dict(self, data):
        """Restore the global state from a dictionary (loaded from a checkpoint or a worker)."""
        def restore_nested(obj):
            if isinstance(obj, dict):
                result = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
                for k, v in obj.items():
                    result[k] = restore_nested(v)
                return result
            elif isinstance(obj, list):
                # Leaves are lists of primitives (possibly empty); restore them as sets.
                return set(obj)
            return obj

        version = data.get("version", 1)

        if "nested_values_hex" in data:
            self.nested_values_hex = restore_nested(data["nested_values_hex"])

        if version < 2:
            # Version 1 checkpoints stored leaf *names*, not paths.
            legacy = set(data.get("blacklisted_by_size", [])) | set(data.get("blacklisted_by_count", []))
            legacy |= set(data.get("blacklisted_attributes", []))
            self.blacklisted_by_size = set()
            self.blacklisted_by_count = set()
            self.legacy_blacklisted_names = legacy
            if legacy:
                logger.warning(
                    "Loaded a version-1 checkpoint: %d blacklist entries are leaf names and will be "
                    "matched by name only", len(legacy))
        else:
            self.blacklisted_by_size = set(data.get("blacklisted_by_size", []))
            self.blacklisted_by_count = set(data.get("blacklisted_by_count", []))
            self.legacy_blacklisted_names = set(data.get("legacy_blacklisted_names", []))

        self.seen_attribute_paths = set(data.get("seen_attribute_paths", []))
        self.dropped_arrays = dict(data.get("dropped_arrays", {}))

        if "checksum_algorithms" in data:
            self.checksum_algorithms = data["checksum_algorithms"]

        self.valid_abstractions_count = data.get("valid_abstractions_count", 0)
        self.valid_abstractions_special_count = data.get("valid_abstractions_special_count", 0)
        self.valid_overwrites_count = data.get("valid_overwrites_count", 0)
