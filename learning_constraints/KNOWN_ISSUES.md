# Learning Constraints: Known Issues

Running list of defects and questionable behaviours found while tracing the module end to end.
Line numbers in the item descriptions are as of 2026-10-09 on branch `thesis`, i.e. *before* the
fixes. Items are ordered by impact. How each item was verified is noted so a fix can be checked
the same way.

**Update 2026-10-21:** items 1 to 17 are fixed; see "Status after the fixes" at the end of this
file for what changed, where, and how it is covered by the test-suite
(`python3 -m unittest discover -s learning_constraints/tests`). The descriptions below are kept
as the record of the original behaviour.

**Formats exercised:** PNG, JPG, AVI, MP4 (full runs, sequential and parallel, 3 input files each,
`testcases/<fmt>/`), ZIP and BMP (parse + extract + checksum detection only).

## Sequential vs parallel on the same 3 files

| Format | Sequential values (leaf paths) | Parallel values (leaf paths) | Wall time seq / par |
|---|---|---|---|
| PNG | 76 (17) | 27 (11) | 10 s / 5 s |
| JPG | 159 (43) | 87 (43) | 24 s / 10 s |
| AVI | 206 (31), 37 names blacklisted by count | 472 (260), 4 by count | 12 m 45 s / 4 m 10 s |
| MP4 | 1842 (329), 187 validator UTF-8 errors | 503 (273) | 18 m 9 s / 5 m 24 s |

Parallel results equal the first worker to finish (its file plus its own mutants) plus any
top-level struct name that was not yet blacklisted (issue 1). AVI sequential is *smaller* than
parallel for a different reason: the by-count blacklist removed 37 field names after lenient
`ffmpeg` validation polluted them (issue 6).

---

## 1. Parallel merge discards values from every worker after the first  (CRITICAL)

**Where:** `parallel.py` `_merge_nested_values` (~L184-L220), fed by the `parsers.py` size
blacklist (~L66-L75).

**What happens:** `<fmt>-fuzzer parse` emits one line per *struct level*, not just per leaf
(`8,32,file~chunk`, `0,11,file~root`, `0,1266,file~file`, `2,19,file~jpgfile~app0`). Any line
spanning more than 8 bytes puts its last path segment into `blacklisted_by_size`. For every format
tested that includes the top-level containers: PNG `chunk`, AVI `root list junk idx1`, MP4 `file`,
JPG `jpgfile`, BMP `bmfh bmih lines`, ZIP `record dirEntry endLocator`. `_merge_nested_values`
compares the cleaned name of **every path segment** against that blacklist, so once the first
worker's blacklist is merged, the whole container subtree of every later worker is skipped.

**Evidence:** table above; two-file replays (PNG 32->32 expected 37; AVI `idx1` 42->42,
`list` 53->53 after merging the second file). Order of completion decides which file "wins".

**Fix direction:** apply the blacklist only at leaf nodes (value is `list`/`set`), exactly as
`utils.filter_blacklisted_attributes` already does since commit 9ae53e5. Separately, do not
size-blacklist struct-level lines at all; they are never mutation targets.

**Note:** any learned-constraints result produced in parallel mode before this is fixed reflects
one input file, not the dataset.

## 2. `remove_attribute_from_nested_dict` deletes intermediate nodes by name  (HIGH, latent)

**Where:** `utils.py` ~L446-L480 (`if key == target_key` has no leaf check).

Blacklisting leaf `data` also deletes AVI's `file~list~avhi~data~*` subtree. In sequential mode
the damage is small because the blacklist is built on the first parse before values exist, but it
is the same root cause as issue 1 and bites as soon as a struct name is first seen late.

## 3. Per-file timeout can never fire; no subprocess timeouts  (HIGH)

**Where:** `parallel.py` ~L422; every `subprocess.run` in `parsers.py`, `mutators.py`, `validators.py`.

`future.result(timeout=...)` is called only after `as_completed` has yielded the future, which
means it is already finished, so `TimeoutError` is unreachable (verified). No `subprocess.run`
passes `timeout=`. A hung fuzzer, `identify` or `ffmpeg` blocks the batch forever.
`PARALLEL_FILE_TIMEOUT` is dead configuration.

