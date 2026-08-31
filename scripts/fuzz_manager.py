#!/usr/bin/env python3
"""Drive a FormatFuzzer binary, generate files, validate with external tools,
and log valid/invalid counts to results.csv.

Generation timing is no longer tracked here - use the fuzzer's own
`<fuzzer> benchmark` command for that. This script only measures validation
time, and cleans up all generated/valid/invalid files after logging results.

Usage:
    python3 fuzz_manager.py [FILETYPE] [COUNT]

If FILETYPE or COUNT are omitted, the defaults configured below are used.

Examples:
    python3 fuzz_manager.py                     # use defaults
    python3 fuzz_manager.py tif-llm             # override filetype only
    python3 fuzz_manager.py tif-llm 100         # override both
    python3 fuzz_manager.py tif-llm 100 --evil-bit  # enable evil bit
"""

import argparse
import csv
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

# ---------------------------------------------------------------------------
# Configuration. Edit these to run the script without CLI arguments.
# CLI arguments, when supplied, always override these values.
# ---------------------------------------------------------------------------
DEFAULT_FILETYPE = "png-llm"
DEFAULT_COUNT = 10000
DEFAULT_WORKDIR = "."
DEFAULT_EVIL_BIT = False  # Set to True to enable evil bit by default
RESULTS_CSV = "results.csv"

# Validator commands from checker scripts - same validation as used in the project
# "{file}" is replaced with the candidate file path
VALIDATORS = {
    # From checkers/*.sh scripts - using same validation methods
    "avi":  "ffmpeg -y -f avi -i - output.avi <{file} 2>/dev/null",
    # -limit flags cap ImageMagick's memory/disk/time so a malformed image
    # (e.g. a corrupted width/height) can't make identify balloon a temp
    # file to tens of GB and take the whole machine down with it.
    # No -verbose: on this ImageMagick build, -verbose forces a full pixel
    # decode that applies a stricter zlib/CRC check than plain `identify` or
    # real-world decoders (verified against Apple ImageIO/Preview), causing
    # false-negative "invalid" results on files that actually decode fine.
    # Plain identify's exit code alone is the validity signal.
    "bmp":  "identify -limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10 - <{file} >/dev/null 2>&1",
    "gif":  "identify -limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10 - <{file} >/dev/null 2>&1",
    "jpg":  "identify -limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10 - <{file} >/dev/null 2>&1",
    "midi": "! timidity - -Ol -o /dev/null <{file} 2>/dev/null | grep -q ^-:",
    # mpg321 crashes (SIGABRT) on macOS after successfully decoding, even for
    # valid files, so it can't be used as a validity check here; ffprobe is
    # used instead (mpg321 is still the reference in checkers/mp3.sh).
    "mp3":  "ffprobe -v error -f mp3 -i - <{file} >/dev/null 2>&1",
    "mp4":  "ffmpeg -y -i - -c:v mpeg4 -c:a copy output.mp4 <{file} 2>/dev/null",
    "pcap": "tcpdump -nr - <{file} >/dev/null 2>/dev/null",
    "png":  "identify -limit memory 512MiB -limit map 512MiB -limit disk 2GiB -limit time 10 - <{file} >/dev/null 2>&1",
    "wav":  "wavpack -y - -o output.wav <{file} 2>/dev/null",
    "zip":  "yes | unzip -P '' -t {file} >/dev/null 2>/dev/null",
}

EXTENSIONS = {
    "7zip": "7z",  "zip":  "zip", "png":  "png", "jpg":  "jpg",
    "gif":  "gif", "bmp":  "bmp", "mp4":  "mp4", "mp3":  "mp3",
    "wav":  "wav", "avi":  "avi", "midi": "mid", "pcap": "pcap",
    "tif":  "tif", "ttf":  "ttf", "sqlite": "db", "wasm": "wasm",
    "webp": "webp", "iso":  "iso", "aud":  "aud", "logfile": "log",
    "javascript": "js",
}


def base_format(filetype: str) -> str:
    """Strip a trailing '-llm' suffix so '7zip-llm' maps to '7zip'."""
    return filetype[: -len("-llm")] if filetype.endswith("-llm") else filetype


def format_duration(seconds: float) -> str:
    minutes, secs = divmod(seconds, 60)
    return f"{seconds:.2f} s ({int(minutes)}m {secs:.2f}s)"


def run_validation(validator_cmd: str, candidate: Path) -> bool:
    """Validate file using checker script commands.

    Uses the same validation methods as the checker scripts in checkers/*.sh

    Runs the validator in its own process group so that on timeout we can
    kill it *and* any children it spawned (shell=True only kills the shell
    itself by default, which can leave a runaway grandchild - e.g. an
    ImageMagick `identify` stuck decoding a malformed image - orphaned and
    still consuming memory/disk after we've given up on it).
    """
    if not validator_cmd:
        return True

    cmd = validator_cmd.replace("{file}", str(candidate))

    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        returncode = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        return False
    except Exception:
        os.killpg(proc.pid, signal.SIGKILL)
        return False

    return returncode == 0


