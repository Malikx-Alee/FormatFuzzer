#!/usr/bin/env python3
"""Run a time-boxed AFL+FFMut campaign for one FormatFuzzer format and
measure real-world target-program (gcov/lcov) code coverage in periodic
batched snapshots.

Unlike scripts/target_coverage.py (which generates a fixed 10,000-file
corpus up front, then measures coverage once), this script drives AFL++'s
FormatFuzzer custom-mutator integration ("AFL+FFMut", see
docs_llm/code_coverage_of_generated_outputs.md Section 5 and the sibling
https://github.com/uds-se/AFLplusplus fork) for a fixed wall-clock budget
(default 8h), and periodically harvests whatever new files AFL's coverage
feedback has added to its queue since the last snapshot, drives just that
small batch through a *separate* gcov-instrumented copy of the same target
program, and discards the driven copies. AFL's own queue/crashes/hangs are
left untouched. Because gcov counters (.gcda files) are never reset during
a run, each snapshot's lcov capture naturally reflects cumulative coverage
so far - this keeps peak disk usage bounded to "one snapshot's delta batch"
instead of the whole run's accumulated corpus, and produces a
coverage-over-time curve as a side effect.

This is the OPTIMIZED-template variant: it fuzzes templates/<format>.bt
(built via ./build.sh <format> into <format>.so). See
target_coverage_afl_ffmut_llm.py, its thin sibling, for the templates_llm/
(pre-optimization) template variant - it imports and reuses everything in
this file.

Choose which formats to run either by editing the FORMATS list at the top of
this file, or by naming them on the command line - the CLI always wins:

    python3 scripts/target_coverage_afl_ffmut.py png
    python3 scripts/target_coverage_afl_ffmut.py png zip gif
    python3 scripts/target_coverage_afl_ffmut.py --all
    python3 scripts/target_coverage_afl_ffmut.py zip --duration 3600 --snapshot-interval 300

Multiple formats run SEQUENTIALLY, each for the full --duration, so N formats
take N * duration. One format failing does not stop the rest, and a summary
is printed at the end. To run formats concurrently instead, launch separate
copies of this script with one format each - safe, because different formats
never share an output directory. Do NOT do that for the same format across
the two variants without checking the directory-sharing notes in
run_one_format().

Output locations are the AFL_TARGETS_DIR / AFL_RUNS_DIR / TARGETS_DIR /
RESULTS_DIR constants at the top of this file, each overridable per-run with
the matching --*-dir flag.

Use --list to see supported formats.

Outputs:
    coverage_targets_afl/<format>/                   AFL-instrumented target build
    afl_runs/<format>-afl-ffmut/main/                afl-fuzz's own output (queue/,
                                                       crashes/, hangs/, fuzzer_stats, ...)
    coverage_results/<format>-afl-ffmut/snapshots/snapshot_<seconds>s/{meta.json, summary.txt}
    coverage_results/<format>-afl-ffmut/final/{<format>_target.info, html/, summary.txt, meta.json}

DEFERRED / NOT VERIFIED ON THIS MACHINE: written and code-reviewed on a Mac
without afl-fuzz/afl-clang-fast installed (only lcov/genhtml/gcov are
present). Before trusting an unattended 8h run, smoke-test on Linux with
AFL++ built first:

    python3 scripts/target_coverage_afl_ffmut.py png --duration 60 --snapshot-interval 30

Known gaps:
  - build.sh/build_new.sh hardcode a Homebrew boost include path; adjust for
    Linux before running there.
  - --cc/--cxx autodetection tries a short candidate list (afl-clang-fast,
    afl-clang, afl-cc, afl-gcc) not yet checked against this fork's actual
    build output.
  - The shell-vs-direct-argv classification (see build_target_argv) and the
    resulting AFL_SKIP_BIN_CHECK requirement are derived from reading AFL++
    source, not from a real run.
  - No cross-invocation --resume; treat a killed run as needing a fresh
    restart (its .gcda state persists, but the in-memory harvested-id
    tracking does not).
  - macOS fork() overhead means no real campaign should run on this machine
    (AFLplusplus/Makefile prints this warning itself).

Requires everything scripts/target_coverage.py requires, plus a built
AFL++ checkout (afl-fuzz, and afl-clang-fast or afl-cc) - see
https://github.com/uds-se/AFLplusplus.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Set, Tuple

import target_coverage as tc

# ---------------------------------------------------------------------------
# Configuration. Edit these to change what runs and where output lands.
# Every one of them can also be set per-run on the command line, and the CLI
# always overrides what is written here.
# ---------------------------------------------------------------------------

# Formats to fuzz when none are named on the command line. Set this to the
# ones you actually want, e.g. ["png", "gif", "zip"]. Leave it empty to be
# forced to name them explicitly each run.
#
# NOTE: formats run SEQUENTIALLY, each for the full --duration (default 8h),
# so a list of N formats takes N * duration to finish. One format failing
# does not stop the others. To run formats in parallel instead, launch
# several copies of this script with one format each - that is safe, since
# different formats never share an output directory.
# Override per-run: positional arguments, or --all for every supported format.
FORMATS: List[str] = ["png"]

# Which model's LLM-generated template set to fuzz. Only used by
# target_coverage_afl_ffmut_llm.py; ignored by this script, which fuzzes
# templates/<fmt>.bt. Must name a templates_llm/llm_<model>/ subdirectory -
# run with --list to see which exist.
# Override per-run: --llm-model
LLM_MODEL = "opus5"

# Where the AFL-instrumented target programs are built and cached.
# Override per-run: --afl-targets-dir
AFL_TARGETS_DIR = tc.REPO_ROOT / "coverage_targets_afl"

# Where afl-fuzz writes its own output (queue/, crashes/, hangs/, fuzzer_stats).
# Override per-run: --afl-runs-dir
AFL_RUNS_DIR = tc.REPO_ROOT / "afl_runs"

# Where coverage snapshots are written, one "<format>-<variant suffix>"
# subdirectory per run. This is target_coverage.py's RESULTS_DIR; setting
# --results-dir rebinds it there so both scripts agree.
# Override per-run: --results-dir
RESULTS_DIR = tc.RESULTS_DIR

# Where the gcov-instrumented measuring copies of the target programs are
# built. This is target_coverage.py's TARGETS_DIR, rebound the same way.
# Override per-run: --targets-dir
TARGETS_DIR = tc.TARGETS_DIR

_QUEUE_ID_RE = re.compile(r"^id[:_](\d+)")
_SHELL_META = re.compile(r"[|<;`]|\$\(")
_DRIVE_SUFFIX = " >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# Which template a campaign fuzzes - the only thing that differs between this
# script and target_coverage_afl_ffmut_llm.py.
#
# There are two axes. The first is optimized (templates/<fmt>.bt, built by
# build.sh) vs. llm (templates_llm/llm_<model>/<fmt>-llm.bt, built by
# build_new.sh), and that is the choice of script. The second applies only to
# the llm side: templates_llm/ holds one subdirectory per model that generated
# the templates, and the model tag is carried through every artifact and output
# directory, so opus4.7 and opus5 campaigns for the same format neither
# overwrite each other's results nor collide while running concurrently.
# ---------------------------------------------------------------------------

TEMPLATES_LLM_DIR = tc.REPO_ROOT / "templates_llm"


@dataclass(frozen=True)
class Variant:
    label: str
    suffix: str                        # afl_runs/<fmt>-<suffix>/, coverage_results/<fmt>-<suffix>/
    so_path: Callable[[str], Path]
    build_so: Callable[[str], None]


def available_llm_models() -> List[str]:
    """Model tags discoverable under templates_llm/, e.g. ['opus4.7', 'opus5'],
    taken from its llm_<model>/ subdirectory names."""
    if not TEMPLATES_LLM_DIR.is_dir():
        return []
    return sorted(p.name[len("llm_"):] for p in TEMPLATES_LLM_DIR.iterdir()
                  if p.is_dir() and p.name.startswith("llm_"))


def _build_so_optimized(fmt: str) -> None:
    so = tc.REPO_ROOT / "build" / f"{fmt}.so"
    if not so.exists():
        # Locked on the shared artifact stem: ./build.sh also writes
        # build/<fmt>-fuzzer, which target_coverage.py guards on
        # independently. See build_lock() in target_coverage.py.
        with tc.build_lock(fmt):
            if not so.exists():
                tc.log(f"{so.name} not found, building it via ./build.sh {fmt}")
                tc.run(["./build.sh", fmt], cwd=tc.REPO_ROOT)
    if not so.exists():
        tc.die(f"{so} still missing after ./build.sh {fmt} - build it manually first")


def _llm_stem(fmt: str, model: str) -> str:
    """The artifact stem build_new.sh produces for this format and model:
    'png-llm-opus5' -> build/png-llm-opus5{-fuzzer,.so}."""
    return f"{fmt}-llm-{model}"


def _build_so_llm(fmt: str, model: str) -> None:
    stem = _llm_stem(fmt, model)
    so = tc.REPO_ROOT / "build" / f"{stem}.so"
    if not so.exists():
        # Locked on the shared artifact stem: build_new.sh also writes
        # build/<stem>-fuzzer, which target_coverage_llm.py guards on
        # independently. See build_lock() in target_coverage.py.
        with tc.build_lock(stem):
            if not so.exists():
                tc.log(f"{so.name} not found, building it via "
                       f"LLM_MODEL={model} ./build_new.sh {fmt}-llm")
                # build_new.sh takes the format as its argument and the model
                # from the environment, appending the model tag to everything
                # it writes.
                tc.run(["./build_new.sh", f"{fmt}-llm"], cwd=tc.REPO_ROOT,
                       env={"LLM_MODEL": model})
    if not so.exists():
        tc.die(f"{so} still missing after LLM_MODEL={model} ./build_new.sh {fmt}-llm "
               f"- build it manually first")


OPTIMIZED = Variant(
    label="optimized (templates/<fmt>.bt)",
    suffix="afl-ffmut",
    so_path=lambda fmt: tc.REPO_ROOT / "build" / f"{fmt}.so",
    build_so=_build_so_optimized,
)


def llm_variant(model: str) -> Variant:
    """The llm Variant for one model's template set. The model tag lands in the
    suffix, so results go to coverage_results/<fmt>-llm-<model>-afl-ffmut/ and
    each model gets its own AFL run, target builds and snapshot tree."""
    available = available_llm_models()
    if available and model not in available:
        tc.die(f"unknown LLM model '{model}'\n"
               f"  available under {TEMPLATES_LLM_DIR}/: {', '.join(available)}\n"
               f"  (pass --llm-model, or edit the LLM_MODEL constant at the top of this script)")
    return Variant(
        label=f"llm/{model} (templates_llm/llm_{model}/<fmt>-llm.bt)",
        suffix=f"llm-{model}-afl-ffmut",
        so_path=lambda fmt: tc.REPO_ROOT / "build" / f"{_llm_stem(fmt, model)}.so",
        build_so=lambda fmt: _build_so_llm(fmt, model),
    )


# ---------------------------------------------------------------------------
# AFL++ toolchain / binary discovery
# ---------------------------------------------------------------------------

def find_afl_fuzz(afl_dir: Path) -> Path:
    p = afl_dir / "afl-fuzz"
    if not p.exists():
        tc.die(f"afl-fuzz not found at {p}\n"
               f"  Build AFL++ first: cd {afl_dir} && make source-only\n"
               f"  (or pass --afl-dir pointing at a built AFLplusplus checkout)")
    if not afl_supports_e(p):
        tc.die(f"{p} does not support the -e (test-case file extension) flag.\n"
               f"  Without it AFL names its test case '.cur_input' with no extension,\n"
               f"  and targets that dispatch on the filename (wavpack appends '.wav'\n"
               f"  to extensionless paths) never open the file at all - a whole\n"
               f"  campaign then measures nothing but the failed fopen().\n"
               f"  Use an AFL++ build that has -e (e.g. the uds-se/AFLplusplus fork\n"
               f"  this project targets), or remove the -e flag in launch_afl_fuzz()\n"
               f"  and accept that wav (at least) is unmeasurable.")
    return p


def afl_supports_e(afl_fuzz_bin: Path) -> bool:
    """afl-fuzz -h exits non-zero and prints its usage to stderr; we only
    care whether "-e ext" appears in it."""
    try:
        r = subprocess.run([str(afl_fuzz_bin), "-h"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return "-e ext" in (r.stdout + r.stderr)


def find_afl_compiler(afl_dir: Path, cc_override: Optional[str], cxx_override: Optional[str]) -> tc.Toolchain:
    if cc_override:
        cxx = cxx_override or cc_override.replace("clang", "clang++").replace("gcc", "g++")
        return tc.Toolchain(cc=cc_override, cxx=cxx, cflags="", ldflags="")
    candidates = [
        ("afl-clang-fast", "afl-clang-fast++"),
        ("afl-clang", "afl-clang++"),
        ("afl-cc", "afl-c++"),
        ("afl-gcc", "afl-g++"),
    ]
    for cc_name, cxx_name in candidates:
        cc_path = afl_dir / cc_name
        if cc_path.exists():
            cxx_path = afl_dir / cxx_name
            return tc.Toolchain(cc=str(cc_path),
                                 cxx=str(cxx_path) if cxx_path.exists() else str(cc_path),
                                 cflags="", ldflags="")
    tried = ", ".join(c for c, _ in candidates)
    tc.die(f"no AFL compiler found in {afl_dir} (tried: {tried})\n"
           f"  Build AFL++ first: cd {afl_dir} && make source-only\n"
           f"  (or pass --cc/--cxx explicitly)")


def find_dict(afl_dir: Path, fmt: str, explicit: Optional[str]) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            tc.die(f"--dict {p} does not exist")
        return p
    candidate = afl_dir / "dictionaries" / f"{fmt}.dict"
    return candidate if candidate.exists() else None


def default_seeds_dir(fmt: str) -> Path:
    return tc.REPO_ROOT / "testcases" / fmt


# ---------------------------------------------------------------------------
# AFL target argv construction
# ---------------------------------------------------------------------------

def build_target_argv(recipe: tc.Recipe, afl_build: tc.BuildResult) -> Tuple[List[str], bool]:
    """Returns (argv, needs_shell) - argv is what follows afl-fuzz's `--`.

    recipe.drive() returns a shell command string built for target_coverage's
    own drive_one() (which always redirects stdout/stderr itself regardless
    of what the string says - see drive_one()'s own stdout=DEVNULL). We strip
    that constant redirect suffix and either pass the remainder as direct
    argv (no shell - avoids AFL's ~20x shell-fork overhead and keeps its
    real instrumentation-signature check active as a build sanity check), or
    fall back to `sh -c` for recipes that genuinely need shell features (a
    pipe, an input redirect) - currently just zip.
    """
    cmd = recipe.drive(afl_build, Path("@@"))
    if not cmd.endswith(_DRIVE_SUFFIX):
        tc.die(f"expected recipe.drive() to end with {_DRIVE_SUFFIX!r}, got: {cmd!r} "
               f"(a drive_*() body changed shape - update build_target_argv())")
    cmd = cmd[: -len(_DRIVE_SUFFIX)]

    if _SHELL_META.search(cmd):
        wrapped = f"cd {shlex.quote(str(afl_build.run_cwd))} && {cmd}"
        return ["/bin/sh", "-c", wrapped], True

    parts = shlex.split(cmd)
    if parts and parts[0].startswith("./"):
        parts[0] = str((afl_build.run_cwd / parts[0][2:]).resolve())
    return parts, False


def launch_afl_fuzz(afl_fuzz_bin: Path, instance_name: str, seeds: Path, sync_dir: Path,
                     so_path: Path, dict_path: Optional[Path], timeout_s: int,
                     target_argv: List[str], needs_shell: bool,
                     extra_flags: List[str], mem_limit: str = "none",
                     file_ext: Optional[str] = None,
                     skip_unruly_seeds: bool = True) -> subprocess.Popen:
    # A "+" suffix on -t makes perform_dry_run() log
    # "Test case results in a timeout (skipping)" and carry on
    # (afl-fuzz-init.c, timeout_given > 1) instead of FATALing the whole
    # campaign over a single seed the target cannot process in time. Without
    # it one unruly seed out of a dozen aborts an 8h run at second zero,
    # which is never what an unattended batch wants - the other seeds are
    # still perfectly good starting points. Note -t cannot be overridden via
    # --extra-afl-flag: a second -t FATALs with "Multiple -t options not
    # supported", so this has to be built into the flag itself.
    timeout_arg = f"{timeout_s * 1000}{'+' if skip_unruly_seeds else ''}"
    args = [str(afl_fuzz_bin), "-i", str(seeds), "-o", str(sync_dir), "-M", instance_name,
            "-t", timeout_arg, "-m", str(mem_limit)]
    if file_ext:
        # -e names AFL's test-case file ".cur_input.<ext>" instead of the
        # bare ".cur_input" that @@ otherwise expands to. Not cosmetic:
        # some targets dispatch on the filename, not on content. wavpack
        # appends ".wav" to any extensionless path, so it was resolving
        # @@ -> ".cur_input" -> ".cur_input.wav", a file that does not
        # exist - it bailed at fopen() without decoding a single byte, on
        # every exec of an entire campaign. -e keeps AFL's @@ substitution
        # intact (unlike -f, which sets out_file early and so skips the
        # detect_file_args() call entirely, leaving a literal "@@" in
        # argv). This also matches the plain-generation path, which has
        # always named its corpus files "f<N>.<ext>".
        args += ["-e", file_ext]
    if dict_path:
        args += ["-x", str(dict_path)]
    args += list(extra_flags)
    args += ["--", *target_argv]

    env = os.environ.copy()
    env["AFL_CUSTOM_MUTATOR_LIBRARY"] = str(so_path)
    if needs_shell:
        # /bin/sh isn't instrumented, so AFL++'s check_binary() would
        # otherwise FATAL("No instrumentation detected") before starting.
        env["AFL_SKIP_BIN_CHECK"] = "1"
    if sys.platform == "darwin":
        # check_crash_handling() (afl-fuzz-init.c, __APPLE__-gated) FATALs
        # unless this is set, because macOS forwards crashes to
        # ReportCrash instead of letting waitpid() see them directly. A
        # no-op on Linux, where the check doesn't exist.
        env["AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES"] = "1"
    else:
        # check_cpu_governor() (afl-fuzz-init.c, __linux__-gated) FATALs on
        # an on-demand/powersave scaling governor unless this is set;
        # switching the governor to "performance" needs root, which this
        # script shouldn't assume it has. A no-op where the check doesn't
        # exist (e.g. macOS).
        env["AFL_SKIP_CPUFREQ"] = "1"

    tc.log("$ " + " ".join(args))
    return subprocess.Popen(args, cwd=tc.REPO_ROOT, env=env, start_new_session=True)


# ---------------------------------------------------------------------------
# Queue harvesting
# ---------------------------------------------------------------------------

def queue_id(p: Path) -> int:
    return int(_QUEUE_ID_RE.match(p.name).group(1))


def list_queue_files(instance_dir: Path) -> List[Path]:
    queue_dir = instance_dir / "queue"
    if not queue_dir.exists():
        return []
    return [p for p in queue_dir.iterdir() if p.is_file() and _QUEUE_ID_RE.match(p.name)]


def is_stable(p: Path, settle_s: float = 0.05) -> bool:
    """Defends against harvesting a queue file mid-write. AFL's queue is
    append-only (save_if_interesting() does one open(O_CREAT|O_EXCL) +
    write + close, never touched again) so the race window is realistically
    microseconds, but this is cheap and precise: anything that fails the
    check is simply left for the next snapshot - nothing is lost."""
    try:
        s1 = p.stat().st_size
        if s1 == 0:
            return False
        time.sleep(settle_s)
        return p.stat().st_size == s1
    except FileNotFoundError:
        return False


def harvest_new_files(instance_dir: Path, seen_ids: Set[int], batch_dir: Path, ext: str) -> int:
    batch_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(list_queue_files(instance_dir), key=queue_id):
        qid = queue_id(p)
        if qid in seen_ids or not is_stable(p):
            continue
        shutil.copy(p, batch_dir / f"{p.name}.{ext}")
        seen_ids.add(qid)
        n += 1
    return n


def drive_batch(recipe: tc.Recipe, gcov_build: tc.BuildResult, batch_dir: Path, timeout: int) -> Tuple[int, int]:
    files = sorted(batch_dir.iterdir()) if batch_dir.exists() else []
    n_timeout = 0
    for f in files:
        if not tc.drive_one(recipe.drive(gcov_build, f), cwd=gcov_build.run_cwd, timeout=timeout):
            n_timeout += 1
    return len(files), n_timeout


# ---------------------------------------------------------------------------
# Coverage capture
# ---------------------------------------------------------------------------

def capture_lcov(gcov_build: tc.BuildResult, out_info: Path, html_dir: Optional[Path]) -> dict:
    empty = {"lines_pct": None, "lines_hit": None, "lines_total": None,
              "functions_pct": None, "functions_hit": None, "functions_total": None}
    partials = []
    for idx, d in enumerate(gcov_build.gcov_dirs):
        partial = out_info.parent / f"_partial_{idx}.info"
        tc.run_lcov(["lcov", "--capture", "--directory", str(d), "--base-directory", str(d),
                     "--output-file", str(partial)],
                    ["inconsistent", "inconsistent", "gcov", "gcov", "unsupported", "unsupported"],
                    cache_key="lcov_capture")
        if partial.exists():
            partials.append(partial)
    if not partials:
        return empty

    if len(partials) == 1:
        shutil.copy(partials[0], out_info)
    else:
        add_args = []
        for p in partials:
            add_args += ["--add-tracefile", str(p)]
        tc.run(["lcov", *add_args, "--output-file", str(out_info)])
    for p in partials:
        p.unlink()

    if html_dir is not None:
        tc.run_lcov(["genhtml", str(out_info), "--output-directory", str(html_dir)],
                    ["category", "category"], cache_key="genhtml")

    summary = subprocess.run(["lcov", "--summary", str(out_info)], capture_output=True, text=True)
    summary_text = summary.stdout + summary.stderr
    (out_info.parent / "summary.txt").write_text(summary_text)

    # Search the combined stream, not summary.stdout alone: this lcov's
    # "Summary coverage rate:" block prints to stderr (version/distro
    # dependent - confirmed different from the lcov this was developed
    # against, which puts it on stdout), so searching stdout only silently
    # left every meta.json's lines_pct/functions_pct etc. null despite
    # summary.txt on disk clearly containing the real numbers.
    m_lines = re.search(r"lines\.+:\s*([\d.]+)%\s*\((\d+) of (\d+) lines\)", summary_text)
    m_funcs = re.search(r"functions\.+:\s*([\d.]+)%\s*\((\d+) of (\d+) functions\)", summary_text)
    return {
        "lines_pct": float(m_lines.group(1)) if m_lines else None,
        "lines_hit": int(m_lines.group(2)) if m_lines else None,
        "lines_total": int(m_lines.group(3)) if m_lines else None,
        "functions_pct": float(m_funcs.group(1)) if m_funcs else None,
        "functions_hit": int(m_funcs.group(2)) if m_funcs else None,
        "functions_total": int(m_funcs.group(3)) if m_funcs else None,
    }


def parse_fuzzer_stats(instance_dir: Path) -> dict:
    p = instance_dir / "fuzzer_stats"
    if not p.exists():
        return {}
    stats = {}
    for line in p.read_text().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        stats[key.strip()] = value.strip()
    wanted = ["execs_done", "paths_total", "pending_total", "unique_crashes",
              "unique_hangs", "bitmap_cvg", "stability"]
    return {k: stats[k] for k in wanted if k in stats}


# ---------------------------------------------------------------------------
# CLI / orchestration
# ---------------------------------------------------------------------------

def build_arg_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    # No choices= here on purpose. With nargs="*", argparse before Python 3.9
    # validates the empty default against choices and rejects it, so simply
    # omitting the positional (to fall back to FORMATS), as --list does, fails
    # with "invalid choice: []" - see bpo-9625. select_formats() validates the
    # names itself, and does it for the FORMATS constant too, which choices=
    # never covered anyway.
    parser.add_argument("format", nargs="*", metavar="FORMAT",
                         help=f"format(s) to fuzz, from: {', '.join(sorted(tc.RECIPES))}. "
                              f"Overrides the FORMATS list at the top of this script; omit "
                              f"to use that list. Multiple formats run sequentially, each "
                              f"for the full --duration.")
    parser.add_argument("--all", action="store_true",
                         help="fuzz every supported format, ignoring FORMATS and any formats "
                              "named on the command line. Note this is len(RECIPES) * --duration "
                              "of wall-clock time.")
    parser.add_argument("--llm-model", default=None,
                         help=f"which templates_llm/llm_<model>/ template set to fuzz "
                              f"(default: {LLM_MODEL}). Only meaningful for "
                              f"target_coverage_afl_ffmut_llm.py; the optimized script "
                              f"always fuzzes templates/<fmt>.bt and ignores this.")
    parser.add_argument("--afl-targets-dir", type=Path, default=None,
                         help=f"where to build/cache AFL-instrumented targets (default: {AFL_TARGETS_DIR})")
    parser.add_argument("--afl-runs-dir", type=Path, default=None,
                         help=f"where afl-fuzz writes its own output (default: {AFL_RUNS_DIR})")
    parser.add_argument("--targets-dir", type=Path, default=None,
                         help=f"where to build/cache gcov-instrumented measuring targets "
                              f"(default: {TARGETS_DIR})")
    parser.add_argument("--results-dir", type=Path, default=None,
                         help=f"where to write coverage snapshots (default: {RESULTS_DIR})")
    parser.add_argument("--duration", type=int, default=28800,
                         help="total wall-clock budget in seconds (default 28800 = 8h)")
    parser.add_argument("--snapshot-interval", type=int, default=1800,
                         help="seconds between coverage snapshots (default 1800 = 30min)")
    parser.add_argument("--timeout", type=int, default=20,
                         help="per-file driver timeout in seconds; also used (as ms) for afl-fuzz's -t")
    parser.add_argument("--mem-limit", default="none",
                         help="afl-fuzz -m value (default: none - AFL's own recommended default for "
                              "dynamically-linked targets, whose shared-library mappings can exceed a "
                              "tight virtual-memory cap and falsely look like a fork-server crash)")
    parser.add_argument("--afl-dir", type=Path, default=tc.REPO_ROOT.parent / "AFLplusplus",
                         help="path to a built AFLplusplus checkout (default: sibling ../AFLplusplus)")
    parser.add_argument("--seeds", type=Path, default=None,
                         help="seed corpus dir (default: testcases/<format>/)")
    parser.add_argument("--dict", default=None,
                         help="AFL dictionary path (default: auto-detect <afl-dir>/dictionaries/<format>.dict)")
    parser.add_argument("--cc", default=None, help="AFL compiler override (default: autodetect in --afl-dir)")
    parser.add_argument("--cxx", default=None, help="AFL C++ compiler override")
    parser.add_argument("--rebuild", action="store_true",
                         help="re-run configure/make/cmake for both the AFL and gcov target builds")
    parser.add_argument("--purge-afl-out", action="store_true",
                         help="delete afl_runs/<name>/ after a successful final snapshot (default: keep)")
    parser.add_argument("--fresh", action="store_true",
                         help="delete afl_runs/<name>/ and coverage_results/<name>/ before starting, "
                              "if they exist. Needed to actually restart from zero: afl-fuzz itself "
                              "refuses to auto-wipe an output dir holding more than "
                              "AFLplusplus/include/config.h's OUTPUT_GRACE (25) minutes of prior "
                              "fuzzing (FATALs with 'At-risk data found') rather than silently "
                              "discard real progress - this flag is the explicit, visible opt-in to "
                              "do that deletion yourself. Also deletes the variant's template build/"
                              "<fmt>[-llm-<model>].so first, forcing build_so() to recompile it from "
                              "the current templates/<fmt>.bt (or templates_llm/llm_<model>/"
                              "<fmt>-llm.bt) instead of "
                              "reusing a stale .so left over from a previous edit. Does NOT touch "
                              "coverage_targets_afl/<fmt>-<suffix>/ (the AFL-instrumented target - safe "
                              "and worth keeping) or coverage_targets/<name>/ (the gcov target; its "
                              ".gcda counters are reset every run regardless, with or without this "
                              "flag).")
    parser.add_argument("--no-skip-unruly-seeds", action="store_true",
                         help="abort the campaign if any seed times out during afl-fuzz's dry run, "
                              "instead of the default of skipping that seed and continuing (the '+' "
                              "suffix on -t). The default keeps one slow seed out of a dozen from "
                              "killing an 8h unattended run; pass this when a timing-out seed should "
                              "be treated as a hard error worth investigating. Skipped seeds are "
                              "visible in the afl-fuzz output as 'Test case results in a timeout "
                              "(skipping)'.")
    parser.add_argument("--extra-afl-flag", action="append", default=[],
                         help="extra flag appended verbatim to the afl-fuzz argv (repeatable). Note "
                              "-t cannot be overridden this way: afl-fuzz FATALs on a second -t.")
    parser.add_argument("--list", action="store_true", help="list supported formats and exit")
    return parser


def select_formats(formats_from_cli: List[str], run_all: bool, configured: List[str]) -> List[str]:
    """Resolve which formats to run. Precedence: --all, then whatever was
    named on the command line, then the FORMATS constant at the top of the
    file. Duplicates are collapsed while preserving order, so repeating a
    format (in FORMATS or on the CLI) never runs it twice."""
    if run_all:
        return sorted(tc.RECIPES)
    chosen = list(formats_from_cli) if formats_from_cli else list(configured)
    unknown = [f for f in chosen if f not in tc.RECIPES]
    if unknown:
        tc.die(f"unsupported format(s): {', '.join(unknown)}\n"
               f"  supported: {', '.join(sorted(tc.RECIPES))}\n"
               f"  (if these came from the FORMATS list at the top of this script, fix it there)")
    return list(dict.fromkeys(chosen))


def run_one_format(variant: Variant, fmt: str, args, afl_dir: Path,
                    afl_fuzz_bin: Path, afl_toolchain: tc.Toolchain) -> dict:
    """Run one format's full campaign and return its final snapshot meta.

    Raises RuntimeError on failure rather than exiting, so a multi-format run
    can record it and carry on. afl_fuzz_bin / afl_toolchain are resolved once
    by main() and passed in, since they do not vary per format.
    """
    recipe = tc.RECIPES[fmt]
    name = f"{fmt}-{variant.suffix}"
    afl_sync_dir = AFL_RUNS_DIR / name
    afl_instance = "main"
    afl_instance_dir = afl_sync_dir / afl_instance
    results_dir = RESULTS_DIR / name
    # Variant-specific (<fmt>-<suffix>), NOT just AFL_TARGETS_DIR / fmt. This
    # used to be shared between the optimized and llm variants on the theory
    # that an AFL-instrumented binary is immutable and safe to exec from
    # several processes at once. Two things make that false:
    #
    #   1. The BUILD is not immutable. Both variants call recipe.build() on
    #      this path; launched together on a cold cache, both run ./configure
    #      and make -j4 in the same tree at the same time, clobbering each
    #      other's object files and producing a truncated or half-linked
    #      binary. AFL then fails with "Fork server handshake failed", which
    #      reads like an instrumentation problem and is very hard to trace
    #      back to a build race.
    #   2. The target RUNS with this directory as its cwd, and several targets
    #      write output there - libpng's pngtest, for instance, writes
    #      pngout.png on every single exec. Two campaigns sharing that file
    #      make each target run depend on the other process's timing, which
    #      AFL measures as instability and which quietly degrades its
    #      scheduling.
    #
    # Isolating costs one extra target build per variant (seconds for libpng,
    # minutes for FFmpeg) and the disk to hold it, in exchange for two
    # campaigns that genuinely cannot touch each other.
    afl_target_work_dir = AFL_TARGETS_DIR / name

    if args.fresh:
        for d in (afl_sync_dir, results_dir):
            if d.exists():
                tc.log(f"--fresh: deleting {d}")
                shutil.rmtree(d)
        template_so = variant.so_path(fmt)
        if template_so.exists():
            tc.log(f"--fresh: deleting {template_so} to force a clean template rebuild")
            template_so.unlink()
    # variant-specific, NOT just tc.TARGETS_DIR / fmt: the gcov copy's .gcda
    # counters accumulate for the life of a run and are never reset except
    # at process start (see the gcda.unlink() loop below), so if the
    # optimized and original variants for the same format are run
    # concurrently (as they naturally would be, launched as two separate
    # background processes) while sharing one directory, each snapshot's
    # lcov capture would silently report the POOLED coverage of both
    # processes' driven files, not either one's own - both variants'
    # coverage would converge and read identically despite AFL genuinely
    # exploring differently for each (confirmed happened: see
    # docs_llm/target_coverage_afl_ffmut_shared_gcov_bug.md). Unlike
    # afl_target_work_dir (the AFL-instrumented binary, which accumulates no
    # mutable state itself and is safe to read/exec from concurrent
    # processes), this one genuinely needs isolation per variant.
    gcov_target_work_dir = TARGETS_DIR / name

    if not recipe.verified:
        tc.log(f"WARNING: the '{fmt}' recipe ({recipe.label}) has not been build-tested end-to-end.")

    tc.log(f"variant: {variant.label}")
    variant.build_so(fmt)
    so_path = variant.so_path(fmt)

    tc.log(f"building AFL-instrumented target: {recipe.label}")
    afl_build = recipe.build(afl_target_work_dir, args.rebuild, afl_toolchain)

    tc.log(f"building gcov-instrumented target: {recipe.label}")
    gcov_build = recipe.build(gcov_target_work_dir, args.rebuild)
    for d in gcov_build.gcov_dirs:
        for gcda in d.rglob("*.gcda"):
            gcda.unlink()

    seeds = args.seeds or default_seeds_dir(fmt)
    if not seeds.exists() or not any(seeds.iterdir()):
        raise RuntimeError(
            f"seed corpus dir {seeds} is missing or empty - FFMut needs real seed files to start from")

    dict_path = find_dict(afl_dir, fmt, args.dict)
    target_argv, needs_shell = build_target_argv(recipe, afl_build)

    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "snapshots").mkdir(parents=True, exist_ok=True)
    # afl-fuzz does a single, non-recursive mkdir() on -o itself, so its
    # parent (AFL_RUNS_DIR) must already exist or it FATALs with ENOENT.
    afl_sync_dir.parent.mkdir(parents=True, exist_ok=True)

    proc = launch_afl_fuzz(afl_fuzz_bin, afl_instance, seeds, afl_sync_dir, so_path, dict_path,
                            args.timeout, target_argv, needs_shell, args.extra_afl_flag, args.mem_limit,
                            file_ext=recipe.ext,
                            skip_unruly_seeds=not args.no_skip_unruly_seeds)

    time.sleep(3)
    if proc.poll() is not None:
        raise RuntimeError(
            f"afl-fuzz exited immediately (code {proc.returncode}) - check {afl_instance_dir}/ for details "
            f"(common cause: check_binary() rejected the target; see this script's docstring)")

    # Under results_dir (variant-specific), NOT afl_target_work_dir. That
    # directory is coverage_targets_afl/<fmt>/, deliberately shared between
    # the optimized and llm variants because an AFL-instrumented binary is
    # safe to exec from several processes at once - but this harvest
    # directory is mutable state, rmtree'd and refilled every snapshot. With
    # it living there, two concurrent variants of the same format would
    # delete each other's harvested queue files mid-snapshot and drive each
    # other's inputs through their own gcov build, silently pooling coverage
    # exactly the way the shared gcov_target_work_dir did before that was
    # fixed (docs_llm/target_coverage_afl_ffmut_shared_gcov_bug.md).
    batch_dir = results_dir / "_harvest_batch"
    seen_ids: Set[int] = set()
    n_driven_total = 0
    n_timeouts_total = 0
    final_meta: dict = {}

    def do_snapshot(elapsed: int, final: bool) -> None:
        nonlocal n_driven_total, n_timeouts_total, final_meta
        if batch_dir.exists():
            shutil.rmtree(batch_dir)
        n_new = harvest_new_files(afl_instance_dir, seen_ids, batch_dir, recipe.ext)
        if n_new:
            n_driven, n_timeout = drive_batch(recipe, gcov_build, batch_dir, args.timeout)
            n_driven_total += n_driven
            n_timeouts_total += n_timeout
        if batch_dir.exists():
            shutil.rmtree(batch_dir)

        snap_dir = (results_dir / "final") if final else (results_dir / "snapshots" / f"snapshot_{elapsed:07d}s")
        snap_dir.mkdir(parents=True, exist_ok=True)
        info_path = snap_dir / f"{fmt}_target.info"
        lcov_stats = capture_lcov(gcov_build, info_path, snap_dir / "html" if final else None)
        if not final and info_path.exists():
            info_path.unlink()  # snapshots keep only meta.json + summary.txt

        afl_stats = parse_fuzzer_stats(afl_instance_dir)
        meta = {
            "format": fmt,
            "variant": variant.label,
            "target_label": recipe.label,
            "elapsed_seconds": elapsed,
            "final": final,
            "cumulative_files_driven": n_driven_total,
            "cumulative_driver_timeouts": n_timeouts_total,
            "timestamp": datetime.now().isoformat(),
            **lcov_stats,
            "afl": afl_stats,
        }
        (snap_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        if final:
            final_meta = meta
        tc.log(f"snapshot @ {elapsed}s: {n_driven_total} files driven cumulative, "
                f"lines {lcov_stats.get('lines_pct')}%, afl execs_done {afl_stats.get('execs_done')}")

    try:
        start = time.time()
        deadline = start + args.duration
        next_boundary = start + args.snapshot_interval
        while True:
            now = time.time()
            if now >= deadline:
                break
            sleep_for = max(0.0, min(next_boundary, deadline) - now)
            if sleep_for > 0:
                time.sleep(sleep_for)
            if proc.poll() is not None:
                tc.log(f"afl-fuzz exited early (code {proc.returncode}) - stopping")
                break
            do_snapshot(int(time.time() - start), final=False)
            next_boundary += args.snapshot_interval
    finally:
        tc.log("stopping afl-fuzz (SIGINT)...")
        try:
            os.killpg(proc.pid, signal.SIGINT)
        except ProcessLookupError:
            pass
        for _ in range(20):
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        else:
            tc.log("afl-fuzz did not exit after SIGINT, sending SIGKILL")
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()

        do_snapshot(int(time.time() - start), final=True)
        if batch_dir.exists():
            shutil.rmtree(batch_dir, ignore_errors=True)
        if args.purge_afl_out:
            shutil.rmtree(afl_sync_dir, ignore_errors=True)

    tc.log(f"done: {results_dir}/ (snapshots/, final/)")
    return final_meta


def optimized_variant_for(args) -> Variant:
    """Variant factory for this script: always the optimized templates/."""
    return OPTIMIZED


def llm_variant_for(args) -> Variant:
    """Variant factory for target_coverage_afl_ffmut_llm.py: the llm template
    set for whichever model --llm-model (or the LLM_MODEL constant) selects."""
    return llm_variant(args.llm_model or LLM_MODEL)


def main(make_variant: Callable[[argparse.Namespace], Variant], argv=None) -> None:
    """make_variant is a factory rather than a Variant because the llm side's
    identity depends on --llm-model, which is not known until args are parsed."""
    global AFL_TARGETS_DIR, AFL_RUNS_DIR, RESULTS_DIR, TARGETS_DIR
    parser = build_arg_parser(
        "Run time-boxed AFL+FFMut coverage campaigns for one or more FormatFuzzer formats.\n"
        "See this script's module docstring for full design details and known gaps.")
    args = parser.parse_args(argv)

    if args.afl_targets_dir:
        AFL_TARGETS_DIR = args.afl_targets_dir.resolve()
    if args.afl_runs_dir:
        AFL_RUNS_DIR = args.afl_runs_dir.resolve()
    if args.results_dir:
        RESULTS_DIR = args.results_dir.resolve()
    if args.targets_dir:
        TARGETS_DIR = args.targets_dir.resolve()

    if args.list:
        tc.list_formats()
        models = available_llm_models()
        print(f"\nLLM template sets under {TEMPLATES_LLM_DIR}/: "
              f"{', '.join(models) if models else '(none found)'}")
        print(f"current --llm-model default: {LLM_MODEL}")
        sys.exit(0)

    # Resolved before any work: an unknown --llm-model should fail immediately,
    # not after the first target build.
    variant = make_variant(args)

    formats = select_formats(args.format, args.all, FORMATS)
    if not formats:
        tc.list_formats()
        tc.die("no formats selected - name one or more above on the command line, pass --all, "
               "or set the FORMATS list at the top of this script")

    # Resolved once: neither depends on the format, and failing here should
    # abort everything rather than be recorded as a per-format failure N times.
    afl_dir = args.afl_dir.resolve()
    afl_fuzz_bin = find_afl_fuzz(afl_dir)
    afl_toolchain = find_afl_compiler(afl_dir, args.cc, args.cxx)

    total_hours = len(formats) * args.duration / 3600.0
    tc.log(f"variant: {variant.label}")
    tc.log(f"formats ({len(formats)}): {', '.join(formats)}")
    tc.log(f"duration: {args.duration}s each, sequentially - about {total_hours:.1f}h total")
    tc.log(f"afl targets dir: {AFL_TARGETS_DIR}")
    tc.log(f"afl runs dir:    {AFL_RUNS_DIR}")
    tc.log(f"gcov targets dir:{TARGETS_DIR}")
    tc.log(f"results dir:     {RESULTS_DIR}")

    outcomes: List[tuple] = []
    for i, fmt in enumerate(formats, 1):
        tc.log(f"===== [{i}/{len(formats)}] {fmt}-{variant.suffix} =====")
        try:
            meta = run_one_format(variant, fmt, args, afl_dir, afl_fuzz_bin, afl_toolchain)
            outcomes.append((fmt, meta, None))
        except RuntimeError as e:
            tc.log(f"ERROR: '{fmt}' failed: {e}")
            outcomes.append((fmt, None, str(e)))
        except SystemExit as e:
            # Helpers in target_coverage.py signal fatal errors with tc.die(),
            # i.e. SystemExit. That is right for a single-format run, but in a
            # batch it must be demoted to a per-format failure so the remaining
            # formats still get their turn.
            outcomes.append((fmt, None, f"fatal error in a helper (exit {e.code})"))
            tc.log(f"ERROR: '{fmt}' aborted (exit {e.code}) - continuing with the next format")

    print()
    tc.log(f"summary ({sum(1 for _, m, _ in outcomes if m)}/{len(outcomes)} succeeded):")
    for fmt, meta, err in outcomes:
        if meta:
            print(f"  {fmt:<6} lines {meta.get('lines_pct')}%  "
                  f"execs {meta.get('afl', {}).get('execs_done')}  "
                  f"-> {RESULTS_DIR / f'{fmt}-{variant.suffix}'}")
        else:
            print(f"  {fmt:<6} FAILED: {err}")
    sys.exit(0 if all(m for _, m, _ in outcomes) else 1)


if __name__ == "__main__":
    main(optimized_variant_for)
