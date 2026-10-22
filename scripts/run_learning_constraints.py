#!/usr/bin/env python3
"""
Runner script for the Learning Constraints module.

Run it with the repository root as the current working directory (it shells out to
./{file_type}-fuzzer, reads templates/{file_type}.bt, and writes to ./logs/), or pass
--fuzzer-dir build to use the binaries in build/.

Usage:
    python scripts/run_learning_constraints.py <file_type> [max_files] [source_dir] [options]

Options:
    --resume            resume the latest incomplete run for this file type
    --new               start a new run even if an incomplete one exists (no prompt)
    --workers N         number of worker processes (1 = sequential); default from config.py
    --strict            strict validator (identify -regard-warnings, ffmpeg -xerror)
    --fuzzer-dir DIR    directory holding <file_type>-fuzzer (default: .)

Examples:
    python scripts/run_learning_constraints.py png                    # all PNGs from the default directory
    python scripts/run_learning_constraints.py jpg 5                  # only 5 JPG files
    python scripts/run_learning_constraints.py gif /path/to/files     # all GIFs from a directory
    python scripts/run_learning_constraints.py bmp 5 /path/to/files   # 5 BMP files from a directory
    python scripts/run_learning_constraints.py png --resume           # resume the last incomplete run
    python scripts/run_learning_constraints.py mp4 --workers 1 --fuzzer-dir build

Exit codes: 0 success, 1 error, 2 no file succeeded, 130 interrupted.

Interactive behaviour: when an *incomplete* run exists and stdin is a terminal, the script
asks whether to resume it. Without a terminal it starts a new run unless --resume is given.
"""

import sys
import os

# The learning_constraints package lives at the repo root, one level above this script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning_constraints import (  # noqa: E402
    LearningConstraintsOrchestrator,
    Config,
    set_file_type,
    get_supported_file_types,
    get_worker_count
)
from learning_constraints.checkpoint import CheckpointManager  # noqa: E402

USAGE = "Usage: python scripts/run_learning_constraints.py <file_type> [max_files] [source_dir] [--resume|--new] [--workers N] [--strict] [--fuzzer-dir DIR]"


def check_for_resume(file_type):
    """Return (log_dir, checkpoint_path, info) of the latest incomplete run, or (None, None, None)."""
    log_dir, checkpoint_path = Config.find_latest_checkpoint(file_type, include_completed=False)
    if checkpoint_path:
        return log_dir, checkpoint_path, CheckpointManager.load_checkpoint_info(checkpoint_path)
    return None, None, None


def prompt_for_resume(checkpoint_info, log_dir):
    """Ask the user whether to resume an incomplete run (only called when stdin is a TTY)."""
    print("\n" + "=" * 60)
    print("FOUND INCOMPLETE RUN")
    print("=" * 60)
    print(f"Log directory: {log_dir}")
    print(f"Started: {checkpoint_info.get('started_at', 'Unknown')}")
    print(f"Last updated: {checkpoint_info.get('last_updated', 'Unknown')}")
    print(f"Files processed: {len(checkpoint_info.get('processed_files', []))}")
    print("=" * 60)

    while True:
        try:
            response = input("\nDo you want to [R]esume or start [N]ew? (R/N): ").strip().upper()
        except EOFError:
            return False
        if response in ('R', 'RESUME'):
            return True
        if response in ('N', 'NEW'):
            return False
        print("Please enter 'R' to resume or 'N' to start a new run.")


def parse_args(argv):
    """Parse positional arguments plus the option flags. Returns a dict or exits on error."""
    opts = {"resume": False, "new": False, "workers": None, "strict": False, "fuzzer_dir": None}
    positional = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--resume":
            opts["resume"] = True
        elif arg == "--new":
            opts["new"] = True
        elif arg == "--strict":
            opts["strict"] = True
        elif arg in ("--workers", "--fuzzer-dir"):
            if i + 1 >= len(argv):
                print(f"Error: {arg} needs a value.\n{USAGE}")
                sys.exit(1)
            value = argv[i + 1]
            if arg == "--workers":
                try:
                    opts["workers"] = int(value)
                    if opts["workers"] < 1:
                        raise ValueError
                except ValueError:
                    print("Error: --workers must be a positive integer.")
                    sys.exit(1)
            else:
                opts["fuzzer_dir"] = value
            i += 1
        elif arg.startswith("--"):
            print(f"Error: unknown option {arg}.\n{USAGE}")
            sys.exit(1)
        else:
            positional.append(arg)
        i += 1

    if not positional:
        print("Error: file_type argument is required.")
        print(USAGE)
        print(f"Supported types: {', '.join(get_supported_file_types())}")
        sys.exit(1)

    opts["file_type"] = positional[0].lower()
    opts["max_files"] = None
    opts["source_dir"] = None
    for value in positional[1:]:
        try:
            max_files = int(value)
            if max_files <= 0:
                print("Error: max_files must be a positive integer.")
                sys.exit(1)
            opts["max_files"] = max_files
        except ValueError:
            if not os.path.isdir(value):
                print(f"Error: source_dir '{value}' does not exist or is not a directory.")
                sys.exit(1)
            opts["source_dir"] = value
    return opts


