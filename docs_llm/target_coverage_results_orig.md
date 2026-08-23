# Target-program coverage results — original templates (10,000 files per format)

Results from running [scripts/target_coverage_llm.py](../scripts/target_coverage_llm.py)
with the default 10,000-file corpus per format, read directly from each
format's `coverage_results/<format>-orig/meta.json`. This is the
`templates_originals_llm/<format>-orig.bt` variant — the untouched original
010 Editor template, built via `./build_new.sh <format>-orig` into
`<format>-orig-fuzzer` — as opposed to
[target_coverage_results.md](target_coverage_results.md), which covers
FormatFuzzer's generation-optimized `templates/<format>.bt` via `./build.sh`.

Same target programs either way (same recipes, same `coverage_targets/`
build cache — see the script's docstring), so these numbers are directly
comparable to the non-`-orig` table row for row. See
[target_coverage_comparison.md](target_coverage_comparison.md) for that
side-by-side comparison and what it shows.

## Results

| Format | Target program | Recipe | Line coverage | Lines hit / total | Function coverage | Functions hit / total | Run timestamp |
|---|---|---|---|---:|---|---:|---|
| `gif`  | giflib 5.2.2 (`gif2rgb`)           | verified     | **24.5%** | 591 / 2,412     | 35.9% | 33 / 92      | 2026-08-20 23:50 |
| `wav`  | WavPack 5.9.0                      | verified     | **22.0%** | 2,487 / 11,286  | 35.0% | 110 / 314    | 2026-08-21 00:36 |
| `png`  | libpng 1.6.57 (`pngtest`)          | verified     | **21.8%** | 2,703 / 12,424  | 36.2% | 194 / 536    | 2026-08-21 00:05 |
| `zip`  | Info-ZIP UnZip 6.0                 | verified     | **15.1%** | 803 / 5,304     | 35.3% | 42 / 119     | 2026-08-20 23:35 |
| `bmp`  | gdk-pixbuf 2.42.12 (custom harness)| verified     | **14.5%** | 795 / 5,469     | 18.4% | 58 / 315     | 2026-08-21 00:29 |
| `jpg`  | libjpeg-turbo 3.2.0 (`djpeg`)      | verified     | **9.8%**  | 1,788 / 18,178  | 13.9% | 104 / 746    | 2026-08-21 00:09 |
| `midi` | TiMidity++ 2.15.0                  | verified     | **8.4%**  | 2,473 / 29,416  | 17.8% | 201 / 1,127  | 2026-08-21 04:20 |
| `pcap` | tcpdump 4.99.6 + libpcap 1.10.6    | verified     | **4.5%**  | 2,042 / 45,648  | 9.9%  | 160 / 1,612  | 2026-08-21 01:07 |
| `avi`  | FFmpeg 6.1                         | verified     | **3.5%**  | 18,095 / 521,084| 5.0%  | 1,212 / 24,013 | 2026-08-21 10:06 |
| `mp4`  | FFmpeg 6.1 (shared with `avi`)     | verified     | **1.6%**  | 8,532 / 521,084 | 3.4%  | 824 / 24,013   | 2026-08-21 11:39 |

Sorted by line coverage %, descending. All formats completed this time — no
pending rows.

## Observations

- **`gif` leads at 24.5%**, and unlike the optimized-template table it
  actually edges out `wav`/`png` for the top spot — see the comparison doc
  for why this is the one format where the original template did *better*.
- **`avi`/`mp4` remain lowest by %** for the same reason as in the
  optimized-template results: FFmpeg is a 521k-line codebase and these
  drivers only exercise a narrow demux/decode/encode path, so percentage
  is not a meaningful cross-target comparison here either — use the raw
  hit-count column instead when comparing against non-FFmpeg targets.
- `driver_timeouts` were `0` across every run — same as the optimized-
  template results, no target hung at the default 20s timeout regardless of
  which template generated the corpus.
- Both FFmpeg-backed recipes (`mp4`, `avi`) are flagged `verified` in
  `target_coverage_llm.py`'s `RECIPES` dict — flipped from best-effort after
  both completed successfully here with real 10k-file runs.

## Regenerating

```bash
python3 scripts/target_coverage_llm.py <format>
```

Re-run any single format and re-read its `meta.json` to refresh a row here.
