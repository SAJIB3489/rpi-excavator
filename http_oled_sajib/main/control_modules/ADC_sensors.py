"""
This module implements an interface for ABelectronics ADCPi Converter to work with sensors using the ADCPi library.

Key features:
1. Configurable ADC channels using a YAML configuration file
2. Support for different types of sensors: pressure and angle sensors
3. Raw voltage reading and scaling based on sensor type
4. Calibration functions for pressure and angle sensors
5. Various filtering options including low-pass and Kalman filters
6. Simulation mode for testing without hardware
7. Tracking and resetting of sensor ranges

The main class, ADC_hat, handles:
- Initialization of ADC boards based on configuration
- Reading raw voltage values from sensors
- Scaling and calibrating sensor readings
- Applying filters to sensor data
- Tracking the range of sensor values
- Simulating ADC behavior when hardware is not available with synthetic voltage generation

Usage:
1. Create a YAML configuration file defining your ADC setup and sensors
2. Initialize the ADC_hat with the configuration file and desired settings
3. Use methods like read_raw(), read_scaled(), or read_filtered() to get sensor data
4. Optionally use simulation mode for testing without physical hardware
"""
import yaml
import math
import time
import random
from typing import Dict, Tuple, Optional, List

try:
    from ADCPi import ADCPi
except ImportError:
    print("ADCPi module not found. Running in simulation mode.")