**Fix direction:** `timeout=` on all `subprocess.run` calls, and `concurrent.futures.wait(..., timeout)`
per batch. A ProcessPoolExecutor cannot cancel a running task, so a true per-file watchdog needs
`multiprocessing.Pool.apply_async(...).get(timeout)` or subprocess-level timeouts.

## 4. Validators reject files the tool accepted when its output is not UTF-8  (HIGH)

**Where:** `validators.py` ~L85 (`ffmpeg`), ~L33 (`identify`), ~L127, ~L152; also `parsers.py` ~L50
and `mutators.py` ~L74. All use `text=True` without `errors=`.

`ffmpeg` echoes string fields from the file into its stderr (handler names, `compressorname`).
A mutant with non-UTF-8 bytes there makes `subprocess.run(text=True)` raise `UnicodeDecodeError`;
the `except` logs it and returns `False`, so an accepted file is recorded as invalid.

**Evidence:** MP4 sequential run: 187 such errors in 18 minutes (every ERROR line in that log);
each one is a mutant `ffmpeg` had accepted. Direct demo: overwrite
`compressorname` (bytes 883-914 of `small_movie.mp4`) with `0xD6`; `ffmpeg` returns 0 and
`FileValidator.is_valid_file` returns `False` with the decode error. The same applies to the fuzzer
parse output if a template `Printf`s file bytes.

**Fix direction:** `errors="replace"` (or capture bytes) on every `subprocess.run`.

## 5. Index stripping fails for names containing an underscore  (HIGH)

**Where:** `utils.clean_single_key` checks `parts[1].isdigit()`; the parser's skip rule checks `parts[-1]`.

`chunk_5 -> chunk` works, but `index_entry_7`, `entry_size_3`, `chunk_offset_12`,
`compatiple_brand_1`, `free_block_4`, `comp_sof_2`, and re-read fields such as `list_datalen_1`
keep their index and become separate keys everywhere. Consequences seen:

- AVI blacklist: 285 names, 266 of them `index_entry_N` (sequential run 48 names, 30 of them `index_entry_N`).
- MP4 flattened output carries 26 bogus keys in the parallel run (`chunk_offset_1 .. chunk_offset_23`,
  `compatiple_brand_1..3`) and over 45 in the sequential run (adds `entry_size_1..16`, `first_chunk_N`,
  `samples_per_chunk_N`, `sample_description_index_N`).
- Every MP4 "special" file is a false discovery: new attribute names were `entry_size_12`,
  `chunk_offset_1`, `chunk_offset_3`, `free_block_3`, i.e. just more array elements.
- By-count blacklisting is per path, so `index_entry_N~dwFlags` never exceeds 30 while the flattened
  `dwFlags` shows 19 pooled values; the two views disagree.

**Fix direction:** strip a trailing `_<digits>` with `rsplit("_", 1)` in one shared helper used by
the parser skip rule, `clean_single_key`, and `flatten_json`.

## 6. Lenient validators + global pooling + by-count blacklist erase the key enums  (HIGH, design)

`clean_attribute_key` keeps only the last `~` segment, so values pool across every context
(`id` under 9 AVI parents, `size`/`type`/`value` under 24-48 MP4 boxes, `marker`/`szSection`
under 5 JPG segments). The validator decides what counts as valid, and `ffmpeg`/`identify -verbose`
accept a lot of garbage with only a warning. Together with the 30-unique-values cap:

- AVI sequential: 37 names blacklisted by count, including `id`, `type`, `dwWidth`, `dwHeight`,
  `biSize`, `biPlanes`, `fccHandler`. The chunk identifier `id` is absent from the final output in
  both modes. `type` (LIST type) kept values like `1f577514`, `d031a5f8`.
- JPG: `dht~marker` collected 13 values (`39f2`, `7073`, ... alongside `ffc4`); `app0~units`
  accepted `0x29`, `0x9b`; `sof0~X_image` accepted `0x21ea`, `0x3dc1` (8682, 15809 px) for a
  32-px scan.
- MP4: `value` is the leaf under 75 paths (box `type`, matrix entries, `preferred_rate`,
  `volume`, ...) and flattens to `"More than 10 values"`, as do `size` and `type`. In the
  sequential run `version`, `flags`, `create_time`, `modify_time`, `time_scale`, `duration` and
  `dummy` are all capped the same way: `ffmpeg` accepted the random values, so no constraint is left.

