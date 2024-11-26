import time
from hx711 import HX711  # Import HX711 library

# Define the GPIO pins connected to the HX711
DT_PIN = 5  # Data pin
SCK_PIN = 6  # Clock pin

# Create an HX711 object
hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN)

# Initialize HX711
hx.reset()  # Reset the HX711
hx.tare()   # Tare (zero out) the scale

print("Place known weight on scale to calibrate.")

# Wait and let the user place a known weight on the scale
time.sleep(5)

# Read data for calibration
value = hx.get_data_mean()
print(f"Calibration Value: {value}")
print("Replace with this value in code to calibrate for accuracy.")

while True:
    try:
        # Get a reading from the HX711
        weight = hx.get_weight_mean(5)  # Average of 5 readings
        print(f"Weight: {weight} grams")
        
        time.sleep(1)  # Wait before taking the next reading
    except (KeyboardInterrupt, SystemExit):
        print("Program interrupted. Cleaning up...")
        hx.power_down()
        break
