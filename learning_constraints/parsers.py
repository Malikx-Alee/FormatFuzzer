"""
File parsing module for the learning constraints system.
Turns the fuzzer's ``parse`` output into byte ranges and extracts field values from files.
"""
import ast
import collections
import logging
import os
import subprocess
import tempfile

from .config import Config, GlobalState
from .utils import (
    ByteRange, split_index, clean_keys_list, clean_attribute_path,
    insert_nested_dict, extract_byte_values, get_leaf, validate_byte_range,
)
from .checksum_detector import ChecksumDetector


class FileParser:
    """File parser class for extracting structure and byte ranges from files."""

    def __init__(self, global_state: GlobalState):
        self.global_state = global_state
        self.logger = logging.getLogger(__name__)
        self.checksum_detector = ChecksumDetector(global_state)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def run_fuzzer_parse(self, file_path):
        """
        Run ``<type>-fuzzer parse <file>`` and return its stdout lines (or None on failure).
        """
        try:
            result = subprocess.run(
                [Config.get_fuzzer_executable(), "parse", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                errors="replace",
                timeout=Config.FUZZER_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout ({Config.FUZZER_TIMEOUT}s) parsing {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error running fuzzer parse on {file_path}: {e}")
            return None
        return result.stdout.splitlines()

    def parse_file_structure(self, file_path):
        """
        Parse a file and extract attributes with byte ranges.

        Returns:
            tuple: (original_byte_ranges, filtered_byte_ranges)
                - original_byte_ranges: every valid leaf field, regardless of size
                - filtered_byte_ranges: the leaf fields that are learned and mutated
                  (size <= MAX_ATTRIBUTE_SIZE_BYTES and not blacklisted)
        """
        try:
            file_size = os.path.getsize(file_path)
        except OSError as e:
            self.logger.error(f"Cannot stat {file_path}: {e}")
            return [], []

        lines = self.run_fuzzer_parse(file_path)
        if lines is None:
            return [], []
        try:
            return self.parse_lines(lines, file_size)
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}")
            return [], []

    @staticmethod
    def parse_csv_lines(lines):
        """
        Turn raw fuzzer output lines into ``(start, end, label, flags)`` tuples.

        Non-CSV lines (template ``Printf`` output, ``FSeek`` notes, the final "parsed" line)
        are skipped.
        """
        entries = []
        for line in lines:
            parts = line.split(',')
            if len(parts) < 3:
                continue
            try:
                start, end = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            label = parts[2].strip()
            if not label:
                continue
            flags = tuple(p.strip() for p in parts[3:] if p.strip())
            entries.append((start, end, label, flags))
        return entries

    def parse_lines(self, lines, file_size):
        """
        Build byte ranges from fuzzer ``parse`` output.

        Steps:
          1. parse CSV lines, dropping ranges that are inverted or outside the file;
          2. keep only *leaf* lines (a line is a struct if another line's label extends it);
          3. collapse identical ranges (template re-reads such as ``size_1``), keeping the first;
          4. drop leaf arrays with more than MAX_ARRAY_ELEMENTS_LEARNED elements;
          5. blacklist (by size) leaves larger than MAX_ATTRIBUTE_SIZE_BYTES;
          6. return all leaves, and the learnable subset.
        """
        entries = self.parse_csv_lines(lines)

        # 1. range validation
        valid = []
        for start, end, label, flags in entries:
            if validate_byte_range(start, end, file_size):
                valid.append((start, end, label, flags))
            else:
                self.logger.debug(f"Skipping invalid range {start}-{end} for {label} (file size {file_size})")

        # 2. struct detection: any label that is a strict prefix of another label is a struct
        parents = set()
        for _, _, label, _ in valid:
            parts = label.split("~")
            for i in range(1, len(parts)):
                parents.add("~".join(parts[:i]))
        leaves = [e for e in valid if e[2] not in parents]

        # 3. identical ranges: keep the first emitted
        seen_ranges = set()
        unique = []
        for entry in leaves:
            key = (entry[0], entry[1])
            if key in seen_ranges:
                continue
            seen_ranges.add(key)
            unique.append(entry)

        # 4. leaf arrays: group by (cleaned parent path, base name)
        groups = collections.defaultdict(set)
        indexed_groups = set()
        for start, end, label, _ in unique:
            parts = label.split("~")
            base, index = split_index(parts[-1])
            group_key = ("~".join(clean_keys_list(parts[:-1])), base)
            groups[group_key].add((start, end))
            if index is not None:
                indexed_groups.add(group_key)
        dropped_groups = set()
        for group_key in indexed_groups:
            count = len(groups[group_key])
            if count > Config.MAX_ARRAY_ELEMENTS_LEARNED:
                dropped_groups.add(group_key)
                path = f"{group_key[0]}~{group_key[1]}" if group_key[0] else group_key[1]
                self.global_state.record_dropped_array(path, count)

        kept = []
        for start, end, label, flags in unique:
            parts = label.split("~")
            base, _ = split_index(parts[-1])
            if ("~".join(clean_keys_list(parts[:-1])), base) in dropped_groups:
                continue
            kept.append((start, end, label, flags))

        kept.sort(key=lambda e: (e[0], -e[1]))

        # 5. size blacklist, over all leaves first: a small instance of a field (PNG chunk_1~data,
        #    4 bytes) must not be learned when another instance (chunk_4~data, 34 bytes) is large.
        original_byte_ranges = [ByteRange(start, end, label, flags) for start, end, label, flags in kept]
        for br in original_byte_ranges:
            if br.size > Config.MAX_ATTRIBUTE_SIZE_BYTES:
                self.global_state.blacklist_by_size(br.cleaned_path)

        # 6. learnable subset
        byte_ranges = [
            br for br in original_byte_ranges
            if br.size <= Config.MAX_ATTRIBUTE_SIZE_BYTES and not self.global_state.is_blacklisted(br.cleaned_path)
        ]

        return original_byte_ranges, byte_ranges

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def extract_bytes_from_file(self, file_path, byte_ranges, original_byte_ranges=None):
        """
        Extract byte values from a file for the given byte ranges and store them in the global state.
        Also registers every range's cleaned path as seen and runs checksum/compression detection.
        """
        if original_byte_ranges is None:
            original_byte_ranges = byte_ranges
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            return

        self.global_state.register_attributes(br.cleaned_path for br in byte_ranges)

        seen_chunk_types_for_file = set()
        for br in byte_ranges:
            if br.end >= len(file_data):
                continue
            try:
                byte_values = extract_byte_values(file_data, br.start, br.end)
            except ValueError as e:
                self.logger.error(f"Error extracting bytes for attribute {br.attribute}: {e}")
                continue

            path = br.cleaned_path
            if self.global_state.is_blacklisted(path):
                continue

            insert_nested_dict(self.global_state.nested_values_hex, br.attribute_keys, byte_values['hex'])

            leaf = get_leaf(self.global_state.nested_values_hex, path)
            if leaf is not None and len(leaf) > Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE:
                if self.global_state.blacklist_by_count(path):
                    self.logger.debug(
                        f"Blacklisted attribute '{path}' - exceeded {Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE} unique values")

            try:
                self.checksum_detector.detect_compression_and_checksum(
                    file_data, byte_ranges, original_byte_ranges,
                    br.start, br.end, br.attribute_keys, byte_values,
                    seen_chunk_types_for_file
                )
            except Exception as e:
                self.logger.debug(f"Checksum detection failed for {br.attribute}: {e}")

    # ------------------------------------------------------------------
    # Attribute bookkeeping
    # ------------------------------------------------------------------

    def get_file_attributes(self, byte_ranges):
        """Return the set of cleaned paths present in the given byte ranges."""
        return {br.cleaned_path for br in byte_ranges}

    def check_for_new_attributes(self, byte_ranges, known_attributes):
        """
        Check whether the byte ranges contain a cleaned path that is neither in
        ``known_attributes`` nor in the run-wide set of seen attributes.

        Returns:
            tuple: (has_new_attributes, first_new_leaf_name, first_new_path)
        """
        seen = self.global_state.seen_attribute_paths
        for br in byte_ranges:
            path = br.cleaned_path
            if path not in known_attributes and path not in seen:
                return True, br.cleaned_key, path
        return False, None, None

    # ------------------------------------------------------------------
    # Template mining
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_mined_value(value):
        clean_value = str(value).strip('"\'')
        if clean_value.startswith('0x'):
            clean_value = clean_value[2:]
        return clean_value

    def parse_mined_values(self, lines):
        """Parse the "Mined interesting values:" section of ffcompile output."""
        template_values = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
        mining_started = False

        for line in lines:
            line = line.strip()

            if "Mined interesting values:" in line:
                mining_started = True
                continue
            if not mining_started:
                continue
            if any(section in line for section in ["File stat functions found:", "Lookahead functions found:", "Finished creating"]):
                break
            if ":" not in line or not ("{" in line or "[" in line):
                continue

            try:
                attr_name, values_str = line.split(":", 1)
                attr_name = attr_name.strip()
                values_str = values_str.strip()

                if values_str.startswith("{"):
                    values_dict = ast.literal_eval(values_str)
                    for key, value_list in values_dict.items():
                        values = value_list if isinstance(value_list, list) else [value_list]
                        for value in values:
                            insert_nested_dict(template_values, [attr_name, str(key)], self._clean_mined_value(value))
                elif values_str.startswith("["):
                    values_list = ast.literal_eval(values_str)
                    if attr_name not in template_values or not isinstance(template_values[attr_name], set):
                        template_values[attr_name] = set()
                    for value in values_list:
                        template_values[attr_name].add(self._clean_mined_value(value))
            except (ValueError, SyntaxError) as e:
                self.logger.error(f"Error parsing mined values line '{line}': {e}")
                continue

        return dict(template_values)

    def mine_interesting_values_from_template(self):
        """
        Mine interesting values from the template by running ffcompile.

        The generated C++ file is written to a temporary directory so the tracked
        ``<type>.cpp`` in the repository is never touched.

        Returns:
            tuple: (success: bool, mined_values: dict)
        """
        template_file = Config.get_template_path()
        self.logger.info(f"Mining interesting values from template: {template_file}")

        try:
            with tempfile.TemporaryDirectory(prefix="lc_ffcompile_") as tmpdir:
                output_file = os.path.join(tmpdir, f"{Config.FILE_TYPE}.cpp")
                result = subprocess.run(
                    [Config.FFCOMPILE_PATH, template_file, output_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    errors="replace",
                    timeout=Config.TEMPLATE_COMPILE_TIMEOUT,
                )
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout ({Config.TEMPLATE_COMPILE_TIMEOUT}s) running ffcompile on {template_file}")
            return False, {}
        except Exception as e:
            self.logger.error(f"Error mining interesting values from template: {e}")
            return False, {}

        if result.returncode != 0:
            self.logger.warning(f"ffcompile exited with {result.returncode} for {template_file}")

        template_values = self.parse_mined_values(result.stdout.splitlines() + result.stderr.splitlines())
        self.logger.info(f"Mined interesting values for {len(template_values)} template attributes")
        return True, template_values
