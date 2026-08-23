# Target-program coverage results (10,000 files per format)

Results from running [scripts/target_coverage.py](../scripts/target_coverage.py)
with the default 10,000-file corpus per format, read directly from each
format's `coverage_results/<format>/meta.json`. All ten formats have a
result now. For the same formats built from the *original* (pre-
optimization) templates instead, see
[target_coverage_results_orig.md](target_coverage_results_orig.md); for a
direct side-by-side of the two, see
[target_coverage_comparison.md](target_coverage_comparison.md).

## Results

| Format | Target program | Recipe | Line coverage | Lines hit / total | Function coverage | Functions hit / total | Run timestamp |
|---|---|---|---|---:|---|---:|---|
| `zip`  | Info-ZIP UnZip 6.0                | verified     | **32.2%** | 1,709 / 5,304   | 58.0% | 69 / 119     | 2026-08-11 14:06 |
| `gif`  | giflib 5.2.2 (`gif2rgb`)           | verified     | **23.5%** | 567 / 2,412     | 35.9% | 33 / 92      | 2026-08-11 13:57 |
| `png`  | libpng 1.6.57 (`pngtest`)          | verified     | **22.3%** | 2,776 / 12,424  | 36.6% | 196 / 536    | 2026-08-11 13:44 |
| `wav`  | WavPack 5.9.0                      | verified     | **22.1%** | 2,493 / 11,286  | 35.0% | 110 / 314    | 2026-08-11 14:36 |
| `bmp`  | gdk-pixbuf 2.42.12 (custom harness)| verified     | **20.3%** | 1,109 / 5,469   | 20.3% | 64 / 315     | 2026-08-11 15:17 |
| `jpg`  | libjpeg-turbo 3.2.0 (`djpeg`)      | verified     | **14.3%** | 2,607 / 18,178  | 18.2% | 136 / 746    | 2026-08-11 14:08 |
| `midi` | TiMidity++ 2.15.0                  | verified     | **11.4%** | 3,359 / 29,416  | 21.7% | 245 / 1,127  | 2026-08-11 17:11 |
| `pcap` | tcpdump 4.99.6 + libpcap 1.10.6    | verified     | **5.6%**  | 2,576 / 45,648  | 11.4% | 184 / 1,612  | 2026-08-11 14:53 |
| `avi`  | FFmpeg 6.1                         | verified     | **4.4%**  | 23,076 / 521,084| 6.3%  | 1,505 / 24,013 | 2026-08-11 15:44 |
| `mp4`  | FFmpeg 6.1 (shared with `avi`)     | verified     | **4.3%**  | 22,390 / 521,084| 6.6%  | 1,579 / 24,013 | 2026-08-11 18:03 |

Sorted by line coverage %, descending.

## Observations

- **`zip` leads at 32.2%** — UnZip 6.0 is by far the smallest target (5,304
  lines total), so a 10k-file corpus covers proportionally more of it than
  the larger libraries.
- **`avi` (FFmpeg) sits lowest at 4.4%**, but that's largely an artifact of
  scale, not a weak corpus: FFmpeg is a 521k-line codebase, and the `avi`
  driver only exercises the AVI demuxer + default encoder path — the *raw*
  hit count (23,076 lines) is actually the largest of any target here, more
  than 8x zip's total line count. Line-coverage *percentage* isn't
  comparable across targets of such different size; treat the hit-count
  column as the more meaningful number when comparing against `avi`/`mp4`.
- **`pcap` (5.6%) is similarly diluted by size** — tcpdump + libpcap
  together are 45,648 lines, most of it protocol-specific dissectors
  (`print-*.c` for hundreds of protocols) that a `.pcap`-format fuzzer
  without traffic-content awareness has no way to reach; the corpus mostly
  exercises the pcap file-format parser itself (`sf-pcap.c`, `pcap.c`)
  rather than packet dissection.
- **Function coverage tracks line coverage closely** for every format
  except `bmp`, where both land at exactly 20.3% (coincidental) — everywhere
  else function-hit % runs noticeably higher than line-hit % (e.g. `zip`:
  58.0% functions vs. 32.2% lines), meaning the corpus is reaching most
  functions at least once but not deeply exercising each one.
- All `driver_timeouts` were `0` across every completed run — no target
  hung on a generated file at the default 20s timeout.
- `avi` and `mp4` share the identical FFmpeg build and land within 0.1
  percentage points of each other (4.4% vs 4.3%) despite driving it with
  completely different corpora and driver commands (`-f avi -i` vs `-i ...
  -c:v mpeg4 -c:a copy`) — consistent with both drivers reaching mostly the
  same demux/generic-decode machinery rather than format-specific code.
- Both FFmpeg-backed recipes (`mp4`, `avi`) are still flagged best-effort/
  unverified in the script (FFmpeg was never build-tested in the session
  that wrote it) but both evidently built and ran successfully end-to-end
  now that both have completed real 10k-file runs — worth flipping both
  `verified` flags to `True` in `RECIPES`.

## Caveats carried over from the methodology doc

- These are **not** directly comparable to the paper's own Table 6/7 numbers
  — different (newer) library versions, black-box generation only (no AFL
  integration), and `gif`/target substituted (giflib instead of gif2png).
  See [code_coverage_of_generated_outputs.md](code_coverage_of_generated_outputs.md)
  and [target_coverage_all_formats.md](target_coverage_all_formats.md) for
  full detail on each substitution.
- `bmp`'s number only reflects `io-bmp.c` and gdk-pixbuf's generic loader
  dispatch — png/jpeg/tiff/gif loaders were deliberately compiled out of
  that target (see target_coverage_all_formats.md) so the number is 100%
  attributable to BMP-relevant code, not diluted by unrelated format
  support.

## Regenerating

```bash
python3 scripts/target_coverage.py <format>
```

Re-run any single format and re-read its `meta.json` to refresh a row here
— just ask.
