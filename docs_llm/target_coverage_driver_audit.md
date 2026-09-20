# Driver audit — what the target programs were actually measuring

Audited all 10 target-program drivers in `scripts/target_coverage.py` against
three questions:

1. Does the driver accept known-good seed files?
2. Does it reject garbage and empty input (i.e. does its exit code carry a
   validity signal)?
3. Does it behave the same on AFL's `.cur_input` as on a `f<N>.<ext>` file?

Question 3 was added after question 1 turned up an anomaly. It found the most
expensive bug of the three.

## Summary

| format | seeds accepted | rejects garbage/empty | filename-independent | verdict |
|---|---|---|---|---|
| zip  | 13/13 | yes | yes | ok |
| gif  | 6/6 *(was 0/6)* | yes | yes | **fixed** |
| jpg  | 7/7   | yes | yes | ok |
| png  | 31/31 | yes | yes | ok |
| midi | 6/6   | **no** | yes | usable for coverage only |
| wav  | 10/13 | yes | **no** | **fixed** |
| pcap | 5/5   | yes | yes | ok |
| mp4  | 10/10 | yes | yes | ok |
| avi  | 10/11 | yes | yes | ok |
| bmp  | 10/10 | yes *(was no)* | yes | **fixed** |

The three remaining seed failures are genuine unsupported inputs, not driver
bugs: `avi` av01 (AV1, not enabled in this FFmpeg build), and `wav` mu-law /
64-bit / 20-bit-with-nonzero-padding (WavPack rejects all three explicitly).

---

## Bug 1 (severe) — wav: AFL was fuzzing a file wavpack never opened

`wavpack` appends `.wav` to any input path that has no extension. AFL's `@@`
expands to `<out_dir>/.cur_input`, so every single exec resolved to
`.cur_input.wav`, a file that does not exist. wavpack bailed at `fopen()`
before reading a byte.

Measured on an identical 312-file corpus (13 seeds + 299 generated), driving
the same inputs under both names:

| input name | valid | line coverage |
|---|---:|---:|
| `in.wav`      | 289/312 | **21.7%** (2449 / 11286) |
| `.cur_input`  | 0/312   | **2.0%** (222 / 11286) |

This is visible in the recorded 8h campaign results, where all three template
variants land on the same near-floor number — three different templates
producing indistinguishable coverage is the signature of an input that is
never read:

```
fmt      hand       opus4.7    opus5
wav      2.9%       3.0%       3.0%      <- never opened the file
png      37.5%      35.9%      36.4%     <- healthy spread for comparison
```

**All three wav AFL+FFMut campaigns must be re-run.** No other format is
affected — the sweep confirmed the other nine drivers are extension-independent.

**Fix:** pass AFL `-e <ext>`, which names the test case `.cur_input.<ext>`
while leaving `@@` substitution intact. `-f` is *not* a substitute: it sets
`out_file` before the `if (!out_file)` block in `src/afl-fuzz.c:831`, so
`detect_file_args()` never runs and a literal `@@` is passed to the target.
`find_afl_fuzz()` now probes `afl-fuzz -h` for `-e` support and fails loudly
at launch rather than silently wasting another 8 hours.

The plain (non-AFL) generation path was never affected — it has always named
its corpus files `f<N>.<ext>` (`target_coverage.py:741`), as has the AFL queue
harvester (`target_coverage_afl_ffmut.py:391`).

## Bug 2 (moderate) — gif: every run failed after decoding

`gif2rgb -o /dev/null` without `-1` writes three separate colour planes by
appending `.R`/`.G`/`.B` to the output name (`DumpScreen2RGB`, gif2rgb.c:250).
`/dev/null.R` cannot be created, so `GIF_EXIT` fired on every run — after the
GIF was parsed but before the RGB dump — giving exit code 253 for valid and
invalid input alike.

Cost: ~2.5 points of line coverage, applied **uniformly** to all three
variants, plus a useless exit code. Re-measured with the fix:

| corpus | broken | fixed | gain |
|---|---:|---:|---:|
| hand    | 23.4% | 26.0% | +64 lines |
| opus4.7 | 23.2% | 25.0% | +42 lines |
| opus5   | 20.5% | 23.4% | +69 lines |

**Ranking is identical under both drivers**, so previously published gif
comparisons are still directionally valid; only their absolute values are
depressed. **Fix:** add `-1`.

## Bug 3 (minor) — bmp: exit code carried no signal

The gdk-pixbuf harness ended in an unconditional `return 0`, so it reported
success for a valid BMP, for random garbage, and for a zero-byte file alike.
Line coverage was unaffected (the decode ran either way, confirmed at +611
lines over garbage), but bmp could never contribute a validity rate.

**Fix:** `return ok ? 0 : 1`. Also note the harness source lives in
`target_coverage.py`, not in the meson build, so `already_built()`'s toolchain
fingerprint cannot see it change — editing it would have been silently ignored
on any machine that had already built bmp once. The harness now rebuilds
whenever its source text differs from the compiled copy.

## Not a bug — midi's exit code

TiMidity returns 0 for garbage and empty input. Line coverage is real and
substantial (+1054 lines over garbage), so midi remains valid for coverage
comparison; it just cannot produce a validity rate. Its low absolute coverage
(~9.8%) is expected — no instrument patch set is configured, so the synthesis
path never runs.

## Not a bug — the extensionless wav seed

`testcases/wav/CreateWithCode_Prototype` is a genuine, decodable WAV (RIFF
PCM 8-bit mono 11025 Hz) that merely lacked a `.wav` extension, which is why
wavpack refused it and an earlier audit misread it as corrupt. Renamed to
`CreateWithCode_Prototype.wav`; it decodes cleanly.

## Run-to-run variance

Coverage is reproducible enough that single-run comparisons are defensible for
the stable variants, but not for opus4.7. Three independent runs, 1000
generated gif files each, fixed driver:

| variant | run 1 | run 2 | run 3 | mean | spread |
|---|---:|---:|---:|---:|---:|
| hand    | 25.2 | 25.2 | 25.0 | 25.1 | 0.2 |
| opus4.7 | 25.0 | 24.4 | 23.5 | 24.3 | **1.5** |
| opus5   | 23.4 | 23.4 | 23.3 | 23.4 | 0.1 |

The hand-vs-opus5 gap of 1.7 points far exceeds both spreads, so the gif
regression is real rather than noise. opus4.7's 1.5-point spread means any
single-run result involving it should be repeated before being reported.
