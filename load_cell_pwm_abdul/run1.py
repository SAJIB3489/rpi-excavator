import time
import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from hx711 import HX711

# OLED setup
RESET_PIN = digitalio.DigitalInOut(board.D4)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3D, reset=RESET_PIN)

# Calibration factor obtained from the Arduino code
calibration_factor = -7050.0  # Use the same calibration factor from your Arduino code

# GPIO pins for HX711 (Data: GPIO 21, Clock: GPIO 20)
hx = HX711(21, 20)  # GPIO 21 for DOUT and GPIO 20 for SCK
hx.set_gain(128)  # Set gain for channel A
hx.set_scale(calibration_factor)  # Set the calibration factor (same as Arduino)

# Function to clear the OLED display
def clear_display():
    oled.fill(0)
    oled.show()

# Function to update the display with the current weight
def update_display(weight):
    width = oled.width
    height = oled.height
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()
    weight_str = f"Weight: {weight:.2f} lbs"  # Display in pounds, change to kg if needed

    # Use textbbox to calculate text width and height
    bbox = draw.textbbox((0, 0), weight_str, font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Center the text on the screen
    x_pos = (width - text_width) // 2
    y_pos = (height - text_height) // 2
    draw.text((x_pos, y_pos), weight_str, font=font, fill=255)

    oled.image(image)
    oled.show()

# Main loop for reading and displaying the weight
while True:
    try:
        # Get raw data from HX711 and apply the calibration factor
        raw_value = hx.read()  # Get a single raw reading
        weight = raw_value / calibration_factor  # Apply calibration factor
        print(f"Weight: {weight:.2f} lbs")  # Print the weight in pounds

        # Update the OLED display
        update_display(weight)
        time.sleep(1)  # Delay to update every second

    except (KeyboardInterrupt, SystemExit):
        print("Exiting...")
        break
