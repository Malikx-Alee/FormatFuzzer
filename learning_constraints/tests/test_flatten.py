import json
import os
import tempfile
import unittest

from helpers import REPO_ROOT  # noqa: F401

from learning_constraints.config import Config
from learning_constraints.transformers import ResultTransformer


class FlattenTests(unittest.TestCase):
    def setUp(self):
        self.t = ResultTransformer()

    def test_leaf_mode_pools_by_cleaned_last_key(self):
        data = {"file": {"a": {"entry_size": ["01"], "entry_size_1": ["02"]}, "b": {"id": ["aa"]}, "b_1": {"id": ["bb"]}}}
        flat = self.t.flatten_json(data)
        self.assertEqual(sorted(flat["entry_size"]), ["01", "02"])
        self.assertEqual(sorted(flat["id"]), ["aa", "bb"])
        self.assertFalse(any(k.endswith("_1") for k in flat))

    def test_path_mode_keeps_parents_apart(self):
        data = {"file": {"a": {"id": ["aa"]}, "b_2": {"id": ["bb"]}}}
        flat = self.t.flatten_json(data, key_mode="path")
        self.assertEqual(flat["file~a~id"], "aa")
        self.assertEqual(flat["file~b~id"], "bb")

    def test_single_value_is_scalar_and_cap_message_matches_limit(self):
        limit = Config.FLATTEN_MAX_VALUES
        data = {"k": [f"{i:02x}" for i in range(limit)], "m": [f"{i:02x}" for i in range(limit + 1)], "s": ["01"]}
        flat = self.t.flatten_json(data)
        self.assertEqual(len(flat["k"]), limit)
        self.assertEqual(flat["m"], f"More than {limit} values")
        self.assertEqual(flat["s"], "01")

    def test_transform_json_file_adds_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "in.json")
            out = os.path.join(tmp, "out.json")
            with open(src, "w") as f:
                json.dump({"file": {"chunk": {"crc": ["aa"]}},
                           "checksum_algorithms": {"by_chunk_type": {"IHDR": ["CRC-32"]},
                                                   "compression_methods": {"0": "DEFLATE"}}}, f)
            self.assertTrue(self.t.transform_json_file(src, out))
            flat = json.load(open(out))
            self.assertEqual(flat["crc"], "aa")
            self.assertEqual(flat["IHDR"], "CRC-32")
            self.assertEqual(flat["compressionMethods"], ["DEFLATE"])
            self.assertEqual(flat["compressionMethodsValues"], [0])


if __name__ == "__main__":
    unittest.main()
