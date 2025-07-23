"""
File validation module for the learning constraints system.
Contains validation functions for different file types.
"""
import subprocess
import zipfile
from .config import Config


class FileValidator:
    """File validation class with methods for different file types."""
    
    @staticmethod
    def validate_image_file(file_path):
        """
        Validate image files using ImageMagick's identify command.
        
        Args:
            file_path (str): Path to the image file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            result = subprocess.run(
                ["identify", "-verbose", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "Elapsed" in result.stdout
        except Exception as e:
            print(f"Error validating image file {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_zip_file(file_path):
        """
        Validate zip files by checking if the file can be opened.
        
        Args:
            file_path (str): Path to the zip file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                return zip_ref.testzip() is None  # Returns None if no errors are found
        except Exception as e:
            print(f"Error validating zip file {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_audio_video_file(file_path, expected_format=None):
        """
        Validate audio/video files using ffprobe (part of FFmpeg).
        
        Args:
            file_path (str): Path to the audio/video file
            expected_format (str, optional): Expected format name for validation
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            if "format_name" not in result.stdout:
                return False
            
            # Check for specific format if provided
            if expected_format:
                return f"format_name={expected_format}" in result.stdout
            
            return True
        except Exception as e:
            print(f"Error validating audio/video file {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_pcap_file(file_path):
        """
        Validate pcap files using tshark.
        
        Args:
            file_path (str): Path to the pcap file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            result = subprocess.run(
                ["tshark", "-r", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error validating pcap file {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_midi_file(file_path):
        """
        Validate MIDI files using timidity.
        
        Args:
            file_path (str): Path to the MIDI file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                result = subprocess.run(
                    ["timidity", "-", "-Ol", "-o", "/dev/null"],
                    stdin=f,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            # Check that there are no error messages starting with "-:"
            return not any(line.startswith("-:") for line in result.stdout.splitlines())
        except Exception as e:
            print(f"Error validating MIDI file {file_path}: {e}")
            return False
    
    @classmethod
    def is_valid_file(cls, file_path, file_type=None):
        """
        Validates a file based on its type.

        Args:
            file_path (str): Path to the file to validate
            file_type (str, optional): The type of the file. If None, uses Config.FILE_TYPE
            
        Returns:
            bool: True if the file is valid, False otherwise
        """
        if file_type is None:
            file_type = Config.FILE_TYPE
        
        try:
            if file_type in Config.VALIDATION_TOOLS["images"]:
                return cls.validate_image_file(file_path)
            
            elif file_type in Config.VALIDATION_TOOLS["archive"]:
                return cls.validate_zip_file(file_path)
            
            elif file_type in Config.VALIDATION_TOOLS["audio"]:
                return cls.validate_audio_video_file(file_path)
            
            elif file_type in Config.VALIDATION_TOOLS["video"]:
                if file_type == "avi":
                    return cls.validate_audio_video_file(file_path, "avi")
                else:
                    return cls.validate_audio_video_file(file_path)
            
            elif file_type in Config.VALIDATION_TOOLS["network"]:
                return cls.validate_pcap_file(file_path)
            
            elif file_type in Config.VALIDATION_TOOLS["music"]:
                return cls.validate_midi_file(file_path)
            
            else:
                print(f"Validation for file type '{file_type}' is not implemented.")
                return False

        except Exception as e:
            print(f"Error validating {file_type} file: {e}")
            return False


# Convenience function for backward compatibility
def is_valid_file(file_path, file_type=None):
    """
    Convenience function that delegates to FileValidator.is_valid_file.
    
    Args:
        file_path (str): Path to the file to validate
        file_type (str, optional): The type of the file
        
    Returns:
        bool: True if the file is valid, False otherwise
    """
    return FileValidator.is_valid_file(file_path, file_type)
