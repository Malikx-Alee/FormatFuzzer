"""
Utility functions for the learning constraints system.
Contains helper functions used across multiple modules.

Key naming conventions used throughout the package:

* An *attribute label* is what the fuzzer prints: ``file~chunk_3~plte~plteChunkData~btRed_2``.
  Segments are separated by ``~`` and array elements / re-reads carry a ``_<N>`` suffix.
* A *cleaned path* is the label with every ``_<N>`` suffix removed:
  ``file~chunk~plte~plteChunkData~btRed``.  Values, blacklists and the "seen attributes" set
  are all keyed by cleaned path, so the same field in different array elements pools together
  while the same field name under different parents stays apart.
* A *cleaned key* (or leaf name) is the last segment of the cleaned path: ``btRed``.  It is used
  only when writing the flattened output, where the downstream consumers expect leaf names.
"""
import collections
import random
import os
import re
import logging
import binascii
import zlib
import hashlib
from typing import Optional, Tuple, List, Dict, Iterator, Any
from dataclasses import dataclass

# Module-level logger
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Key handling
# ---------------------------------------------------------------------------

_INDEX_SUFFIX_RE = re.compile(r"^(.+?)_(\d+)$")


def split_index(name: str) -> Tuple[str, Optional[int]]:
    """
    Split a trailing ``_<digits>`` index off a single path segment.

    ``chunk_5`` -> ``("chunk", 5)``, ``index_entry_12`` -> ``("index_entry", 12)``,
    ``dw_flags`` -> ``("dw_flags", None)``.
    """
    match = _INDEX_SUFFIX_RE.match(name)
    if not match:
        return name, None
    return match.group(1), int(match.group(2))


def strip_index(name: str) -> str:
    """Remove a trailing ``_<digits>`` suffix from a single path segment, if present."""
    return split_index(name)[0]


def clean_single_key(key: str) -> str:
    """Backward-compatible alias for :func:`strip_index`."""
    return strip_index(key)


def clean_keys_list(keys: List[str]) -> List[str]:
    """Strip array indices from every segment of a split attribute label."""
    return [strip_index(key) for key in keys]


def clean_attribute_key(attribute: str) -> str:
    """Return the cleaned *leaf name* (last segment, index stripped) of an attribute label."""
    return strip_index(attribute.split("~")[-1])


def clean_attribute_path(attribute: str) -> str:
    """Return the cleaned *full path* (every segment index-stripped) of an attribute label."""
    return "~".join(clean_keys_list(attribute.split("~")))


# ---------------------------------------------------------------------------
# ByteRange
# ---------------------------------------------------------------------------

@dataclass
class ByteRange:
    """
    Represents a byte range with an associated attribute.

    Attributes:
        start: Start position of the byte range (inclusive)
        end: End position of the byte range (inclusive)
        attribute: Hierarchical attribute label as printed by the fuzzer (e.g. "file~chunk_1~crc")
        flags: Extra CSV fields the fuzzer emitted for this line ("Optional", "Appendable", ...)
    """
    start: int
    end: int
    attribute: str
    flags: Tuple[str, ...] = ()

    @property
    def size(self) -> int:
        """Return the size of the byte range in bytes (inclusive end)."""
        return self.end - self.start + 1

    @property
    def cleaned_key(self) -> str:
        """Return the cleaned leaf name (last segment without array index)."""
        return clean_attribute_key(self.attribute)

    @property
    def cleaned_path(self) -> str:
        """Return the cleaned full path (all segments without array indices)."""
        return clean_attribute_path(self.attribute)

    @property
    def attribute_keys(self) -> List[str]:
        """Return the raw attribute split into hierarchical keys."""
        return self.attribute.split("~")

    @property
    def optional(self) -> bool:
        """True when the fuzzer flagged this range as Optional."""
        return "Optional" in self.flags

    def is_within_size_limit(self, max_bytes: int = 8) -> bool:
        """Check if the byte range is within the size limit (size in bytes, inclusive)."""
        return self.size <= max_bytes

    def as_tuple(self) -> Tuple[int, int, str]:
        """Return the byte range as a tuple for backward compatibility."""
        return (self.start, self.end, self.attribute)


# ---------------------------------------------------------------------------
# Checksum helpers
# ---------------------------------------------------------------------------

# Optional: third-party hashes may not be available; guard imports
try:
    import Crypto.Hash.RIPEMD as _RIPEMD
    HAVE_RIPEMD160 = True
except Exception:
    HAVE_RIPEMD160 = False

# TIGER is uncommon; skip if not available
try:
    from Crypto.Hash import TIGER as _TIGER  # type: ignore
    HAVE_TIGER = True
except Exception:
    HAVE_TIGER = False


