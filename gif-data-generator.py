import os
import shutil
import subprocess

# Paths
OUTPUT_DIR = "./gif_data/stats/old"
PASSED_DIR = os.path.join(OUTPUT_DIR, "passed/")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed/")
GIF_FUZZER_CMD = "./gif-fuzzer fuzz"

# Ensure output directories exist
os.makedirs(PASSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

# Step 1: Generate and Validate GIFs
def is_valid_gif(file_path):
    try:
        result = subprocess.run(
            ["identify", "-verbose", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        return "Elapsed" in result.stdout
    except Exception:
        return False

valid_count = 0
invalid_count = 0
attempt = 1  # Track total attempts to generate valid GIFs

while attempt < 100:
    gif_path = os.path.join(OUTPUT_DIR, f"out{attempt}.gif")
    cmd = f"{GIF_FUZZER_CMD} {gif_path}"
    subprocess.run(cmd, shell=True, check=True)
    print(f"Generated: {gif_path}")
    
    if is_valid_gif(gif_path):
        shutil.move(gif_path, os.path.join(PASSED_DIR, f"out{attempt + 1}.gif"))
        print(f"Valid GIF: Moved to {PASSED_DIR} as out{attempt + 1}.gif")
        valid_count += 1
    else:
        shutil.move(gif_path, os.path.join(FAILED_DIR, f"out{attempt}.gif"))
        print(f"Invalid GIF: Moved to {FAILED_DIR}")
        invalid_count += 1
    
    attempt += 1

print("Processing complete! GIFs generated.")
print(f"Valid GIFs: {valid_count}, Invalid GIFs: {invalid_count}")