class ADC_hat:
    def __init__(self, config_file: str, decimals: int = 2, simulation_mode: bool = False,
                 min_sim_voltage: float = 0.5, max_sim_voltage: float = 4.5, frequency: float = 1.0):
        """
        Initialize ADC_hat with configuration from a YAML file.

        :param config_file: Path to the YAML configuration file.
        :param decimals: Number of decimal places for calibration values.
        :param simulation_mode: Whether to run in simulation mode.
        :param min_sim_voltage: Minimum voltage for the SIMULATED ADC.
        :param max_sim_voltage: Maximum voltage for the SIMULATED ADC.
        :param frequency: Frequency of the sine wave for simulation.
        """
        self.decimals = decimals
        self.simulation_mode = simulation_mode

        if simulation_mode:
            global ADCPi
            ADCPi = lambda addr1, addr2, bit_rate: ADCPiStub(addr1, addr2, bit_rate, min_sim_voltage, max_sim_voltage,
                                                             frequency)
            print("Running in simulation mode.")

        self._load_config(config_file)
        self.adcs: Dict[str, ADCPi] = {}
        self.initialized = False
        self.min_voltage: Dict[str, float] = {}
        self.min_angle: Dict[str, float] = {}
        self.max_angle: Dict[str, float] = {}
        self.min_pressure: Dict[str, float] = {}
        self.max_pressure: Dict[str, float] = {}

        self.initialize_adc()

    def _load_config(self, config_file: str):
        """Load configuration from YAML file."""
        try:
            with open(config_file, 'r') as file:
                configs = yaml.safe_load(file)
                self.pressure_sensors = configs.get('PRESSURE_SENSORS', {})
                self.angle_sensors = configs.get('ANGLE_SENSORS', {})
                self.i2c_addresses = configs['ADC_CONFIG']['i2c_addresses']
                self.pga_gain = configs['ADC_CONFIG']['pga_gain']
                self.bit_rate = configs['ADC_CONFIG']['bit_rate']
                self.conversion_mode = configs['ADC_CONFIG']['conversion_mode']
                self.filter_configs = configs.get('FILTER_CONFIG', {})
        except (yaml.YAMLError, KeyError) as e:
            raise ValueError(f"Error parsing configuration file: {e}")

    def initialize_adc(self):
        """Initialize ADC boards based on sensor configurations."""
        board_needs_initialization = {board_name: False for board_name in self.i2c_addresses.keys()}

        for sensor_config in {**self.pressure_sensors, **self.angle_sensors}.values():
            board_name = sensor_config['input'][0]
            if board_name in board_needs_initialization:
                board_needs_initialization[board_name] = True

        for board_name, need_init in board_needs_initialization.items():
            if need_init:
                addr1, addr2 = self.i2c_addresses[board_name]
                try:
                    adc_instance = ADCPi(addr1, addr2, self.bit_rate)
                    adc_instance.set_conversion_mode(self.conversion_mode)
                    adc_instance.set_pga(self.pga_gain)
                    self.adcs[board_name] = adc_instance
                    print(f"Initialized {board_name} with addresses {hex(addr1)}, {hex(addr2)}")
                except OSError as e:
                    raise OSError(f"Failed to initialize ADCPi for {board_name}! Error: {e}")

        self.initialized = True

    def read_raw(self) -> Dict[str, float]:
        """Read raw voltage from all sensors as specified in the configuration."""
        if not self.initialized:
            print("ADCPi not initialized!")
            return {}

        raw_readings = {}
        for sensor_name, sensor_config in {**self.pressure_sensors, **self.angle_sensors}.items():
            voltage = self._read_raw(sensor_config)
            if voltage is not None:
                raw_readings[sensor_name] = round(voltage,self.decimals)

        return raw_readings

    def _read_raw(self, sensor_config: Dict) -> Optional[float]:
        """Read raw voltage based on the sensor configuration."""
        board_name = sensor_config['input'][0]
        channel = sensor_config['input'][1]
        adc_instance = self.adcs.get(board_name)
        if adc_instance:
            return adc_instance.read_voltage(channel)
        else:
            print(f"ADC instance for board {board_name} not found.")
            return None

    def read_scaled(self, read: Optional[str] = None) -> Dict[str, float]:
        """
        Read and scale the sensor data.

        :param read: Optional; Specify 'pressure', 'angle', or None to read both types.
        :return: A dictionary of scaled sensor readings.
        """
        scaled_readings = {}

        if read is None or read == 'pressure':
            for sensor_name, sensor_config in self.pressure_sensors.items():
                voltage = self._read_raw(sensor_config)
                if voltage is not None:
                    scaled_value = self.calibrate_pressure(voltage, sensor_config)
                    scaled_readings[sensor_name] = round(scaled_value,self.decimals)
                    self._update_sensor_range('pressure', sensor_name, scaled_value)

        if read is None or read == 'angle':
            for sensor_name, sensor_config in self.angle_sensors.items():
                voltage = self._read_raw(sensor_config)
                if voltage is not None:
                    scaled_value = self.calibrate_angle(voltage, sensor_config)
                    scaled_readings[sensor_name] = round(scaled_value,self.decimals)
                    self._update_sensor_range('angle', sensor_name, scaled_value)

        return scaled_readings

    def read_filtered(self, read: Optional[str] = None) -> Dict[str, float]:
        """Read, scale, and filter sensor data."""
        scaled_data = self.read_scaled(read)  # Get scaled values directly from sensors
        filtered_data = {}

        for sensor_name, scaled_value in scaled_data.items():
            sensor_config = self.pressure_sensors.get(sensor_name) or self.angle_sensors.get(sensor_name)

            if not sensor_config:
                print(f"[Debug] Unexpected sensor name '{sensor_name}' found in scaled_data.")
                continue

            if sensor_name in self.angle_sensors:
                if sensor_name not in self.min_angle:
                    self.min_angle[sensor_name] = scaled_value
                    self.max_angle[sensor_name] = scaled_value

                # remember the smallest and largest SCALED value
                self.min_angle[sensor_name] = min(self.min_angle[sensor_name], scaled_value)
                self.max_angle[sensor_name] = max(self.max_angle[sensor_name], scaled_value)

                # print(f"MIN/MAX: {self.min_angle[sensor_name]} / {self.max_angle[sensor_name]}")

                # Apply the filter
                sensor_filter_type = sensor_config.get('filter', self.filter_configs.get('default_filter'))
                filtered_value = self._apply_filter([scaled_value], sensor_filter_type, sensor_name)[0]

                # print(f"filtered value: {filtered_value}")

                # Adjust the filtered_value
                #filtered_data[sensor_name] = round(abs(filtered_value - self.max_angle[sensor_name]), self.decimals)
                filtered_data[sensor_name] = round(filtered_value - self.min_angle[sensor_name], self.decimals)

            else:
                filtered_data[sensor_name] = scaled_value

        return filtered_data

    @staticmethod
    def calibrate_pressure(voltage: float, sensor_config: Dict) -> float:
        """Calibrate pressure value based on the voltage."""
        if voltage > 0.40:
            return (1000 * (voltage - 0.5) / (4.5 - 0.5)) * sensor_config['calibration_value']
        else:
            return 0

    @staticmethod
    def calibrate_angle(voltage: float, sensor_config: Dict) -> float:
        """Calibrate angle value based on the voltage."""
        steps_per_revolution = sensor_config.get('steps_per_revolution')
        angle = (voltage - 0.5) * steps_per_revolution / (4.5 - 0.5)
        return angle

    def _update_sensor_range(self, sensor_type: str, sensor_name: str, value: float):
        """Update the minimum and maximum range for a sensor."""
        if sensor_type == 'pressure':
            min_dict, max_dict = self.min_pressure, self.max_pressure
        elif sensor_type == 'angle':
            min_dict, max_dict = self.min_angle, self.max_angle
        else:
            print(f"Unknown sensor type: {sensor_type}")
            return

        if sensor_name not in min_dict or value < min_dict[sensor_name]:
            min_dict[sensor_name] = value
        if sensor_name not in max_dict or value > max_dict[sensor_name]:
            max_dict[sensor_name] = value

    def _apply_filter(self, data: List[float], filter_type: str, sensor_name: Optional[str] = None) -> List[float]:
        """Apply the specified filter to the data."""
        filter_settings = self.filter_configs.get(filter_type, {})

        if sensor_name and sensor_name in self.filter_configs:
            sensor_filter_config = self.filter_configs.get(sensor_name, {})
            filter_settings.update(sensor_filter_config)

        if filter_type == 'low_pass':
            alpha = filter_settings.get('alpha')
            return self._low_pass_filter(data, alpha)
        elif filter_type == 'kalman':
            Q = filter_settings.get('Q')
            R = filter_settings.get('R')
            P = filter_settings.get('P')

            return self._kalman_filter(data, Q, R, P)  # Removed x0 here
        else:
            print(f"Unknown filter type: {filter_type}. Returning raw data.")
            return data

    @staticmethod
    def _low_pass_filter(data: List[float], alpha: float) -> List[float]:
        """Apply a low-pass filter to the data."""
        filtered_data = []
        prev_value = data[0] if data else 0
        for value in data:
            filtered_value = alpha * prev_value + (1 - alpha) * value
            filtered_data.append(filtered_value)
            prev_value = filtered_value
        return filtered_data

    @staticmethod
    def _kalman_filter(data: List[float], Q: float, R: float, P: float) -> List[float]:
        """Apply a Kalman filter to the data."""
        if not data:
            return []

        # Initialize the first estimate with the first data point
        x = data[0]
        filtered_data = [x]  # Start the filtered data list with the initial value

        for z in data[1:]:
            # Prediction step
            P = P + Q  # Increase the estimate uncertainty
            # Measurement update
            K = P / (P + R)  # Calculate the Kalman Gain
            x = x + K * (z - x)  # Update the estimate with measurement z
            P = (1 - K) * P  # Update the error covariance

            filtered_data.append(x)

        return filtered_data

    def get_angle_range(self) -> Dict[str, Tuple[float, float, float, float]]:
        """Calculate and return the calibrated angle range for each sensor."""
        angle_ranges = {}
        for sensor_name in self.angle_sensors.keys():
            min_angle = round(self.min_angle.get(sensor_name), self.decimals)
            max_angle = round(self.max_angle.get(sensor_name), self.decimals)

            if min_angle is not None and max_angle is not None:
                angle_range = max_angle - min_angle
                # round self.decimals
                angle_ranges[sensor_name] = (0, angle_range, min_angle, max_angle)
            else:
                angle_ranges[sensor_name] = (None, None, None, None)

        return angle_ranges

    def reset_angle_range(self):
        """Reset the range of calibrated angles."""
        self.min_angle = {sensor: float('inf') for sensor in self.angle_sensors}
        self.max_angle = {sensor: float('-inf') for sensor in self.angle_sensors}

    def get_pressure_range(self) -> Dict[str, Tuple[float, float]]:
        """Get the range of observed pressures for each sensor."""
        ranges = {}
        for sensor_name in self.pressure_sensors.keys():
            min_pressure = self.min_pressure.get(sensor_name)
            max_pressure = self.max_pressure.get(sensor_name)
            ranges[sensor_name] = (min_pressure, max_pressure)
        return ranges

    def reset_pressure_range(self):
        """Reset the range of calibrated pressures."""
        self.min_pressure = {}
        self.max_pressure = {}

    def list_sensors(self):
        """List all available sensors."""
        if not self.initialized:
            print("ADCPi not initialized!")
            return

        print("Available Sensors:")
        print("Pressure Sensors:")
        for sensor_name in self.pressure_sensors.keys():
            print(f"  {sensor_name}")

        print("Angle Sensors:")
        for sensor_name in self.angle_sensors.keys():
            print(f"  {sensor_name}")
        print("-" * 30)


