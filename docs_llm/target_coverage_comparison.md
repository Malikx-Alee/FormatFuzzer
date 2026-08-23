# Optimized vs. original templates: target-program coverage, head-to-head

Direct comparison of the two complete 10,000-file result sets:
[target_coverage_results.md](target_coverage_results.md) (FormatFuzzer's
generation-optimized `templates/<format>.bt`, built via `./build.sh`) vs.
[target_coverage_results_orig.md](target_coverage_results_orig.md) (the
untouched original 010 Editor template, `templates_originals_llm/<format>-
orig.bt`, built via `./build_new.sh`). Same target-program build/drive code
either way — only the FormatFuzzer template (and therefore the generated
corpus) differs. This is the question the two-script setup exists to answer:
**does FormatFuzzer's template optimization actually move target-program
coverage, or only validity%** (the metric this repo's existing
`BENCHMARK_REPORT.md` / `benchmark_all.py` already tracks)?

## Line coverage, side by side

| Format | Optimized (`templates/`) | Original (`templates_originals_llm/`) | Δ line pts | Winner |
|---|---:|---:|---:|---|
| `zip`  | 32.2% | 15.1% | **+17.1** | optimized |
| `bmp`  | 20.3% | 14.5% | **+5.8**  | optimized |
| `jpg`  | 14.3% | 9.8%  | **+4.5**  | optimized |
| `midi` | 11.4% | 8.4%  | **+3.0**  | optimized |
| `mp4`  | 4.3%  | 1.6%  | **+2.7**  | optimized |
| `pcap` | 5.6%  | 4.5%  | **+1.1**  | optimized |
| `avi`  | 4.4%  | 3.5%  | **+0.9**  | optimized |
| `png`  | 22.3% | 21.8% | **+0.5**  | optimized |
| `wav`  | 22.1% | 22.0% | **+0.1**  | optimized (negligible) |
| `gif`  | 23.5% | 24.5% | **−1.0**  | original |

Average delta across all 10 formats: **+3.47 percentage points** in favor of
the optimized templates (simple unweighted mean of the Δ column — the
targets range from 2,412 to 521,084 lines, so this average isn't
size-weighted; treat it as "typical per-format effect," not "aggregate
codebase coverage").

## Function coverage, side by side

| Format | Optimized | Original | Δ function pts |
|---|---:|---:|---:|
| `zip`  | 58.0% | 35.3% | **+22.7** |
| `jpg`  | 18.2% | 13.9% | +4.3 |
| `midi` | 21.7% | 17.8% | +3.9 |
| `mp4`  | 6.6%  | 3.4%  | +3.2 |
| `pcap` | 11.4% | 9.9%  | +1.5 |
| `bmp`  | 20.3% | 18.4% | +1.9 |
| `avi`  | 6.3%  | 5.0%  | +1.3 |
| `png`  | 36.6% | 36.2% | +0.4 |
| `wav`  | 35.0% | 35.0% | 0.0 |
| `gif`  | 35.9% | 35.9% | 0.0 |

Unlike line coverage, **every format is a tie or a win for the optimized
template on function coverage** — `gif`'s line-coverage regression doesn't
carry over to functions (tied at 35.9%), meaning the original `gif` template
reaches a few more *lines* within functions both templates already reach,
rather than reaching any function the optimized template misses.

## Reading the results

- **`zip` is the standout**: +17.1 line points, +22.7 function points. It's
  also the smallest target (5,304 lines) and the format where FormatFuzzer's
  own README documents the most deliberate hand-tuning (lookahead-function
  known-value hints, evil-bit-aware generation) — consistent with template
  optimization mattering most when the target is small enough for corpus
  diversity to actually reach a large fraction of it.
- **`bmp` and `jpg` show solid, consistent gains** (+5.8 / +4.5 line points)
  — comparable in kind to `zip`, smaller in magnitude.
- **`mp4`/`avi`/`pcap` show small absolute % gains but the underlying targets
  are huge** (521k and 45k lines respectively) — e.g. `mp4`'s +2.7 points is
  +13,858 raw lines hit (22,390 vs 8,532), the largest single line-count
  swing in either direction across all ten formats. Don't read the small
  percentage as "optimization barely matters" for these three; the
  percentage is diluted by target size the same way it is within either
  individual results table.
- **`gif` is the one regression** (−1.0 line points, tied on functions) —
  worth a closer look at `templates/gif.bt` vs
  `templates_originals_llm/gif-orig.bt` if this format's optimization is
  ever revisited; it's a small, real signal, not noise, but also the
  smallest magnitude regression possible to call "a signal" at all given
  these are single 10k-file runs, not averaged over repeated runs (see
  caveats).
- **`wav`/`png` show essentially no difference** (+0.1 / +0.5) — for these
  two formats, whatever hand-tuning went into `templates/` isn't reaching
  new *target-program* code, even though (per this repo's own
  `BENCHMARK_REPORT.md`) template optimization measurably changed
  *validity%* for some formats. Coverage and validity are genuinely
  different axes — an optimization can raise one without moving the other.

## Caveats

- **Single runs, not averages.** The FormatFuzzer paper itself runs each
  configuration 10 times over 24 hours and reports averages (§7, Tables 6–9)
  precisely because generation has randomness in it. Every number here is a
  single 10,000-file run per format per variant — small deltas (`wav` +0.1,
  `png` +0.5, and arguably `gif` −1.0) are within the range that could shift
  or flip on a re-run. The larger deltas (`zip` +17.1, `bmp` +5.8, `jpg`
  +4.5) are large enough to very likely be real, but "very likely" is doing
  work in that sentence — this is one data point, not a statistically
  powered comparison.
- **Black-box generation only** — no AFL/AFL++ integration in either
  variant, so neither table reflects the paper's finding that coverage-
  guided fuzzing (not just template quality) matters for reaching error-
  handling code. See [code_coverage_of_generated_outputs.md §5](code_coverage_of_generated_outputs.md).
- All other per-format caveats (giflib substituting gif2png, library
  version drift from the paper's Table 4, `midi`'s missing instrument
  patches, `bmp`'s deliberately narrowed loader set) apply identically to
  both sides of this comparison, since both scripts share the exact same
  target-program recipes — see
  [target_coverage_all_formats.md](target_coverage_all_formats.md).

## Regenerating

```bash
python3 scripts/target_coverage.py <format>       # optimized (templates/)
python3 scripts/target_coverage_llm.py <format>    # original (templates_originals_llm/)
```

Re-run either side for any format and re-read both `meta.json`s to refresh
a row here.
