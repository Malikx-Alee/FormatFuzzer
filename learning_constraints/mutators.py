"""
File mutation module for the learning constraints system.
Mutates each learnable field of a file with the fuzzer's smart abstraction and with random
bytes, validates the result, and harvests values (and new attributes) from valid mutants.
"""
import os
import shutil
import subprocess
import hashlib
import logging
from .config import Config, GlobalState
from .validators import FileValidator
from .parsers import FileParser
from .utils import overwrite_bytes_randomly

# Module-level logger
logger = logging.getLogger(__name__)


def _short_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


def _get_unique_suffix(file_path: str) -> str:
    """Unique suffix for temp files: hash of input path + process id (safe across workers)."""
    return _short_hash(f"{file_path}_{os.getpid()}")


class FileMutator:
    """Performs smart-abstraction and random-overwrite mutations and processes valid mutants."""

    def __init__(self, global_state: GlobalState):
        self.global_state = global_state
        self.parser = FileParser(global_state)
        self.validator = FileValidator()
        self._special_this_file = 0

    # ------------------------------------------------------------------
    # Primitive mutations
    # ------------------------------------------------------------------

    def smart_abstraction_mutation(self, file_path, start, end, output_path):
        """
        Run ``<type>-fuzzer abstract`` on one byte range.

        Returns:
            bool: True if the fuzzer produced an output file and exited 0.
        """
        if os.path.exists(output_path):
            os.remove(output_path)
        try:
            result = subprocess.run(
                [
                    Config.get_fuzzer_executable(), "abstract",
                    "--targetfile", file_path,
                    "--targetstart", str(start),
                    "--targetend", str(end),
                    output_path
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                errors="replace",
                timeout=Config.FUZZER_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout ({Config.FUZZER_TIMEOUT}s) abstracting {file_path} [{start}-{end}]")
            return False
        except Exception as e:
            logger.error(f"Error performing smart abstraction mutation on {file_path} from {start} to {end}: {e}")
            return False
        return result.returncode == 0 and os.path.exists(output_path)

    def random_overwrite_mutation(self, file_path, start, end, output_path):
        """Copy the file and overwrite one byte range with random bytes."""
        try:
            shutil.copy(file_path, output_path)
            overwrite_bytes_randomly(output_path, start, end)
            return True
        except Exception as e:
            logger.error(f"Error performing random overwrite mutation on {file_path}: {e}")
            return False

    # ------------------------------------------------------------------
    # Special files
    # ------------------------------------------------------------------

    def _special_quota_left(self):
        return (self._special_this_file < Config.MAX_SPECIAL_FILES_PER_FILE
                and self.global_state.valid_abstractions_special_count < Config.MAX_SPECIAL_FILES)

    def save_special_file(self, source_path, new_attribute, start, end, operation_type, origin_file):
        """
        Save a mutant that exposed a never-seen attribute path to the special directory.

        The filename carries the operation, the new leaf name, the mutated range and a short
        hash of the originating file so two source files cannot overwrite each other.
        """
        safe_attr = "".join(c if c.isalnum() or c in "-_" else "_" for c in new_attribute)[:60]
        filename = f"special_{operation_type}_{safe_attr}_{start}_{end}_{_short_hash(origin_file)}.{Config.FILE_TYPE}"
        special_file_path = os.path.join(Config.CURRENT_ABSTRACTED_SPECIAL_DIR, filename)

        shutil.copy(source_path, special_file_path)
        self.global_state.valid_abstractions_special_count += 1
        self._special_this_file += 1
        logger.info(f"New attribute '{new_attribute}' found by {operation_type} of [{start}-{end}]; saved {filename}")
        return special_file_path

    # ------------------------------------------------------------------
    # Mutant handling
    # ------------------------------------------------------------------

    def _process_valid_mutant(self, mutant_path, origin_file, start, end, known_attributes, operation_type):
        """Parse a validated mutant, save it if it exposes new attributes, and harvest its values."""
        mutated_original_ranges, mutated_ranges = self.parser.parse_file_structure(mutant_path)

        has_new, new_leaf, new_path = self.parser.check_for_new_attributes(mutated_ranges, known_attributes)
        if has_new:
            if self._special_quota_left():
                self.save_special_file(mutant_path, new_leaf, start, end, operation_type, origin_file)
            else:
                logger.debug(f"Special-file quota reached; not saving mutant exposing '{new_path}'")

        # Extracting also registers the mutant's paths as seen, so the same discovery is not
        # reported again by later mutants or other files.
        self.parser.extract_bytes_from_file(mutant_path, mutated_ranges, mutated_original_ranges)

    def process_smart_abstraction_mutation_attempt(self, file_path, start, end, known_attributes, original_byte_ranges=None):
        """
        Try up to MAX_ABSTRACTION_ATTEMPTS smart abstractions of one range; process the first
        valid mutant.

        Returns:
            bool: True if a valid mutant was produced.
        """
        output_file = os.path.join(Config.CURRENT_ABSTRACTED_DIR,
                                   f"abstracted_{_get_unique_suffix(file_path)}.{Config.FILE_TYPE}")
        try:
            for attempt in range(1, Config.MAX_ABSTRACTION_ATTEMPTS + 1):
                try:
                    if not self.smart_abstraction_mutation(file_path, start, end, output_file):
                        continue
                    if not self.validator.is_valid_file(output_file):
                        continue
                    self._process_valid_mutant(output_file, file_path, start, end, known_attributes, "smart_abstraction")
                    self.global_state.valid_abstractions_count += 1
                    return True
                except Exception as e:
                    logger.error(f"Error in smart abstraction mutation attempt {attempt} for {file_path}: {e}")
            return False
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)

    def process_random_overwrite_mutation_attempt(self, file_path, start, end, known_attributes, original_byte_ranges=None):
        """
        Try up to MAX_OVERWRITE_ATTEMPTS random overwrites of one range; process the first
        valid mutant.

        Returns:
            bool: True if a valid mutant was produced.
        """
        output_file = os.path.join(Config.CURRENT_ABSTRACTED_DIR,
                                   f"overwrite_{_get_unique_suffix(file_path)}.{Config.FILE_TYPE}")
        try:
            for attempt in range(1, Config.MAX_OVERWRITE_ATTEMPTS + 1):
                try:
                    if not self.random_overwrite_mutation(file_path, start, end, output_file):
                        continue
                    if not self.validator.is_valid_file(output_file):
                        continue
                    self._process_valid_mutant(output_file, file_path, start, end, known_attributes, "random_overwrite")
                    self.global_state.valid_overwrites_count += 1
                    return True
                except Exception as e:
                    logger.error(f"Error in random overwrite mutation attempt {attempt} for {file_path}: {e}")
            return False
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)

    def mutate_file_completely(self, file_path, byte_ranges, original_byte_ranges):
        """
        Mutate every learnable byte range of a file with both strategies.

        Returns:
            list: the byte ranges that were processed (for compatibility)
        """
        self._special_this_file = 0
        file_attributes = self.parser.get_file_attributes(byte_ranges)
        self.global_state.register_attributes(file_attributes)
        # "Known" = this file's own attributes plus everything the run has seen so far.
        known_attributes = file_attributes | set(self.global_state.seen_attribute_paths)

        for br in byte_ranges:
            try:
                self.process_smart_abstraction_mutation_attempt(file_path, br.start, br.end, known_attributes, original_byte_ranges)
            except Exception as e:
                logger.error(f"Error in smart abstraction mutation for {file_path}: {e}")

            try:
                self.process_random_overwrite_mutation_attempt(file_path, br.start, br.end, known_attributes, original_byte_ranges)
            except Exception as e:
                logger.error(f"Error in random overwrite mutation for {file_path}: {e}")

        return byte_ranges
