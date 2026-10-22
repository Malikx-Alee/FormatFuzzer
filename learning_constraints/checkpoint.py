"""
Checkpoint management module for the learning constraints system.
Handles saving and loading checkpoints to enable resumable processing.
"""
import os
import json
import time
from datetime import datetime
from .config import Config, GlobalState


class CheckpointManager:
    """
    Manages checkpoints for resumable processing.

    A checkpoint is written after every CHECKPOINT_SAVE_INTERVAL files, whenever
    CHECKPOINT_SAVE_SECONDS have passed since the last save, after every parallel batch, on
    completion, and (via the orchestrator's signal handlers) on interruption.
    """

    def __init__(self, global_state: GlobalState, checkpoint_path: str = None):
        self.global_state = global_state
        self.checkpoint_path = checkpoint_path or Config.get_checkpoint_path()
        self.processed_files = set()
        self.started_at = None
        self.last_updated = None
        self.file_type = Config.FILE_TYPE
        self.source_dir = None
        self.max_files = None
        self.files_processed_count = 0
        self.failed_count = 0
        self.completed = False
        self._save_counter = 0
        self._last_save_time = time.monotonic()
        self.saves_this_run = 0

    def set_run_info(self, source_dir: str, max_files: int = None):
        self.source_dir = source_dir
        self.max_files = max_files
        if self.started_at is None:
            self.started_at = datetime.now().isoformat()

    @property
    def has_saved(self) -> bool:
        """True if this run wrote at least one checkpoint file."""
        return self.saves_this_run > 0

    def mark_file_processed(self, file_path: str, save_immediately: bool = None):
        """Mark a file as processed and save the checkpoint when due."""
        self.processed_files.add(file_path)
        self.files_processed_count += 1
        self._save_counter += 1

        should_save = save_immediately
        if should_save is None:
            interval_due = self._save_counter >= Config.CHECKPOINT_SAVE_INTERVAL
            time_due = (Config.CHECKPOINT_SAVE_SECONDS is not None
                        and time.monotonic() - self._last_save_time >= Config.CHECKPOINT_SAVE_SECONDS)
            should_save = interval_due or time_due

        if should_save:
            self.save_checkpoint()

    def is_file_processed(self, file_path: str) -> bool:
        return file_path in self.processed_files

    def get_unprocessed_files(self, file_paths: list) -> list:
        return [f for f in file_paths if not self.is_file_processed(f)]

    def save_checkpoint(self):
        """Write the checkpoint atomically."""
        if not self.checkpoint_path:
            return False

        self.last_updated = datetime.now().isoformat()
        checkpoint_data = {
            "version": Config.CHECKPOINT_VERSION,
            "run_id": os.path.basename(Config.CURRENT_LOG_DIR) if Config.CURRENT_LOG_DIR else None,
            "file_type": self.file_type,
            "source_dir": self.source_dir,
            "max_files": self.max_files,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "completed": self.completed,
            "processed_files": sorted(self.processed_files),
            "files_processed_count": self.files_processed_count,
            "failed_count": self.failed_count,
            "global_state": self.global_state.to_dict(),
            "log_dir": Config.CURRENT_LOG_DIR,
        }

        temp_path = self.checkpoint_path + ".tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            os.replace(temp_path, self.checkpoint_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

        self._save_counter = 0
        self._last_save_time = time.monotonic()
        self.saves_this_run += 1
        return True

    def load_checkpoint(self) -> bool:
        """Load the checkpoint at ``self.checkpoint_path`` into this manager and its GlobalState."""
        if not self.checkpoint_path or not os.path.exists(self.checkpoint_path):
            return False

        try:
            with open(self.checkpoint_path, 'r') as f:
                data = json.load(f)

            self.file_type = data.get("file_type", Config.FILE_TYPE)
            self.source_dir = data.get("source_dir")
            self.max_files = data.get("max_files")
            self.started_at = data.get("started_at")
            self.last_updated = data.get("last_updated")
            self.completed = bool(data.get("completed", False))
            self.processed_files = set(data.get("processed_files", []))
            self.files_processed_count = data.get("files_processed_count", len(self.processed_files))
            self.failed_count = data.get("failed_count", 0)

            if "global_state" in data:
                self.global_state.from_dict(data["global_state"])
            return True
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            return False

    def get_checkpoint_info(self) -> dict:
        return {
            "checkpoint_path": self.checkpoint_path,
            "file_type": self.file_type,
            "source_dir": self.source_dir,
            "max_files": self.max_files,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "completed": self.completed,
            "files_processed": len(self.processed_files),
            "files_processed_count": self.files_processed_count,
            "failed_count": self.failed_count,
        }

    def mark_complete(self):
        """Mark the run as complete and save the final checkpoint."""
        self.completed = True
        self.save_checkpoint()

    @staticmethod
    def load_checkpoint_info(checkpoint_path: str) -> dict:
        """Read a checkpoint file without touching any state."""
        if not os.path.exists(checkpoint_path):
            return {}
        try:
            with open(checkpoint_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
