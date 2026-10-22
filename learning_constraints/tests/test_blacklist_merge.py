"""Leaf-only, path-keyed blacklist semantics in merge, remove and filter."""
import unittest

from helpers import leaf_map

from learning_constraints.config import Config, GlobalState
from learning_constraints.parallel import merge_global_states, _merge_nested_values
from learning_constraints.utils import (
    insert_nested_dict, remove_attribute_from_nested_dict, remove_path_from_nested_dict,
    filter_blacklisted_attributes, convert_sets_to_lists, get_leaf,
)


class MergeSemanticsTests(unittest.TestCase):
    def test_blacklisted_leaf_name_does_not_hide_a_struct_of_the_same_name(self):
        main = GlobalState()
        main.blacklisted_by_size.add("file~movi~data")          # AVI payload leaf
        worker = GlobalState()
        insert_nested_dict(worker.nested_values_hex, "file~list~avhi~data~dwWidth".split("~"), "0140")
        insert_nested_dict(worker.nested_values_hex, "file~movi~data".split("~"), "aa")
        merge_global_states(main, worker.to_dict())
        leaves = leaf_map(main.nested_values_hex)
        self.assertEqual(leaves.get("file~list~avhi~data~dwWidth"), {"0140"})
        self.assertNotIn("file~movi~data", leaves)

    def test_container_blacklisted_by_first_worker_does_not_drop_later_workers(self):
        """The original bug: 'chunk' blacklisted by size hid every later file's chunk fields."""
        first = GlobalState()
        insert_nested_dict(first.nested_values_hex, "file~chunk~ihdr~width".split("~"), "00000020")
        first.blacklisted_by_size.add("file~chunk~data")
        second = GlobalState()
        insert_nested_dict(second.nested_values_hex, "file~chunk~ihdr~width".split("~"), "00000010")
        insert_nested_dict(second.nested_values_hex, "file~chunk~sbit~sbitRed".split("~"), "01")

        main = GlobalState()
        merge_global_states(main, first.to_dict())
        merge_global_states(main, second.to_dict())
        leaves = leaf_map(main.nested_values_hex)
        self.assertEqual(leaves["file~chunk~ihdr~width"], {"00000020", "00000010"})
        self.assertEqual(leaves["file~chunk~sbit~sbitRed"], {"01"})

    def test_values_exceeding_limit_across_workers_are_blacklisted_and_removed(self):
        main = GlobalState()
        for i in range(Config.MAX_UNIQUE_VALUES_PER_ATTRIBUTE + 10):
            w = GlobalState()
            insert_nested_dict(w.nested_values_hex, "file~chunk~time~timeYear".split("~"), f"{i:04x}")
            merge_global_states(main, w.to_dict())
        self.assertIn("file~chunk~time~timeYear", main.blacklisted_by_count)
        self.assertIsNone(get_leaf(main.nested_values_hex, "file~chunk~time~timeYear"))

    def test_merge_unions_bookkeeping(self):
        main = GlobalState()
        w = GlobalState()
        w.register_attributes(["file~a~b"])
        w.record_dropped_array("file~x~y", 40)
        w.blacklisted_by_count.add("file~c~d")
        insert_nested_dict(w.nested_values_hex, ["file", "c", "d"], "aa")   # value for a path the worker blacklisted
        merge_global_states(main, w.to_dict())
        self.assertEqual(main.seen_attribute_paths, {"file~a~b"})
        self.assertEqual(main.dropped_arrays, {"file~x~y": 40})
        self.assertIn("file~c~d", main.blacklisted_by_count)
        self.assertIsNone(get_leaf(main.nested_values_hex, "file~c~d"))

    def test_merge_nested_values_prunes_empty_subtrees(self):
        main = {}
        _merge_nested_values(main, {"file": {"chunk": {"data": ["aa"]}}}, is_blacklisted=lambda p: p == "file~chunk~data")
        self.assertEqual(main, {})


class RemoveAndFilterTests(unittest.TestCase):
    def _nested(self):
        st = GlobalState()
        insert_nested_dict(st.nested_values_hex, "file~list~avhi~data~dwWidth".split("~"), "0140")
        insert_nested_dict(st.nested_values_hex, "file~list~avhi~data~dwHeight".split("~"), "00f0")
        insert_nested_dict(st.nested_values_hex, "file~movi~data".split("~"), "aa")
        return st.nested_values_hex

    def test_remove_by_label_only_removes_that_leaf(self):
        nested = self._nested()
        self.assertTrue(remove_attribute_from_nested_dict(nested, "file~movi_3~data"))
        leaves = leaf_map(nested)
        self.assertIn("file~list~avhi~data~dwWidth", leaves)
        self.assertNotIn("file~movi~data", leaves)
        self.assertNotIn("movi", nested["file"], "empty parents are pruned")

    def test_remove_path_refuses_intermediate_nodes(self):
        nested = self._nested()
        self.assertFalse(remove_path_from_nested_dict(nested, "file~list~avhi~data"))
        self.assertIn("file~list~avhi~data~dwWidth", leaf_map(nested))

    def test_filter_is_path_based(self):
        data = convert_sets_to_lists(self._nested())
        out = filter_blacklisted_attributes(data, {"file~movi~data"})
        self.assertIn("dwWidth", out["file"]["list"]["avhi"]["data"])
        self.assertNotIn("movi", out["file"])


if __name__ == "__main__":
    unittest.main()
