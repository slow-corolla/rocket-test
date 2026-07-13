# Imports and Configurations
# Schedule using cron via 0 * * * * /home/nathaniel/rocket_project/rocket-test/.venv/bin/python /home/nathaniel/rocket_project/rocket-test/camera.py >> /home/nathaniel/camera.log 2>&1

import os           # Access OS for file and path management
import subprocess   # Access external processes from within this script
from pathlib import Path            # Allow this script to search this Path for imported modules
from datetime import datetime, time # Load the datetime module; access the date and time per the system
import numpy as np  # Load Numpy package
import cv2          # Load OpenCV package
from ultralytics import YOLO        # Load YOLO11x model

import smtplib
import traceback
from email.mime.text import MIMEText

# Notification Configuration
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SENDER_EMAIL  = "nathaniel.augimeri@gmail.com"    # Gmail account used to send the alert
SENDER_PASS   = os.environ.get("GMAIL_APP_PASSWORD", "")       # Gmail App Password
RECIPIENT     = "nathaniel.augimeri@gmail.com"    # Email address (or email-to-SMS gateway address)

def send_failure_alert(error_info: str) -> None:
    # Compose an alert email with the timestamp and error traceback.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"camera.py failed at {timestamp}.\n\n{error_info}"
    msg = MIMEText(body)
    msg["Subject"] = "RPi Camera Script Failure"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT

    # Open a TLS connection, authenticate, and send.
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASS)
            server.sendmail(SENDER_EMAIL, RECIPIENT, msg.as_string())
    except Exception as mail_err:
        # If the alert itself fails, log it locally rather than raising.
        print(f"Failed to send alert: {mail_err}")

CAPTURE_WIDTH = 4056            # X-axis image resolution
CAPTURE_HEIGHT = 3040           # Y-axis image resolution

PROTOCOL_NAME = "dataset_5"  # Change per grow protocol; also creates the matching subfolder in Drive on next sync

SCRIPT_DIR = Path(__file__).resolve().parent
# OUT_DIR = SCRIPT_DIR / "output_photos"                    # Use the "output_photos" folder
# OUT_DIR = SCRIPT_DIR / "stress_feasibility"               # Use the "stress_feasibility" folder
# OUT_DIR = SCRIPT_DIR / "second_stress_feasibility"        # Use the "second_stress_feasibility" folder
# OUT_DIR = SCRIPT_DIR / "fourth_stress_feasibility"        # Use the "third_stress_feasibility" folder

OUT_DIR = SCRIPT_DIR / "dataset_photos" / PROTOCOL_NAME   # Nest a protocol-specific subfolder within dataset_photos
OUT_DIR.mkdir(parents=True, exist_ok=True)                # Create both dataset_photos 

# Helper Functions

def next_daily_photo_number(directory=OUT_DIR): 
    # Return the next photo number for today's date.
    today_str = datetime.now().strftime("%d_%m_%y") # Obtain the current date
    existing_nums = []                              # Existing photo numbers
    
    for f in directory.glob(f"{today_str}_photo_*.jpg"): 
        stem = f.stem 
        parts = stem.split("_") 
        if len(parts) >= 5 and parts[-1].isdigit():  # Changed: parts has 5 elements, just check if last is digit
            num = int(parts[-1]) 
            existing_nums.append(num)
            
    return (max(existing_nums) + 1) if existing_nums else 1

def capture_with_rpicam_still(out_path: Path):
    # Capture an image using rpicam-still with autofocus enabled. 
    cmd = [ 
        "rpicam-still", 
        "-o", str(out_path),
        "--width", str(CAPTURE_WIDTH), 
        "--height", str(CAPTURE_HEIGHT), 

        "--autofocus-mode", "auto", # Enable autofocus 
        "--autofocus-range", "normal", # Typical plant distance 
        "--autofocus-speed", "normal", 
        "--autofocus-window", "0.25,0.25,0.5,0.5", # Focus on center region 

        # NEW: Quality & sharpness
        "--quality", "100",  # Max JPEG quality (default is 93)
        "--sharpness", "2.0",  # Increase sharpness (0-16, default 1.0)
    
        # NEW: Ensure proper exposure
        "--timeout", "5000",  # 3 sec for AF to settle (default 5000ms)
        "--shutter", "8000",  # Fixed 5ms shutter (adjust based on lighting)
    
        # NEW: Consider lower ISO for less noise
         "--gain", "1.0",  # ISO equivalent (1.0-8.0, lower = cleaner)
        ] 
        
    subprocess.run(cmd, check=True)

def within_operating_hours():
    # Return True if the current hour is between 5 AM and 4 PM inclusive.
    now = datetime.now().time()
    return 5 <= now.hour <= 16 # Previous script used and instead of or; "or" allows this to wrap around midnight
    
#def on_the_hour(): 
    # Return True if the current minute == 0.
    # return datetime.now().minute == 0
    # return 0 <= datetime.now().minute <= 60

# Main Code

def main(): 
    # Cron runs this script once. We only capture if conditions are met. 
    if not within_operating_hours(): 
        return 
        
    # if not on_the_hour(): 
    #    return 
        
    now = datetime.now() 
    day_number = now.strftime("%d")     # Day of month 
    month_number = now.strftime("%m")   # Month
    year_number = now.strftime("%y")    # Year
    # date_str = now.strftime("%d-%m-%y") 
    photo_num = next_daily_photo_number() 
    
    filename = f"{day_number}_{month_number}_{year_number}_photo_{photo_num}.jpg" 
    out_path = OUT_DIR / filename 
    
    capture_with_rpicam_still(out_path) 
    print(f"Captured image -> {out_path}") 
    
if __name__ == "__main__":
    try:
        main()   # Replace with whatever your entry-point call is
    except Exception:
        # Capture the full traceback and dispatch the alert.
        send_failure_alert(traceback.format_exc())
        raise    # Re-raise so the cron log still records the failure