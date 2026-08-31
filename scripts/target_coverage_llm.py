#!/usr/bin/env python3
"""Measure target-program code coverage for one format, using the ORIGINAL
(pre-optimization) 010 Editor template instead of this repo's FormatFuzzer-
tuned one.

This is a variant of scripts/target_coverage.py that swaps which fuzzer
binary drives the corpus:
  - target_coverage.py     builds `<format>-fuzzer`      via ./build.sh
                            (source: templates/<format>.bt - hand-optimized
                            for generation, per README's "Creating and
                            Customizing Binary Templates")
  - target_coverage_llm.py builds `<format>-orig-fuzzer`  via ./build_new.sh
                            (source: templates_originals_llm/<format>-orig.bt
                            - the untouched original template)

Same real-world target program, build system, and drive command per format
either way (both scripts share the RECIPES below) - only the corpus-
generating fuzzer differs. Running both for the same format and comparing
coverage_results/<format>/ vs coverage_results/<format>-orig/ answers "does
FormatFuzzer's template optimization actually improve target-program
coverage, not just validity%?" (this repo's existing BENCHMARK_REPORT.md /
benchmark_all.py already runs this original-vs-optimized comparison for
validity% - this is the code-coverage equivalent).

Run once per format - re-run manually for each one you want:

    python3 scripts/target_coverage_llm.py zip
    python3 scripts/target_coverage_llm.py png
    ...

Use --list to see all supported formats (and which recipes are build-tested
vs. best-effort - identical list to target_coverage.py, since the target
program per format is unchanged).

Outputs land in coverage_results/<format>-orig/ (distinct from
target_coverage.py's coverage_results/<format>/, so both can coexist):
    coverage_results/<format>-orig/<format>_target.info   lcov trace file
    coverage_results/<format>-orig/html/index.html         HTML report
    coverage_results/<format>-orig/summary.txt             lcov --summary text
    coverage_results/<format>-orig/meta.json               machine-readable summary

The target program's build (e.g. libpng, unzip) is cached under
coverage_targets/<format>/ - the SAME directory target_coverage.py uses,
deliberately shared, since it's the identical real-world library regardless
of which FormatFuzzer template produced the corpus driving it. This avoids
rebuilding e.g. FFmpeg or gdk-pixbuf twice. Only run target_coverage.py and
target_coverage_llm.py for the same format truly concurrently and you could
race on that shared build/corpus directory - sequential runs (the intended
usage) are unaffected either order.

Requires: curl, tar, make, a C compiler, cmake (for a few recipes), lcov +
genhtml (`brew install lcov` on macOS), git (for the bmp/gdk-pixbuf recipe).
"""
import argparse
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGETS_DIR = REPO_ROOT / "coverage_targets"
RESULTS_DIR = REPO_ROOT / "coverage_results"

COVERAGE_CFLAGS = "-O0 -g --coverage"
COVERAGE_LDFLAGS = "--coverage"


def log(msg: str) -> None:
    print(f"[target_coverage_llm] {msg}", flush=True)


