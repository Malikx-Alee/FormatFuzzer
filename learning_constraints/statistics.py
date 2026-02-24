"""
Statistics and reporting module for the learning constraints system.
Handles printing statistics and logging detected algorithms.
"""
import logging

try:
    from .config import Config
except ImportError:
    from learning_constraints.config import Config


class StatisticsReporter:
    """Handles statistics reporting and algorithm logging."""

    def __init__(self, global_state):
        """
        Initialize the statistics reporter.

        Args:
            global_state: The GlobalState instance containing collected data
        """
        self.global_state = global_state
        self.logger = logging.getLogger(__name__)

    def print_statistics(self):
        """Print processing statistics to console."""
        stats = self.global_state.get_stats()

        print("\n" + "=" * 50)
        print("PROCESSING STATISTICS")
        print("=" * 50)
        print(f"File Type: {Config.FILE_TYPE}")
        print(f"Valid Abstractions: {stats['valid_abstractions']}")
        print(f"Valid Abstractions (Special): {stats['valid_abstractions_special']}")
        print(f"Valid Overwrites: {stats['valid_overwrites']}")
        print(f"Blacklisted by Size (>{Config.MAX_ATTRIBUTE_SIZE_BYTES} bytes): {stats['blacklisted_by_size']}")
        print(f"Blacklisted by Count (>{Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE} values): {stats['blacklisted_by_count']}")
        print(f"Blacklisted Total: {stats['blacklisted_total']}")
        print("=" * 50)

    def log_checksum_algorithms(self):
        """Log detected checksum algorithms (by chunk type)."""
        try:
            if not getattr(Config, "ENABLE_CHECKSUM_DETECTION", False):
                return

            algos = self.global_state.checksum_algorithms or {}
            by_type = algos.get("by_chunk_type", {}) if isinstance(algos, dict) else {}

            if Config.FILE_TYPE == "zip":
                self._log_zip_algorithms(algos, by_type)
            else:
                self._log_generic_algorithms(by_type)

        except Exception as e:
            print(f"[ChecksumAlgo LOG][ERROR] {e}")

    def _log_zip_algorithms(self, algos, by_type):
        """Log ZIP-specific checksum and compression information."""
        print("\n----- ZIP checksum algorithms (by_chunk_type) -----")
        print(f"recordCrc: {by_type.get('recordCrc')}")
        print(f"dirEntryCrc: {by_type.get('dirEntryCrc')}")

        # Show compression methods found
        compression_methods = algos.get("compression_methods", {})
        if compression_methods:
            print("\n----- ZIP compression methods found -----")
            for method_id, method_name in sorted(compression_methods.items(), key=lambda x: int(x[0])):
                print(f"  {method_id}: {method_name}")

    def _log_generic_algorithms(self, by_type):
        """Log checksum algorithms for non-ZIP file types."""
        print("\n----- Checksum algorithms (by_chunk_type) -----")
        if isinstance(by_type, dict) and by_type:
            for k, v in by_type.items():
                print(f"{k}: {v}")
        else:
            print("<none>")

    def format_duration(self, total_seconds):
        """
        Format a duration in seconds to a human-readable string.

        Args:
            total_seconds: Duration in seconds

        Returns:
            str: Human-readable duration string
        """
        if total_seconds < 60:
            return f"{total_seconds:.2f} seconds"
        elif total_seconds < 3600:
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes} minutes {seconds:.2f} seconds"
        else:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = total_seconds % 60
            return f"{hours} hours {minutes} minutes {seconds:.2f} seconds"

