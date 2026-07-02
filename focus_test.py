import subprocess
from pathlib import Path
from datetime import datetime

CAPTURE_WIDTH = 4056            # X-axis image resolution
CAPTURE_HEIGHT = 3040           # Y-axis image resolution

SCRIPT_DIR = Path(__file__).resolve().parent

 # Create the output directory 
OUT_DIR = SCRIPT_DIR / "test_photos"        # Use the "test photos" folder
OUT_DIR.mkdir(exist_ok=True)

def capture_image(output_path: Path):
    cmd = [
        "rpicam-still",
        "-o", str(output_path),
        "--width", str(CAPTURE_WIDTH),
        "--height", str(CAPTURE_HEIGHT),

        "--autofocus-mode", "auto",
        "--autofocus-range", "full",
        "--autofocus-speed", "normal",
        "--autofocus-window", "0.25,0.25,0.5,0.5",

        "--quality", "100",
        "--sharpness", "2.0",       # Reduced from 3.5; high values amplify noise

        "--timeout", "5000",        # Allow AE/AWB to settle before capture
        "--shutter", "8000",        # Restored original exposure
        "--gain", "1.0",            # Restored original gain
    ]

    subprocess.run(cmd, check=True)
    print(f"Saved image to {output_path}")

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = OUT_DIR / f"test_capture_{timestamp}.jpg"
    capture_image(out_file)