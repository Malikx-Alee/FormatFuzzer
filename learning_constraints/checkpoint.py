"""
Checkpoint management module for the learning constraints system.
Handles saving and loading checkpoints to enable resumable processing.
"""
import os
import json
from datetime import datetime
from .config import Config, GlobalState


class CheckpointManager:
    """
    Manages checkpoints for resumable processing.
    
    Saves progress after each file is processed, allowing the system
    to resume from where it left off if interrupted.
    """
    
    def __init__(self, global_state: GlobalState, checkpoint_path: str = None):
        """
        Initialize the checkpoint manager.
        
        Args:
            global_state (GlobalState): The global state object to save/restore
            checkpoint_path (str, optional): Path to checkpoint file. 
                                            If None, uses Config.get_checkpoint_path()
        """
        self.global_state = global_state
        self.checkpoint_path = checkpoint_path or Config.get_checkpoint_path()
        self.processed_files = set()
        self.started_at = None
        self.last_updated = None
        self.file_type = Config.FILE_TYPE
        self.source_dir = None
        self.max_files = None
        self.files_processed_count = 0
        self._save_counter = 0
        
    def set_run_info(self, source_dir: str, max_files: int = None):
        """
        Set run information for the checkpoint.
        
        Args:
            source_dir (str): Source directory being processed
            max_files (int, optional): Maximum files limit
        """
        self.source_dir = source_dir
        self.max_files = max_files
        if self.started_at is None:
            self.started_at = datetime.now().isoformat()
    
    def mark_file_processed(self, file_path: str, save_immediately: bool = None):
        """
        Mark a file as processed and optionally save checkpoint.
        
        Args:
            file_path (str): Path to the file that was processed
            save_immediately (bool, optional): Whether to save checkpoint immediately.
                                              If None, uses CHECKPOINT_SAVE_INTERVAL
        """
        self.processed_files.add(file_path)
        self.files_processed_count += 1
        self._save_counter += 1
        
        # Determine if we should save
        should_save = save_immediately
        if should_save is None:
            should_save = (self._save_counter >= Config.CHECKPOINT_SAVE_INTERVAL)
        
        if should_save:
            self.save_checkpoint()
            self._save_counter = 0
    
    def is_file_processed(self, file_path: str) -> bool:
        """
        Check if a file has already been processed.
        
        Args:
            file_path (str): Path to check
            
        Returns:
            bool: True if file was already processed
        """
        return file_path in self.processed_files
    
    def get_unprocessed_files(self, file_paths: list) -> list:
        """
        Filter a list of files to only include unprocessed ones.
        
        Args:
            file_paths (list): List of file paths to filter
            
        Returns:
            list: List of file paths that haven't been processed yet
        """
        return [f for f in file_paths if not self.is_file_processed(f)]
    
    def save_checkpoint(self):
        """Save the current state to the checkpoint file."""
        if not self.checkpoint_path:
            return
            
        self.last_updated = datetime.now().isoformat()
        
        checkpoint_data = {
            "run_id": os.path.basename(Config.CURRENT_LOG_DIR) if Config.CURRENT_LOG_DIR else None,
            "file_type": self.file_type,
            "source_dir": self.source_dir,
            "max_files": self.max_files,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "processed_files": list(self.processed_files),
            "files_processed_count": self.files_processed_count,
            "global_state": self.global_state.to_dict(),
            "log_dir": Config.CURRENT_LOG_DIR,
        }
        
        # Write atomically using temp file
        temp_path = self.checkpoint_path + ".tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            os.replace(temp_path, self.checkpoint_path)
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    def load_checkpoint(self) -> bool:
        """
        Load checkpoint from file.
        
        Returns:
            bool: True if checkpoint was loaded successfully, False otherwise
        """
        if not self.checkpoint_path or not os.path.exists(self.checkpoint_path):
            return False
            
        try:
            with open(self.checkpoint_path, 'r') as f:
                data = json.load(f)
            
            # Restore checkpoint data
            self.file_type = data.get("file_type", Config.FILE_TYPE)
            self.source_dir = data.get("source_dir")
            self.max_files = data.get("max_files")
            self.started_at = data.get("started_at")
            self.last_updated = data.get("last_updated")
            self.processed_files = set(data.get("processed_files", []))
            self.files_processed_count = data.get("files_processed_count", len(self.processed_files))
            
            # Restore global state
            if "global_state" in data:
                self.global_state.from_dict(data["global_state"])
            
            return True
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            return False
    
    def get_checkpoint_info(self) -> dict:
        """
        Get information about the current checkpoint.
        
        Returns:
            dict: Checkpoint information including files processed, timestamps, etc.
        """
        return {
            "checkpoint_path": self.checkpoint_path,
            "file_type": self.file_type,
            "source_dir": self.source_dir,
            "max_files": self.max_files,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "files_processed": len(self.processed_files),
            "files_processed_count": self.files_processed_count,
        }
    
    def mark_complete(self):
        """Mark the run as complete and save final checkpoint."""
        self.save_checkpoint()
    
    @staticmethod
    def load_checkpoint_info(checkpoint_path: str) -> dict:
        """
        Load checkpoint info from a file without modifying any state.
        
        Args:
            checkpoint_path (str): Path to checkpoint file
            
        Returns:
            dict: Checkpoint data or empty dict if loading fails
        """
        if not os.path.exists(checkpoint_path):
            return {}
            
        try:
            with open(checkpoint_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