This may be intended (the flattened output is also last-key), but it should be stated as a design
decision, or keyed by cleaned full path. See also `docs_llm/identify_verbose_false_negatives.md`.

## 7. "New attribute" detection fires on every mutated chunk id  (MEDIUM)

**Where:** `parsers.check_for_new_attributes` compares cleaned leaf names only; `mutators.save_special_file`.

Randomising a chunk `id`/`type` makes the template take its fallback path (`genblk`, `junk`,
`garbage`, `unknown_block`), whose field names are "new". AVI produced 188 special files
(sequential) / 115 (parallel): `list_datalen_1` 95, `idx1_hdr_datalen` 59, `junk_hdr_datalen` 50,
`garbage` 34, `genblk_datalen` 25. Examples: `genblk_datalen_20_23` came from mutating
`file~list~type`; `genblk_datalen_2036_2039` from `movi_list~id`; `junk_hdr_datalen_184_185`
from `biPlanes`. The second pass processes only the files present when it starts (29 / 40) and
itself produces more that are never processed. `garbage` then gets blacklisted by count. The
sequential AVI run spent most of its 12 m 45 s on this.

## 8. Inverted byte ranges from the fuzzer are accepted  (MEDIUM)

**Where:** `parsers.parse_file_structure`; `utils.validate_byte_range` / `ByteRange.is_within_size_limit` exist but are never called.

`zip-fuzzer parse` emits `2158942,50,file~record~frExtraField~efData` and three similar lines for
`small_archive.zip` (start > end, start beyond EOF). They pass every filter (`end - start > 8` is
false for a negative span), `extract_byte_values` stores `''` as a learned value for `efData`,
and each range costs 10 failing overwrite attempts with an ERROR log line plus 10 abstraction
attempts the fuzzer cannot target. The fuzzer-side position bug should be reported too.

## 9. One-byte array elements: index >= 1 dropped, element 0 kept  (MEDIUM, intent unclear)

**Where:** `parsers.py` steps 3 and 4, `start == end and "_" in attribute and parts[-1].isdigit()`.

Dropped per sample file: PNG PLTE `btRed_1..btBlue_3`, BMP palette 224 bytes, MP4 `reserved_N` 21,
JPG 1808 lines (`scanData` 1382, `random` 344, `lengthEntry` 60, `HTV` 22). For JPG this is
desirable (entropy-coded bytes), for palettes it is lossy. The fuzzer omits the suffix on element 0,
so the first byte of every such array leaks through and becomes a learned "constraint":
JPG `scanData` ended with 8 random byte values, `random` with 18; PNG `btRed`, BMP `rgbBlue`
likewise. Introduced in 34ad448 (2025-07-23). Decide whether to drop arrays by name/size instead.

## 10. The "overlap filter" only removes identical-range duplicates  (MEDIUM)

**Where:** `parsers.py` steps 3 and 4, condition `start > current_parent_end or end < current_parent_end`.

Because `current_parent_end` is reset to each accepted child's end, nested children always pass.
Only a parent emitted *after* a leaf with the same range is dropped (`type` after `type~cname`,
MP4 `size_1..3` re-reads). Small structs (<= 9 bytes) survive as mutation targets alongside
their children: PNG `sbit`, MP4 `tkhd~flags`, `header_block~opcolor`, `stts~entry`, JPG
`comp_sof`, ZIP `frVersion`. Their concatenated value is silently dropped when a child is
inserted afterwards (`insert_nested_dict` converts the leaf set into a dict), or persists as a
bogus leaf if no child survives. The comments describing parent/child filtering do not match.

## 11. Special-directory second pass is skipped whenever `max_files` <= source file count  (MEDIUM)

**Where:** `main.py` `run_complete_process`, `remaining_files = max_files - passed_total`.

`run_learning_constraints.py png 3` on a 3-file directory logs "Skipping abstracted special
directory - file limit reached" and never processes discovered special files.

## 12. Checkpoints are written every 10 files, so short runs cannot be resumed  (MEDIUM)

**Where:** `config.CHECKPOINT_SAVE_INTERVAL = 10`; `checkpoint.mark_file_processed`; parallel mode
saves once per 100-file batch.

Verified: 6 PNGs sequential, SIGTERM during file 4/6, no `checkpoint.json` on disk, `--resume`
says "No checkpoint found" and starts over. The runner's Ctrl-C handler prints "Progress has been
saved to checkpoint", which is false in that case. Nothing saves on interrupt.

