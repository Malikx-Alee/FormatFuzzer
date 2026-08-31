# Target-program coverage script: per-format verification notes

> **Naming note:** this document was written before `templates_originals_llm/`
> and the `-orig` suffix were renamed to `templates_llm/`/`-llm`. Paths and
> flags below showing `-orig`/`templates_originals_llm` reflect the naming
> at the time this was written; current code uses `-llm`/`templates_llm`.

[scripts/target_coverage.py](../scripts/target_coverage.py) automates the
target-program coverage recipe (§4 of
[code_coverage_of_generated_outputs.md](code_coverage_of_generated_outputs.md))
for one format at a time:

```bash
python3 scripts/target_coverage.py <format>          # 10,000 files by default
python3 scripts/target_coverage.py --list             # see all formats + verified/best-effort status
python3 scripts/target_coverage.py zip --count 500    # smaller run for a quick check
```

It downloads+builds a real-world consumer with `--coverage` instrumentation
(cached under `coverage_targets/<format>/`, skipped on re-run unless
`--rebuild`), generates a corpus with this repo's `<format>-fuzzer`, drives
the corpus through the instrumented binary, and writes
`coverage_results/<format>/{<format>_target.info, html/, summary.txt,
meta.json}`. Run it once per format — it does not loop over formats itself.

[scripts/target_coverage_llm.py](../scripts/target_coverage_llm.py) is a
parallel script sharing all the same target-program recipes below, but
driven by `<format>-orig-fuzzer` (built from the untouched original
`templates_originals_llm/<format>-orig.bt` template via `./build_new.sh`
instead of `templates/<format>.bt` via `./build.sh`) and writing to
`coverage_results/<format>-orig/` — see its own docstring and
[target_coverage_results_orig.md](target_coverage_results_orig.md) /
[target_coverage_comparison.md](target_coverage_comparison.md) for what it's
for. Every verification note below applies equally to both scripts, since
the target-program build/drive code is identical between them.

## Verified (built + smoke-tested with a real `<format>-fuzzer` corpus in this session)

| Format | Target | Notes |
|---|---|---|
| `zip` | Info-ZIP UnZip 6.0 | Bypasses the Makefile's `macosx` target (hardcodes `-O3`, ignores `CFLAGS` overrides — see [target_coverage_zip_unzip.md](target_coverage_zip_unzip.md)); drives `unzips` directly. |
| `gif` | giflib 5.2.2 (`gif2rgb`) | **Substitutes** the paper's target, gif2png — its SourceForge download link 404s and the project is largely abandoned. giflib is the standard, actively-maintained GIF decoder; `gif2rgb -o /dev/null <file>` exercises the same `DGifSlurp`/decode path. |
| `jpg` | libjpeg-turbo 3.2.0 | CMake build; the make target is `djpeg-static`, not `djpeg` (that name is the final binary, not the make target — `make help` lists the real target names). `-DWITH_SIMD=FALSE` since `nasm`/`yasm` aren't installed; irrelevant to coverage since SIMD is a codegen detail, not new source lines. |
| `png` | libpng 1.6.57 | `pnggroup/libpng` (the project moved off `glennrp/libpng` on GitHub). `./configure` autodetects the SDK's bundled zlib. Driver is `pngtest -m <file>` (the library's own read-only self-test mode). |
| `midi` | TiMidity++ 2.15.0 | Needed two fixes: (1) its bundled `config.sub`/`config.guess` predate Apple Silicon and reject `arm64-apple-darwin` — replaced with Homebrew's copies (`find_brew_build_aux()` in the script locates them via `/opt/homebrew/Cellar/{autoconf,libtool}/*/share/*/build-aux/`). (2) modern clang errors (not just warns) on implicit function declarations that this 2018-era code relies on — added `-Wno-implicit-function-declaration -Wno-implicit-int`. No instrument patch set is configured (`-c dummy.cfg`, an empty file), so it fails past `readmidi.c` parsing into actual synthesis for most files — MIDI-parsing coverage is real, full-synthesis coverage is understated. |
| `wav` | WavPack 5.9.0 | CMake build, `make wavpackapp` target produces the `wavpack` CLI. Straightforward. |
| `pcap` | tcpdump 4.99.6 + libpcap 1.10.6 | Two-stage: libpcap is built and `make install`-ed to a local prefix (`coverage_targets/pcap/local/`) first, then tcpdump's CMake build is pointed at that prefix via `CMAKE_PREFIX_PATH` so it statically links the *instrumented* libpcap rather than the system one. The script captures coverage from both build directories and merges them with `lcov --add-tracefile` — this is the pattern to reuse for any other multi-component target. |
| `bmp` | gdk-pixbuf 2.42.12 via meson, plus a small custom C harness (`gdk_pixbuf_new_from_file()`) written by the script | No existing driver to copy — `checkers/bmp.sh` targets ImageMagick, not gdk-pixbuf, so there's nothing to mirror. Uses meson's built-in `-Db_coverage=true` plus `-Ddefault_library=static`, then links the harness against the local **uninstalled** build via meson's generated `meson-uninstalled/*.pc` pkg-config files. Two real bugs found and fixed by actually running it: (1) `man` defaults to `true` and needs `rst2man` (not installed) — fixed with `-Dman=false`. (2) BMP is filed under gdk-pixbuf's `others` ("weakly maintained loaders") option group, *not* its own toggle — `-Dothers=disabled` (the obvious way to trim unrelated build surface) silently compiles out `io-bmp.c` entirely, so the harness "succeeds" while decoding nothing. Confirmed via lcov: with `others=disabled`, `io-bmp.c` doesn't even appear in the coverage report; with `-Dothers=enabled -Dbuiltin_loaders=bmp`, it shows real coverage (49% of `io-bmp.c` from a 40-file smoke corpus). |
| `mp4`, `avi` | FFmpeg 6.1 (shared build, cached once under `coverage_targets/_ffmpeg_shared/`) | Originally left untested pending a full default `./configure`/`make` (FFmpeg's configure probes a large number of optional codecs/libraries and the build is the slowest of any target here). Since confirmed via real 10,000-file runs for both formats, on both the `templates/` corpus ([target_coverage_results.md](target_coverage_results.md)) and the `templates_originals_llm/` corpus ([target_coverage_results_orig.md](target_coverage_results_orig.md)) — flipped to verified in both scripts' `RECIPES`. |

Smoke-tested via the actual script (not just hand-run commands) for `zip`,
`png`, `pcap`, and `bmp` with small `--count` values, confirming the Python
build/drive/capture glue works, not just the underlying shell commands; all
ten formats (including `mp4`/`avi`) have since completed full 10,000-file
runs.

## Known deltas from the paper's exact setup (Table 4)

- `gif` uses giflib instead of gif2png (see above).
- Paper versions are from ~2021 (e.g. libpng 1.6.37, libjpeg-turbo 2.0.6);
  this script pins whatever the latest stable tag was when written (libpng
  1.6.57, libjpeg-turbo 3.2.0, WavPack 5.9.0, tcpdump-4.99.6/libpcap-1.10.6) —
  newer point releases of the same library, not a different codebase, so
  coverage numbers are comparable in spirit but not bit-for-bit reproductions
  of the paper's tables.
- `midi` coverage undercounts real-playback code paths (no instrument
  patches configured, see above).
