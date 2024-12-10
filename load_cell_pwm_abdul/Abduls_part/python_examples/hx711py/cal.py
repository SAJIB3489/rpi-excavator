from gpiozero import DigitalInputDevice, DigitalOutputDevice
import time

class HX711:
    def __init__(self, dout_pin, clk_pin):
        self.dout = DigitalInputDevice(dout_pin)
        self.clk = DigitalOutputDevice(clk_pin)

    def read_raw(self):
        """Read raw data from the HX711."""
        while self.dout.value == 1:  # Wait for HX711 to be ready
            pass

        count = 0
        for _ in range(24):  # Read 24-bit data
            self.clk.on()
            time.sleep(0.000001)
            self.clk.off()
            count = (count << 1) | self.dout.value

        # Read the 25th pulse to set the gain
        self.clk.on()
        time.sleep(0.000001)
        self.clk.off()

        # If the 24th bit is 1, the value is negative
        if count & 0x800000:
            count -= 0x1000000

        return count

    def get_weight(self, reference_unit):
        """Convert raw data to weight using the reference unit."""
        raw_value = self.read_raw()
        return raw_value / reference_unit

# GPIO pins for HX711
DOUT_PIN = 20  # Data pin (DT/DOUT)
CLK_PIN = 21   # Clock pin (SCK/CLK)

hx711 = HX711(dout_pin=DOUT_PIN, clk_pin=CLK_PIN)

print("Starting calibration...")

# Step 1: Get the zero value (no weight on scale)
print("Place no weight on the scale and press Enter.")
input("Press Enter to continue...")

zero_value = hx711.read_raw()
print(f"Zero value (no weight): {zero_value}")

# Step 2: Add known weight (e.g., 195g)
print("Now place a known weight of 195g on the scale and press Enter.")
input("Press Enter when weight is added...")

known_weight = 195  # Known weight in grams (195g)
measured_value = hx711.read_raw()
print(f"Measured value with 195g weight: {measured_value}")

# Step 3: Calculate the reference unit
reference_unit = measured_value / known_weight
print(f"Calibration factor (Reference Unit): {reference_unit}")

print("\nNow you can use the calibration factor for further readings.")
print("Press Ctrl+C to exit.")

# Use this reference_unit for further weight readings
while True:
    weight = hx711.get_weight(reference_unit)
    print(f"Weight: {weight:.2f} grams")
    time.sleep(1)