## 13. Runner offers to resume *completed* runs and crashes when stdin is not a TTY  (MEDIUM)

**Where:** `scripts/run_learning_constraints.py` `check_for_resume` / `prompt_for_resume`;
`Config.find_latest_checkpoint` has no notion of a finished run.

Any later invocation for the same format finds the old checkpoint, prints "FOUND INCOMPLETE RUN"
and calls `input()`. With stdin closed (cron, CI, `< /dev/null`) this is an `EOFError` traceback.

## 14. A run where every file fails still reports success  (MEDIUM)

Verified: driver without a `__main__` guard on macOS (spawn start method) killed every worker
("A process in the process pool was terminated abruptly"), yet the orchestrator returned normally,
exit code 0, and the runner would print "PROCESSING COMPLETED SUCCESSFULLY!". `README.md` Quick
Start shows exactly that unguarded usage. Surface failed counts in the exit code and in the summary.

## 15. Validators run without resource limits  (MEDIUM)

`validate_image_file` runs `identify -verbose <file>` with no `-limit` flags, while
`scripts/fuzz_manager.py` uses `-limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10`
for the reasons in `docs_llm/identify_validator_resource_exhaustion.md`. During this session the
AVI run logged `[Errno 28] No space left on device` at 17:00:49 while an unlimited `identify` run
on fuzzed PNG mutants was in progress; free space was back to 40 GiB minutes later. Attribution is
by timing only, but it matches the documented failure. `ffmpeg -f null -` has no `-t`/time limit either.

## 16. Test suite is stale and fails  (MEDIUM)

- `tests/test_learning_constraints.py`: `KeyError: 'blacklisted_attributes'`; calls `.add()` on the
  read-only property (no-op); expects old return shapes; references removed `Config.ensure_directories_exist`.
- `tests/test_parse.py`: input string is empty. `tests/test_parse_result.py`: 645 lines, all comments.
- `tests/test_blacklist_debug.py` passes but only covers the leaf case (misses issue 1).

## 17. Low-severity items

- `eval()` on ffcompile output (`parsers.py` ~L288, ~L319). Use `ast.literal_eval`.
- Template mining runs `./ffcompile templates/<t>.bt <t>.cpp` in the cwd; from the repo root this
  silently regenerates the tracked `png.cpp`, `jpg.cpp`, `gif.cpp`.
- `MAX_ATTRIBUTE_SIZE_BYTES = 8` admits 9-byte fields (`end - start > 8`, inclusive end).
- `transformers.flatten_json` writes `"More than 10 values"` but triggers at `> 20` (~L55).
- `main.process_directory` slices unsorted `os.listdir` output for `max_files`; not reproducible.
- Smart-abstraction temp files `abstracted/abstracted_<hash>.<ext>` are never deleted: one per
  processed file (AVI parallel left 43, sequential 32).
- Special filenames `special_<op>_<attr>_<start>_<end>.<ext>` collide across source files.
- `GlobalState.from_dict`: an empty leaf list is restored as `list`; later inserts are dropped.
- `processed_success.log` / `processed_failed.log` exist only in parallel mode.
- Parse stdout mixes template `Printf` output with CSV lines (`Intel format`, `left: 40`,
  `Start of Scan Marker`, `Generated record 0`); skipping on field count works today but is fragile.
- Defaults and docs: `Config.DATA_DIR = ../Dataset/<type>/` does not exist on this machine; README
  lists MP3 but `SUPPORTED_FILE_TYPES` omits it; `README_COMPREHENSIVE.md` describes the old layout.

## 18. Observations (not defects)

- The parser discards the `,Optional` / `,Appendable` flags the fuzzer emits. Optionality is
  potentially useful learned information.
- What is "learned" is bounded by the oracle. PNG: abstraction of `ihdr~width` was rejected 10/10
  (IDAT no longer matches), `crc` accepted (fuzzer recomputes it), random `sbit*` accepted
  (ancillary chunk). AVI/MP4: `ffmpeg` accepted thousands of mutants per file (AVI 2806/2557
  valid abstractions/overwrites sequential), hence issues 6 and 7.
