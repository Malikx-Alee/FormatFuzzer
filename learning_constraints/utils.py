"""
Utility functions for the learning constraints system.
Contains helper functions used across multiple modules.
"""
import collections
import random
import os

import binascii
import zlib
import hashlib
from typing import Optional, Tuple, List, Dict

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
    # MD2/MD4 generally unavailable in hashlib; skip unless present via openssl backed
    for name in ["md5", "sha1", "sha256", "sha384", "sha512"]:
        h = hashlib.new(name)
        h.update(data)
        results[name.upper().replace("SHA1", "SHA-1").replace("SHA256", "SHA-256").replace("SHA384", "SHA-384").replace("SHA512", "SHA-512")] = h.digest()
    # RIPEMD160 if available
    if HAVE_RIPEMD160:
        rh = _RIPEMD.new()
        rh.update(data)
        results["RIPEMD160"] = rh.digest()
    # TIGER if available
    if HAVE_TIGER:
        th = _TIGER.new()
        th.update(data)
        results["TIGER"] = th.digest()
    return results


def _crc_algorithms(data: bytes) -> Dict[str, bytes]:
    """Compute CRCs using Python stdlib where possible."""
    res: Dict[str, bytes] = {}
    # CRC-32
    crc32_val = binascii.crc32(data) & 0xFFFFFFFF
    res["CRC-32"] = crc32_val.to_bytes(4, "big")
    # Adler32 (use zlib; binascii may not provide adler32 in some environments)
    adler_val = zlib.adler32(data) & 0xFFFFFFFF
    res["Adler32"] = adler_val.to_bytes(4, "big")
    # CRC-16 and CRC-16/CCITT not in stdlib: simple implementations
    # CRC-16 (IBM/ARC) poly=0xA001 (reflected) init=0x0000
    crc = 0x0000
    for b in data:
        crc ^= b
        for _ in range(8):
            if (crc & 1) != 0:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    res["CRC-16"] = crc.to_bytes(2, "little")
    # CRC-16/CCITT-FALSE poly=0x1021 init=0xFFFF
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    res["CRC-16/CCITT"] = crc.to_bytes(2, "big")
    return res


def detect_checksum_algorithm_first(data: bytes, expected_value: bytes) -> Optional[str]:
    """Return the first matching algorithm name; stop testing after the first match."""
    exp = expected_value

    # 1) CRCs (PNG should match here quickly)
    crc32_val = binascii.crc32(data) & 0xFFFFFFFF
    if crc32_val.to_bytes(4, "big") == exp:
        return "CRC-32"
    adler_val = zlib.adler32(data) & 0xFFFFFFFF
    if adler_val.to_bytes(4, "big") == exp:
        return "Adler32"
    # CRC-16 (IBM/ARC)
    crc = 0x0000
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    if crc.to_bytes(2, "little") == exp:
        return "CRC-16"
    # CRC-16/CCITT-FALSE
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if (crc & 0x8000) != 0:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    if crc.to_bytes(2, "big") == exp:
        return "CRC-16/CCITT"

    # 2) Sum-based checks
    total = sum(data) & ((1 << 64) - 1)
    if (total & 0xFF).to_bytes(1, "big") == exp:
        return "Checksum - UByte (8 bit)"
    if (total & 0xFFFF).to_bytes(2, "little") == exp:
        return "Checksum - UShort (16 bit) - Little Endian"
    if (total & 0xFFFF).to_bytes(2, "big") == exp:
        return "Checksum - UShort (16 bit) - Big Endian"
    if (total & 0xFFFFFFFF).to_bytes(4, "little") == exp:
        return "Checksum - UInt (32 bit) - Little Endian"
    if (total & 0xFFFFFFFF).to_bytes(4, "big") == exp:
        return "Checksum - UInt (32 bit) - Big Endian"
    if (total & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little") == exp:
        return "Checksum - UInt64 (64 bit) - Little Endian"
    if (total & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "big") == exp:
        return "Checksum - UInt64 (64 bit) - Big Endian"

    # 3) Hashes (only if lengths match)
    # Only try when expected value length matches the digest length to avoid extra work.
    try_hashes: List[Tuple[str, int]] = [
        ("MD5", 16), ("SHA-1", 20), ("SHA-256", 32), ("SHA-384", 48), ("SHA-512", 64)
    ]
    if len(exp) in [l for _, l in try_hashes] or len(exp) in (16, 20, 32, 48, 64):
        # md5
        if len(exp) == 16:
            h = hashlib.md5(); h.update(data)
            if h.digest() == exp:
                return "MD5"
        # sha-1
        if len(exp) == 20:
            h = hashlib.sha1(); h.update(data)
            if h.digest() == exp:
                return "SHA-1"
        # sha-256
        if len(exp) == 32:
            h = hashlib.sha256(); h.update(data)
            if h.digest() == exp:
                return "SHA-256"
        # sha-384
        if len(exp) == 48:
            h = hashlib.sha384(); h.update(data)
            if h.digest() == exp:
                return "SHA-384"
        # sha-512
        if len(exp) == 64:
            h = hashlib.sha512(); h.update(data)
            if h.digest() == exp:
                return "SHA-512"

    # Optional RIPEMD160
    if HAVE_RIPEMD160 and len(exp) == 20:
        rh = _RIPEMD.new(); rh.update(data)
        if rh.digest() == exp:
            return "RIPEMD160"

    # Optional TIGER
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

    normalized_expected = expected_value
    matches = [name for name, digest in candidates.items() if digest == normalized_expected]
    return matches


def convert_sets_to_lists(obj):
    """
    Recursively converts sets to lists in a nested dictionary.

    Args:
        obj: The object to convert (dict, set, list, or other)

    Returns:
        The converted object with sets replaced by lists
    """
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    elif isinstance(obj, collections.defaultdict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    return obj


def clean_attribute_key(attribute):
    """
    Extracts the last part after '~' and removes trailing _<number> if present.

    Args:
        attribute (str): The attribute string to clean

    Returns:
        str: The cleaned attribute key
    """
    key = attribute.split("~")[-1]
    if "_" in key:
        parts = key.split("_")
        if len(parts) > 1 and parts[1].isdigit():
            key = parts[0]
    return key


def insert_nested_dict(root, original_keys, value):
    """
    Recursively inserts values into a nested dictionary with special handling for hierarchical arrays.

    Args:
        root: The root dictionary to insert into
        original_keys (list): List of keys representing the path
        value: The value to insert
    """
    current = root

    # Clean keys by removing array indices if present
    keys = []
    for key in original_keys:
        if "_" in key:
            # If the key contains an underscore, split it
            parts = key.split("_")
            # Check if the second part is a number
            if parts[1].isdigit():
                # If it's a number, only keep the first part
                key = parts[0]
            # If it's not a number, keep the whole key
        keys.append(key)

    # Navigate through all keys except the last one
    for key in keys[:-1]:  # Traverse and create intermediate levels
        if key not in current:
            # Create new nested defaultdict if key doesn't exist
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], set):
            # If the current level is a set, convert it to a defaultdict for deeper nesting
            current[key] = collections.defaultdict(lambda: set())
        elif isinstance(current[key], list):
            current[key] = collections.defaultdict(lambda: set())
        # Move to the next level
        current = current[key]

    last_key = keys[-1]  # Final key where value should be stored

    # Handle the final key insertion
    if last_key not in current:
        # Initialize as a set if it doesn't exist
        current[last_key] = set()

    if isinstance(current[last_key], set):
        # If it's a set, add the value
        current[last_key].add(value)