class ADCPiStub:
    """
    ADC stub class used for simulating ADC behavior in the absence of actual hardware.
    Generates synthetic voltage readings using sine waves and various types of noise.
    Includes options for configuring the sine wave properties, noise levels, and adding spikes.
    """
    # TODO: noise and spike customization
    # TODO: "black box" -data output
    def __init__(self, addr1, addr2, bit_rate, min_voltage, max_voltage, frequency):
        """
        Initialize a stub for simulating ADCPi behavior.

        :param addr1: First I2C address (does not matteri when using stubs).
        :param addr2: Second I2C address (does not matter when using stubs).
        :param bit_rate: Bit rate of the ADC.
        :param min_voltage: Minimum voltage for simulation.
        :param max_voltage: Maximum voltage for simulation.
        :param frequency: Frequency of the sine wave for simulation.
        """
        self.addr1 = addr1
        self.addr2 = addr2
        self.bit_rate = bit_rate
        self.conversion_mode = 0
        self.pga_gain = 1
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage
        self.frequency = frequency
        self.start_time = time.time()

        # Noise stuff
        self.white_noise_level = 0.05
        self.pink_noise_level = 0.02
        self.spike_probability = 0.01
        self.spike_magnitude = 0.2

    def set_conversion_mode(self, mode):
        self.conversion_mode = mode

    def set_pga(self, gain):
        self.pga_gain = gain

    def generate_noise(self):
        """
        Generate noise for simulation.

        :return: Random noise value.
        """
        white_noise = random.uniform(-self.white_noise_level, self.white_noise_level)
        pink_noise = self.pink_noise_level * (random.random() - 0.5) / 2
        noise = white_noise + pink_noise
        if random.random() < self.spike_probability:
            noise += random.choice([-1, 1]) * self.spike_magnitude
        return noise

    def generate_wave(self, elapsed_time):
        """
        Generate a sine wave for simulation.

        :param elapsed_time: Time elapsed since the start.
        :return: Simulated voltage value.
        """
        amplitude = (self.max_voltage - self.min_voltage) / 2
        mid_point = self.min_voltage + amplitude
        return mid_point + amplitude * math.sin(2 * math.pi * self.frequency * elapsed_time)

    def read_voltage(self, channel, create_sine=True, add_noise=True):

        # TODO: Return same amount of values as there are sensors configured

        """
        Read simulated voltage value.

        :param channel: ADC channel (not used in simulation).
        :param add_noise: Whether to add noise to the value.
        :return: Simulated voltage value.
        """
        elapsed_time = time.time() - self.start_time

        # Sine wave
        if create_sine:
            voltage = self.generate_wave(elapsed_time)
        else:
            voltage = random.uniform(self.min_voltage, self.max_voltage)
        # Noise
        if add_noise:
            voltage += self.generate_noise()
        return round(max(min(voltage, self.max_voltage), self.min_voltage), 2)