- Checksum detection worked where supported: PNG CRC-32 per chunk type, ZIP `recordCrc`/`dirEntryCrc`
  CRC-32 via DEFLATE decompression, BMP `BI_RGB`, PNG `DEFLATE`.
- Checkpoint resume round-trip on a completed JPG run restored 159/159 values.

---

## Status after the fixes (2026-10-21)

Decisions taken (see FIX_PLAN.md): D1 = B, D2 = B, D3 = configurable switch defaulting to the
historical lenient oracle, D4 = B.

1. **FIXED.** `FileParser.parse_lines` keeps only leaf lines (a label that is a prefix of another
   label is a struct), so container names never enter the blacklist. Blacklists hold cleaned full
   paths and `_merge_nested_values` applies them to leaves only. Covered by
   `tests/test_merge_equivalence.py` (three files per format, parse + extract, merged in both orders,
   must equal the sequential state; all six formats) and `tests/test_blacklist_merge.py`.
2. **FIXED.** `utils.remove_path_from_nested_dict` removes one leaf by cleaned path and prunes empty
   parents; `remove_attribute_from_nested_dict` delegates to it. Covered by `test_blacklist_merge.py`.
3. **FIXED.** Every `subprocess.run` has a timeout (`FUZZER_TIMEOUT`, `VALIDATOR_TIMEOUT`,
   `TEMPLATE_COMPILE_TIMEOUT`, all 60 s / 300 s). A parallel batch is bounded by
   `as_completed(..., timeout=PARALLEL_FILE_TIMEOUT * ceil(batch / workers) + 60)`; files still
   running are recorded as failed and the executor is shut down without waiting for them.
   Covered by `tests/test_validators.py` (timeout path).
4. **FIXED.** `errors="replace"` on all seven `subprocess.run` calls. Covered by `test_validators.py`,
   including a live `ffmpeg` test that corrupts `compressorname` with `0xD6` bytes.
5. **FIXED.** One helper, `utils.strip_index` (regex `_\d+$`), used by `clean_single_key`,
   `clean_keys_list`, `clean_attribute_key`, `clean_attribute_path`, the parser and `flatten_json`.
   Covered by `tests/test_keys.py`, `test_parse_filter.py` (AVI index entries pool under one path,
   MP4 output has no `_N` keys) and `test_flatten.py`.
6. **ADDRESSED (design).** All state is keyed by cleaned full path (`GlobalState.is_blacklisted`,
   by-count per path); leaf-name pooling happens only when `*_flattened.json` is written, and a
   path-keyed `*_flattened_paths.json` is written next to it. Oracle strictness is a switch:
   `Config.VALIDATOR_STRICT` / runner `--strict` adds `identify -regard-warnings` and
   `ffmpeg -xerror`; the default stays lenient so results remain comparable. Choosing strict for
   the thesis runs is still open (Phase 4).
7. **FIXED.** `GlobalState.seen_attribute_paths` is run-wide (merged across workers; workers start
   from the main snapshot). A mutant is "special" only when it exposes a path never seen before,
   capped by `MAX_SPECIAL_FILES_PER_FILE = 5` and `MAX_SPECIAL_FILES = 50`; special filenames carry
   a hash of the source file.
8. **FIXED.** `validate_byte_range(start, end, file_size)` is applied to every parse line; invalid
   lines are dropped (debug log). Covered by `test_parse_filter.py` (ZIP fixture keeps the
   inverted `efData` lines) and `test_keys.py`.
9. **FIXED (D2 = B).** Leaf arrays are recognised from `_N` siblings; arrays with more than
   `MAX_ARRAY_ELEMENTS_LEARNED = 16` elements are dropped entirely, element 0 included, and listed in
   `<type>_dropped_arrays.json`; smaller arrays are kept and pooled. Covered by `test_parse_filter.py`
   (JPG `scanData`/`random` gone, PNG PLTE keeps all four entries, BMP palette dropped).
10. **FIXED.** Struct lines are excluded by prefix detection and identical ranges are collapsed
    explicitly; the sBIT struct is no longer a mutation target. Covered by `test_parse_filter.py`.
11. **FIXED.** `max_files` applies to the source directory only; the special pass always runs,
    capped by `MAX_SPECIAL_FILES`.
