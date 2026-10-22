"""
File validation module for the learning constraints system.

The validator is the oracle that decides which mutants count as "valid", so it defines what
is learned. Two modes exist (``Config.VALIDATOR_STRICT``):

* lenient (default, historical behaviour): ``identify -verbose`` must print its summary
  ("Elapsed"), ``ffmpeg -f null -`` must exit 0. Decoder warnings do not fail a file.
* strict: additionally ``identify -regard-warnings`` and ``ffmpeg -xerror``, so any warning
  fails the file.

Every external call has a timeout and decodes output with ``errors="replace"`` so a mutant
whose bytes end up in the tool's output cannot crash the check.
"""
import re
import subprocess
import zipfile
import logging
from .config import Config

# Module-level logger
logger = logging.getLogger(__name__)


def _run(cmd, **kwargs):
    """
    Run an external tool with the configured timeout.

    Returns:
        subprocess.CompletedProcess, or None if the tool timed out.
    """
    kwargs.setdefault("stdout", subprocess.PIPE)
    kwargs.setdefault("stderr", subprocess.PIPE)
    kwargs.setdefault("text", True)
    kwargs.setdefault("errors", "replace")
    kwargs.setdefault("timeout", Config.VALIDATOR_TIMEOUT)
    try:
        return subprocess.run(cmd, **kwargs)
    except subprocess.TimeoutExpired:
        logger.warning(f"Validator timed out after {kwargs['timeout']}s: {' '.join(cmd[:1])} ...")
        return None


class FileValidator:
    """File validation class with methods for different file types."""

    @staticmethod
    def identify_command(file_path):
        """Build the ImageMagick command for the current strictness and resource limits."""
        cmd = ["identify"] + list(Config.IDENTIFY_RESOURCE_LIMITS)
        if Config.VALIDATOR_STRICT:
            cmd.append("-regard-warnings")
        cmd += ["-verbose", file_path]
        return cmd

    @staticmethod
    def ffmpeg_command(file_path):
        """Build the ffmpeg command for the current strictness."""
        cmd = ["ffmpeg", "-nostdin"]
        if Config.VALIDATOR_STRICT:
            cmd.append("-xerror")
        cmd += ["-i", file_path, "-f", "null", "-"]
        return cmd

    @classmethod
    def validate_image_file(cls, file_path):
        """Validate image files using ImageMagick's identify command."""
        try:
            result = _run(cls.identify_command(file_path), stderr=subprocess.DEVNULL)
            if result is None:
                return False
            if Config.VALIDATOR_STRICT and result.returncode != 0:
                return False
            return "Elapsed" in result.stdout
        except Exception as e:
            logger.error(f"Error validating image file {file_path}: {e}")
            return False

    @staticmethod
    def validate_zip_file(file_path):
        """Validate zip files by checking that every member passes its CRC."""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                return zip_ref.testzip() is None
        except Exception as e:
            logger.debug(f"Invalid zip file {file_path}: {e}")
            return False

    @classmethod
    def validate_audio_video_file(cls, file_path, expected_format=None):
        """
        Validate audio/video files using ffmpeg.

        If ``expected_format`` is given, the container reported by ffmpeg
        ("Input #0, mov,mp4,m4a,3gp,3g2,mj2, from ...") must include it.
        """
        try:
            result = _run(cls.ffmpeg_command(file_path))
            if result is None or result.returncode != 0:
                return False
            if not expected_format:
                return True

            match = re.search(r'Input #\d+,\s*([^,\s]+(?:,[^,\s]+)*),\s*from', result.stderr)
            if match:
                formats = [f.strip() for f in match.group(1).split(',')]
                return expected_format in formats
            # Decoded fine but the format line was not found: accept.
            return True
        except Exception as e:
            logger.error(f"Error validating audio/video file {file_path}: {e}")
            return False

    @staticmethod
    def validate_pcap_file(file_path):
        """Validate pcap files using tshark."""
        try:
            result = _run(["tshark", "-r", file_path], stderr=subprocess.DEVNULL)
            return result is not None and result.returncode == 0
        except Exception as e:
            logger.error(f"Error validating pcap file {file_path}: {e}")
            return False

    @staticmethod
    def validate_midi_file(file_path):
        """Validate MIDI files using timidity."""
        try:
            with open(file_path, 'rb') as f:
                result = _run(["timidity", "-", "-Ol", "-o", "/dev/null"], stdin=f)
            if result is None:
                return False
            return not any(line.startswith("-:") for line in result.stdout.splitlines())
        except Exception as e:
            logger.error(f"Error validating MIDI file {file_path}: {e}")
            return False

    @classmethod
    def is_valid_file(cls, file_path, file_type=None):
        """
        Validate a file based on its type.

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