def overwrite_bytes_randomly(file_path, start, end):
    """
    Randomly overwrites bytes in a file between the given start and end positions.

    Args:
        file_path (str): Path to the file to modify
        start (int): Start position (inclusive) of the range to overwrite
        end (int): End position (inclusive) of the range to overwrite

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If start > end or positions are out of bounds
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if start > end:
        raise ValueError("Start position must be less than or equal to the end position.")

    try:
        with open(file_path, "r+b") as f:  # Open file in read/write binary mode
            file_size = os.path.getsize(file_path)

            if start < 0 or end >= file_size:
                raise ValueError(f"Start and end positions must be within the file size (0 to {file_size - 1}).")

            # Seek to the start position
            f.seek(start)

            # Overwrite bytes with random values
            for position in range(start, end + 1):
                random_byte = random.randint(0, 255)  # Generate a random byte (0-255)
                f.write(bytes([random_byte]))  # Write the random byte

            # print(f"Successfully overwrote bytes from position {start} to {end} in {file_path}.")

    except Exception as e:
        print(f"Error overwriting bytes in {file_path}: {e}")
        raise


def extract_byte_values(file_data, start, end):
    """
    Extract byte values from file data and convert to different formats.

    Args:
        file_data (bytes): The file data
        start (int): Start position
        end (int): End position

    Returns:
        dict: Dictionary containing hex, base10, and ascii representations
    """
    if end >= len(file_data):
        raise ValueError(f"End position {end} exceeds file size {len(file_data)}")

    # Extract the byte range
    byte_range = file_data[start:end + 1]

    return {
        'hex': byte_range.hex(),
        'base10': "".join(str(byte) for byte in byte_range),
        'ascii': "".join(chr(byte) if 32 <= byte <= 126 else '.' for byte in byte_range)
    }


def validate_byte_range(start, end, file_size, max_size=8):
    """
    Validate that a byte range is within acceptable bounds.

    Args:
        start (int): Start position
        end (int): End position
        file_size (int): Size of the file
        max_size (int): Maximum allowed range size

    Returns:
        bool: True if valid, False otherwise
    """
    if start < 0 or end >= file_size:
        return False
    if start > end:
        return False
    if end - start > max_size:
        return False
    return True


def remove_attribute_from_nested_dict(root, attribute_label):
    """
    Remove all entries for a specific attribute from nested_values_hex.
    This function removes entries based on the cleaned attribute key, which means
    it will remove all variations of the attribute (e.g., attr_1, attr_2, etc.)

    Args:
        root: The root nested dictionary (nested_values_hex)
        attribute_label (str): The attribute label (e.g., "file~dirEntry_5~deExtraField~efHeaderID")
    """
    # Get the cleaned attribute key (last part after '~', without array indices)
    cleaned_key = clean_attribute_key(attribute_label)

    def _remove_from_dict(current_dict, target_key):
        """Recursively search and remove target_key from all levels of the dictionary."""
        keys_to_remove = []

        for key, value in current_dict.items():
            if key == target_key:
                # Mark this key for removal
                keys_to_remove.append(key)
            elif isinstance(value, dict):
                # Recursively search in nested dictionaries
                _remove_from_dict(value, target_key)
                # If the nested dict becomes empty after removal, mark it for removal too
                if not value:
                    keys_to_remove.append(key)

        # Remove marked keys
        for key in keys_to_remove:
            current_dict.pop(key, None)

    # Start the recursive removal
    _remove_from_dict(root, cleaned_key)