def generate_files(
    fuzzer: Path,
    generated_dir: Path,
    count: int,
    evil_bit: bool,
    ext: str,
) -> int:
    """Generate fuzzer files to generated_dir. Returns success_count.

    Uses DONT_BE_EVIL environment variable to control evil bit:
    - evil_bit=True: Do NOT set DONT_BE_EVIL (allow evil values)
    - evil_bit=False: Set DONT_BE_EVIL=1 (disallow evil values)

    Generates all files in a single fuzzer invocation using shell expansion.
    """
    generated_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if not evil_bit:
        env["DONT_BE_EVIL"] = "1"
    elif "DONT_BE_EVIL" in env:
        del env["DONT_BE_EVIL"]

    # Build pattern for brace expansion: file_{1..10000}.ext
    pattern = f"file_{{1..{count}}}.{ext}"
    cmd = f"{str(fuzzer)} fuzz {pattern}"

    print(f"  Running fuzzer with {count} file arguments (shell expansion)...")

    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(generated_dir),  # Run in generated_dir so paths are relative
            timeout=600,  # 10 minutes for very large runs
            check=False,
            env=env,
            shell=True,  # Use shell for brace expansion
        )
    except subprocess.TimeoutExpired:
        print(f"[warn] fuzzer generation timed out after 10 minutes")

    success_count = len(list(generated_dir.glob(f"file_*.{ext}")))
    print(f"  Generation completed: {success_count}/{count} files")

    return success_count


def validate_and_organize(
    generated_dir: Path,
    valid_dir: Path,
    invalid_dir: Path,
    validator_cmd: str,
) -> Tuple[int, int]:
    """Validate generated files using checker script methods and organize into folders.
    Returns (valid_count, invalid_count)."""
    valid_count = 0
    invalid_count = 0

    generated_files = list(generated_dir.glob("file_*"))
    total = len(generated_files)

    for idx, generated_file in enumerate(generated_files, 1):
        ok = run_validation(validator_cmd, generated_file)

        if ok:
            valid_count += 1
            target = valid_dir / generated_file.name
        else:
            invalid_count += 1
            target = invalid_dir / generated_file.name

        os.rename(str(generated_file), str(target))

        if idx % 500 == 0 or idx == total:
            print(f"  progress: {idx}/{total} (valid: {valid_count}, invalid: {invalid_count})")

    return valid_count, invalid_count


def log_result_csv(csv_path: Path, row: dict) -> None:
    """Append a result row to the CSV log, writing the header if the file is new."""
    is_new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "filetype",
        nargs="?",
        default=DEFAULT_FILETYPE,
        help=f"Fuzzer prefix, e.g. 'tif-llm' (default: {DEFAULT_FILETYPE!r})",
    )
    ap.add_argument(
        "count",
        nargs="?",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Number of files to generate (default: {DEFAULT_COUNT})",
    )
    ap.add_argument(
        "--workdir",
        default=DEFAULT_WORKDIR,
        help=f"Repo root containing build/*-fuzzer (default: {DEFAULT_WORKDIR!r})",
    )
    ap.add_argument(
        "--evil-bit",
        action="store_true",
        default=DEFAULT_EVIL_BIT,
        help="Enable evil bit during file generation",
    )
    args = ap.parse_args()

    workdir = Path(args.workdir).resolve()
    fuzzer = workdir / "build" / f"{args.filetype}-fuzzer"
    if not fuzzer.is_file():
        print(f"[error] fuzzer binary not found: {fuzzer}", file=sys.stderr)
        return 1

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = workdir / "output" / args.filetype / timestamp
    generated_dir = run_dir / "generated"
    valid_dir = run_dir / "valid"
    invalid_dir = run_dir / "invalid"
    valid_dir.mkdir(parents=True, exist_ok=True)
    invalid_dir.mkdir(parents=True, exist_ok=True)

    fmt = base_format(args.filetype)
    ext = EXTENSIONS.get(fmt, "bin")
    validator_cmd = VALIDATORS.get(fmt, "")

    # =========================================================================
    # Phase 1: Generate files
    # =========================================================================
    print()
    print("=" * 52)
    print("Phase 1: Generating files")
    print("=" * 52)
    print(f"  Filetype          : {args.filetype}")
    print(f"  Evil bit enabled  : {args.evil_bit}")
    print(f"  Target count      : {args.count}")
    print()

    generated_count = generate_files(fuzzer, generated_dir, args.count, args.evil_bit, ext)

    # =========================================================================
    # Phase 2: Validate and organize
    # =========================================================================
    print()
    print("=" * 52)
    print("Phase 2: Validating files")
    print("=" * 52)
    print()

    val_start = time.monotonic()
    valid_count, invalid_count = validate_and_organize(
        generated_dir, valid_dir, invalid_dir, validator_cmd
    )
    val_time = time.monotonic() - val_start

    # =========================================================================
    # Calculate statistics
    # =========================================================================
    valid_rate = (valid_count / generated_count * 100) if generated_count > 0 else 0
    validation_speed = generated_count / val_time if val_time > 0 else 0

    # =========================================================================
    # Print summary
    # =========================================================================
    print()
    print("=" * 52)
    print("Fuzz run summary")
    print("=" * 52)
    print(f"  Timestamp              : {timestamp}")
    print(f"  Filetype               : {args.filetype}")
    print(f"  Evil bit enabled       : {args.evil_bit}")
    print()
    print(f"  Files generated        : {generated_count}/{args.count}")
    print(f"  Valid files            : {valid_count} ({valid_rate:.2f}%)")
    print(f"  Invalid files          : {invalid_count}")
    print()
    print(f"  Validation time        : {format_duration(val_time)}")
    print(f"  Validation speed       : {validation_speed:.2f} files/sec")

    # =========================================================================
    # Log result and clean up generated files
    # =========================================================================
    log_result_csv(workdir / RESULTS_CSV, {
        "timestamp": timestamp,
        "filetype": args.filetype,
        "evil_bit": args.evil_bit,
        "target_count": args.count,
        "generated_count": generated_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "valid_percent": round(valid_rate, 2),
        "validation_time_seconds": round(val_time, 2),
        "validation_files_per_second": round(validation_speed, 2),
    })
    print(f"\n  Result logged to       : {workdir / RESULTS_CSV}")

    shutil.rmtree(run_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
