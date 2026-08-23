# How to measure code coverage of FormatFuzzer-generated outputs

## TL;DR

This repo currently measures **validity** (does a generated file parse without
error in some real-world tool?), via [checkers/*.sh](../checkers/) and
[fuzz_manager.py](../scripts/fuzz_manager.py) → `results.csv` / `BENCHMARK_REPORT.md`.
It does **not** measure **code coverage** (how much of a parser's source code
actually executed while consuming that file). Those are different questions —
a file can be "invalid" yet still hit new lines in the parser's error-handling
code, and a file can be "valid" yet only ever exercise the same 20% of the
parser. The FormatFuzzer paper treats coverage as the primary quality metric
(validity is just a precondition), and this doc explains how to reproduce
that kind of measurement against this repo's generated corpora.

There are three independent things you can measure, from cheapest to most
faithful to the paper:

1. **Self-coverage** of the FormatFuzzer-generated `.cpp` parser itself
   (e.g. `png.cpp`) — zero external dependencies, works today on this machine.
2. **Target-program coverage** — feed generated files into a real consumer
   (libpng, unzip, ffmpeg, ...) built with coverage instrumentation. This is
   what the paper's Tables 5–9 actually report.
3. **Coverage-guided fuzzing via AFL++** (the `uds-se/AFLplusplus` fork) —
   closes the loop so new coverage actively drives generation, and lets you
   track coverage growth over a campaign instead of a single snapshot.

---

## 1. What the paper does (arXiv:2109.11277)

FormatFuzzer, Dutra, Gopinath & Zeller, "FormatFuzzer: Effective Fuzzing of
Binary File Formats" (<https://arxiv.org/abs/2109.11277>).

- **Target programs** (Table 4) — one real-world consumer per format, e.g.
  PNG→libpng 1.6.37, JPG→libjpeg-turbo 2.0.6, GIF→gif2png 2.5.14,
  MIDI→TiMidity++ 2.14.0, MP4/AVI→FFmpeg 4.4, ZIP→UnZip 6.0, PCAP→tcpdump/
  libpcap, WAV→WavPack 5.4.0, BMP→libgdk-pixbuf 2.42.6.
- **Tool**: LCOV, reporting **line coverage** of the target program's source,
  averaged over multiple runs.
- **Two black-box coverage numbers** (Table 5, Table 6):
  - "Language coverage" — % of variable-declaration statements in the `.bt`
    template itself that got exercised (a FormatFuzzer-internal proxy metric,
    not target-program coverage).
  - Line coverage of the actual target program after generating 10,000 files
    black-box (`FFGen`) or via smart mutation (`FFMut`).
- **AFL-integrated coverage** (Table 7, Table 8, Table 9): 24-hour fuzzing
  runs (10 repetitions each) comparing plain AFL vs. `AFL+FFGen` vs.
  `AFL+FFMut`, plus a head-to-head against AFLSmart, using LCOV snapshots at
  the 24-hour mark (Table 7/8) and the 1-hour mark (Table 9). Statistical
  significance via Vargha–Delaney Â₁₂ + Wilcoxon signed-rank test.
- **Key finding worth remembering**: black-box, valid-by-construction inputs
  barely touch error-handling code in the target program (Section 7.5) — pure
  `FFGen`/`FFMut` coverage numbers plateau below what AFL-integrated modes
  reach, because AFL contributes the *invalid* mutations that trip error
  paths. If your goal is a coverage number that's representative of "how good
  is this generator," measuring only black-box output (§3 below) will
  systematically undercount; §5's AFL integration is what actually finds the
  error-handling code.

The paper does not report branch/edge coverage, only line coverage snapshots
at fixed time budgets — worth keeping in mind if you want a more granular
number than it does.

---

## 2. Don't confuse this repo's existing "validity %" with coverage

[checkers/*.sh](../checkers/) and [fuzz_manager.py](../scripts/fuzz_manager.py)
already run generated files through real-world consumers — `identify`
(ImageMagick) for bmp/gif/jpg/png, `ffmpeg` for avi/mp4, `timidity` for midi,
`unzip` for zip, `tcpdump` for pcap, `wavpack` for wav — but only check the
process's **exit status**, not what fraction of that consumer's source ran.
`BENCHMARK_REPORT.md` and `results.csv` report a `valid_percent` column;
that's orthogonal to coverage and can't be turned into a coverage number
without rebuilding those consumers from source with instrumentation (§4).

Also note: several of these checkers wrap a *different* implementation than
the paper's Table 4 target (ImageMagick's bundled libpng/libjpeg/giflib/BMP
decoder, not standalone libpng/libjpeg-turbo/gif2png/gdk-pixbuf). If you want
numbers comparable to the paper, build the paper's exact library, not
ImageMagick.

---

## 3. Fastest path: self-coverage of the generated `.cpp` parser

This needs nothing beyond the compiler already used to build the fuzzers, and
answers "how much of the FormatFuzzer-*generated* code (e.g. `gif.cpp`,
produced by `ffcompile` from `templates/gif.bt`) does a corpus exercise?" —
useful as a quick sanity check while iterating on a `.bt` template, distinct
from target-program coverage.

`build.sh` / `Makefile.am` compile with `-O3`, which is fine for production
binaries but makes gcov's line attribution unreliable (inlining/reordering
merges lines together). Build a **separate, unoptimized, `--coverage`**
binary instead:

```bash
fmt=gif   # any template name under templates/

./ffcompile templates/$fmt.bt ${fmt}.cpp
g++ -c -I . -std=c++17 -g -O0 --coverage -Wall fuzzer.cpp -o fuzzer.cov.o
g++ -c -I . -std=c++17 -g -O0 --coverage -Wall ${fmt}.cpp -o ${fmt}.cov.o
g++ -O0 --coverage ${fmt}.cov.o fuzzer.cov.o -o ${fmt}-fuzzer-cov -lz
```

(`--coverage` is shorthand for `-fprofile-arcs -ftest-coverage` at compile
time and links in `libgcov`; it works with both `gcc` and Apple
clang/`g++` on this machine — `/usr/bin/gcov` is already present via Xcode
Command Line Tools.)

Run the corpus through the coverage build — generation and parsing are both
part of the generated code, so cover both directions:

```bash
mkdir -p /tmp/${fmt}_corpus
./${fmt}-fuzzer-cov fuzz $(for i in $(seq 1 2000); do echo /tmp/${fmt}_corpus/f$i.$fmt; done)
for f in /tmp/${fmt}_corpus/*; do ./${fmt}-fuzzer-cov parse "$f" >/dev/null 2>&1; done
```

Collect and summarize with either `gcov` directly, or `lcov`/`genhtml` for an
HTML report (`brew install lcov` — not installed on this machine yet):

```bash
gcov -b ${fmt}.cov.o ${fmt}.cpp    # quick per-line %, writes *.gcov next to the source

# or, for an HTML report:
lcov --capture --directory . --base-directory . --output-file ${fmt}_self.info \
     --include "*/${fmt}.cpp"
genhtml ${fmt}_self.info --output-directory coverage_html_${fmt}
open coverage_html_${fmt}/index.html
```

Caveat: this measures coverage of FormatFuzzer's *generated* C++, which is a
mechanical translation of the `.bt` template — it is **not** the same as the
paper's "language coverage" metric (which counts covered `.bt` variable
declarations directly), and it is **not** target-program coverage (§4). It's
a cheap proxy for "did this corpus exercise every branch the template can
produce," useful mainly for template debugging.

---

## 4. The methodology that matters: target-program coverage

This is what the paper actually reports in Tables 5–9. General recipe:

1. Get the source of a real consumer for the format (ideally the paper's
   Table 4 program, or whatever `checkers/<fmt>.sh` already shells out to, if
   you can get *its* source rather than a prebuilt/Homebrew binary — you
   cannot gcov a binary you didn't compile yourself).
2. Build it with coverage instrumentation: `CFLAGS="--coverage -O0 -g"
   CXXFLAGS="--coverage -O0 -g" LDFLAGS="--coverage"` (name varies per build
   system — configure/make, cmake, meson all support this pattern).
3. Generate a corpus with this repo's fuzzer: `./gif-fuzzer fuzz
   out1.gif out2.gif ...` (or reuse whatever's already under `output/<fmt>/`
   from prior benchmark runs, if still present).
4. Feed every generated file through the instrumented target — reuse the
   exact invocation from `checkers/<fmt>.sh` / `fuzz_manager.py`'s
   `VALIDATORS` dict so you're driving the same code path the existing
   validity numbers already exercise.
5. Aggregate `.gcda` files with `lcov`/`genhtml` (or the cross-platform,
   pip-installable `gcovr` as an alternative — no Perl/Homebrew dependency).

### Worked example: ZIP → Info-ZIP UnZip 6.0

Chosen because it's the exact program in the paper's Table 4, it's what
[checkers/zip.sh](../checkers/zip.sh) already calls, and it builds in under a
minute with no dependencies.

```bash
curl -LO https://downloads.sourceforge.net/infozip/unzip60.tar.gz
tar xzf unzip60.tar.gz && cd unzip60

# Info-ZIP's makefile takes flags via a target; macosx works for both Intel/ARM Macs
make -f unix/Makefile macosx \
     LOCAL_UNZIP="--coverage -O0 -g" CFLAGS="--coverage -O0 -g -DHAVE_TERMIOS_H"
# resulting instrumented binary: ./unzip
cd ..

./zip-fuzzer fuzz $(for i in $(seq 1 2000); do echo /tmp/zip_corpus/f$i.zip; done)
for f in /tmp/zip_corpus/*.zip; do
  ( cd unzip60 && yes | ./unzip -P '' -t "$f" >/dev/null 2>&1 )
done

lcov --capture --directory unzip60 --base-directory unzip60 \
     --output-file zip_target.info
genhtml zip_target.info --output-directory coverage_html_zip
open coverage_html_zip/index.html
# or a one-line summary without HTML:
lcov --summary zip_target.info
```

### Applying this to other formats

Same five steps, different source tree and driver command (lift the driver
command straight from `checkers/<fmt>.sh` / `fuzz_manager.py`'s
`VALIDATORS`). [scripts/target_coverage.py](../scripts/target_coverage.py)
automates exactly this for one format at a time (`python3
scripts/target_coverage.py <format>`, 10,000 files by default, writes to
`coverage_results/<format>/`) — build-tested end-to-end for `zip`, `gif`
(via giflib, substituting the paper's hard-to-fetch gif2png), `jpg`, `png`,
`midi`, `wav`, `pcap`, and `bmp`; only `mp4`/`avi` (FFmpeg) remain
best-effort/not build-tested — see
[target_coverage_all_formats.md](target_coverage_all_formats.md) for the
per-format verification notes and worked results. See
[target_coverage_zip_unzip.md](target_coverage_zip_unzip.md) for the manual
walkthrough this script automates.

| Template | Paper's target (Table 4) | Source | Driver command basis |
|---|---|---|---|
| `zip` | UnZip 6.0 | sourceforge.net/projects/infozip | [checkers/zip.sh](../checkers/zip.sh) |
| `png` | libpng 1.6.37 | github.com/glennrp/libpng (`pngtest`/`contrib/libtests`) | [checkers/png.sh](../checkers/png.sh) targets ImageMagick, not libpng directly — you'll need libpng's own test driver instead |
| `jpg` | libjpeg-turbo 2.0.6 | github.com/libjpeg-turbo/libjpeg-turbo (`djpeg`) | [checkers/jpg.sh](../checkers/jpg.sh) has a commented-out `djpeg` line — use that |
| `gif` | gif2png 2.5.14 | sourceforge.net/projects/gif2png | [checkers/gif.sh](../checkers/gif.sh) has a commented-out `gif2png` line |
| `midi` | TiMidity++ 2.14.0 | sourceforge.net/projects/timidity | [checkers/midi.sh](../checkers/midi.sh) |
| `mp4`/`avi` | FFmpeg 4.4 | github.com/FFmpeg/FFmpeg | [checkers/mp4.sh](../checkers/mp4.sh), [checkers/avi.sh](../checkers/avi.sh) |
| `pcap` | tcpdump/libpcap | github.com/the-tcpdump-group | [checkers/pcap.sh](../checkers/pcap.sh) |
| `wav` | WavPack 5.4.0 | github.com/dbry/WavPack | [checkers/wav.sh](../checkers/wav.sh) |
| `bmp` | libgdk-pixbuf 2.42.6 | gitlab.gnome.org/GNOME/gdk-pixbuf | [checkers/bmp.sh](../checkers/bmp.sh) targets ImageMagick, not gdk-pixbuf — building gdk-pixbuf standalone on macOS is the most involved of this list (GLib/meson dependency chain); ImageMagick's own coverage build is a workable substitute if gdk-pixbuf proves impractical |

For any of these, `FFmpeg` and `libpng`/`libjpeg-turbo` ship an `configure
--enable-coverage`/`CFLAGS=--coverage` path already; check `./configure
--help` in each source tree rather than guessing flags.

If you'd rather not hand-roll `lcov` invocations per format, `gcovr` (`pip
install gcovr`, works inside the repo's existing `venv/`) can walk a whole
build directory and emit `--html-details` or `--json-summary` in one command,
which is easier to script across all ten formats than juggling ten separate
`.info` files.

---

## 5. Closing the loop: coverage-guided fuzzing via AFL++

FormatFuzzer's README ([README.md:194-205](../README.md)) documents
integration with a FormatFuzzer-aware fork of AFL++:
<https://github.com/uds-se/AFLplusplus> (upstream AFL++:
<https://github.com/AFLplusplus/AFLplusplus>). Two modes, both driven by
pointing AFL++ at this repo's `.so` build of a format (`./build.sh gif` also
produces `gif.so`, or `make gif.so`):

- **`AFL+FFGen`**: AFL++ mutates FormatFuzzer's *decision seeds* (see
  [README.md:172-191](../README.md) — a byte sequence recording which
  parsing/generation alternative was taken at each branch point); FormatFuzzer
  turns each mutated seed into a well-formed binary file; the target program's
  actual code coverage feeds AFL's normal power schedule. This is the "AFL
  drives smart, always-valid generation" mode.
- **`AFL+FFMut`**: AFL++ mutates files directly as usual, but every input that
  finds new coverage also gets parsed by FormatFuzzer and mutated with its
  format-aware operations (smart chunk deletion/insertion/replacement/
  splicing — [README.md:172-191](../README.md)) before being re-queued. This
  is "AFL's normal loop, augmented with format-aware mutation."

Per that fork's README, both are driven by environment variables at
`afl-fuzz` invocation time — `AFL_CUSTOM_MUTATOR_LIBRARY` points at the
format's `.so`, with a mode flag (`AFL_FFGEN=1` for the seed-mutation mode)
selecting which of the two behaviors above is active. **Verify the exact
current variable names against that fork's own README before relying on
them** — it's a separate, actively-developed repo not vendored into this one,
so names may have shifted since this doc was written.

### Getting a coverage *number* out of an AFL++ campaign

AFL++'s own bitmap/"map density" is an edge-hit proxy for its scheduling
heuristics, not a human-readable line-coverage percentage — don't quote it as
if it were LCOV's number. To get an actual line-coverage figure (comparable
to §4 and to the paper's tables) out of a running or finished campaign, you
still need a target build instrumented with `--coverage` (as in §4), and then
replay the AFL queue through it:

```bash
for f in out/ffgen/queue/id:*; do
  ( cd unzip60 && yes | ./unzip -P '' -t "$f" >/dev/null 2>&1 )
done
lcov --capture --directory unzip60 --output-file zip_afl.info
lcov --summary zip_afl.info
```

Michael Rash's third-party `afl-cov` (<https://github.com/mrash/afl-cov>)
automates exactly this replay-and-lcov loop against a live campaign's
`out/queue/`, producing coverage-over-time reports instead of one endpoint
snapshot — closer to what you'd want for a paper-style coverage-vs-time
comparison across FFGen/FFMut/AFL+FFGen/AFL+FFMut. `afl-plot` (bundled with
AFL++) instead plots AFL's internal execs/paths-found metrics, which is a
different, complementary chart.

### Platform note

AFL++'s fast instrumentation (`afl-clang-fast`, `afl-clang-lto`, using
LLVM SanitizerCoverage) is developed and tested primarily on Linux. On this
machine (macOS/Darwin) `afl-fuzz`, `afl-clang-fast`, `afl-cov`, and `lcov`/
`genhtml` are **not currently installed** — only `/usr/bin/gcov` (Xcode CLT)
is present. For the AFL++ integration step specifically, building/running
inside a Linux container or VM is the path of least resistance; §3 and §4
(plain gcov/lcov) work natively on macOS once `brew install lcov` is run.

---

## 6. Checklist for this machine

Confirmed installed: `gcov` (`/usr/bin/gcov`, via Xcode CLT).
Confirmed **not** installed: `lcov`, `genhtml`, `afl-fuzz`, `afl-clang-fast`,
`afl-cov`.

```bash
brew install lcov                 # for §3 and §4
pip install gcovr                 # optional cross-platform alternative to lcov+genhtml
# AFL++ integration (§5) is best done in a Linux container:
docker run --rm -it -v "$PWD":/ff -w /ff ubuntu:22.04 bash
```

## References

- Paper: Dutra, Gopinath, Zeller. *FormatFuzzer: Effective Fuzzing of Binary
  File Formats*, arXiv:2109.11277. <https://arxiv.org/abs/2109.11277>
  (Table 4: target programs; Table 5: language coverage; Tables 6–9: line
  coverage via LCOV, black-box vs. AFL-integrated, 24h and 1h budgets;
  §7.5–7.6: methodology and the error-handling-coverage takeaway).
- AFL++ fork for FormatFuzzer integration: <https://github.com/uds-se/AFLplusplus>
- Upstream AFL++: <https://github.com/AFLplusplus/AFLplusplus>
- `afl-cov` (third-party AFL↔lcov bridge): <https://github.com/mrash/afl-cov>
- This repo's existing validity-testing infra (not coverage, see §2):
  [checkers/](../checkers/), [fuzz_manager.py](../scripts/fuzz_manager.py),
  [BENCHMARK_REPORT.md](../BENCHMARK_REPORT.md)
- Decision seeds / smart mutation, referenced in §5:
  [README.md:172-291](../README.md)
