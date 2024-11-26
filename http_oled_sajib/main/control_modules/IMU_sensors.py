import yaml
import adafruit_tca9548a
from adafruit_lsm6ds import Rate
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX as AdafruitISM330DHCX
import board
import numpy as np
from time import time

class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, initial_value=0, initial_estimate_error=1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimate = initial_value
        self.estimate_error = initial_estimate_error
        self.last_update = time()

    def update(self, measurement):
        current_time = time()
        dt = current_time - self.last_update
        self.last_update = current_time

        # Prediction
        prediction = self.estimate
        prediction_error = self.estimate_error + self.process_variance * dt

        # Update
        innovation = measurement - prediction
        innovation_variance = prediction_error + self.measurement_variance
        kalman_gain = prediction_error / innovation_variance
        self.estimate = prediction + kalman_gain * innovation
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimate

class ComplementaryFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.angle = 0

    def update(self, accel_angle, gyro_rate, dt):
        self.angle = self.alpha * (self.angle + gyro_rate * dt) + (1 - self.alpha) * accel_angle
        return self.angle

class ISM330DHCX:
    def __init__(self, config_file, decimals=2):
        # Load configs from .yaml file
        with open(config_file, 'r') as file:
            configs = yaml.safe_load(file)
            self.sensor_configs = configs['IMU_CONFIG']

        self.decimals = decimals
        self.i2c = board.I2C()
        self.tca = adafruit_tca9548a.TCA9548A(self.i2c, address=self.sensor_configs['multiplexer_address'])
        self.sensors = {}
        self.kalman_filters = {}
        self.complementary_filters = {}
        self.last_time = {}
        self.__initialize_ism330()

    def __initialize_ism330(self):
        multiplexer_channels = self.sensor_configs['multiplexer_channels']
        for channel, name in self.sensor_configs['channel_names'].items():
            try:
                self.sensors[channel] = AdafruitISM330DHCX(self.tca[channel])

                # Set the data rates for accelerometer and gyro from config
                accel_data_rate = eval(self.sensor_configs['accelerometer_data_rate'])
                gyro_data_rate = eval(self.sensor_configs['gyro_data_rate'])

                self.sensors[channel].accelerometer_data_rate = accel_data_rate
                self.sensors[channel].gyro_data_rate = gyro_data_rate

                # Initialize Kalman filters for pitch and roll
                self.kalman_filters[channel] = {
                    'pitch': KalmanFilter(0.001, 0.1),
                    'roll': KalmanFilter(0.001, 0.1)
                }

                # Initialize Complementary filters for pitch and roll
                self.complementary_filters[channel] = {
                    'pitch': ComplementaryFilter(alpha=0.98),
                    'roll': ComplementaryFilter(alpha=0.98)
                }

                self.last_time[channel] = time()

                print(f"ISM330DHCX on channel {channel} ({name}) initialized.")
            except Exception as e:
                error_msg = f"Error initializing ISM330DHCX on channel {channel} ({name}): {e}"
                print(error_msg)
                raise RuntimeError(error_msg)

    def read_all(self, read_mode='all'):
        combined_data = {}

        # Read data from each ISM330 sensor
        for channel, name in self.sensor_configs['channel_names'].items():
            try:
                ism330_data = self.read_ism330(channel, read_mode)
                combined_data[name] = ism330_data
            except Exception as e:
                error_msg = f"Failed to read from ISM330 sensor at channel {channel} ({name}): {e}"
                print(error_msg)
                raise RuntimeError(error_msg)

        return combined_data

    def read_ism330(self, channel, read_mode='all'):
        try:
            sensor = self.sensors[channel]
            accel_x, accel_y, accel_z = [round(val, self.decimals) for val in sensor.acceleration]
            gyro_x, gyro_y, gyro_z = [round(val, self.decimals) for val in sensor.gyro]

            if read_mode == 'raw':
                return {
                    'accel_x': accel_x,
                    'accel_y': accel_y,
                    'accel_z': accel_z,
                    'gyro_x': gyro_x,
                    'gyro_y': gyro_y,
                    'gyro_z': gyro_z
                }

            # Calculate pitch and roll from accelerometer data
            accel_pitch = np.arctan2(accel_x, np.sqrt(accel_y**2 + accel_z**2))
            accel_roll = np.arctan2(accel_y, np.sqrt(accel_x**2 + accel_z**2))

            # Apply Kalman filter
            kalman_pitch = self.kalman_filters[channel]['pitch'].update(accel_pitch)
            kalman_roll = self.kalman_filters[channel]['roll'].update(accel_roll)

            # Apply Complementary filter
            current_time = time()
            dt = current_time - self.last_time[channel]
            self.last_time[channel] = current_time

            comp_pitch = self.complementary_filters[channel]['pitch'].update(accel_pitch, gyro_x, dt)
            comp_roll = self.complementary_filters[channel]['roll'].update(accel_roll, gyro_y, dt)

            # Convert to degrees
            kalman_pitch_deg = round(np.degrees(kalman_pitch), self.decimals)
            kalman_roll_deg = round(np.degrees(kalman_roll), self.decimals)
            comp_pitch_deg = round(np.degrees(comp_pitch), self.decimals)
            comp_roll_deg = round(np.degrees(comp_roll), self.decimals)

            if read_mode == 'angles':
                return {
                    'kalman_pitch': kalman_pitch_deg,
                    'kalman_roll': kalman_roll_deg,
                    'comp_pitch': comp_pitch_deg,
                    'comp_roll': comp_roll_deg
                }
            elif read_mode == 'all':
                return {
                    'accel_x': accel_x,
                    'accel_y': accel_y,
                    'accel_z': accel_z,
                    'gyro_x': gyro_x,
                    'gyro_y': gyro_y,
                    'gyro_z': gyro_z,
                    'kalman_pitch': kalman_pitch_deg,
                    'kalman_roll': kalman_roll_deg,
                    'comp_pitch': comp_pitch_deg,
                    'comp_roll': comp_roll_deg
                }
            else:
                raise ValueError("Invalid read_mode. Use 'raw', 'angles', or 'all'.")

        except Exception as e:
            error_msg = f"Error reading from ISM330DHCX on channel {channel}: {e}"
            print(error_msg)
            raise RuntimeError(error_msg)