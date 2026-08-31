# Bug: concurrent optimized/original AFL+FFMut runs shared one gcov target, pooling their coverage

## Summary

`scripts/target_coverage_afl_ffmut.py` (optimized templates) and
`scripts/target_coverage_afl_ffmut_llm.py` (original templates,
`templates_originals_llm/`) each build their own AFL-instrumented copy of
the target program to fuzz, correctly isolated per variant. But the
*separate* gcov-instrumented copy used only to measure coverage
(`gcov_target_work_dir`) was **not** variant-specific — both scripts pointed
at the same `coverage_targets/<fmt>/` directory and its `.gcda` runtime
counters. Running the optimized and original 8-hour campaigns for the same
format concurrently (the natural thing to do on a 64-core box, and what
happened here) meant both processes drove their own harvested files into
the *same* shared counters. Every periodic lcov snapshot then reported the
pooled coverage of both runs combined, not either one's own — so the two
variants' reported coverage converged and became indistinguishable, even
though AFL itself explored genuinely different amounts.

## Symptom

User: "I think because of the `.so` path, I have got the output coverage
result same for both template and original variant" — provided
`coverage_results_server/` with real 8h-run results for 7 formats.

## Diagnosis

For every completed format pair (`avi`, `bmp`, `gif`, `jpg`, `png`, `wav`,
`zip`), the `final/meta.json` timestamps for the optimized and original runs
were within 1–9 minutes of each other despite each being a 28,800s (8h)
run — only possible if both were launched at close to the same wall-clock
time, i.e. concurrently.

Checked `png` in detail (`coverage_results_server/coverage_results/png{,-orig}-afl-ffmut/`):

| elapsed | optimized | original |
|---|---|---|
| 300s | 3812/10778 lines | 3817/10778 lines |
| 14400s | 4037/10778 lines (48.7% funcs) | 4037/10778 lines (48.7% funcs) — **identical** |
| 28800s (final) | 4064/10778 lines (49.2%) | 4064/10778 lines (49.2%) — **identical** |

Near-identical from the very first snapshot, converging to bit-for-bit
identical by mid-run — exactly the signature of two processes accumulating
into one shared gcov counter set rather than measuring independently.
`jpg`, `gif`, and `zip` final snapshots showed the same pattern (identical
line/function hit *and* total counts between variants). Meanwhile each
pair's own `afl.execs_done`/`afl.paths_total`/`afl.bitmap_cvg` genuinely
differ between variants (e.g. png: 44,692,065 vs 43,324,855 execs;
1145 vs 1152 paths) — confirming AFL itself, and the `.so` custom-mutator
wiring, were correctly variant-isolated the whole time (via separate
`afl_runs/<fmt>-{afl-ffmut,orig-afl-ffmut}/` directories and separate
`build/<fmt>{,-orig}.so` files) — it was specifically the *coverage
measurement* side, not the fuzzing side, that was shared.

`midi` and `pcap` have no completed results in this dataset (unaffected —
`pcap` never finished a run before the libpcap link-flag fixes went in).
`mp4`'s original variant hasn't completed yet either.

## Why `afl_target_work_dir` (the AFL-instrumented copy) didn't need this fix

That directory holds a compiled binary that afl-fuzz only forks and execs
repeatedly — it accumulates no mutable state of its own (AFL's coverage
feedback lives in each afl-fuzz process's private shared-memory bitmap, not
in the file), so multiple concurrent processes reading/exec'ing the same
binary is safe and was already correctly shared to avoid a redundant
rebuild. Only the gcov copy, whose whole purpose is accumulating `.gcda`
counters across a run, needed isolation.

## Fix

In `scripts/target_coverage_afl_ffmut.py`'s `main()`:

```python
gcov_target_work_dir = tc.TARGETS_DIR / fmt          # before: shared across variants
gcov_target_work_dir = tc.TARGETS_DIR / name          # after: name = f"{fmt}-{variant.suffix}"
```

So the optimized variant now builds+measures against
`coverage_targets/<fmt>-afl-ffmut/` and the original variant against
`coverage_targets/<fmt>-orig-afl-ffmut/` — fully isolated from each other
*and* from the plain (non-AFL) `target_coverage.py`/`target_coverage_llm.py`
scripts' own `coverage_targets/<fmt>/`. Costs one extra one-time build of
the gcov-instrumented target per variant (cached afterward via the existing
toolchain-fingerprinted `already_built()` marker) — negligible next to an
8-hour campaign.

While investigating, also fixed an unrelated but real bug in the same
function (`capture_lcov`): the `lines_pct`/`functions_pct`/etc. regexes
searched `summary.stdout` only, but this lcov build apparently prints its
"Summary coverage rate:" block to stderr, not stdout (version/distro
dependent) — so every `meta.json` on the server has those fields as `null`
even though `summary.txt` (written from `stdout + stderr` combined) has the
real numbers right there. Now searches the combined stream instead.

## Verification

Confirmed the regex fix against the server's actual saved `summary.txt`
text directly (not a live re-run): `re.search(r"lines\.+:...", combined)`
correctly extracts `36.5%, 1803, 4944` from a real sample line. The
shared-directory diagnosis is inferential (no direct process-list evidence
of concurrent execution, since this was diagnosed from artifacts after the
fact) but is strongly and consistently supported: tight finish-timestamps
across every completed pair, near-identical coverage from the earliest
snapshot converging to exact identity by mid-run, combined with genuinely
differing AFL-side stats ruling out "the mutator was never actually
different" as an alternative explanation.

## Impact on existing data

**All 7 completed format pairs in `coverage_results_server/` (avi, bmp,
gif, jpg, png, wav, zip) cannot be used for an optimized-vs-original
coverage comparison** — the numbers reflect pooled coverage from both
variants' runs, not either one independently. The AFL-side stats
(`execs_done`, `paths_total`, `bitmap_cvg`, `unique_crashes`/`unique_hangs`)
in the same `meta.json` files remain valid and variant-specific; only the
`lines_pct`/`functions_pct`/etc. fields (once the stdout/stderr fix lets
them populate at all) are affected.

## Notes for future work

- Re-running is required for a valid comparison. After syncing the fix,
  concurrent optimized+original runs are safe again (that's the whole
  point of the fix) — no need to serialize them.
- If re-running is expensive, an alternative fix that preserves the
  *already-collected* AFL queues would be to replay each variant's
  `afl_runs/<fmt>-{,orig-}afl-ffmut/main/queue/` from scratch through a
  freshly-built, this-time-isolated gcov target (i.e. reuse the harvested
  files that already exist on disk, just re-drive them post-fix) rather
  than re-running the AFL campaigns themselves. Not implemented here since
  it wasn't asked for, but the pieces (`recipe.build()` +
  `recipe.drive()` + `capture_lcov()`) already exist to script this if
  wanted.
- `target_coverage_afl_ffmut_llm.py` needed no direct code change — it
  imports `main()` from `target_coverage_afl_ffmut.py` and only supplies a
  different `Variant`, so the fix applies to both automatically.
