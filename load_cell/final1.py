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

# Load known reference values
ZERO_VALUE = 8388608  # Use your obtained zero value here
REFERENCE_UNIT = 1000  # You need to calculate or define the reference unit here (e.g., 1000 for 1kg)

# Initialize HX711
hx = HX711(21, 20)  # GPIO pins for HX711
hx.set_gain(128)    # Set gain for channel A
hx.set_offset(ZERO_VALUE)  # Set the zero value obtained during calibration
hx.set_scale(REFERENCE_UNIT)  # Set the scale factor (to be determined)

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
    weight_str = f"Weight: {weight:.2f} g"

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
        # Get weight from the load cell
        raw_value = hx.get_grams()  # Get the weight in grams
        print(f"Weight: {raw_value:.2f} grams")  # Print the raw value (for debugging)

        # Update the OLED display
        update_display(raw_value)
        time.sleep(1)  # Delay to update every second

    except (KeyboardInterrupt, SystemExit):
        print("Exiting...")
        break
