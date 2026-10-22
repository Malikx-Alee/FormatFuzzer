# Learning Constraints: Fix Plan

Plan for working off the 18 items in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). Written 2026-10-21 against
branch `thesis`; the module has not changed since the issues were recorded on 2026-10-09.

## Status (2026-10-21)

Phases 0 to 3 are implemented; see the per-item status lines in KNOWN_ISSUES.md. Decisions taken:
D1 = B (state keyed by cleaned full path, leaf-name pooling only in the flattened output, plus a
path-keyed flattened file), D2 = B (`MAX_ARRAY_ELEMENTS_LEARNED = 16`), D3 = switch
(`VALIDATOR_STRICT`, default lenient so results stay comparable; `--strict` on the runner),
D4 = B (run-wide seen set, `MAX_SPECIAL_FILES_PER_FILE = 5`, `MAX_SPECIAL_FILES = 50`).
Phase 4 (re-baselining the thesis results and choosing strict vs lenient) is left to the author.
Test-suite: `python3 -m unittest discover -s learning_constraints/tests`.

Ordering principle: first make the *results* trustworthy (that is what feeds the thesis numbers), then
make runs robust, then clean up. Build the regression harness before touching any logic, so every fix
is checked the same way the bug was found. Issue numbers below refer to KNOWN_ISSUES.md.

Rough effort: 4 to 5 working days of code plus a few hours of machine time for re-baselining.

---

## Decisions to take before Phase 1

These change the shape of the fixes, so settle them first. Recommendations are marked.

**D1. Blacklist and value granularity (issues 6, 11).**
- A: keep leaf-name pooling everywhere (status quo) and document it as a design decision.
- B (recommended): track values, unique-value counts and both blacklists by *cleaned full path*
  internally (`file~chunk~ihdr~width`), and pool by leaf name only when writing the flattened file.
  Also write a path-keyed flattened variant so `size`/`type`/`value` in MP4 stay usable.
  Cost: touches every `clean_attribute_key` call site; checkpoint schema changes (bump a version
  field, keep `from_dict` reading old files).

**D2. Array elements (issue 9).**
- A: minimal consistency: also drop element 0 whenever a sibling `name_1` exists.
- B (recommended): decide per array. From the parse output, a base name with `_N` siblings under the
  same parent is an array. Keep arrays with at most `MAX_ARRAY_ELEMENTS_LEARNED` (default 16)
  elements, pooled under the base name; drop larger arrays entirely. Palettes stay, scan data goes.

**D3. Oracle strictness (issues 6, 15).**
Validity is whatever `identify -verbose` / `ffmpeg -f null` accept, and both pass files with only
warnings. Options: keep lenient; or add a strict mode (`ffmpeg -xerror -err_detect explode`, and
for images compare against a second decoder). Recommended: make strictness a `Config` switch, run
the whole known-good corpus through both and require zero false negatives before adopting strict
for learning runs. Record the choice in the thesis; it directly determines what "constraint" means.
Note the conflicting evidence in `docs_llm/identify_verbose_false_negatives.md` (`-verbose` was too
strict for some PNGs) before choosing.

**D4. "New attribute" semantics (issue 7).**
- A: per source file (status quo).
- B (recommended): a global set of attribute paths seen so far in the run (merged across workers);
  a mutant is "special" only when it introduces a path never seen before, plus a per-run cap
  (`MAX_SPECIAL_FILES`, default 50). One special file per fallback path instead of hundreds.

---

## Phase 0: Regression harness (about half a day)

Do this before any logic change. The current tests are stale (issue 16); replace them.

1. **Fixtures.** Record `build/<fmt>-fuzzer parse` stdout for one sample per format
   (png, jpg, avi, mp4, zip, bmp) into `learning_constraints/tests/fixtures/<fmt>.parse.txt`. The
   sample files already live in `testcases/<fmt>/` and are small; reference them by path. The ZIP
   fixture must keep its inverted `efData` lines, the JPG one its `Printf` noise, the MP4 one its
   `size_1..3` re-reads, the AVI one its `index_entry_N` names.
2. **Make the parser testable without a subprocess.** Split `FileParser.parse_file_structure` into
   `parse_lines(lines, file_size) -> (original, filtered)` and a thin wrapper that runs the fuzzer.
