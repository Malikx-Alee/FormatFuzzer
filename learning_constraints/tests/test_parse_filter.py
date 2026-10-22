"""Parse-output filtering, checked against recorded fuzzer output (no binaries needed)."""
import unittest

from helpers import load_manifest, fixture_lines, leaf_map  # noqa: F401

from learning_constraints.config import Config, GlobalState
from learning_constraints.parsers import FileParser
from learning_constraints.utils import clean_attribute_path


def _parents(entries):
    parents = set()
    for _, _, label, _ in entries:
        parts = label.split("~")
        for i in range(1, len(parts)):
            parents.add("~".join(parts[:i]))
    return parents


class ParseFilterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()
        cls.results = {}
        for fmt, info in cls.manifest.items():
            Config.set_file_type(fmt)
            state = GlobalState()
            parser = FileParser(state)
            lines = fixture_lines(fmt)
            entries = parser.parse_csv_lines(lines)
            original, filtered = parser.parse_lines(lines, info["primary_size"])
            cls.results[fmt] = (state, entries, original, filtered, info["primary_size"])

    def test_every_format_yields_ranges(self):
        for fmt, (state, entries, original, filtered, size) in self.results.items():
            with self.subTest(fmt=fmt):
                self.assertGreater(len(entries), 0)
                self.assertGreater(len(filtered), 0)
                self.assertGreaterEqual(len(original), len(filtered))

    def test_no_struct_lines_become_ranges(self):
        for fmt, (state, entries, original, filtered, size) in self.results.items():
            with self.subTest(fmt=fmt):
                parents = _parents(entries)
                for br in original:
                    self.assertNotIn(br.attribute, parents, f"{fmt}: struct {br.attribute} leaked into ranges")

    def test_all_ranges_are_valid_and_unique(self):
        for fmt, (state, entries, original, filtered, size) in self.results.items():
            with self.subTest(fmt=fmt):
                seen = set()
                for br in original:
                    self.assertTrue(0 <= br.start <= br.end < size, f"{fmt}: bad range {br}")
                    self.assertNotIn((br.start, br.end), seen, f"{fmt}: duplicate range {br}")
                    seen.add((br.start, br.end))

    def test_filtered_ranges_respect_size_and_blacklist(self):
        for fmt, (state, entries, original, filtered, size) in self.results.items():
            with self.subTest(fmt=fmt):
                for br in filtered:
                    self.assertLessEqual(br.size, Config.MAX_ATTRIBUTE_SIZE_BYTES)
                    self.assertFalse(state.is_blacklisted(br.cleaned_path))

    def test_size_blacklist_holds_full_paths_of_large_leaves_only(self):
        for fmt, (state, entries, original, filtered, size) in self.results.items():
            with self.subTest(fmt=fmt):
                large = {br.cleaned_path for br in original if br.size > Config.MAX_ATTRIBUTE_SIZE_BYTES}
                self.assertEqual(state.blacklisted_by_size, large)
                for path in state.blacklisted_by_size:
                    self.assertIn("~", path, "blacklist entries must be full paths, not leaf names")

    def test_blacklist_never_names_a_container(self):
        """The bug behind the parallel-merge data loss: struct names in the blacklist."""
        for fmt, (state, entries, original, filtered, size) in self.results.items():
            with self.subTest(fmt=fmt):
                parents = {clean_attribute_path(p) for p in _parents(entries)}
                self.assertFalse(state.blacklisted_by_size & parents,
                                 f"{fmt}: container paths blacklisted: {state.blacklisted_by_size & parents}")

    # -- format specific expectations --------------------------------------

    def test_png_specifics(self):
        state, entries, original, filtered, size = self.results["png"]
        paths = [br.cleaned_path for br in filtered]
        self.assertIn("file~chunk~ihdr~width", paths)
        self.assertIn("file~chunk~crc", paths)
        self.assertIn("file~chunk~data", state.blacklisted_by_size)      # IDAT payload
        self.assertNotIn("file~chunk", state.blacklisted_by_size)
        self.assertNotIn("file~chunk~ihdr", state.blacklisted_by_size)
        # the 3-byte sBIT struct is no longer a mutation target, its children are
        self.assertNotIn("file~chunk_2~sbit", [br.attribute for br in filtered])
        self.assertIn("file~chunk~sbit~sbitRed", paths)
        # PLTE: all four palette entries are kept (small array), pooled under the base name
        self.assertEqual(sum(1 for p in paths if p == "file~chunk~plte~plteChunkData~btRed"), 4)

    def test_zip_inverted_ranges_are_dropped(self):
        state, entries, original, filtered, size = self.results["zip"]
        inverted = [e for e in entries if e[0] > e[1]]
        self.assertTrue(inverted, "fixture should contain the fuzzer's inverted efData ranges")
        for br in original:
            self.assertLessEqual(br.start, br.end)
        self.assertNotIn("file~record~frExtraField~efData", [br.cleaned_path for br in filtered])

    def test_jpg_large_byte_arrays_are_dropped_including_element_zero(self):
        state, entries, original, filtered, size = self.results["jpg"]
        self.assertIn("file~jpgfile~scanData", state.dropped_arrays)
        self.assertGreater(state.dropped_arrays["file~jpgfile~scanData"], Config.MAX_ARRAY_ELEMENTS_LEARNED)
        self.assertNotIn("scanData", [br.cleaned_key for br in original])
        self.assertNotIn("random", [br.cleaned_key for br in original])
        self.assertIn("file~jpgfile~sof0~X_image", [br.cleaned_path for br in filtered])
        # the three component descriptors pool under one path now
        self.assertEqual(sum(1 for br in filtered if br.cleaned_path == "file~jpgfile~sof0~comp_sof~compId"), 3)

    def test_mp4_rereads_collapse_and_tables_are_dropped(self):
        state, entries, original, filtered, size = self.results["mp4"]
        ftyp_sizes = [br for br in original if br.attribute.startswith("file~file~ftyp_block~size")]
        self.assertEqual(len(ftyp_sizes), 1, "size, size_1, size_2, size_3 share one range")
        # the 23-byte 'reserved' byte array is dropped; the small chunk-offset table (3 entries) is kept and pooled
        self.assertIn("file~file~moov_block~trak_block~mdia_block~minf_block~stbl_block~stsd_block~mixed_box~reserved",
                      state.dropped_arrays)
        offsets = [br for br in filtered if br.cleaned_path.endswith("~stco_block~chunk_offset")]
        self.assertGreaterEqual(len(offsets), 2)
        self.assertFalse(any("chunk_offset_" in br.cleaned_path for br in filtered))
        self.assertEqual(sum(1 for br in filtered if br.cleaned_path == "file~file~ftyp_block~compatiple_brand"), 2)
        self.assertNotIn("file~file", state.blacklisted_by_size)

    def test_avi_index_entries_pool_under_one_path(self):
        state, entries, original, filtered, size = self.results["avi"]
        paths = {br.cleaned_path for br in filtered}
        self.assertIn("file~idx1~index_entry~ckid", paths)
        self.assertFalse(any(p.startswith("file~idx1~index_entry_") for p in paths))
        self.assertIn("file~list~avhi~data~dwWidth", paths)
        self.assertNotIn("file~root", state.blacklisted_by_size)

    def test_bmp_palette_is_dropped_as_large_array(self):
        state, entries, original, filtered, size = self.results["bmp"]
        self.assertIn("file~lines~colors~rgbBlue", state.dropped_arrays)
        self.assertIn("file~bmih~biCompression", [br.cleaned_path for br in filtered])


if __name__ == "__main__":
    unittest.main()