12. **FIXED.** Checkpoints are saved every `CHECKPOINT_SAVE_INTERVAL` files or every
    `CHECKPOINT_SAVE_SECONDS` (30 s), after each parallel batch, on completion, and on SIGINT/SIGTERM
    via handlers installed in `run_complete_process`; the runner's message reflects whether a save
    happened. Verified: SIGTERM during file 3 of 6 left a checkpoint with 2 files; `--resume`
    processed the remaining 4 and exited 0.
13. **FIXED.** Checkpoints carry `completed`; `find_latest_checkpoint` skips finished runs; the
    runner prompts only when stdin is a TTY and accepts `--new`. Verified with stdin closed.
14. **FIXED.** `run_complete_process` returns `ok`; the runner exits 0 / 1 / 2 / 130 and prints
    failed counts; `<type>_run_summary.json` records them. README Quick Start shows the required
    `__main__` guard. Verified exit codes for a missing fuzzer (1), a good run (0), a bad type (1).
15. **FIXED.** `identify` runs with `IDENTIFY_RESOURCE_LIMITS` (memory/map 512MiB, disk 2GiB,
    time 10 s) and a timeout; `ffmpeg` runs with `-nostdin` and a timeout.
16. **FIXED.** New `unittest` suite (49 tests) over recorded parse fixtures in `tests/fixtures/`
    for png, jpg, avi, mp4, zip, bmp; stale scripts removed.
17. **FIXED** item by item: `ast.literal_eval`; ffcompile output to a temporary directory; size
    limit is inclusive bytes; flatten marker text matches `FLATTEN_MAX_VALUES`; sorted directory
    listing; abstraction temp files removed in `finally`; special filenames unique per source file;
    empty leaf lists restore as sets; `processed_*.log` in both modes; `mp3` added to
    `SUPPORTED_FILE_TYPES`; README updated. `DATA_DIR` keeps its environment-specific default (the
    runner now errors clearly). `README_COMPREHENSIVE.md` is left as a historical document.
18. Observations: the `Optional`/`Appendable` flags are now kept on `ByteRange.flags` (not yet used).

Fuzzer-side follow-up still open: the ZIP template's inverted `efData` ranges (filtered out on the
Python side).

### Same 3 files per format, after the fixes (2026-10-21, lenient oracle, `--fuzzer-dir build`)

| Format | Mode | Values (leaf paths) | Blacklisted size / count | Special files | Errors in log | Wall time |
|---|---|---|---|---|---|---|
| PNG | sequential | 68 (16) | 1 / 1 | 0 | 0 | 12 s |
| PNG | parallel | 65 (16) | 1 / 1 | 0 | 0 | 6 s |
| JPG | sequential | 140 (36) | 2 / 0 | 1 | 0 | 30 s |
| JPG | parallel | 125 (34) | 1 / 0 | 0 | 0 | 9 s |
| AVI | parallel | 1085 (73) | 6 / 12 | 10 | 0 | 2 m 46 s |
| MP4 | parallel | 3948 (826) | 60 / 17 | 21 | 0 | 7 m 46 s |

Sequential and parallel now learn the same field set (PNG 16/16, JPG 36 vs 34, the difference
being one special file found by chance); value counts differ only through mutation randomness.
Before the fixes, parallel PNG kept 11 of 17 fields and 27 of 76 values, and the AVI blacklist
held 285 names. The leaf-keyed flattened files for AVI and MP4 still cap many fields at
"More than 20 values" because the lenient oracle accepts random values for them; the path-keyed
files keep e.g. `file~root~id` and `file~list~id` intact while only `movi_chunk~id` is capped.
Choosing `--strict` for the thesis runs is the open Phase 4 decision.

---

## How these were verified

Sandboxes outside the repo (`<scratch>/sandbox_<fmt>`) with symlinks `<fmt>-fuzzer -> build/<fmt>-fuzzer`,
`ffcompile`, `templates`, and 3 files from `testcases/<fmt>/` in `input/`. Sequential runs used a
driver setting `Config.PARALLEL_WORKERS = 1`; parallel runs the same driver with 10 workers inside a
`__main__` guard. Results compared with a script over `results/*_parsed_values_hex_original.json`.
JPG runs used `MAGICK_*_LIMIT` environment variables to protect the host. Per-format parse profiles
came from `<fmt>-fuzzer parse` on one sample each, then `FileParser.parse_file_structure` and
`extract_bytes_from_file` on the same file.