def die(msg: str) -> None:
    print(f"[target_coverage_llm] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def run(cmd, cwd=None, check=True):
    """Run cmd (list or shell string) with output streamed live."""
    shell = isinstance(cmd, str)
    printable = cmd if shell else " ".join(cmd)
    log(f"$ {printable}" + (f"   (cwd={cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed (exit {result.returncode}): {printable}")
    return result


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        log(f"already downloaded: {dest.name}")
        return
    run(["curl", "-L", "--fail", "-o", str(dest), url])


def extract(archive: Path, dest_dir: Path) -> Path:
    """Extract archive into dest_dir and return the newly created top-level dir."""
    before = {p.name for p in dest_dir.iterdir()}
    run(["tar", "xf", str(archive), "-C", str(dest_dir)])
    after = {p.name for p in dest_dir.iterdir()}
    new_dirs = [dest_dir / n for n in (after - before) if (dest_dir / n).is_dir()]
    if not new_dirs:
        raise RuntimeError(f"extracting {archive} produced no new directory in {dest_dir}")
    return new_dirs[0]


def ensure_extracted(work_dir: Path, url: str, archive_name: str, expected_dir: Path) -> None:
    """Download+extract url into work_dir if expected_dir doesn't exist yet."""
    if expected_dir.exists():
        return
    work_dir.mkdir(parents=True, exist_ok=True)
    archive = work_dir / archive_name
    download(url, archive)
    extracted = extract(archive, work_dir)
    if extracted != expected_dir:
        extracted.rename(expected_dir)


def marker(build_dir: Path) -> Path:
    return build_dir / ".coverage_build_ok"


def already_built(build_dir: Path, force: bool) -> bool:
    return (not force) and marker(build_dir).exists()


def mark_built(build_dir: Path) -> None:
    marker(build_dir).write_text(datetime.now().isoformat())


def find_brew_build_aux(name: str) -> Optional[Path]:
    """Locate a Homebrew-bundled config.sub/config.guess (autoconf/libtool
    ship current copies; some older release tarballs bundle ones too old to
    recognize arm64/newer macOS build triples)."""
    for base in (Path("/opt/homebrew/Cellar"), Path("/usr/local/Cellar")):
        matches = sorted(base.glob(f"*/*/share/*/build-aux/{name}"))
        if matches:
            return matches[-1]
    return None


def fix_config_sub(src_dir: Path) -> None:
    for name, brew_src in (
        ("config.sub", find_brew_build_aux("config.sub")),
        ("config.guess", find_brew_build_aux("config.guess")),
    ):
        if not brew_src:
            continue
        for target in src_dir.rglob(name):
            shutil.copy(brew_src, target)
            os.chmod(target, 0o755)


def drive_one(cmd: str, cwd: Path, timeout: int) -> bool:
    """Run one shell driver command against one generated file. A non-zero
    exit code is expected and fine (fuzzed input often isn't valid) - only a
    timeout is treated as noteworthy, and it kills the whole process group
    (a plain subprocess timeout only kills the shell, not children it spawned
    - see docs_llm/identify_validator_resource_exhaustion.md for why that
    matters)."""
    proc = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        proc.wait(timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        return False


@dataclass
class BuildResult:
    gcov_dirs: List[Path]   # directories to `lcov --capture --directory` over
    run_cwd: Path            # cwd to invoke the driver command from


@dataclass
class Recipe:
    ext: str
    label: str
    verified: bool
    build: Callable[[Path, bool], BuildResult]
    drive: Callable[[BuildResult, Path], str]


# ---------------------------------------------------------------------------
# zip -> Info-ZIP UnZip 6.0  (verified working; matches checkers/zip.sh)
# ---------------------------------------------------------------------------

def build_zip(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "unzip60"
    ensure_extracted(work_dir, "https://downloads.sourceforge.net/infozip/unzip60.tar.gz",
                      "unzip60.tar.gz", src)
    if not already_built(src, force):
        run(f'make -f unix/Makefile unzips CFLAGS="{COVERAGE_CFLAGS} -Wall -DBSD" '
            f'LF2="{COVERAGE_LDFLAGS}"', cwd=src)
        mark_built(src)
    return BuildResult([src], src)


def drive_zip(build: BuildResult, f: Path) -> str:
    return f"yes | ./unzip -P '' -t '{f}' >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# gif -> giflib 5.2.2 (gif2rgb)
# Substitutes the paper's gif2png (hard to fetch, largely abandoned) with
# giflib, the standard actively-maintained GIF decoder library.
# ---------------------------------------------------------------------------

def build_gif(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "giflib-5.2.2"
    ensure_extracted(work_dir, "https://sourceforge.net/projects/giflib/files/giflib-5.2.2.tar.gz/download",
                      "giflib.tar.gz", src)
    if not already_built(src, force):
        run(f'make CFLAGS="-std=gnu99 -fPIC {COVERAGE_CFLAGS} -Wall" '
            f'LDFLAGS="{COVERAGE_LDFLAGS}" gif2rgb', cwd=src)
        mark_built(src)
    return BuildResult([src], src)


def drive_gif(build: BuildResult, f: Path) -> str:
    return f"./gif2rgb -o /dev/null '{f}' >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# jpg -> libjpeg-turbo 3.2.0 (djpeg-static)
# ---------------------------------------------------------------------------

def build_jpg(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "libjpeg-turbo-3.2.0"
    ensure_extracted(work_dir, "https://github.com/libjpeg-turbo/libjpeg-turbo/archive/refs/tags/3.2.0.tar.gz",
                      "libjpeg-turbo.tar.gz", src)
    build_dir = src / "build"
    if not already_built(build_dir, force):
        build_dir.mkdir(exist_ok=True)
        run(f'cmake -G "Unix Makefiles" -DCMAKE_C_FLAGS="{COVERAGE_CFLAGS}" '
            f'-DCMAKE_EXE_LINKER_FLAGS="{COVERAGE_LDFLAGS}" -DENABLE_SHARED=FALSE '
            f'-DWITH_SIMD=FALSE ..', cwd=build_dir)
        run("make -j4 djpeg-static", cwd=build_dir)
        mark_built(build_dir)
    return BuildResult([build_dir], build_dir)


def drive_jpg(build: BuildResult, f: Path) -> str:
    return f"./djpeg-static '{f}' >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# png -> libpng 1.6.57 (pngtest -m)
# ---------------------------------------------------------------------------

def build_png(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "libpng-1.6.57"
    ensure_extracted(work_dir, "https://github.com/pnggroup/libpng/archive/refs/tags/v1.6.57.tar.gz",
                      "libpng.tar.gz", src)
    if not already_built(src, force):
        run(f'./configure CFLAGS="{COVERAGE_CFLAGS}" LDFLAGS="{COVERAGE_LDFLAGS}" --disable-shared',
            cwd=src)
        run("make pngtest", cwd=src)
        mark_built(src)
    return BuildResult([src], src)


def drive_png(build: BuildResult, f: Path) -> str:
    return f"./pngtest -m '{f}' >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# midi -> TiMidity++ 2.15.0
# 2018-era autotools project; needs a fixed config.sub/config.guess (see
# fix_config_sub) and -Wno-implicit-function-declaration to compile on a
# modern clang. No instrument patch set is configured, so playmidi.c/
# synthesis coverage is lower than a full install with real patches would
# give - readmidi.c (parsing) coverage is unaffected.
# ---------------------------------------------------------------------------

def build_midi(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "TiMidity++-2.15.0"
    ensure_extracted(
        work_dir,
        "https://downloads.sourceforge.net/project/timidity/TiMidity%2B%2B/TiMidity%2B%2B-2.15.0/TiMidity%2B%2B-2.15.0.tar.gz",
        "timidity.tar.gz", src)
    timidity_dir = src / "timidity"
    if not already_built(timidity_dir, force):
        fix_config_sub(src)
        run(f'./configure CFLAGS="{COVERAGE_CFLAGS} -Wno-implicit-function-declaration -Wno-implicit-int" '
            f'LDFLAGS="{COVERAGE_LDFLAGS}" --without-x --disable-network --disable-alsaseq '
            f'--disable-server --build={platform.machine()}-apple-darwin', cwd=src)
        run("make -j4", cwd=src)
        mark_built(timidity_dir)
    cfg = timidity_dir / "dummy.cfg"
    if not cfg.exists():
        cfg.write_text("\n")
    return BuildResult([timidity_dir], timidity_dir)


def drive_midi(build: BuildResult, f: Path) -> str:
    return f"./timidity -c dummy.cfg - -Ol -o /dev/null < '{f}' >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# wav -> WavPack 5.9.0
# ---------------------------------------------------------------------------

def build_wav(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "WavPack-5.9.0"
    ensure_extracted(work_dir, "https://github.com/dbry/WavPack/archive/refs/tags/5.9.0.tar.gz",
                      "wavpack.tar.gz", src)
    build_dir = src / "build"
    if not already_built(build_dir, force):
        build_dir.mkdir(exist_ok=True)
        run(f'cmake -DCMAKE_C_FLAGS="{COVERAGE_CFLAGS}" -DCMAKE_EXE_LINKER_FLAGS="{COVERAGE_LDFLAGS}" '
            f'-DBUILD_SHARED_LIBS=OFF ..', cwd=build_dir)
        run("make -j4 wavpackapp", cwd=build_dir)
        mark_built(build_dir)
    return BuildResult([build_dir], build_dir)


def drive_wav(build: BuildResult, f: Path) -> str:
    # PID-suffixed, not a fixed name: concurrent processes would otherwise
    # race on writing the same /tmp file.
    return f"./wavpack -y '{f}' -o /tmp/target_coverage_wav_out_{os.getpid()}.wv >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# pcap -> tcpdump 4.99.6 + libpcap 1.10.6 (two-stage: libpcap built+installed
# to a local prefix first, then tcpdump built against that local libpcap so
# both binaries' coverage is instrumented, matching the paper's
# "tcpdump/libpcap" combined target).
# ---------------------------------------------------------------------------

def build_pcap(work_dir: Path, force: bool) -> BuildResult:
    libpcap_src = work_dir / "libpcap-libpcap-1.10.6"
    tcpdump_src = work_dir / "tcpdump-tcpdump-4.99.6"
    local_prefix = work_dir / "local"
    libpcap_build = libpcap_src / "build"
    tcpdump_build = tcpdump_src / "build"

    ensure_extracted(work_dir, "https://github.com/the-tcpdump-group/libpcap/archive/refs/tags/libpcap-1.10.6.tar.gz",
                      "libpcap.tar.gz", libpcap_src)
    ensure_extracted(work_dir, "https://github.com/the-tcpdump-group/tcpdump/archive/refs/tags/tcpdump-4.99.6.tar.gz",
                      "tcpdump.tar.gz", tcpdump_src)

    if not already_built(tcpdump_build, force):
        # Disable every optional hardware-capture backend and optional
        # network-library integration libpcap's cmake auto-detects
        # (RDMA/InfiniBand, Endace DAG, Septel, Myricom SNF, Riverbed
        # TurboCap, netmap, Linux usbmon, libnl-based netlink queries,
        # rpcap remote-capture) in addition to Bluetooth/D-Bus. None of
        # these are needed for replaying .pcap *files* (our only use case:
        # `tcpdump -nr <file>`), and any of them auto-enabling because the
        # relevant hardware/dev library happens to be installed (seen in
        # practice on an HPC cluster: libibverbs enabled RDMA, then
        # libnl-genl-3 enabled netlink support - neither present on a Mac)
        # breaks the final tcpdump link with "undefined reference": the
        # object file referencing the library's symbols gets compiled into
        # libpcap.a, but tcpdump's own link step is never told to link
        # against that library too. ENABLE_REMOTE is disabled pre-emptively
        # for the same reason, not because it's failed yet.
        if libpcap_build.exists():
            shutil.rmtree(libpcap_build)  # clear any stale cache/objects from a build with different DISABLE_* flags
        libpcap_build.mkdir(parents=True, exist_ok=True)
        run(f'cmake -DCMAKE_C_FLAGS="{COVERAGE_CFLAGS}" -DCMAKE_EXE_LINKER_FLAGS="{COVERAGE_LDFLAGS}" '
            f'-DCMAKE_INSTALL_PREFIX="{local_prefix}" -DBUILD_SHARED_LIBS=OFF '
            f'-DDISABLE_DBUS=ON -DDISABLE_BLUETOOTH=ON -DDISABLE_RDMA=ON -DDISABLE_DAG=ON '
            f'-DDISABLE_SEPTEL=ON -DDISABLE_SNF=ON -DDISABLE_TC=ON -DDISABLE_NETMAP=ON '
            f'-DDISABLE_LINUX_USBMON=ON -DBUILD_WITH_LIBNL=OFF -DENABLE_REMOTE=OFF ..', cwd=libpcap_build)
        run("make -j4", cwd=libpcap_build)
        if local_prefix.exists():
            shutil.rmtree(local_prefix)  # stale install from a previous (differently-configured) libpcap build
        run("make install", cwd=libpcap_build)

        if tcpdump_build.exists():
            shutil.rmtree(tcpdump_build)
        tcpdump_build.mkdir(parents=True, exist_ok=True)
        run(f'cmake -DCMAKE_C_FLAGS="{COVERAGE_CFLAGS}" -DCMAKE_EXE_LINKER_FLAGS="{COVERAGE_LDFLAGS}" '
            f'-DCMAKE_PREFIX_PATH="{local_prefix}" ..', cwd=tcpdump_build)
        run("make -j4 tcpdump", cwd=tcpdump_build)
        mark_built(tcpdump_build)

    return BuildResult([tcpdump_build, libpcap_build], tcpdump_build)


def drive_pcap(build: BuildResult, f: Path) -> str:
    return f"./tcpdump -nr '{f}' >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# mp4 / avi -> FFmpeg 6.1 (shared build). Verified: both formats completed
# real 10,000-file runs against the `-orig` corpus - see
# docs_llm/target_coverage_results_orig.md.
# ---------------------------------------------------------------------------

def build_ffmpeg(force: bool) -> BuildResult:
    ff_dir = TARGETS_DIR / "_ffmpeg_shared"
    src = ff_dir / "ffmpeg-6.1"
    ensure_extracted(ff_dir, "https://ffmpeg.org/releases/ffmpeg-6.1.tar.xz", "ffmpeg-6.1.tar.xz", src)
    if not already_built(src, force):
        run(f'./configure --extra-cflags="{COVERAGE_CFLAGS}" --extra-ldflags="{COVERAGE_LDFLAGS}" '
            f'--disable-doc --disable-ffplay --disable-debug', cwd=src)
        run("make -j4", cwd=src)
        mark_built(src)
    return BuildResult([src], src)


def build_mp4(work_dir: Path, force: bool) -> BuildResult:
    return build_ffmpeg(force)


def build_avi(work_dir: Path, force: bool) -> BuildResult:
    return build_ffmpeg(force)


def drive_mp4(build: BuildResult, f: Path) -> str:
    # PID-suffixed for the same reason as drive_wav above.
    return f"./ffmpeg -y -i '{f}' -c:v mpeg4 -c:a copy /tmp/target_coverage_mp4_out_{os.getpid()}.mp4 >/dev/null 2>&1"


def drive_avi(build: BuildResult, f: Path) -> str:
    # PID-suffixed for the same reason as drive_wav above.
    return f"./ffmpeg -y -f avi -i '{f}' /tmp/target_coverage_avi_out_{os.getpid()}.avi >/dev/null 2>&1"


# ---------------------------------------------------------------------------
# bmp -> gdk-pixbuf (via meson, custom decode-only harness). Verified: built
# and smoke-tested, confirmed gdk-pixbuf/io-bmp.c (the actual BMP decoder) is
# compiled in and exercised (not just the generic loader dispatch code) -
# see docs_llm/target_coverage_all_formats.md.
# ---------------------------------------------------------------------------

_GDK_PIXBUF_HARNESS = """
#include <gdk-pixbuf/gdk-pixbuf.h>
int main(int argc, char **argv) {
    if (argc < 2) return 1;
    GError *error = NULL;
    GdkPixbuf *pixbuf = gdk_pixbuf_new_from_file(argv[1], &error);
    if (pixbuf) g_object_unref(pixbuf);
    if (error) g_error_free(error);
    return 0;
}
"""


def build_bmp(work_dir: Path, force: bool) -> BuildResult:
    src = work_dir / "gdk-pixbuf"
    build_dir = src / "_build"
    if not src.exists():
        work_dir.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", "--branch", "2.42.12",
             "https://gitlab.gnome.org/GNOME/gdk-pixbuf.git", str(src)])
    if not already_built(build_dir, force):
        if build_dir.exists():
            shutil.rmtree(build_dir)
        # -Dman=false: avoids requiring rst2man (python-docutils), not installed here.
        # -Dothers=enabled: gdk-pixbuf files BMP under its "others" (weakly
        # maintained) loader group in meson.build, not its own option - with
        # the more obvious-looking "-Dothers=disabled" (trying to trim
        # unrelated build surface), io-bmp.c is never even compiled and the
        # harness silently can't decode BMP at all.
        # -Dbuiltin_loaders=bmp: the default is "png,jpeg" only - without
        # explicitly listing bmp here, the BMP loader (even once compiled)
        # would only be registered as a dynamically dlopen'd module via a
        # loaders.cache we haven't set up, not linked into our static harness.
        run(["meson", "setup", "_build", "-Db_coverage=true", "-Ddefault_library=static",
             "-Dman=false", "-Dtests=false", "-Dinstalled_tests=false",
             "-Dintrospection=disabled", "-Dgtk_doc=false",
             "-Dpng=disabled", "-Djpeg=disabled", "-Dtiff=disabled", "-Dgif=disabled",
             "-Dothers=enabled", "-Dbuiltin_loaders=bmp"], cwd=src)
        run(["ninja", "-C", "_build"], cwd=src)
        harness_c = build_dir / "harness.c"
        harness_c.write_text(_GDK_PIXBUF_HARNESS)
        env = os.environ.copy()
        pc_dir = build_dir / "meson-uninstalled"
        env["PKG_CONFIG_PATH"] = f"{pc_dir}{os.pathsep}{env.get('PKG_CONFIG_PATH', '')}"
        cflags = subprocess.run(["pkg-config", "--cflags", "gdk-pixbuf-2.0"], cwd=src, env=env,
                                 capture_output=True, text=True, check=True).stdout.strip()
        libs = subprocess.run(["pkg-config", "--libs", "--static", "gdk-pixbuf-2.0"], cwd=src, env=env,
                               capture_output=True, text=True, check=True).stdout.strip()
        run(f'cc {COVERAGE_CFLAGS} {cflags} harness.c {libs} {COVERAGE_LDFLAGS} -o harness', cwd=build_dir)
        mark_built(build_dir)
    return BuildResult([build_dir], build_dir)


def drive_bmp(build: BuildResult, f: Path) -> str:
    return f"./harness '{f}' >/dev/null 2>&1"


RECIPES = {
    "zip":  Recipe("zip", "Info-ZIP UnZip 6.0",                     True,  build_zip,  drive_zip),
    "gif":  Recipe("gif", "giflib 5.2.2 (gif2rgb)",                 True,  build_gif,  drive_gif),
    "jpg":  Recipe("jpg", "libjpeg-turbo 3.2.0 (djpeg)",            True,  build_jpg,  drive_jpg),
    "png":  Recipe("png", "libpng 1.6.57 (pngtest)",                True,  build_png,  drive_png),
    "midi": Recipe("mid", "TiMidity++ 2.15.0",                      True,  build_midi, drive_midi),
    "wav":  Recipe("wav", "WavPack 5.9.0",                          True,  build_wav,  drive_wav),
    "pcap": Recipe("pcap", "tcpdump 4.99.6 + libpcap 1.10.6",       True,  build_pcap, drive_pcap),
    "mp4":  Recipe("mp4", "FFmpeg 6.1",                             True,  build_mp4,  drive_mp4),
    "avi":  Recipe("avi", "FFmpeg 6.1",                             True,  build_avi,  drive_avi),
    "bmp":  Recipe("bmp", "gdk-pixbuf 2.42.12 (custom harness)",    True,  build_bmp,  drive_bmp),
}


def list_formats() -> None:
    print(f"{'format':<6} {'ext':<5} {'status':<20} target                          fuzzer binary used")
    for name, r in sorted(RECIPES.items()):
        status = "verified" if r.verified else "best-effort/unverified"
        print(f"{name:<6} {r.ext:<5} {status:<20} {r.label:<32} {name}-orig-fuzzer")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("format", nargs="?", choices=sorted(RECIPES), help="format to measure")
    parser.add_argument("--count", type=int, default=10000, help="number of files to generate (default 10000)")
    parser.add_argument("--batch-size", type=int, default=500, help="files per fuzz-generation subprocess call")
    parser.add_argument("--timeout", type=int, default=20, help="per-file driver timeout in seconds")
    parser.add_argument("--rebuild", action="store_true", help="re-run configure/make/cmake even if already built")
    parser.add_argument("--keep-corpus", action="store_true", help="don't delete the generated corpus afterwards")
    parser.add_argument("--list", action="store_true", help="list supported formats and exit")
    args = parser.parse_args()

    if args.list or not args.format:
        list_formats()
        if not args.format:
            sys.exit(0 if args.list else 1)

    recipe = RECIPES[args.format]
    fuzzer_bin = REPO_ROOT / "build" / f"{args.format}-orig-fuzzer"
    work_dir = TARGETS_DIR / args.format
    results_dir = RESULTS_DIR / f"{args.format}-orig"
    work_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    if not recipe.verified:
        log(f"WARNING: the '{args.format}' recipe ({recipe.label}) has not been build-tested "
            f"end-to-end. It may fail - if it does, please report the exact error.")

    if not fuzzer_bin.exists():
        log(f"{fuzzer_bin.name} not found, building it via ./build_new.sh {args.format}-orig")
        run(["./build_new.sh", f"{args.format}-orig"], cwd=REPO_ROOT)
    if not fuzzer_bin.exists():
        die(f"{fuzzer_bin} still missing after ./build_new.sh {args.format}-orig - build it manually first")

    corpus_dir = work_dir / "corpus"
    if corpus_dir.exists():
        shutil.rmtree(corpus_dir)
    corpus_dir.mkdir(parents=True)
    log(f"generating {args.count} '{args.format}' files with {fuzzer_bin.name} ...")
    generated = 0
    while generated < args.count:
        n = min(args.batch_size, args.count - generated)
        files = [str(corpus_dir / f"f{generated + i}.{recipe.ext}") for i in range(n)]
        subprocess.run([str(fuzzer_bin), "fuzz", *files], cwd=REPO_ROOT,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        generated += n
        log(f"  generated {generated}/{args.count}")

    try:
        log(f"building target: {recipe.label}")
        build_result = recipe.build(work_dir, args.rebuild)
    except RuntimeError as e:
        die(f"build failed for '{args.format}' ({recipe.label}): {e}")

    for d in build_result.gcov_dirs:
        for gcda in d.rglob("*.gcda"):
            gcda.unlink()

    log(f"driving corpus through {recipe.label} ...")
    files = sorted(corpus_dir.glob(f"*.{recipe.ext}"))
    n_timeout = 0
    for i, f in enumerate(files, 1):
        cmd = recipe.drive(build_result, f)
        if not drive_one(cmd, cwd=build_result.run_cwd, timeout=args.timeout):
            n_timeout += 1
        if i % 500 == 0 or i == len(files):
            log(f"  drove {i}/{len(files)} files ({n_timeout} timeouts so far)")

    log("capturing coverage with lcov ...")
    partials = []
    for idx, d in enumerate(build_result.gcov_dirs):
        partial = results_dir / f"_partial_{idx}.info"
        r = run(["lcov", "--capture", "--directory", str(d), "--base-directory", str(d),
                 "--output-file", str(partial),
                 "--ignore-errors", "inconsistent,inconsistent,gcov,gcov,unsupported,unsupported"],
                check=False)
        if partial.exists():
            partials.append(partial)
    if not partials:
        die("lcov produced no trace file - check the build/drive steps above for errors")

    info_path = results_dir / f"{args.format}_target.info"
    if len(partials) == 1:
        shutil.copy(partials[0], info_path)
    else:
        add_args = []
        for p in partials:
            add_args += ["--add-tracefile", str(p)]
        run(["lcov", *add_args, "--output-file", str(info_path)])
    for p in partials:
        p.unlink()

    html_dir = results_dir / "html"
    run(["genhtml", str(info_path), "--output-directory", str(html_dir),
         "--ignore-errors", "category,category"], check=False)

    summary = subprocess.run(["lcov", "--summary", str(info_path)], capture_output=True, text=True)
    (results_dir / "summary.txt").write_text(summary.stdout + summary.stderr)
    print(summary.stdout)

    m_lines = re.search(r"lines\.+:\s*([\d.]+)%\s*\((\d+) of (\d+) lines\)", summary.stdout)
    m_funcs = re.search(r"functions\.+:\s*([\d.]+)%\s*\((\d+) of (\d+) functions\)", summary.stdout)
    meta = {
        "format": args.format,
        "variant": "templates_originals_llm",
        "fuzzer_binary": fuzzer_bin.name,
        "target_label": recipe.label,
        "verified_recipe": recipe.verified,
        "file_count": args.count,
        "driver_timeouts": n_timeout,
        "timestamp": datetime.now().isoformat(),
        "lines_pct": float(m_lines.group(1)) if m_lines else None,
        "lines_hit": int(m_lines.group(2)) if m_lines else None,
        "lines_total": int(m_lines.group(3)) if m_lines else None,
        "functions_pct": float(m_funcs.group(1)) if m_funcs else None,
        "functions_hit": int(m_funcs.group(2)) if m_funcs else None,
        "functions_total": int(m_funcs.group(3)) if m_funcs else None,
    }
    (results_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    log(f"done: {results_dir}/ ({info_path.name}, html/, summary.txt, meta.json)")

    if not args.keep_corpus:
        shutil.rmtree(corpus_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
