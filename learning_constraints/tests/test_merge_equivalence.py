"""
Regression test for the parallel-merge data loss.

Parse + extract (no mutation, so fully deterministic) each sample file into its own GlobalState,
merge the states in both orders, and compare with one shared GlobalState fed sequentially.
Requires the built fuzzers in build/; skipped otherwise.
"""
import unittest

from helpers import load_manifest, repo_path, fuzzer_available, configure, leaf_map

from learning_constraints.config import GlobalState
from learning_constraints.parsers import FileParser
from learning_constraints.parallel import merge_global_states


def _extract(path, state):
    parser = FileParser(state)
    original, filtered = parser.parse_file_structure(path)
    parser.extract_bytes_from_file(path, filtered, original)
    return len(filtered)


class MergeEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def _run_format(self, fmt):
        if not fuzzer_available(fmt):
            self.skipTest(f"build/{fmt}-fuzzer not available")
        configure(fmt)
        files = [repo_path(p) for p in self.manifest[fmt]["files"]]

        sequential = GlobalState()
        for f in files:
            self.assertGreater(_extract(f, sequential), 0, f"no ranges for {f}")

        worker_dicts = []
        for f in files:
            state = GlobalState()
            _extract(f, state)
            worker_dicts.append(state.to_dict())

        forward = GlobalState()
        for d in worker_dicts:
            merge_global_states(forward, d)
        reverse = GlobalState()
        for d in reversed(worker_dicts):
            merge_global_states(reverse, d)

        seq_leaves = leaf_map(sequential.nested_values_hex)
        self.assertGreater(len(seq_leaves), 0)
        for name, merged in (("forward", forward), ("reverse", reverse)):
            with self.subTest(order=name):
                self.assertEqual(leaf_map(merged.nested_values_hex), seq_leaves)
                self.assertEqual(merged.blacklisted_by_size, sequential.blacklisted_by_size)
                self.assertEqual(merged.blacklisted_by_count, sequential.blacklisted_by_count)
                self.assertEqual(merged.seen_attribute_paths, sequential.seen_attribute_paths)
                self.assertEqual(merged.dropped_arrays, sequential.dropped_arrays)
                self.assertEqual(merged.checksum_algorithms["by_chunk_type"].keys(),
                                 sequential.checksum_algorithms["by_chunk_type"].keys())

        # Merging more files must never lose paths that a single file produced.
        for d in worker_dicts:
            single = GlobalState()
            single.from_dict(d)
            for path in leaf_map(single.nested_values_hex):
                if not forward.is_blacklisted(path):
                    self.assertIn(path, seq_leaves)

    def test_png(self):
        self._run_format("png")

    def test_jpg(self):
        self._run_format("jpg")

    def test_avi(self):
        self._run_format("avi")

    def test_mp4(self):
        self._run_format("mp4")

    def test_zip(self):
        self._run_format("zip")

    def test_bmp(self):
        self._run_format("bmp")


if __name__ == "__main__":
    unittest.main()
