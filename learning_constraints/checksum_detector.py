"""
Checksum and compression detection module for the learning constraints system.
Contains logic for detecting checksum algorithms and compression methods in various file formats.
"""
import logging
import zlib
from .config import Config, GlobalState
from .utils import detect_checksum_algorithm_first, ByteRange


# Module-level logger
logger = logging.getLogger(__name__)


class ChecksumDetector:
    """Handles checksum and compression detection for various file formats."""
    
    def __init__(self, global_state: GlobalState):
        """
        Initialize the checksum detector with global state.
        
        Args:
            global_state (GlobalState): The global state object
        """
        self.global_state = global_state
        self.logger = logging.getLogger(__name__)
    
    def detect_compression_and_checksum(
        self,
        file_data: bytes,
        byte_ranges: list,
        original_byte_ranges: list,
        start: int,
        end: int,
        attribute_keys: list,
        byte_values: dict,
        seen_chunk_types_for_file: set
    ):
        """
        Detect compression methods and checksum algorithms for the current attribute.
        
        Args:
            file_data: The raw file data
            byte_ranges: List of filtered byte ranges
            original_byte_ranges: List of all byte ranges including large ones
            start: Start position of current attribute
            end: End position of current attribute
            attribute_keys: List of hierarchical keys for the attribute
            byte_values: Dictionary with extracted byte values (hex, etc.)
            seen_chunk_types_for_file: Set tracking which chunk types have been processed
        """
        last_key = attribute_keys[-1]
        
        # Detect PNG compression method from IHDR chunk
        if Config.FILE_TYPE == "png" and Config.ENABLE_CHECKSUM_DETECTION:
            self._detect_png_compression(file_data, end, attribute_keys, last_key)
        
        # Detect BMP compression method from BITMAPINFOHEADER
        if Config.FILE_TYPE == "bmp" and Config.ENABLE_CHECKSUM_DETECTION:
            self._detect_bmp_compression(file_data, start, end, attribute_keys, last_key)
        
        # Detect checksum algorithms if enabled
        if getattr(Config, "ENABLE_CHECKSUM_DETECTION", False):
            self._detect_checksum(
                file_data, byte_ranges, original_byte_ranges,
                start, attribute_keys, byte_values,
                seen_chunk_types_for_file
            )
    
    def _detect_png_compression(self, file_data: bytes, end: int, attribute_keys: list, last_key: str):
        """Detect PNG compression method from IHDR chunk."""
        if last_key == "compr_method" and len(attribute_keys) >= 3 and "ihdr" in attribute_keys:
            compr_method_value = file_data[end]
            method_name = self._get_png_compression_method_name(compr_method_value)
            self._record_compression_method(compr_method_value, method_name, "PNG")
    
    def _detect_bmp_compression(self, file_data: bytes, start: int, end: int, attribute_keys: list, last_key: str):
        """Detect BMP compression method from BITMAPINFOHEADER."""
        if last_key == "biCompression" and len(attribute_keys) >= 2:
            compr_method_value = int.from_bytes(file_data[start:end + 1], "little")
            method_name = self._get_bmp_compression_method_name(compr_method_value)
            self._record_compression_method(compr_method_value, method_name, "BMP")
    
    def _record_compression_method(self, method_value: int, method_name: str, file_type: str):
        """Record a compression method in the global state."""
        key = str(method_value)
        if key not in self.global_state.checksum_algorithms["compression_methods"]:
            self.global_state.checksum_algorithms["compression_methods"][key] = method_name
            self.logger.info(f"[{file_type}] Detected compression method: {method_value} ({method_name})")
        else:
            self.global_state.checksum_algorithms["compression_methods"][key] = method_name
    
    def _detect_checksum(
        self,
        file_data: bytes,
        byte_ranges: list,
        original_byte_ranges: list,
        start: int,
        attribute_keys: list,
        byte_values: dict,
        seen_chunk_types_for_file: set
    ):
        """Main checksum detection dispatcher."""
        try:
            last_key = attribute_keys[-1]
            
            if last_key == "crc" and Config.FILE_TYPE == "png":
                self._detect_png_checksum(
                    file_data, byte_ranges, start,
                    attribute_keys, byte_values, seen_chunk_types_for_file
                )
            elif Config.FILE_TYPE == "zip" and last_key in ("frCrc", "deCrc"):
                self._detect_zip_checksum(
                    file_data, original_byte_ranges,
                    attribute_keys, byte_values, seen_chunk_types_for_file
                )
        except Exception:
            # Best-effort detection; continue silently
            pass
    
    def _detect_png_checksum(
        self,
        file_data: bytes,
        byte_ranges: list,
        start: int,
        attribute_keys: list,
        byte_values: dict,
        seen_chunk_types_for_file: set
    ):
        """Detect PNG CRC-32 checksums."""
        prefix = "~".join(attribute_keys[:-1])
        expected_crc_bytes = bytes.fromhex(byte_values['hex'])
        
        # Find type range
        type_start, type_end = self._find_png_type_range(byte_ranges, prefix)
        
        crc_start = start
        if type_start is not None and type_end is not None:
            checksum_start = type_start
            checksum_end = crc_start - 1
            if checksum_end >= checksum_start:
                checksum_input = file_data[checksum_start:checksum_end + 1]
                first_match = detect_checksum_algorithm_first(checksum_input, expected_crc_bytes)
                matches = [first_match] if first_match else []
                
                # Record by chunk type
                try:
                    chunk_type = file_data[type_start:type_end + 1]
                    chunk_type_str = chunk_type.decode("ascii", errors="ignore")
                    if chunk_type_str and chunk_type_str not in seen_chunk_types_for_file:
                        existing = self.global_state.checksum_algorithms["by_chunk_type"].get(chunk_type_str, [])
                        merged = sorted(set(existing + matches))
                        self.global_state.checksum_algorithms["by_chunk_type"][chunk_type_str] = merged
                        seen_chunk_types_for_file.add(chunk_type_str)
                except Exception:
                    pass

    def _find_png_type_range(self, byte_ranges: list, prefix: str):
        """Find the type range for a PNG chunk."""
        type_start = None
        type_end = None

        # Try to find explicit type range
        type_prefix = prefix + "~type"
        for br in byte_ranges:
            if br.attribute.startswith(type_prefix):
                type_start, type_end = br.start, br.end
                break

        # If not found, infer type immediately after length
        if type_start is None:
            length_prefix = prefix + "~length"
            for br in byte_ranges:
                if br.attribute.startswith(length_prefix):
                    type_start = br.end + 1
                    type_end = type_start + 3
                    break

        return type_start, type_end

    def _detect_zip_checksum(
        self,
        file_data: bytes,
        original_byte_ranges: list,
        attribute_keys: list,
        byte_values: dict,
        seen_chunk_types_for_file: set
    ):
        """Detect ZIP CRC checksums."""
        try:
            last_key = attribute_keys[-1]
            expected_crc_bytes = bytes.fromhex(byte_values['hex'])

            if last_key == "frCrc":
                self._detect_zip_record_crc(
                    file_data, original_byte_ranges, attribute_keys,
                    expected_crc_bytes, seen_chunk_types_for_file
                )
            else:  # deCrc
                self._detect_zip_direntry_crc(seen_chunk_types_for_file)
        except Exception:
            pass

    def _detect_zip_record_crc(
        self,
        file_data: bytes,
        original_byte_ranges: list,
        attribute_keys: list,
        expected_crc_bytes: bytes,
        seen_chunk_types_for_file: set
    ):
        """Detect ZIP file record CRC."""
        unified_key = "recordCrc"

        if "frCrc" in seen_chunk_types_for_file:
            return

        record_element = attribute_keys[1] if len(attribute_keys) > 1 else "record"
        first_match = None

        # Find frData and frCompression
        record_prefix = f"file~{record_element}"
        frdata_prefix = f"{record_prefix}~frData"
        frmethod_prefix = f"{record_prefix}~frCompression"

        frdata_start = None
        frdata_end = None
        frmethod_value = None

        for br in original_byte_ranges:
            if br.attribute.startswith(frdata_prefix):
                frdata_start, frdata_end = br.start, br.end
            elif br.attribute.startswith(frmethod_prefix):
                method_bytes = file_data[br.start:br.end + 1]
                if len(method_bytes) == 2:
                    frmethod_value = int.from_bytes(method_bytes, "little")
            if frdata_start is not None and frmethod_value is not None:
                break

        # Track compression method
        if frmethod_value is not None:
            method_name = self._get_compression_method_name(frmethod_value)
            self._record_compression_method(frmethod_value, method_name, "ZIP")

        # Validate checksum with decompression if enabled
        if getattr(Config, "ZIP_VALIDATE_CHECKSUM_WITH_DECOMPRESSION", False):
            if frdata_start is not None and frdata_end is not None and frmethod_value is not None:
                compressed_data = file_data[frdata_start:frdata_end + 1]
                try:
                    uncompressed_data = self._decompress_zip_data(compressed_data, frmethod_value)
                    if uncompressed_data is not None:
                        first_match = self._validate_zip_crc(uncompressed_data, expected_crc_bytes)
                except Exception:
                    pass

        # Default to CRC-32 per ZIP spec if no match found
        if first_match is None:
            first_match = "CRC-32"

        # Record result
        if first_match:
            existing = self.global_state.checksum_algorithms["by_chunk_type"].get(unified_key, [])
            merged = sorted(set(existing + [first_match]))
            self.global_state.checksum_algorithms["by_chunk_type"][unified_key] = merged

        seen_chunk_types_for_file.add("frCrc")

    def _detect_zip_direntry_crc(self, seen_chunk_types_for_file: set):
        """Detect ZIP directory entry CRC (mirrors record CRC)."""
        unified_key = "dirEntryCrc"

        if "deCrc" in seen_chunk_types_for_file:
            return

        # Mirror from recordCrc
        record_algos = self.global_state.checksum_algorithms["by_chunk_type"].get("recordCrc")
        if record_algos:
            self.global_state.checksum_algorithms["by_chunk_type"][unified_key] = list(record_algos)

        seen_chunk_types_for_file.add("deCrc")

    def _validate_zip_crc(self, uncompressed_data: bytes, expected_crc_bytes: bytes):
        """Validate CRC for ZIP uncompressed data."""
        if len(expected_crc_bytes) == 4:
            be = expected_crc_bytes
            le = expected_crc_bytes[::-1]
        else:
            be = expected_crc_bytes
            le = expected_crc_bytes

        first_match = detect_checksum_algorithm_first(uncompressed_data, be)
        if not first_match and len(expected_crc_bytes) == 4:
            first_match = detect_checksum_algorithm_first(uncompressed_data, le)

        return first_match

    # ========== Compression Method Lookup Tables ==========

    def _get_compression_method_name(self, method_value: int) -> str:
        """Get the name of a ZIP compression method."""
        compression_methods = {
            0: "STORED",
            1: "SHRUNK",
            2: "REDUCED_1",
            3: "REDUCED_2",
            4: "REDUCED_3",
            5: "REDUCED_4",
            6: "IMPLODED",
            7: "RESERVED",
            8: "DEFLATE",
            9: "DEFLATE64",
            10: "PKWARE_IMPLODE",
            11: "RESERVED",
            12: "BZIP2",
            13: "RESERVED",
            14: "LZMA",
            15: "RESERVED",
            16: "RESERVED",
            17: "RESERVED",
            18: "IBM_TERSE",
            19: "IBM_LZ77",
            20: "ZSTD_DEPRECATED",
            93: "ZSTD",
            94: "MP3",
            95: "XZ",
            96: "JPEG",
            97: "WAVPACK",
            98: "PPMD",
            99: "AE-x"
        }
        return compression_methods.get(method_value, f"UNKNOWN_{method_value}")

    def _get_png_compression_method_name(self, method_value: int) -> str:
        """Get the name of a PNG compression method."""
        compression_methods = {
            0: "DEFLATE"
        }
        return compression_methods.get(method_value, f"UNKNOWN_{method_value}")

    def _get_bmp_compression_method_name(self, method_value: int) -> str:
        """Get the name of a BMP compression method."""
        compression_methods = {
            0: "BI_RGB",
            1: "BI_RLE8",
            2: "BI_RLE4",
            3: "BI_BITFIELDS",
            4: "BI_JPEG",
            5: "BI_PNG",
            6: "BI_ALPHABITFIELDS",
            11: "BI_CMYK",
            12: "BI_CMYKRLE8",
            13: "BI_CMYKRLE4"
        }
        return compression_methods.get(method_value, f"UNKNOWN_{method_value}")

    # ========== Decompression Methods ==========

    def _decompress_zip_data(self, compressed_data: bytes, method_value: int):
        """
        Decompress ZIP data based on compression method.

        Args:
            compressed_data: The compressed data
            method_value: The compression method value

        Returns:
            bytes or None: The uncompressed data, or None if unsupported/failed
        """
        try:
            if method_value == 0:
                # STORED (no compression)
                return compressed_data
            elif method_value == 8:
                # DEFLATE
                return zlib.decompress(compressed_data, -zlib.MAX_WBITS)
            elif method_value == 12:
                # BZIP2
                try:
                    import bz2
                    return bz2.decompress(compressed_data)
                except ImportError:
                    self.logger.warning("[ZIP] BZIP2 decompression not available (bz2 module not found)")
                    return None
            elif method_value == 14:
                # LZMA
                try:
                    import lzma
                    return lzma.decompress(compressed_data)
                except ImportError:
                    self.logger.warning("[ZIP] LZMA decompression not available (lzma module not found)")
                    return None
            else:
                # Unsupported compression method
                return None
        except Exception as e:
            self.logger.error(f"[ZIP] Decompression failed for method {method_value}: {e}")
            return None
