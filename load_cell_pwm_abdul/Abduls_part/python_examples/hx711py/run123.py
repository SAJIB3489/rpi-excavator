from gpiozero import DigitalInputDevice, DigitalOutputDevice
import time

class HX711:
    def __init__(self, dout_pin, clk_pin, reference_unit=1):
        self.dout = DigitalInputDevice(dout_pin)
        self.clk = DigitalOutputDevice(clk_pin)
        self.reference_unit = reference_unit

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

    def get_weight(self):
        """Convert raw data to weight using the reference unit."""
        raw_value = self.read_raw()
        return raw_value / self.reference_unit

# GPIO pins for HX711
DOUT_PIN = 20  # Data pin (DT/DOUT)
CLK_PIN = 21   # Clock pin (SCK/CLK)

# Reference unit (calibration factor, adjust this for your load cell)
REFERENCE_UNIT = 2280  # Adjust this value for accurate weight readings

hx711 = HX711(dout_pin=DOUT_PIN, clk_pin=CLK_PIN, reference_unit=REFERENCE_UNIT)

print("Place an object on the scale...")

try:
    while True:
        weight = hx711.get_weight()
        print(f"Weight: {weight:.2f} grams")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExiting...")