3. **Tests (pytest):**
   - `test_keys.py`: index stripping on `chunk_5`, `index_entry_7`, `list_datalen_1`, `comp_sof_2`,
     `dw_flags`, `root_datalen`, `btRed`.
   - `test_parse_filter.py`: per fixture, assert no struct-level line and no inverted range reaches
     `byte_ranges`, identical-range duplicates collapse to the leaf, blacklist content is as expected.
   - `test_merge_equivalence.py`: for each format, parse + extract (no mutation, so deterministic)
     each of 3 sample files into its own `GlobalState`, merge in both orders, and compare with one
     shared `GlobalState` fed sequentially. Leaf paths and value sets must be identical. This is the
     regression test for issue 1 and must fail on today's code.
   - `test_validators.py`: monkeypatch `subprocess.run` to return non-UTF-8 stderr with exit 0;
     `is_valid_file` must return True (issue 4).
   - `test_flatten.py`, `test_checkpoint_roundtrip.py`, and keep `test_blacklist_debug.py` as a test.
4. Delete `test_parse.py` (empty input) and turn `test_parse_result.py` into fixture data or remove it.

Exit criterion: `python -m pytest learning_constraints/tests` runs; the merge-equivalence test is red.

---

## Phase 1: Result correctness (1.5 to 2 days)

In dependency order. Each step ends with the Phase 0 suite plus the sandbox runs described under
"Verification" in KNOWN_ISSUES.md.

**1.1 Index stripping (issue 5).** One helper `strip_index(name)` in `utils.py` using
`re.sub(r"_\d+$", "", name)`. Use it in `clean_single_key`, `clean_keys_list`, the parser skip rule
(`parsers.py` ~L90, ~L105), `flatten_json` (`transformers.py`, flatten by the *cleaned* last key),
and `check_for_new_attributes`. Re-read duplicates such as `list_datalen_1` and `size_1..3`
collapse onto their base name, which is correct.
Verify: MP4 flattened output has zero keys ending in `_N`; AVI size blacklist drops from 285
names to about 20; `test_keys.py` green.

**1.2 Struct/leaf classification and range validation (issues 1 in part, 8, 10).** In
`parse_lines`, build the set of parent paths (any path `p` such that some other line starts with
`p + "~"`). Only leaf lines become mutation targets and only leaf lines can be size-blacklisted.
Validate every line with `validate_byte_range(start, end, file_size)` (currently unused) and log
and skip failures. Keep `original_byte_ranges` as the full leaf list for the checksum detector
(it finds `type`/`length`/`frData` by prefix on leaves, so it keeps working).
Verify: PNG filtered list no longer contains `file~chunk_2~sbit`; ZIP has no inverted ranges and
no `''` value for `efData`; PNG/ZIP/BMP checksum and compression detection output unchanged.

**1.3 Leaf-only blacklist application (issues 1, 2).** In `parallel._merge_nested_values`, skip a
key only when its value is a `list`/`set` (a leaf). In `utils.remove_attribute_from_nested_dict`,
delete only leaf entries. Both then match `filter_blacklisted_attributes`. Keep this guard even
after 1.2, because a leaf name can equal an intermediate name elsewhere (AVI `data`).
Verify: `test_merge_equivalence.py` green for all formats; a 3-file parallel run has every leaf
path that each file's own sequential run has.

**1.4 Path-keyed internal state (only if D1 = B).** Blacklist sets hold cleaned full paths; the
by-count check already navigates per path, so only the recorded key changes; `result_saver`
filters by path; `flatten_json` pools at output; add the path-keyed flattened file. Bump the
checkpoint `version` and keep reading the old format.

**1.5 Validator and subprocess decoding (issue 4).** Add `errors="replace"` to all seven
`subprocess.run(..., text=True)` calls (`validators.py` x4, `parsers.py` x2, `mutators.py` x1).
Verify: the `compressorname` probe returns True; an MP4 sequential run logs zero decode errors.

**1.6 Array elements (per D2, issue 9).** Implement the chosen rule in `parse_lines`, replacing the
`start == end and _N` heuristic. Verify on PNG PLTE (kept under D2-B), BMP palette, JPG `scanData`
(dropped including element 0).

**1.7 Special-file semantics (per D4, issue 7).** Add `seen_attribute_paths` to `GlobalState`
(serialised, merged in `merge_global_states`); `check_for_new_attributes` consults it; cap the
number of special files; include a short hash of the source file in the special filename
(issue 17 collision). Verify: AVI 3-file run produces a handful of special files, one per fallback
attribute, and the second pass finishes in seconds.

**1.8 Special pass vs `max_files` (issue 11).** Apply `max_files` to the source directory only;
process the special directory fully (or with its own cap). Verify: `run_learning_constraints.py png 3`
on a 3-file directory processes its special files.

