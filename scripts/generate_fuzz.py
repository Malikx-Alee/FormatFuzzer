import os
import sys
import subprocess

# Usage: python generate_fuzz.py <filetype> <output_dir> <count>
# Example: python generate_fuzz.py png ./testcases_fuzz_generated/png 100

def main():
    # Set default values here if you want to hardcode
    DEFAULT_FILETYPE = "bmp"
    DEFAULT_OUTPUT_DIR = "./testcases_fuzz_generated/bmp"
    DEFAULT_COUNT = 1000

    if len(sys.argv) == 4:
        filetype = sys.argv[1]
        output_dir = sys.argv[2]
        count = int(sys.argv[3])
    else:
        filetype = DEFAULT_FILETYPE
        output_dir = DEFAULT_OUTPUT_DIR
        count = DEFAULT_COUNT
        print(f"No arguments provided. Using defaults: filetype={filetype}, output_dir={output_dir}, count={count}")

    os.makedirs(output_dir, exist_ok=True)

    fuzzer_cmd = f"./{filetype}-fuzzer"

    for i in range(count):
        filename = f"F_{i:03d}.{filetype}"
        output_path = os.path.join(output_dir, filename)
        try:
            subprocess.run([fuzzer_cmd, "fuzz", output_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {fuzzer_cmd} for {output_path}: {e}")

    print(f"Generated {count} {filetype} fuzzed files in {output_dir}")

if __name__ == "__main__":
    main()
