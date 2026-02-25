"""
File validation module for the learning constraints system.
Contains validation functions for different file types.
"""
import subprocess
import zipfile
import logging
from .config import Config

# Module-level logger
logger = logging.getLogger(__name__)


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
            logger.error(f"Error validating image file {file_path}: {e}")
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
            logger.error(f"Error validating zip file {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_audio_video_file(file_path, expected_format=None):
        """
        Validate audio/video files using ffmpeg.

        Uses ffmpeg with null output to validate the file can be decoded.
        If expected_format is provided, also checks that the detected format
        matches (handles comma-separated format lists like "mov,mp4,m4a,3gp,3g2,mj2").

        Args:
            file_path (str): Path to the audio/video file
            expected_format (str, optional): Expected format name for validation

        Returns:
            bool: True if valid, False otherwise
        """
        import re

        try:
            # Use ffmpeg to validate and get format info
            # -i: input file
            # -f null -: output to null (just validate, don't produce output)
            # We capture stderr because ffmpeg prints format info there
            result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-f", "null", "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # If ffmpeg returns non-zero, file is invalid
            if result.returncode != 0:
                return False

            # If no specific format check needed, file is valid
            if not expected_format:
                return True

            # Parse format from ffmpeg's stderr output
            # ffmpeg prints: "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'file.mp4':"
            match = re.search(r'Input #\d+,\s*([^,\s]+(?:,[^,\s]+)*),\s*from', result.stderr)
            if match:
                # Split the comma-separated format list and check if expected format is in it
                formats = [f.strip() for f in match.group(1).split(',')]
                return expected_format in formats

            # If we can't parse format but file decoded successfully, accept it
            return True

        except Exception as e:
            logger.error(f"Error validating audio/video file {file_path}: {e}")
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
            logger.error(f"Error validating pcap file {file_path}: {e}")
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
            logger.error(f"Error validating MIDI file {file_path}: {e}")
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
                logger.warning(f"Validation for file type '{file_type}' is not implemented.")
                return False

        except Exception as e:
            logger.error(f"Error validating {file_type} file: {e}")
            return False



