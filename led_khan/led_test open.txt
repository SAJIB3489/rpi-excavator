import gpiod
import time

# Define the GPIO pins for the LEDs
LED_PIN_18 = 18  # First LED on GPIO 18
LED_PIN_23 = 23  # Second LED on GPIO 23

# Initialize the GPIO
chip = gpiod.Chip('gpiochip4')

# Setup the first LED (GPIO 18)
led_line_18 = chip.get_line(LED_PIN_18)
led_line_18.request(consumer='LED_18', type=gpiod.LINE_REQ_DIR_OUT)

# Setup the second LED (GPIO 23)
led_line_23 = chip.get_line(LED_PIN_23)
led_line_23.request(consumer='LED_23', type=gpiod.LINE_REQ_DIR_OUT)

try:
    # Turn both LEDs on together
    led_line_18.set_value(1)  # Turn the first LED on (GPIO 18)
    led_line_23.set_value(1)  # Turn the second LED on (GPIO 23)

    print("Both LEDs are ON")  # Print message when both LEDs are on

    # Keep both LEDs on indefinitely
    while True:
        time.sleep(1)  # Keep the program alive without doing anything

except KeyboardInterrupt:
    # Clean up when the user interrupts the script
    led_line_18.set_value(0)  # Turn off the first LED
    led_line_23.set_value(0)  # Turn off the second LED
    print("Both LEDs are OFF")

    led_line_18.release()
    led_line_23.release()
    chip.close()

