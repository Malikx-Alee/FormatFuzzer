import os
import tempfile
import unittest

from helpers import REPO_ROOT, leaf_map  # noqa: F401

from learning_constraints.config import Config, GlobalState
from learning_constraints.checkpoint import CheckpointManager
from learning_constraints.utils import insert_nested_dict, filter_blacklisted_attributes, convert_sets_to_lists


def _populated_state():
    st = GlobalState()
    insert_nested_dict(st.nested_values_hex, "file~chunk_1~ihdr~width".split("~"), "00000020")
    insert_nested_dict(st.nested_values_hex, "file~chunk_2~crc".split("~"), "aabbccdd")
    insert_nested_dict(st.nested_values_hex, "file~chunk_2~crc".split("~"), "11223344")
    insert_nested_dict(st.nested_values_hex, "file~chunk~data".split("~"), "ff")
    st.blacklist_by_size("file~chunk~data")           # removes the stored value too
    st.register_attributes(["file~chunk~ihdr~width", "file~chunk~crc", "file~chunk~data"])
    st.record_dropped_array("file~jpgfile~scanData", 1383)
    st.checksum_algorithms["by_chunk_type"]["IHDR"] = ["CRC-32"]
    st.valid_abstractions_count = 7
    return st


class CheckpointRoundTripTests(unittest.TestCase):
    def setUp(self):
        self._saved = {k: getattr(Config, k) for k in ("LOGS_BASE_DIR", "CURRENT_LOG_DIR", "CURRENT_RESULTS_DIR",
                                                        "CURRENT_ABSTRACTED_DIR", "CURRENT_ABSTRACTED_SPECIAL_DIR", "LOG_FILE")}
        self.tmp = tempfile.TemporaryDirectory()
        Config.LOGS_BASE_DIR = os.path.join(self.tmp.name, "logs")
        Config.set_file_type("png")
        Config.initialize_logging("png")

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(Config, k, v)
        self.tmp.cleanup()

    def test_state_survives_save_and_load(self):
        st = _populated_state()
        cm = CheckpointManager(st)
        cm.set_run_info("input", None)
        cm.mark_file_processed("input/a.png", save_immediately=True)
        self.assertTrue(cm.has_saved)
        cm.mark_complete()
        self.assertTrue(os.path.exists(cm.checkpoint_path))

        st2 = GlobalState()
        cm2 = CheckpointManager(st2, cm.checkpoint_path)
        self.assertTrue(cm2.load_checkpoint())
        self.assertTrue(cm2.completed)
        self.assertEqual(cm2.processed_files, {"input/a.png"})
        self.assertEqual(leaf_map(st2.nested_values_hex), leaf_map(st.nested_values_hex))
        self.assertEqual(st2.blacklisted_by_size, {"file~chunk~data"})
        self.assertEqual(st2.seen_attribute_paths, st.seen_attribute_paths)
        self.assertEqual(st2.dropped_arrays, {"file~jpgfile~scanData": 1383})
        self.assertEqual(st2.valid_abstractions_count, 7)
        self.assertEqual(st2.checksum_algorithms["by_chunk_type"], {"IHDR": ["CRC-32"]})

    def test_completed_runs_are_not_offered_for_resume(self):
        cm = CheckpointManager(_populated_state())
        cm.set_run_info("input", None)
        cm.mark_complete()
        self.assertEqual(Config.find_latest_checkpoint("png"), (None, None))
        log_dir, path = Config.find_latest_checkpoint("png", include_completed=True)
        self.assertEqual(path, cm.checkpoint_path)

    def test_incomplete_runs_are_found(self):
        cm = CheckpointManager(_populated_state())
        cm.set_run_info("input", None)
        cm.save_checkpoint()
        _, path = Config.find_latest_checkpoint("png")
        self.assertEqual(path, cm.checkpoint_path)

    def test_time_based_save(self):
        Config.CHECKPOINT_SAVE_SECONDS = 0  # always due
        try:
            cm = CheckpointManager(_populated_state())
            cm.set_run_info("input", None)
            cm.mark_file_processed("input/a.png")
            self.assertTrue(cm.has_saved)
        finally:
            Config.CHECKPOINT_SAVE_SECONDS = 30


class LegacyCheckpointTests(unittest.TestCase):
    def test_version1_blacklist_names_are_matched_by_leaf_name(self):
        st = GlobalState()
        st.from_dict({
            "nested_values_hex": {"file": {"chunk": {"ihdr": {"width": ["00000020"]}, "crc": []}}},
            "blacklisted_by_size": ["data", "chunk"],
            "blacklisted_by_count": ["crc"],
        })
        self.assertEqual(st.legacy_blacklisted_names, {"data", "chunk", "crc"})
        self.assertTrue(st.is_blacklisted("file~chunk~crc"))
        self.assertFalse(st.is_blacklisted("file~chunk~ihdr~width"))
        # an empty leaf list restores as a set and accepts new values
        insert_nested_dict(st.nested_values_hex, ["file", "chunk", "crc"], "aa")
        self.assertEqual(st.nested_values_hex["file"]["chunk"]["crc"], {"aa"})
        filtered = filter_blacklisted_attributes(convert_sets_to_lists(st.nested_values_hex), set(), st.legacy_blacklisted_names)
        self.assertIn("width", filtered["file"]["chunk"]["ihdr"])
        self.assertNotIn("crc", filtered["file"]["chunk"])


if __name__ == "__main__":
    unittest.main()
