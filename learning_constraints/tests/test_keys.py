import unittest

from helpers import REPO_ROOT  # noqa: F401  (sets sys.path)

from learning_constraints.utils import (
    strip_index, split_index, clean_single_key, clean_attribute_key, clean_attribute_path,
    validate_byte_range, extract_byte_values,
)


class StripIndexTests(unittest.TestCase):
    def test_single_underscore_names(self):
        self.assertEqual(strip_index("chunk_5"), "chunk")
        self.assertEqual(strip_index("junk_1"), "junk")
        self.assertEqual(strip_index("size_12"), "size")

    def test_multi_underscore_names(self):
        self.assertEqual(strip_index("index_entry_7"), "index_entry")
        self.assertEqual(strip_index("entry_size_12"), "entry_size")
        self.assertEqual(strip_index("list_datalen_1"), "list_datalen")
        self.assertEqual(strip_index("comp_sof_2"), "comp_sof")
        self.assertEqual(strip_index("compatiple_brand_3"), "compatiple_brand")

    def test_names_without_index_are_untouched(self):
        for name in ("dw_flags", "root_datalen", "btRed", "crc", "X_image", "sha256"):
            self.assertEqual(strip_index(name), name)

    def test_split_index(self):
        self.assertEqual(split_index("btRed_3"), ("btRed", 3))
        self.assertEqual(split_index("btRed"), ("btRed", None))
        self.assertEqual(split_index("a_1_2"), ("a_1", 2))

    def test_aliases(self):
        self.assertEqual(clean_single_key("index_entry_7"), "index_entry")
        self.assertEqual(clean_attribute_key("file~idx1~index_entry_7~dwFlags"), "dwFlags")
        self.assertEqual(clean_attribute_key("file~chunk_3~plte~plteChunkData~btRed_2"), "btRed")

    def test_clean_attribute_path(self):
        self.assertEqual(clean_attribute_path("file~chunk_3~plte~plteChunkData~btRed_2"),
                         "file~chunk~plte~plteChunkData~btRed")
        self.assertEqual(clean_attribute_path("file~idx1~index_entry_266~dwFlags"), "file~idx1~index_entry~dwFlags")


class RangeHelperTests(unittest.TestCase):
    def test_validate_byte_range(self):
        self.assertTrue(validate_byte_range(0, 3, 100))
        self.assertTrue(validate_byte_range(99, 99, 100))
        self.assertFalse(validate_byte_range(2158942, 50, 289))   # inverted (ZIP efData)
        self.assertFalse(validate_byte_range(-1, 3, 100))
        self.assertFalse(validate_byte_range(0, 100, 100))        # end past EOF
        self.assertTrue(validate_byte_range(0, 7, 100, max_size=8))
        self.assertFalse(validate_byte_range(0, 8, 100, max_size=8))  # 9 bytes

    def test_extract_byte_values_rejects_bad_ranges(self):
        data = bytes(range(16))
        self.assertEqual(extract_byte_values(data, 0, 1)["hex"], "0001")
        with self.assertRaises(ValueError):
            extract_byte_values(data, 5, 2)
        with self.assertRaises(ValueError):
            extract_byte_values(data, 0, 16)


if __name__ == "__main__":
    unittest.main()
