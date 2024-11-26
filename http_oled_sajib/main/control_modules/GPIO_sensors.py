"""
GPIO_sensors.py

This module implements interfaces for sensors connected to GPIO (General Purpose Input/Output) pins,
specifically designed for Raspberry Pi or similar single-board computers. It provides classes for
RPM (Revolutions Per Minute) sensors and center position sensors.

Key features:
1. Configurable GPIO sensors using a YAML configuration file
2. Support for RPM sensors with configurable number of magnets
3. High-performance RPM calculation using hardware interrupts and efficient timing
4. Center position sensing for positional feedback
5. Clean GPIO setup and cleanup procedures

The module includes two main classes:
1. RPMSensor:
   - Initializes GPIO for RPM sensing
   - Calculates RPM in real-time using hardware interrupts
   - Provides methods to read current RPM

2. GPIOSensor:
   - Base class for GPIO sensors
   - Provides method to read current sensor state
"""

from time import time
import threading
import yaml
from typing import Dict
from collections import deque
from statistics import mean

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO module not found. Make sure you're running on a Raspberry Pi.")

class RPMSensor:
    def __init__(self, config_file: str, sensor_name: str, decimals: int = 1, window_size: int = 10):
        """
        Initialize RPM sensor with configuration from a YAML file.

        :param config_file: Path to the YAML configuration file.
        :param sensor_name: Name of the sensor in the configuration.
        :param decimals: Number of decimal places for RPM value.
        :param window_size: Size of the moving average window for RPM calculation.
        """
        self.sensor_configs = self._load_config(config_file, sensor_name)
        self.sensor_pin = self.sensor_configs['GPIO pin']
        self.magnets = self.sensor_configs['magnets']
        self.decimals = decimals
        self.window_size = window_size
        self.pulse_times = deque(maxlen=window_size)
        self.last_pulse_time = time()
        self.rpm = 0
        self.lock = threading.Lock()
        self._setup_gpio()

    def _load_config(self, config_file: str, sensor_name: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_file, 'r') as file:
                configs = yaml.safe_load(file)
                return configs['RPM_SENSORS'][sensor_name]
        except (yaml.YAMLError, KeyError) as e:
            raise ValueError(f"Error parsing configuration file: {e}")

    def _setup_gpio(self):
        """Set up GPIO for the RPM sensor using hardware interrupt."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.sensor_pin, GPIO.FALLING, callback=self._sensor_callback, bouncetime=1)

    def _sensor_callback(self, channel):
        """Callback function for GPIO event detection."""
        current_time = time()
        with self.lock:
            self.pulse_times.append(current_time - self.last_pulse_time)
            self.last_pulse_time = current_time
            self._calculate_rpm()

    def _calculate_rpm(self):
        """Calculate RPM based on recent pulse times."""
        if len(self.pulse_times) >= 2:
            avg_time_between_pulses = mean(self.pulse_times)
            self.rpm = 60 / (avg_time_between_pulses * self.magnets)

    def read_rpm(self) -> float:
        """Read the current RPM value."""
        with self.lock:
            return round(self.rpm, self.decimals)

    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.remove_event_detect(self.sensor_pin)
        GPIO.cleanup(self.sensor_pin)


class GPIOSensor:
    """
    Base class for GPIO sensors.
    Returns the current state of the GPIO pin as a boolean value.
    """
    def __init__(self, sensor_pin: int, pull_up_down: int = GPIO.PUD_UP):
        """
        Initialize a universal GPIO Sensor.

        :param sensor_pin: GPIO pin number for the sensor.
        :param pull_up_down: Pull-up/down resistor setting (GPIO.PUD_UP or GPIO.PUD_DOWN).
        """
        self.sensor_pin = sensor_pin
        self.pull_up_down = pull_up_down
        self._setup_gpio()

    def _setup_gpio(self):
        """Set up GPIO for the sensor."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sensor_pin, GPIO.IN, pull_up_down=self.pull_up_down)

    def read_value(self) -> bool:
        """Read the current state of the GPIO pin."""
        return GPIO.input(self.sensor_pin)

    def cleanup(self):
        """Clean up GPIO resources."""
        GPIO.cleanup(self.sensor_pin)