"""
This module implements a PWM (Pulse Width Modulation) controller for servo motors and other PWM-controlled devices.
It is designed on top of Adafruit ServoKit library.

Key features:
1. Configurable PWM channels using a YAML configuration file
2. Support for different types of PMW outputs: angle (servo), throttle, switch(WIP), and pump
3. Input rate monitoring to detect communication issues
4. Deadzone implementation to prevent unwanted small movements
5. Gamma correction for non-linear servo response
6. Simulation mode for testing without hardware

The main class, PWM_hat, handles:
- Initialization of PWM channels
- Parsing and validating configuration
- Updating PWM values based on input
- Handling special cases like pump control and track disabling
- Resetting the controller to a safe state
- Monitoring input rate for safety

Usage:
1. Create a YAML configuration file defining your PWM channels
2. Initialize the PWM_hat with the configuration file and desired settings
3. Call update_values() method with your input values to control the PWM outputs

"""

#TODO: Better Debugging with Logging!
#TODO: Instead of ServoKit, use the Adafruit_PCA9685 library directly (for more control)
#TODO: channel specific PMW ranges!
#TODO: well not that todo but currently we're controlling motors with angle values, so deprecate the "type" parameter (this goes with the PCA9685 library)


import threading
import yaml # PyYAML
import time

try:
    from adafruit_servokit import ServoKit
    SERVOKIT_AVAILABLE = True
except ImportError:
    SERVOKIT_AVAILABLE = False
    print("PWM module not found. Running in simulation mode.")


