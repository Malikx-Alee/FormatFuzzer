#!/usr/bin/env python3
"""Generate and validate files for every template in templates/, and report
valid/invalid counts per filetype.

Reuses the generation/validation logic from fuzz_manager.py. Each filetype's
run is logged to results.csv (same schema as fuzz_manager.py), and a summary
table across all filetypes is printed and written to
template_validation_summary.md.

Usage:
    python3 validate_all_templates.py [COUNT] [FILETYPE...]

If no FILETYPEs are given, every templates/*.bt basename is used. Pass
explicit filetypes (e.g. "-orig" variants) to restrict the run to those.

Examples:
    python3 validate_all_templates.py                        # all templates/*.bt, 10000 files each
    python3 validate_all_templates.py 1000                   # all templates/*.bt, 1000 files each
    python3 validate_all_templates.py 10000 png-orig mp3-orig  # only these two, 10000 files each
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

from fuzz_manager import (
    DEFAULT_EVIL_BIT,
    EXTENSIONS,
    RESULTS_CSV,
    VALIDATORS,
    base_format,
    format_duration,
    generate_files,
    log_result_csv,
    validate_and_organize,
)

WORKDIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = WORKDIR / "templates"
DEFAULT_COUNT = 10000
SUMMARY_MD = "template_validation_summary.md"


def discover_filetypes() -> list:
    """Filetypes are derived from templates/*.bt, e.g. templates/gif.bt -> 'gif'."""
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.bt"))


def write_summary(results: list, count: int, summary_path: Path) -> None:
    lines = [
        "# Template validation summary",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Target count per filetype: {count}",
        "",
        "| Filetype | Generated | Valid | Invalid | Valid % |",
        "|----------|-----------|-------|---------|---------|",
    ]
    for r in results:
        lines.append(
            f"| {r['filetype']} | {r['generated']} | {r['valid']} | "
            f"{r['invalid']} | {r['valid_rate']:.2f}% |"
        )
    summary_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_COUNT
    filetypes = sys.argv[2:] if len(sys.argv) > 2 else discover_filetypes()

    results = []
    for filetype in filetypes:
        fuzzer = WORKDIR / "build" / f"{filetype}-fuzzer"
        if not fuzzer.is_file():
            print(f"[skip] {filetype}: fuzzer binary not found ({fuzzer})")
            continue

        print()
        print("=" * 52)
        print(f"{filetype}")
        print("=" * 52)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = WORKDIR / "output" / filetype / timestamp
        generated_dir = run_dir / "generated"
        valid_dir = run_dir / "valid"
        invalid_dir = run_dir / "invalid"
        valid_dir.mkdir(parents=True, exist_ok=True)
        invalid_dir.mkdir(parents=True, exist_ok=True)

        fmt = base_format(filetype)
        ext = EXTENSIONS.get(fmt, "bin")
        validator_cmd = VALIDATORS.get(fmt, "")

        generated_count = generate_files(fuzzer, generated_dir, count, DEFAULT_EVIL_BIT, ext)

        valid_count, invalid_count = validate_and_organize(
            generated_dir, valid_dir, invalid_dir, validator_cmd
        )

        valid_rate = (valid_count / generated_count * 100) if generated_count > 0 else 0

        log_result_csv(WORKDIR / RESULTS_CSV, {
            "timestamp": timestamp,
            "filetype": filetype,
            "evil_bit": DEFAULT_EVIL_BIT,
            "target_count": count,
            "generated_count": generated_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "valid_percent": round(valid_rate, 2),
        })

        results.append({
            "filetype": filetype,
            "generated": generated_count,
            "valid": valid_count,
            "invalid": invalid_count,
            "valid_rate": valid_rate,
        })

        print(f"  {filetype}: {valid_count} valid / {invalid_count} invalid "
              f"({valid_rate:.2f}% valid)")

        shutil.rmtree(run_dir, ignore_errors=True)

    print()
    print("=" * 52)
    print("Summary")
    print("=" * 52)
    print(f"{'Filetype':<10} {'Generated':>10} {'Valid':>8} {'Invalid':>8} {'Valid %':>9}")
    for r in results:
        print(f"{r['filetype']:<10} {r['generated']:>10} {r['valid']:>8} "
              f"{r['invalid']:>8} {r['valid_rate']:>8.2f}%")

    summary_path = WORKDIR / SUMMARY_MD
    write_summary(results, count, summary_path)
    print(f"\nSummary written to: {summary_path}")
    print(f"Per-run results logged to: {WORKDIR / RESULTS_CSV}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