Exit criteria: merge-equivalence test green; for png, jpg, avi, mp4 the parallel and sequential
full runs show the same leaf paths and value counts that differ only by mutation randomness; AVI
output contains `id` and `type` (also depends on D3); no `_N` keys anywhere.

---

## Phase 2: Operational robustness (about 1 day)

**2.1 Timeouts (issue 3).** `Config.FUZZER_TIMEOUT` and `Config.VALIDATOR_TIMEOUT` (30 s each);
pass `timeout=` to every `subprocess.run`; catch `TimeoutExpired` and treat it as parse failure or
invalid file with a log line. In `parallel.py`, remove the dead `result(timeout=...)` and use
`concurrent.futures.wait(futures, timeout=...)` per batch, marking stragglers as failed. A
`ProcessPoolExecutor` cannot kill a running task; the subprocess timeouts are what bound a hang.
If a true per-file kill is needed later, switch to `multiprocessing.Pool.apply_async(...).get(timeout)`.

**2.2 Resource limits (issue 15).** Run `identify` with
`-limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10`, mirroring
`scripts/fuzz_manager.py`; run `ffmpeg` with `-nostdin -v error` under the timeout from 2.1.
Whether to keep `-verbose` is part of D3.

**2.3 Checkpoint cadence and interrupts (issue 12).** Save after every file (the JSON is small),
or at least whenever fewer than `CHECKPOINT_SAVE_INTERVAL` files remain; in parallel mode save after
each completed future rather than per 100-file batch; install SIGINT/SIGTERM handlers that save
before exiting; make the runner's Ctrl-C message conditional on an actual save.

**2.4 Resume logic (issue 13).** Write `"completed": true` from `mark_complete`;
`find_latest_checkpoint` ignores completed runs; when stdin is not a TTY, never prompt (default to
a new run; `--resume` stays explicit; add `--new` to skip the prompt interactively).

**2.5 Exit codes and reporting (issue 14).** Non-zero exit when zero files succeeded (and
optionally when any failed, behind a flag); print failed and timed-out counts in the summary;
fix the README Quick Start to use an `if __name__ == "__main__":` guard and say why.

**2.6 Logging parity.** Use `FileResultLogger` in sequential mode too, and add ERROR counts to the
final statistics so validator failures are visible without reading the log.

---

## Phase 3: Cleanup (about half a day, issue 17)

- `ast.literal_eval` instead of `eval` in template mining.
- Write ffcompile output to a temporary directory, not the cwd.
- Delete the smart-abstraction temp file in a `finally`, as the overwrite path already does.
- `sorted(os.listdir(...))` before slicing with `max_files`.
- Size semantics: use `ByteRange.size <= MAX_ATTRIBUTE_SIZE_BYTES` and say "8 bytes inclusive" in the README.
- Flatten cap: one constant, and a message that matches it.
- `GlobalState.from_dict`: restore empty leaf lists as sets.
- Config and docs: `DATA_DIR` default, MP3 in `SUPPORTED_FILE_TYPES` or out of the README,
  retire or mark `README_COMPREHENSIVE.md`.
- Keep the `,Optional` flag as metadata on `ByteRange` for later use (no behaviour change).

---

## Phase 4: Re-baseline (half a day plus machine time)

1. Re-run all formats with the fixed code in parallel mode using the sandbox recipe.
2. Compare against `testcases_4_learn/results_old/` and the results currently cited in the
   benchmarking report; write down what changed and why (issues 1, 5, 6 explain most of it).
3. Record the D3 oracle choice and the D1 granularity choice in the thesis method section.
4. For each fixed item, add the commit hash next to it in KNOWN_ISSUES.md.

---

## Fuzzer-side follow-ups (separate, optional)

- `bt.h`: the ZIP `efData` lines carry a garbage start offset for extra-field data. Look at how
  `stack_cell.min/max` are initialised for arrays reached through `FSeek`. Until then 1.2 filters them.
- Emitting a struct/leaf marker as an extra CSV field in the parse output would remove the need
  to infer structs on the Python side.

## Quick wins (about one hour, if a full pass has to wait)

These six changes remove the worst data corruption on their own: `errors="replace"` on the
subprocess calls (1.5), the leaf-only guard in `_merge_nested_values` and
`remove_attribute_from_nested_dict` (1.3), `strip_index` with the regex (1.1), skipping inverted
ranges (1.2 in part), subprocess timeouts (2.1), and `identify -limit` flags (2.2). Run the
merge-equivalence check afterwards; it should turn green from the leaf-only guard alone.