class PWM_hat:
    def __init__(self, config_file: str, simulation_mode: bool = False, pump_variable: bool = True,
                 tracks_disabled: bool = False, input_rate_threshold: float = 5, deadzone: float = 6) -> None:
        pwm_channels = 16

        self.simulation_mode = simulation_mode

        with open(config_file, 'r') as file:
            configs = yaml.safe_load(file)
            self.channel_configs = configs['CHANNEL_CONFIGS']

        self.pump_variable = pump_variable
        self.tracks_disabled = tracks_disabled

        self.values = [0.0 for _ in range(pwm_channels)]
        self.num_inputs = self.calculate_num_inputs()
        self.num_outputs = pwm_channels

        print(f"PWM channels in use: {pwm_channels}, inputs in use: {self.num_inputs}")

        self.input_rate_threshold = input_rate_threshold
        self.skip_rate_checking = (input_rate_threshold == 0)
        self.is_safe_state = not self.skip_rate_checking

        self.input_event = threading.Event()
        self.monitor_thread = None
        self.running = False

        self.is_safe_state = True
        self.input_count = 0
        self.last_input_time = time.time()
        self.input_timestamps = []

        self.center_val_servo = 90
        self.deadzone = deadzone

        self.return_servo_angles = False
        self.servo_angles = {}

        self.pump_enabled = True    # Enable pump by default
        self.pump_variable_sum = 0.0
        self.manual_pump_load = 0.0

        if SERVOKIT_AVAILABLE and not self.simulation_mode:
            self.kit = ServoKit(channels=pwm_channels) # refrence_clock_speed=25000000, frequency=50
        else:
            if not self.simulation_mode:
                print("ServoKit is not available. Falling back to simulation mode.")
            print("Using ServoKitStub for simulation.")
            self.kit = ServoKitStub(channels=pwm_channels)

        self.validate_configuration()
        self.defined_channel_types = self.get_defined_channel_types()

        # set servo angles to None at start
        self.servo_angles = {f"{channel_name} angle": None
                             for channel_name, config in self.channel_configs.items()
                             if config['type'] == 'angle'}

        self.reset()

        if not self.skip_rate_checking:    # Start monitoring if threshold is set
            self.start_monitoring()

    def calculate_num_inputs(self) -> int:
        """Calculate the number of input channels specified in the configuration."""
        input_channels = set()
        for config in self.channel_configs.values():
            input_channel = config.get('input_channel')
            if isinstance(input_channel, int):
                input_channels.add(input_channel)
        return len(input_channels)

    def validate_configuration(self) -> None:
        """Validate the configuration file."""
        required_keys = ['type', 'input_channel', 'output_channel', 'direction', 'offset']
        angle_specific_keys = ['multiplier_positive', 'multiplier_negative', 'gamma_positive', 'gamma_negative']
        pump_specific_keys = ['idle', 'multiplier']

        for channel_name, config in self.channel_configs.items():
            # Validate existence of required keys
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing '{key}' in configuration for channel '{channel_name}'")

            # Validate types of operation
            if config['type'] not in ['angle', 'pump']:
                raise ValueError(f"Invalid type '{config['type']}' for channel '{channel_name}'")

            # Validate input_channel
            if config['input_channel'] != 'None':
                if not isinstance(config['input_channel'], int) or not (0 <= config['input_channel'] < self.num_inputs):
                    raise ValueError(f"Invalid input_channel {config['input_channel']} for channel '{channel_name}'")

            # Validate output_channel
            if not isinstance(config['output_channel'], int) or not (0 <= config['output_channel'] < self.num_outputs):
                raise ValueError(f"Invalid output_channel {config['output_channel']} for channel '{channel_name}'")

            # Validate direction
            if config['direction'] not in [-1, 1]:
                raise ValueError(f"Invalid direction {config['direction']} for channel '{channel_name}'")

            # Validate offset
            if not (-30 <= config['offset'] <= 30):
                raise ValueError(f"Offset {config['offset']} out of range (-30 to 30) for channel '{channel_name}'")

            # Validate angle-specific configuration
            if config['type'] == 'angle':
                for key in angle_specific_keys:
                    if key not in config:
                        raise ValueError(f"Missing '{key}' in configuration for angle type channel '{channel_name}'")
                    if 'gamma' in key:
                        if not (0.1 <= config[key] <= 3.0):
                            raise ValueError(
                                f"{key} {config[key]} out of range (0.1 to 3.0) for channel '{channel_name}'")
                    elif 'multiplier' in key:
                        if not (1 <= abs(config[key]) <= 50):
                            raise ValueError(f"{key} {config[key]} out of range (1 to 50) for channel '{channel_name}'")

                # Validate affects_pump
                if 'affects_pump' not in config or not isinstance(config['affects_pump'], bool):
                    raise ValueError(f"Missing or invalid 'affects_pump' for angle type channel '{channel_name}'")

            # Validate pump-specific configuration
            elif config['type'] == 'pump':
                for key in pump_specific_keys:
                    if key not in config:
                        raise ValueError(f"Missing '{key}' in configuration for pump type channel '{channel_name}'")

                if not (-1 <= config['idle'] <= 1):
                    raise ValueError(f"Idle {config['idle']} out of range (-1 to 1) for pump channel '{channel_name}'")

                if not (0 < config['multiplier'] <= 10):
                    raise ValueError(
                        f"Multiplier {config['multiplier']} out of range (0 to 10) for pump channel '{channel_name}'")

        print("Configuration validation completed successfully.")

    def start_monitoring(self) -> None:
        """Start the input rate monitoring thread."""
        if self.skip_rate_checking:
            print("Input rate checking is disabled.")
            return

        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.running = True
            self.monitor_thread = threading.Thread(target=self.monitor_input_rate, daemon=True)
            self.monitor_thread.start()
        else:
            print("Monitoring is already running.")

    def stop_monitoring(self) -> None:
        """Stop the input rate monitoring thread."""
        self.running = False
        if self.monitor_thread is not None:
            self.input_event.set()  # Wake up the thread if it's waiting
            self.monitor_thread.join()
            self.monitor_thread = None
            print("Stopped input rate monitoring...")

    def monitor_input_rate(self) -> None:
        print("Monitoring input rate...")
        while self.running:
            if self.input_event.wait(timeout=1.0 / self.input_rate_threshold):
                self.input_event.clear()
                current_time = time.time()
                time_diff = current_time - self.last_input_time
                self.last_input_time = current_time

                if time_diff > 0:
                    current_rate = 1 / time_diff
                    if current_rate >= self.input_rate_threshold:
                        self.input_count += 1
                        # Require consecutive good inputs. 25% of threshold rate, rounded down
                        if self.input_count >= int(self.input_rate_threshold * 0.25):
                            self.is_safe_state = True
                            self.input_count = 0
                    else:
                        self.input_count = 0

                    # Save the timestamp for monitoring
                    self.input_timestamps.append(current_time)

                    # Remove timestamps older than 30 seconds
                    self.input_timestamps = [t for t in self.input_timestamps if current_time - t <= 30]

            else:
                if self.is_safe_state:
                    print("Input rate too low. Entering safe state...")
                    self.reset(reset_pump=False)
                    self.is_safe_state = False
                    self.input_count = 0

    def update_values(self, raw_values, min_cap=-1, max_cap=1, debug=False):
        # Reset all angles to None at the start of each update
        for key in self.servo_angles:
            self.servo_angles[key] = None

        # Signal the monitoring thread that we have new input
        if not self.skip_rate_checking:
            self.input_event.set()

        if debug:
            print(f"Debug: update_values called with raw_values: {raw_values}")
            print(f"Debug: Current safe state: {self.is_safe_state}")
            print(f"Debug: skip_rate_checking: {self.skip_rate_checking}")



        if not self.skip_rate_checking and not self.is_safe_state:
            print(f"System in safe state. Ignoring input. Average rate: {self.get_average_input_rate():.2f}Hz")
            return

        if raw_values is None:
            self.reset()
            raise ValueError("Input values are None")

        # Turn single input value to a list
        if isinstance(raw_values, (float, int)):
            raw_values = [raw_values]

        if len(raw_values) != self.num_inputs:
            self.reset()
            raise ValueError(f"Expected {self.num_inputs} inputs, but received {len(raw_values)}.")

        deadzone_threshold = self.deadzone / 100.0 * (max_cap - min_cap)

        self.pump_variable_sum = 0.0
        for channel_name, config in self.channel_configs.items():
            input_channel = config['input_channel']
            if input_channel is None or not isinstance(input_channel, int) or input_channel >= len(raw_values):
                continue

            # Check if the value is within the limits
            capped_value = max(min_cap, min(raw_values[input_channel], max_cap))

            # Check deadzone
            if abs(capped_value) < deadzone_threshold:
                capped_value = 0.0

            self.values[config['output_channel']] = capped_value

            if config.get('affects_pump', False):
                self.pump_variable_sum += abs(capped_value)

        # Handle pump if configured
        if 'pump' in self.defined_channel_types:
            self.handle_pump(self.values)

        # Handle angles if configured
        if 'angle' in self.defined_channel_types:
            self.handle_angles(self.values)

    def handle_pump(self, values, debug=False):
        pump_config = self.channel_configs['pump']
        pump_channel = pump_config['output_channel']
        pump_multiplier = pump_config['multiplier']
        pump_idle = pump_config['idle']
        input_channel = pump_config.get('input_channel')

        if debug:
            print(f"Debug: input_channel = {input_channel}, type = {type(input_channel)}")
            print(f"Debug: pump_variable = {self.pump_variable}")
            print(f"Debug: pump_variable_sum = {self.pump_variable_sum}")
            print(f"Debug: manual_pump_load = {self.manual_pump_load}")

        if not self.pump_enabled:
            throttle_value = -1.0  # Set to -1 when pump is disabled
            print("Debug: Pump is disabled")
        elif input_channel is None or input_channel == 'None':
            # No direct input channel, use variable pump sum if enabled
            #print("Debug: No direct input channel")
            if self.pump_variable:
                throttle_value = pump_idle + (pump_multiplier * self.pump_variable_sum)
                #print(f"Debug: Using variable pump sum. Calculated throttle: {throttle_value}")
            else:
                throttle_value = pump_idle + (pump_multiplier / 10)
                #print(f"Debug: Not using variable pump sum. Calculated throttle: {throttle_value}")

            # Add manual pump load
            throttle_value += self.manual_pump_load
            #print(f"Debug: After adding manual pump load. Throttle: {throttle_value}")
        elif isinstance(input_channel, int) and 0 <= input_channel < len(values):
            throttle_value = values[input_channel]
            # print(f"Debug: Using direct input channel {input_channel}. Throttle: {throttle_value}")
        else:
            print(f"Warning: Invalid input channel {input_channel}. Using pump_idle.")
            throttle_value = pump_idle

        throttle_value = max(-1.0, min(1.0, throttle_value))
        #print(f"Debug: Final throttle value after clamping: {throttle_value}")

        self.kit.continuous_servo[pump_channel].throttle = throttle_value

        return throttle_value  # Return the final throttle value for debugging

    def handle_angles(self, values):
        for channel_name, config in self.channel_configs.items():
            if config['type'] == 'angle':
                if self.tracks_disabled and channel_name in ['trackL', 'trackR']:
                    continue

                output_channel = config['output_channel']

                if output_channel >= len(values):
                    print(f"Channel '{channel_name}': No data available.")
                    continue

                input_value = values[output_channel]
                center = self.center_val_servo + config['offset']

                if input_value >= 0:
                    gamma = config.get('gamma_positive', 1)
                    multiplier = config.get('multiplier_positive', 1)
                    normalized_input = input_value
                else:
                    gamma = config.get('gamma_negative', 1)
                    multiplier = config.get('multiplier_negative', 1)
                    normalized_input = -input_value

                adjusted_input = normalized_input ** gamma
                gamma_corrected_value = adjusted_input if input_value >= 0 else -adjusted_input

                angle = center + (gamma_corrected_value * multiplier * config['direction'])
                angle = max(0, min(180, angle))

                self.kit.servo[config['output_channel']].angle = angle
                self.servo_angles[f"{channel_name} angle"] = round(angle, 1)

    def reset(self, reset_pump=True, pump_reset_point=-1.0):
        """
        Reset the controller to the initial state.

        :param reset_pump: Reset the pump to the idle state.
        :param pump_reset_point: The throttle value to set the pump to when resetting. ESC dependant.
        """

        for config in self.channel_configs.values():
            if config['type'] == 'angle':
                self.kit.servo[config['output_channel']].angle = self.center_val_servo + config.get('offset', 0)

        if reset_pump and 'pump' in self.channel_configs:
            self.kit.continuous_servo[self.channel_configs['pump']['output_channel']].throttle = pump_reset_point

        self.is_safe_state = False
        self.input_count = 0

    def set_threshold(self, number_value):
        """Update the input rate threshold value."""
        if not isinstance(number_value, (int, float)) or number_value <= 0:
            print("Threshold value must be a positive number.")
            return
        self.input_rate_threshold = number_value
        print(f"Threshold rate set to: {self.input_rate_threshold}Hz")

    def set_deadzone(self, int_value):
        """Update the Deadzone value"""
        if not isinstance(int_value, int):
            print("Deadzone value must be an integer.")
            return
        self.deadzone = int_value
        print(f"Deadzone set to: {self.deadzone}%")

    def set_tracks(self, bool_value):
        """Enable/Disable tracks"""
        if not isinstance(bool_value, bool):
            print("Tracks value value must be boolean.")
            return
        self.tracks_disabled = bool_value
        print(f"Tracks boolean set to: {self.tracks_disabled}!")

    def set_pump(self, bool_value):
        """Enable/Disable pump"""
        if not isinstance(bool_value, bool):
            print("Pump value must be boolean.")
            return
        self.pump_enabled = bool_value
        print(f"Pump enabled set to: {self.pump_enabled}!")
        # Update pump state immediately
        # self.handle_pump(self.values)

    def toggle_pump_variable(self, bool_value):
        """Enable/Disable pump variable sum (vs static speed)"""
        if not isinstance(bool_value, bool):
            print("Pump variable value must be boolean.")
            return
        self.pump_variable = bool_value
        print(f"Pump variable set to: {self.pump_variable}!")

    def reload_config(self, config_file):
        """Update the configuration file and reinitialize the controller."""
        # Reset the controller
        self.reset()

        # Re-read the config file
        with open(config_file, 'r') as file:
            configs = yaml.safe_load(file)
            self.channel_configs = configs['CHANNEL_CONFIGS']

        # Validate the new configuration
        self.validate_configuration()

        # Reinitialize necessary components
        if SERVOKIT_AVAILABLE and not self.simulation_mode:
            self.kit = ServoKit(channels=self.num_outputs)

        # Restart monitoring if it was running
        if self.running:
            self.stop_monitoring()
            self.start_monitoring()

        print(f"Configuration updated successfully from {config_file}")

    def print_input_mappings(self):
        """Print the input and output mappings for each channel."""
        print("Input mappings:")
        input_to_name_and_output = {}

        for channel_name, config in self.channel_configs.items():
            input_channel = config['input_channel']
            output_channel = config.get('output_channel', 'N/A')  # Get output channel or default to 'N/A'

            if input_channel != 'none' and isinstance(input_channel, int):
                if input_channel not in input_to_name_and_output:
                    input_to_name_and_output[input_channel] = []
                input_to_name_and_output[input_channel].append((channel_name, output_channel))

        for input_num in range(self.num_inputs):
            if input_num in input_to_name_and_output:
                names_and_outputs = ', '.join(
                    f"{name} (PWM output {output})" for name, output in input_to_name_and_output[input_num]
                )
                print(f"Input {input_num}: {names_and_outputs}")
            else:
                print(f"Input {input_num}: Not assigned")

    def get_defined_channel_types(self):
        return set(config['type'] for config in self.channel_configs.values())

    def get_average_input_rate(self) -> float:
        """
        Calculate the average input rate over the last 30 seconds.

        :return: Average input rate in Hz, or 0 if no inputs in the last 30 seconds.
        """
        current_time = time.time()

        # Filter timestamps to last 30 seconds
        recent_timestamps = [t for t in self.input_timestamps if current_time - t <= 30]

        if len(recent_timestamps) < 2:
            return 0.0  # Not enough data to calculate rate

        # Calculate rate based on number of inputs and time span
        time_span = recent_timestamps[-1] - recent_timestamps[0]
        if time_span > 0:
            return (len(recent_timestamps) - 1) / time_span
        else:
            return 0.0  # Avoid division by zero

    def update_pump(self, adjustment, debug=False):
        """
        Manually update the pump load.

        :param adjustment: The adjustment to add to the pump load (float between -1.0 and 1.0)
        :param debug: If True, print debug information
        """
        self.manual_pump_load = max(-1.0, min(1.0, self.manual_pump_load + adjustment))

        # Re-calculate pump throttle with new manual load
        current_throttle = self.handle_pump(self.values)

        if debug:
            print(f"Current pump throttle: {current_throttle:.2f}")
            print(f"Current manual pump load: {self.manual_pump_load:.2f}")
            print(f"Current pump variable sum: {self.pump_variable_sum:.2f}")

    def reset_pump_load(self, debug=False):
        """
        Reset the manual pump load to zero.

        :param debug: If True, print debug information
        """
        self.manual_pump_load = 0.0

        # Re-calculate pump throttle without manual load
        current_throttle = self.handle_pump(self.values)

        if debug:
            print(f"Pump load reset. Current pump throttle: {current_throttle:.2f}")

class ServoKitStub:
    def __init__(self, channels):
        self.channels = channels
        self.servo = [ServoStub() for _ in range(channels)]
        self.continuous_servo = [ContinuousServoStub() for _ in range(channels)]

class ServoStub:
    def __init__(self):
        self._angle = 90

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = max(0, min(180, value))
        print(f"[SIMULATION] Servo angle set to: {self._angle} degrees")

class ContinuousServoStub:
    def __init__(self):
        self._throttle = 0

    @property
    def throttle(self):
        return self._throttle

    @throttle.setter
    def throttle(self, value):
        self._throttle = max(-1, min(1, value))
        print(f"[SIMULATION] Continuous servo throttle set to: {self._throttle}")
