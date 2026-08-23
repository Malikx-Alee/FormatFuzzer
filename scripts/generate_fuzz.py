import os
import shutil
import subprocess
import sys
import ast


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from learning_constraints.validators import FileValidator

# Usage: python generate_fuzz.py <filetypes> <output_root> <count>
# Examples:
#   python generate_fuzz.py png ./testcases_fuzz_generated/png 100
#   python generate_fuzz.py png,bmp ./testcases_fuzz_generated 100
#   python generate_fuzz.py '["png", "bmp"]' ./testcases_fuzz_generated 100


def is_valid_generated_file(file_path, filetype):
    """Validate a generated file using the shared validation logic."""
    return FileValidator.is_valid_file(file_path, filetype)


def parse_filetypes(filetypes_arg):
    """Parse file types from a string into a list.

    Supports:
    - single value: "png"
    - comma-separated: "png,bmp"
    - list literal: '["png", "bmp"]'
    """
    if isinstance(filetypes_arg, list):
        return [ft.strip() for ft in filetypes_arg if ft and ft.strip()]

    raw_value = filetypes_arg.strip()
    if raw_value.startswith("[") and raw_value.endswith("]"):
        parsed = ast.literal_eval(raw_value)
        if not isinstance(parsed, list):
            raise ValueError("filetypes must be a list when using bracket syntax")
        return [str(ft).strip() for ft in parsed if str(ft).strip()]

    return [ft.strip() for ft in raw_value.split(",") if ft.strip()]


def resolve_output_dir(output_root, filetype, multi_type_mode):
    """Resolve the per-filetype output directory.

    For multi-type runs, files are always written to <output_root>/<filetype>.
    For single-type runs, preserve backward compatibility if output_root already
    points to a filetype-specific directory.
    """
    normalized_root = os.path.normpath(output_root)
    if multi_type_mode:
        return os.path.join(normalized_root, filetype)

    if os.path.basename(normalized_root) == filetype:
        return normalized_root

    return os.path.join(normalized_root, filetype)


def generate_for_filetype(filetype, output_dir, count, max_attempts_multiplier):
    """Generate valid fuzzed files for one file type."""
    os.makedirs(output_dir, exist_ok=True)
    failed_dir = os.path.join(output_dir, "failed")
    os.makedirs(failed_dir, exist_ok=True)

    fuzzer_cmd = os.path.join(REPO_ROOT, "build", f"{filetype}-fuzzer")
    max_attempts = max(count * max_attempts_multiplier, count)
    valid_count = 0
    invalid_count = 0
    attempt = 0

    print(f"\n=== Generating {filetype.upper()} files in {output_dir} ===")

    while valid_count < count and attempt < max_attempts:
        attempt += 1
        temp_filename = f".tmp_{attempt:06d}.{filetype}"
        temp_output_path = os.path.join(output_dir, temp_filename)

        try:
            subprocess.run([fuzzer_cmd, "fuzz", temp_output_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {fuzzer_cmd} for {temp_output_path}: {e}")
            if os.path.exists(temp_output_path):
                failed_path = os.path.join(failed_dir, f"failed_{attempt:06d}.{filetype}")
                shutil.move(temp_output_path, failed_path)
                invalid_count += 1
            continue

        print(f"Generated: {temp_output_path}")

        if is_valid_generated_file(temp_output_path, filetype):
            final_filename = f"F_{valid_count:03d}.{filetype}"
            final_output_path = os.path.join(output_dir, final_filename)
            os.replace(temp_output_path, final_output_path)
            valid_count += 1
            print(f"Valid {filetype.upper()}: kept as {final_output_path} ({valid_count}/{count})")
        else:
            failed_path = os.path.join(failed_dir, f"failed_{attempt:06d}.{filetype}")
            shutil.move(temp_output_path, failed_path)
            invalid_count += 1
            print(f"Invalid {filetype.upper()}: moved to {failed_path}")

    print("Generation complete!")
    print(f"Requested valid files: {count}")
    print(f"Valid files generated: {valid_count}")
    print(f"Invalid files generated: {invalid_count}")
    print(f"Total attempts: {attempt}")

    if valid_count < count:
        print(f"Stopped after reaching max attempts ({max_attempts}) before generating all requested valid files.")
    else:
        print(f"Generated {valid_count} valid {filetype} fuzzed files in {output_dir}")

    return {
        "filetype": filetype,
        "output_dir": output_dir,
        "requested": count,
        "valid": valid_count,
        "invalid": invalid_count,
        "attempts": attempt,
    }

def main():
    # Set default values here if you want to hardcode
    DEFAULT_FILETYPES = ["bmp", "gif", "jpg", "mp4", "png", "zip", "avi", "wav", "pcap", "midi"]
    DEFAULT_OUTPUT_ROOT = "./testcases_fuzz_generated"
    DEFAULT_COUNT = 1000
    MAX_ATTEMPTS_MULTIPLIER = 10

    if len(sys.argv) == 4:
        filetypes = parse_filetypes(sys.argv[1])
        output_root = sys.argv[2]
        count = int(sys.argv[3])
    else:
        filetypes = DEFAULT_FILETYPES
        output_root = DEFAULT_OUTPUT_ROOT
        count = DEFAULT_COUNT
        print(
            "No arguments provided. Using defaults: "
            f"filetypes={filetypes}, output_root={output_root}, count={count}"
        )

    if not filetypes:
        raise ValueError("At least one file type must be provided")

    multi_type_mode = len(filetypes) > 1
    results = []

    for filetype in filetypes:
        output_dir = resolve_output_dir(output_root, filetype, multi_type_mode)
        results.append(
            generate_for_filetype(
                filetype=filetype,
                output_dir=output_dir,
                count=count,
                max_attempts_multiplier=MAX_ATTEMPTS_MULTIPLIER,
            )
        )

    print("\n=== Overall summary ===")
    for result in results:
        print(
            f"{result['filetype']}: valid={result['valid']}/{result['requested']}, "
            f"invalid={result['invalid']}, attempts={result['attempts']}, "
            f"output_dir={result['output_dir']}"
        )

if __name__ == "__main__":
    main()
