import math
import threading
import time
import evdev
from evdev import InputDevice, categorize, ecodes


class XboxController:
    """
    A comprehensive Xbox controller interface using evdev.

    Features:
    - Precise joystick mapping with proper center position at 0
    - Dead zone handling for accurate stick positions
    - Automatic reconnection on disconnects
    - Full 16-bit precision for smooth control
    - Complete button and axis mapping
    - Thread-safe monitoring
    """

    # Controller constants
    STICK_MAX = 65536  # Maximum value for joysticks (16-bit)
    #STICK_MAX = 32768  # Maximum value for joysticks (15-bit unsigned)
    STICK_CENTER = STICK_MAX // 2  # Center position
    TRIGGER_MAX = 1024  # Maximum value for triggers
    CENTER_TOLERANCE = 350  # Dead zone size around center position
    MAX_RECONNECT_ATTEMPTS = 5

    def __init__(self):
        """Initialize the controller interface."""
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._connected = False
        self._reconnect_count = 0
        self._device = None

        # Initialize controller values
        self.reset_values()

        # Mapping for analog inputs
        self.axis_map = {
            ecodes.ABS_X: 'LeftJoystickX',
            ecodes.ABS_Y: 'LeftJoystickY',
            ecodes.ABS_BRAKE: 'LeftTrigger',
            ecodes.ABS_GAS: 'RightTrigger',
            ecodes.ABS_Z: 'RightJoystickX',
            ecodes.ABS_RZ: 'RightJoystickY',
            ecodes.ABS_HAT0X: 'DPadX',
            ecodes.ABS_HAT0Y: 'DPadY'
        }

        # Start the monitoring thread
        self.start_monitoring()

    def reset_values(self):
        """Reset all controller values to their defaults."""
        # Joysticks (-1 to 1)
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0

        # Triggers (0 to 1)
        self.LeftTrigger = 0
        self.RightTrigger = 0

        # Buttons (0 or 1)
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0

        # D-pad (-1, 0, or 1 for each axis)
        self.DPadX = 0  # -1 left, +1 right
        self.DPadY = 0  # -1 up, +1 down

    def _find_controller(self):
        """
        Find and return the first available Xbox controller.
        Returns None if no controller is found.
        """
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if "xbox" in device.name.lower():
                return device
        return None

    def start_monitoring(self):
        """Start the controller monitoring thread."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_controller)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop the controller monitoring thread."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()

    def _process_event(self, event):
        if event.type == ecodes.EV_KEY:
            # Button handling remains unchanged
            value = 1 if event.value else 0

            if event.code == ecodes.BTN_SOUTH:
                self.A = value
            elif event.code == ecodes.BTN_NORTH:
                self.Y = value
            elif event.code == ecodes.BTN_WEST:
                self.X = value
            elif event.code == ecodes.BTN_EAST:
                self.B = value
            elif event.code == ecodes.BTN_TL:
                self.LeftBumper = value
            elif event.code == ecodes.BTN_TR:
                self.RightBumper = value
            elif event.code == ecodes.BTN_THUMBL:
                self.LeftThumb = value
            elif event.code == ecodes.BTN_THUMBR:
                self.RightThumb = value
            elif event.code == ecodes.BTN_SELECT:
                self.Back = value
            elif event.code == ecodes.BTN_START:
                self.Start = value

        elif event.type == ecodes.EV_ABS:
            axis_name = self.axis_map.get(event.code)
            if not axis_name:
                return

            if axis_name in ['LeftJoystickX', 'LeftJoystickY', 'RightJoystickX', 'RightJoystickY']:
                # Print raw value first
                #print(f"Raw value: {event.value}")

                # Map the full range (0 to STICK_MAX) to -1 to 1
                # This is a direct linear mapping:
                # 0 -> -1
                # STICK_MAX/2 -> 0
                # STICK_MAX -> 1
                normalized_value = (event.value / (self.STICK_MAX / 2)) - 1.0

                # Print pre-deadzone value
                #print(f"Pre-deadzone: {normalized_value}")

                # Apply deadzone
                if abs(normalized_value) < (self.CENTER_TOLERANCE / (self.STICK_MAX / 2)):
                    normalized_value = 0

                # Print final value
                #print(f"Final value: {normalized_value}\n")

                setattr(self, axis_name, normalized_value)

            elif axis_name in ['LeftTrigger', 'RightTrigger']:
                normalized_value = event.value / self.TRIGGER_MAX
                setattr(self, axis_name, normalized_value)

            elif axis_name in ['DPadX', 'DPadY']:
                setattr(self, axis_name, event.value)

    def _monitor_controller(self):
        """Monitor controller events and handle disconnections."""
        while not self._stop_event.is_set():
            try:
                if not self._device:
                    self._device = self._find_controller()
                    if not self._device:
                        raise OSError("Controller not found")

                self._connected = True
                self._reconnect_count = 0

                for event in self._device.read_loop():
                    if event.type != ecodes.EV_SYN:
                        self._process_event(event)
                    if self._stop_event.is_set():
                        break

            except (OSError, IOError):
                if self._connected:
                    print("[JOYSTICK] Controller disconnected. Attempting to reconnect...")
                    self._connected = False
                    self.reset_values()
                if not self._attempt_reconnect():
                    print("[ERROR] Maximum reconnection attempts reached.")
                    self._stop_event.set()
                    break

    def _attempt_reconnect(self):
        """Attempt to reconnect to the controller."""
        wait_delay = 3
        while not self._stop_event.is_set() and self._reconnect_count < self.MAX_RECONNECT_ATTEMPTS:
            try:
                self._device = self._find_controller()
                if self._device:
                    print("[JOYSTICK] Controller reconnected successfully!")
                    self._connected = True
                    return True
            except OSError:
                pass

            self._reconnect_count += 1
            remaining = self.MAX_RECONNECT_ATTEMPTS - self._reconnect_count
            print(f"[JOYSTICK] Reconnection attempt {self._reconnect_count}/{self.MAX_RECONNECT_ATTEMPTS} "
                  f"failed. {remaining} attempts remaining. "
                  f"Retrying in {wait_delay} seconds...")
            time.sleep(wait_delay)
        return False

    def read(self):
        """
        Read the current state of all controller inputs.
        Returns a dictionary containing all controller values.
        """
        if not self._connected:
            print("[Warning] Controller not connected! (press any button to connect)")
            self.reset_values()

        return {
            'LeftJoystickY': self.LeftJoystickY,
            'LeftJoystickX': self.LeftJoystickX,
            'RightJoystickY': self.RightJoystickY,
            'RightJoystickX': self.RightJoystickX,
            'LeftTrigger': self.LeftTrigger,
            'RightTrigger': self.RightTrigger,
            'LeftBumper': self.LeftBumper,
            'RightBumper': self.RightBumper,
            'A': self.A,
            'X': self.Y, # flipped
            'Y': self.X, # flipped
            'B': self.B,
            'LeftThumb': self.LeftThumb,
            'RightThumb': self.RightThumb,
            'Back': self.Back,
            'Start': self.Start,
            'DPadY': self.DPadY,    # these need to be flipped for some reason
            'DPadX': self.DPadX     # these need to be flipped for some reason
        }

    def is_connected(self):
        """Check if the controller is currently connected."""
        return self._connected

    def __del__(self):
        """Cleanup when the object is deleted."""
        self.stop_monitoring()
        if self._device:
            self._device.close()

"""
# Example usage
if __name__ == "__main__":
    controller = XboxController()

    try:
        while True:
            state = controller.read()
            # print(f"Left stick: X={state['LeftJoystickX']:.2f}, Y={state['LeftJoystickY']:.2f}")
            #print(f"Left trigger: {state['LeftTrigger']:.2f}")
            print(state)
            time.sleep(0.1)
    except KeyboardInterrupt:
        controller.stop_monitoring()
"""