def _sum_checks(data: bytes) -> Dict[str, bytes]:
    """Compute simple sum-based checks with various widths/endianness."""
    total = sum(data) & ((1 << 64) - 1)
    res = {
        "Checksum - UByte (8 bit)": (total & 0xFF).to_bytes(1, "big"),
        "Checksum - UShort (16 bit) - Little Endian": (total & 0xFFFF).to_bytes(2, "little"),
        "Checksum - UShort (16 bit) - Big Endian": (total & 0xFFFF).to_bytes(2, "big"),
        "Checksum - UInt (32 bit) - Little Endian": (total & 0xFFFFFFFF).to_bytes(4, "little"),
        "Checksum - UInt (32 bit) - Big Endian": (total & 0xFFFFFFFF).to_bytes(4, "big"),
        "Checksum - UInt64 (64 bit) - Little Endian": (total & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little"),
        "Checksum - UInt64 (64 bit) - Big Endian": (total & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "big"),
    }
    return res


def _hash_algorithms(data: bytes) -> Dict[str, bytes]:
    """Compute hash digests for supported algorithms."""
    results: Dict[str, bytes] = {}
    for name in ["md5", "sha1", "sha256", "sha384", "sha512"]:
        h = hashlib.new(name)
        h.update(data)
        results[name.upper().replace("SHA1", "SHA-1").replace("SHA256", "SHA-256").replace("SHA384", "SHA-384").replace("SHA512", "SHA-512")] = h.digest()
    if HAVE_RIPEMD160:
        rh = _RIPEMD.new()
        rh.update(data)
        results["RIPEMD160"] = rh.digest()
    if HAVE_TIGER:
        th = _TIGER.new()
        th.update(data)
        results["TIGER"] = th.digest()
    return results


def _crc16_arc(data: bytes) -> int:
    crc = 0x0000
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc


def _crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _crc_algorithms(data: bytes) -> Dict[str, bytes]:
    """Compute CRCs using Python stdlib where possible."""
    res: Dict[str, bytes] = {}
    res["CRC-32"] = (binascii.crc32(data) & 0xFFFFFFFF).to_bytes(4, "big")
    res["Adler32"] = (zlib.adler32(data) & 0xFFFFFFFF).to_bytes(4, "big")
    res["CRC-16"] = _crc16_arc(data).to_bytes(2, "little")
    res["CRC-16/CCITT"] = _crc16_ccitt_false(data).to_bytes(2, "big")
    return res


def detect_checksum_algorithm_first(data: bytes, expected_value: bytes) -> Optional[str]:
    """Return the first matching algorithm name; stop testing after the first match."""
    exp = expected_value

    # 1) CRCs (PNG should match here quickly)
    if (binascii.crc32(data) & 0xFFFFFFFF).to_bytes(4, "big") == exp:
        return "CRC-32"
    if (zlib.adler32(data) & 0xFFFFFFFF).to_bytes(4, "big") == exp:
        return "Adler32"
    if _crc16_arc(data).to_bytes(2, "little") == exp:
        return "CRC-16"
    if _crc16_ccitt_false(data).to_bytes(2, "big") == exp:
        return "CRC-16/CCITT"

    # 2) Sum-based checks
    for name, digest in _sum_checks(data).items():
        if digest == exp:
            return name

    # 3) Hashes (only when the expected length matches the digest length)
    hash_by_len = {16: ("MD5", hashlib.md5), 20: ("SHA-1", hashlib.sha1), 32: ("SHA-256", hashlib.sha256),
                   48: ("SHA-384", hashlib.sha384), 64: ("SHA-512", hashlib.sha512)}
    if len(exp) in hash_by_len:
        name, ctor = hash_by_len[len(exp)]
        if ctor(data).digest() == exp:
            return name

    if HAVE_RIPEMD160 and len(exp) == 20:
        rh = _RIPEMD.new(); rh.update(data)
        if rh.digest() == exp:
            return "RIPEMD160"

    if HAVE_TIGER and len(exp) == 24:
        th = _TIGER.new(); th.update(data)
        if th.digest() == exp:
            return "TIGER"

    return None


def detect_checksum_algorithms(data: bytes, expected_value: bytes) -> List[str]:
    """Try all supported checksum/hash algorithms and return matches by name."""
    candidates: Dict[str, bytes] = {}
    candidates.update(_sum_checks(data))
    candidates.update(_crc_algorithms(data))
    candidates.update(_hash_algorithms(data))
    return [name for name, digest in candidates.items() if digest == expected_value]


# ---------------------------------------------------------------------------
# Nested value dictionary helpers
# ---------------------------------------------------------------------------

def convert_sets_to_lists(obj):
    """Recursively convert sets to (sorted) lists in a nested dictionary."""
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        try:
            return sorted(obj)
        except TypeError:
            return list(obj)
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    return obj


def new_nested_dict():
    """Create an empty nested value dictionary."""
    return collections.defaultdict(lambda: collections.defaultdict(lambda: set()))


def insert_nested_dict(root, original_keys, value):
    """
    Insert a value into the nested dictionary under the *cleaned* path of ``original_keys``.

    Args:
        root: The root dictionary to insert into
        original_keys (list): Raw attribute segments (array indices are stripped here)
        value: The value to insert
    """
    current = root
    keys = clean_keys_list(original_keys)

    for key in keys[:-1]:
        if key not in current or isinstance(current[key], (set, list)):
            current[key] = collections.defaultdict(lambda: set())
        current = current[key]

    last_key = keys[-1]
    if last_key not in current:
        current[last_key] = set()
    if isinstance(current[last_key], list):
        current[last_key] = set(current[last_key])
    if isinstance(current[last_key], set):
        current[last_key].add(value)


def iter_leaf_paths(nested, prefix: str = "") -> Iterator[Tuple[str, Any]]:
    """Yield ``(cleaned_path, values)`` for every leaf (set or list) in a nested dictionary."""
    for key, value in nested.items():
        path = f"{prefix}~{key}" if prefix else key
        if isinstance(value, dict):
            yield from iter_leaf_paths(value, path)
        elif isinstance(value, (set, list)):
            yield path, value


def get_leaf(nested, path: str):
    """Return the leaf (set or list) stored under a cleaned path, or None."""
    current = nested
    for key in path.split("~"):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current if isinstance(current, (set, list)) else None


def remove_path_from_nested_dict(root, path: str) -> bool:
    """
    Remove the leaf stored under a cleaned path and prune parents that become empty.

    Only a leaf (set/list) is ever removed. Intermediate nodes that merely share the leaf's name
    are untouched, which is what makes this safe for formats where a struct and a field share a
    name (AVI ``data``, PNG ``type``).

    Returns:
        bool: True if a leaf was removed.
    """
    keys = path.split("~")
    parents = []
    current = root
    for key in keys[:-1]:
        if isinstance(current, dict) and key in current and isinstance(current[key], dict):
            parents.append((current, key))
            current = current[key]
        else:
            return False

    leaf_key = keys[-1]
    if not (isinstance(current, dict) and leaf_key in current and isinstance(current[leaf_key], (set, list))):
        return False
    del current[leaf_key]

    for parent, key in reversed(parents):
        if not parent[key]:
            del parent[key]
        else:
            break
    return True


def remove_attribute_from_nested_dict(root, attribute_label: str) -> bool:
    """Remove the leaf for an attribute label (any array index) from the nested dictionary."""
    return remove_path_from_nested_dict(root, clean_attribute_path(attribute_label))


def filter_blacklisted_attributes(nested_dict, blacklisted_paths, legacy_leaf_names=None):
    """
    Return a copy of ``nested_dict`` without the blacklisted leaves.

    Args:
        nested_dict: Nested dictionary (sets or lists at the leaves)
        blacklisted_paths: Set of cleaned full paths to drop
        legacy_leaf_names: Optional set of leaf names from pre-v2 checkpoints; a leaf whose
            name is in this set is dropped regardless of its path.
    """
    blacklisted_paths = set(blacklisted_paths or ())
    legacy_leaf_names = set(legacy_leaf_names or ())
    if not blacklisted_paths and not legacy_leaf_names:
        return nested_dict

    def _filter(current, prefix):
        result = {}
        for key, value in current.items():
            path = f"{prefix}~{key}" if prefix else key
            if isinstance(value, dict):
                filtered = _filter(value, path)
                if filtered:
                    result[key] = filtered
            else:
                if path in blacklisted_paths or key in legacy_leaf_names:
                    continue
                result[key] = value
        return result

    return _filter(nested_dict, "")


# ---------------------------------------------------------------------------
# Byte helpers
# ---------------------------------------------------------------------------

def overwrite_bytes_randomly(file_path, start, end):
    """
    Randomly overwrite bytes in a file between the given start and end positions (inclusive).

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If start > end or positions are out of bounds
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if start > end:
        raise ValueError("Start position must be less than or equal to the end position.")

    file_size = os.path.getsize(file_path)
    if start < 0 or end >= file_size:
        raise ValueError(f"Start and end positions must be within the file size (0 to {file_size - 1}).")

    with open(file_path, "r+b") as f:
        f.seek(start)
        f.write(bytes(random.randint(0, 255) for _ in range(start, end + 1)))


def extract_byte_values(file_data, start, end):
    """
    Extract byte values from file data and convert to different formats.

    Raises:
        ValueError: if the range is not within the data.
    """
    if start < 0 or start > end or end >= len(file_data):
        raise ValueError(f"Invalid byte range {start}-{end} for data of size {len(file_data)}")

    byte_range = file_data[start:end + 1]
    return {
        'hex': byte_range.hex(),
        'base10': "".join(str(byte) for byte in byte_range),
        'ascii': "".join(chr(byte) if 32 <= byte <= 126 else '.' for byte in byte_range)
    }


def validate_byte_range(start, end, file_size, max_size=None):
    """
    Validate that a byte range is within acceptable bounds.

    Args:
        start (int): Start position (inclusive)
        end (int): End position (inclusive)
        file_size (int): Size of the file
        max_size (int, optional): Maximum allowed range size in bytes; None disables the check

    Returns:
        bool: True if valid, False otherwise
    """
    if start < 0 or end < start or end >= file_size:
        return False
    if max_size is not None and (end - start + 1) > max_size:
        return False
    return True
