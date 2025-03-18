import os
import shutil
import subprocess
from PIL import Image

# Paths
OUTPUT_DIR = "./gif_data/"
PASSED_DIR = os.path.join(OUTPUT_DIR, "passed/")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed/")
GIF_FUZZER_CMD = "./gif-fuzzer fuzz"

# Ensure output directories exist
os.makedirs(PASSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

# Step 1: Generate 100 GIFs
for i in range(1, 101):
    gif_path = os.path.join(OUTPUT_DIR, f"out{i}.gif")
    cmd = f"{GIF_FUZZER_CMD} {gif_path}"
    subprocess.run(cmd, shell=True)
    print(f"Generated: {gif_path}")

# Step 2: Validate GIF files using Pillow
def is_valid_gif(file_path):
    try:
        with Image.open(file_path) as img:
            return img.format == "GIF"
    except Exception:
        return False

# Step 3: Move files based on validation
for i in range(1, 101):
    gif_path = os.path.join(OUTPUT_DIR, f"out{i}.gif")
    
    if os.path.exists(gif_path):  # Ensure file exists
        if is_valid_gif(gif_path):
            shutil.move(gif_path, os.path.join(PASSED_DIR, f"out{i}.gif"))
            print(f"Valid GIF: Moved to {PASSED_DIR}")
        else:
            shutil.move(gif_path, os.path.join(FAILED_DIR, f"out{i}.gif"))
            print(f"Invalid GIF: Moved to {FAILED_DIR}")

print("Processing complete!")