def main():
    opts = parse_args(sys.argv[1:])
    file_type = opts["file_type"]

    supported_types = get_supported_file_types()
    if file_type not in supported_types:
        print(f"Error: '{file_type}' is not a supported file type.")
        print(f"Supported types: {', '.join(supported_types)}")
        return 1

    set_file_type(file_type)
    if opts["workers"] is not None:
        Config.PARALLEL_WORKERS = opts["workers"]
    if opts["strict"]:
        Config.VALIDATOR_STRICT = True
    if opts["fuzzer_dir"]:
        Config.FUZZER_DIR = opts["fuzzer_dir"]

    fuzzer = Config.get_fuzzer_executable()
    if not os.path.exists(fuzzer):
        print(f"Error: fuzzer executable not found: {fuzzer} (build it, or pass --fuzzer-dir build)")
        return 1

    # Decide whether to resume an incomplete run.
    should_resume = False
    log_dir, checkpoint_path, checkpoint_info = check_for_resume(file_type)
    if opts["resume"]:
        if checkpoint_path:
            should_resume = True
            print(f"\nResuming from checkpoint: {checkpoint_path}")
        else:
            print("\nNo incomplete run found to resume. Starting fresh.")
    elif checkpoint_path and not opts["new"]:
        if sys.stdin.isatty():
            should_resume = prompt_for_resume(checkpoint_info, log_dir)
        else:
            print(f"\nNote: incomplete run found at {log_dir}; starting a new run (use --resume to continue it).")
    Config.set_resume_mode(should_resume)

    effective_source_dir = opts["source_dir"] if opts["source_dir"] else Config.DATA_DIR
    if not os.path.isdir(effective_source_dir):
        print(f"\nError: source directory {effective_source_dir} does not exist.")
        if opts["source_dir"] is None:
            print(f"Pass a source directory as an argument or put files in {Config.DATA_DIR}")
        return 1

    if not should_resume:
        files_info = "all files" if opts["max_files"] is None else f"up to {opts['max_files']} files"
        num_workers = get_worker_count()
        print(f"\nLearning Constraints - Processing {file_type.upper()} files ({files_info})")
        print("=" * 60)
        print(f"Source directory: {effective_source_dir}")
        print(f"Results directory: ./logs/<timestamp>_{file_type}/results/")
        print(f"Fuzzer: {fuzzer}")
        print(f"Validator: {'strict' if Config.VALIDATOR_STRICT else 'lenient'}")
        print(f"Parallel processing: {num_workers} workers" if num_workers > 1 else "Parallel processing: disabled (sequential mode)")

    orchestrator = None
    try:
        orchestrator = LearningConstraintsOrchestrator(file_type=file_type, max_files=opts["max_files"],
                                                       source_dir=opts["source_dir"])
        results = orchestrator.run_complete_process()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        if orchestrator is not None and orchestrator.checkpoint_manager.has_saved:
            print(f"Progress was saved to {orchestrator.checkpoint_manager.checkpoint_path}.")
            print("Run with --resume to continue from where you left off.")
        else:
            print("No checkpoint was written; the run cannot be resumed.")
        return 130
    except Exception as e:
        print(f"Error during processing: {e}")
        return 1

    passed = results['passed_files']
    special = results['special_files']
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETED" if results['ok'] else "PROCESSING FINISHED - NO FILE SUCCEEDED")
    print("=" * 60)
    print(f"Source files processed: {passed['successful']}/{passed['total']} "
          f"(failed {passed['failed']}, skipped {passed['skipped']} already processed)")
    print(f"Special files processed: {special['successful']}/{special['total']} (failed {special['failed']})")
    print(f"Result files transformed: {results['transformed_files']['successful']}/{results['transformed_files']['total']}")
    print(f"Learned: {results['stats']['learned_values']} values over {results['stats']['learned_leaves']} fields; "
          f"blacklisted {results['stats']['blacklisted_total']}")
    if results.get('resumed'):
        print("(This was a resumed run)")
    print(f"Total time: {results['total_time_formatted']}")
    print(f"Output: {results['log_dir']}")
    return 0 if results['ok'] else 2


if __name__ == "__main__":
    sys.exit(main())
