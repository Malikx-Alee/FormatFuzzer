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
target_coverage_afl_ffmut_llm.py, its thin sibling, for the original/-llm
template variant - it imports and reuses everything in this file.

Run once per format:

    python3 scripts/target_coverage_afl_ffmut.py png
    python3 scripts/target_coverage_afl_ffmut.py zip --duration 3600 --snapshot-interval 300

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

AFL_TARGETS_DIR = tc.REPO_ROOT / "coverage_targets_afl"
AFL_RUNS_DIR = tc.REPO_ROOT / "afl_runs"

_QUEUE_ID_RE = re.compile(r"^id[:_](\d+)")
_SHELL_META = re.compile(r"[|<;`]|\$\(")
_DRIVE_SUFFIX = " >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# Optimized vs. original template variant - the only thing that differs
# between this script and target_coverage_afl_ffmut_llm.py.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Variant:
    label: str
    suffix: str                        # afl_runs/<fmt>-<suffix>/, coverage_results/<fmt>-<suffix>/
    so_path: Callable[[str], Path]
    build_so: Callable[[str], None]


def _build_so_optimized(fmt: str) -> None:
    so = tc.REPO_ROOT / "build" / f"{fmt}.so"
    if not so.exists():
        tc.log(f"{so.name} not found, building it via ./build.sh {fmt}")
        tc.run(["./build.sh", fmt], cwd=tc.REPO_ROOT)
    if not so.exists():
        tc.die(f"{so} still missing after ./build.sh {fmt} - build it manually first")


def _build_so_original(fmt: str) -> None:
    orig_fmt = f"{fmt}-orig"
    so = tc.REPO_ROOT / "build" / f"{orig_fmt}.so"
    if not so.exists():
        tc.log(f"{so.name} not found, building it via ./build_new.sh {orig_fmt}")
        tc.run(["./build_new.sh", orig_fmt], cwd=tc.REPO_ROOT)
    if not so.exists():
        tc.die(f"{so} still missing after ./build_new.sh {orig_fmt} - build it manually first")


OPTIMIZED = Variant(
    label="optimized (templates/<fmt>.bt)",
    suffix="afl-ffmut",
    so_path=lambda fmt: tc.REPO_ROOT / "build" / f"{fmt}.so",
    build_so=_build_so_optimized,
)

ORIGINAL = Variant(
    label="original (templates_originals_llm/<fmt>-orig.bt)",
    suffix="orig-afl-ffmut",
    so_path=lambda fmt: tc.REPO_ROOT / "build" / f"{fmt}-orig.so",
    build_so=_build_so_original,
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
    return p


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
    fall back to `sh -c` for the two recipes (zip, midi) that genuinely need
    shell features (a pipe, an input redirect).
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
                     extra_flags: List[str], mem_limit: str = "none") -> subprocess.Popen:
    args = [str(afl_fuzz_bin), "-i", str(seeds), "-o", str(sync_dir), "-M", instance_name,
            "-t", str(timeout_s * 1000), "-m", str(mem_limit)]
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
    parser.add_argument("format", nargs="?", choices=sorted(tc.RECIPES), help="format to measure")
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
    parser.add_argument("--extra-afl-flag", action="append", default=[],
                         help="extra flag appended verbatim to the afl-fuzz argv (repeatable)")
    parser.add_argument("--list", action="store_true", help="list supported formats and exit")
    return parser


def main(variant: Variant, argv=None) -> None:
    parser = build_arg_parser(
        f"Run a time-boxed AFL+FFMut coverage campaign for one FormatFuzzer format.\n"
        f"Variant: {variant.label}\n"
        f"See this script's module docstring for full design details and known gaps.")
    args = parser.parse_args(argv)

    if args.list or not args.format:
        tc.list_formats()
        if not args.format:
            sys.exit(0 if args.list else 1)

    fmt = args.format
    recipe = tc.RECIPES[fmt]
    name = f"{fmt}-{variant.suffix}"
    afl_sync_dir = AFL_RUNS_DIR / name
    afl_instance = "main"
    afl_instance_dir = afl_sync_dir / afl_instance
    results_dir = tc.RESULTS_DIR / name
    afl_target_work_dir = AFL_TARGETS_DIR / fmt
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
    gcov_target_work_dir = tc.TARGETS_DIR / name
    afl_dir = args.afl_dir.resolve()

    if not recipe.verified:
        tc.log(f"WARNING: the '{fmt}' recipe ({recipe.label}) has not been build-tested end-to-end.")

    afl_fuzz_bin = find_afl_fuzz(afl_dir)
    afl_toolchain = find_afl_compiler(afl_dir, args.cc, args.cxx)

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
        tc.die(f"seed corpus dir {seeds} is missing or empty - FFMut needs real seed files to start from")

    dict_path = find_dict(afl_dir, fmt, args.dict)
    target_argv, needs_shell = build_target_argv(recipe, afl_build)

    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "snapshots").mkdir(parents=True, exist_ok=True)
    # afl-fuzz does a single, non-recursive mkdir() on -o itself, so its
    # parent (AFL_RUNS_DIR) must already exist or it FATALs with ENOENT.
    afl_sync_dir.parent.mkdir(parents=True, exist_ok=True)

    proc = launch_afl_fuzz(afl_fuzz_bin, afl_instance, seeds, afl_sync_dir, so_path, dict_path,
                            args.timeout, target_argv, needs_shell, args.extra_afl_flag, args.mem_limit)

    time.sleep(3)
    if proc.poll() is not None:
        tc.die(f"afl-fuzz exited immediately (code {proc.returncode}) - check {afl_instance_dir}/ for details "
               f"(common cause: check_binary() rejected the target; see this script's docstring)")

    batch_dir = afl_target_work_dir / "_harvest_batch"
    seen_ids: Set[int] = set()
    n_driven_total = 0
    n_timeouts_total = 0

    def do_snapshot(elapsed: int, final: bool) -> None:
        nonlocal n_driven_total, n_timeouts_total
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


if __name__ == "__main__":
    main(OPTIMIZED)
