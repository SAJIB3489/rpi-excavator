from hx711 import HX711
import os
import time

SCALE_FILE = "scale_factor.txt"  # File to save the scale factor

def load_scale_factor():
    """Load the scale factor from a file."""
    if os.path.exists(SCALE_FILE):
        with open(SCALE_FILE, "r") as f:
            scale_factor = float(f.read())
        print(f"Loaded scale factor: {scale_factor}")
        return scale_factor
    else:
        print("Scale factor not found. Please calibrate first.")
        exit(1)

# Initialize HX711
hx = HX711(21, 20)  # GPIO 21 for DOUT, GPIO 20 for SCK
hx.set_gain(128)    # Set gain for channel A
hx.tare()           # Tare the scale
print("Scale tared. Offset is set.")

# Load scale factor
scale_factor = load_scale_factor()
hx.set_scale(scale_factor)

# Read weight
weights = []
print("Starting weight readings...")
while True:
    try:
        weight = hx.get_grams()
        weights.append(weight)

        # Apply rolling average
        if len(weights) > 10:
            weights.pop(0)

        smoothed_weight = sum(weights) / len(weights)
        print(f"Smoothed Weight: {smoothed_weight:.2f} grams")
        time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Exiting...")
        break
