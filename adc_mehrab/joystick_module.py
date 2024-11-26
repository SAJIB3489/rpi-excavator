

import math
import threading
import time
from inputs import get_gamepad, UnpluggedError


class XboxController:
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):
        self.reset_values()
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._connected = False
        self.start_monitoring()

    def reset_values(self):
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
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
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

    def start_monitoring(self):
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_controller)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()

    def stop_monitoring(self):
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()

    def read(self):
        if not self._connected:
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
            'X': self.X,
            'Y': self.Y,
            'B': self.B,
            'LeftThumb': self.LeftThumb,
            'RightThumb': self.RightThumb,
            'Back': self.Back,
            'Start': self.Start,
            'LeftDPad': self.LeftDPad,
            'RightDPad': self.RightDPad,
            'UpDPad': self.UpDPad,
            'DownDPad': self.DownDPad
        }

    def _monitor_controller(self):
        while not self._stop_event.is_set():
            try:
                events = get_gamepad()
                self._connected = True
                for event in events:
                    self._process_event(event)
            except UnpluggedError:
                if self._connected:
                    print("Controller disconnected. Attempting to reconnect...")
                    self._connected = False
                    self.reset_values()
                self._attempt_reconnect()

    def _process_event(self, event):
        if event.code == 'ABS_Y':
            self.LeftJoystickY = event.state / self.MAX_JOY_VAL
        elif event.code == 'ABS_X':
            self.LeftJoystickX = event.state / self.MAX_JOY_VAL
        elif event.code == 'ABS_RY':
            self.RightJoystickY = event.state / self.MAX_JOY_VAL
        elif event.code == 'ABS_RX':
            self.RightJoystickX = event.state / self.MAX_JOY_VAL
        elif event.code == 'ABS_Z':
            self.LeftTrigger = event.state / self.MAX_TRIG_VAL
        elif event.code == 'ABS_RZ':
            self.RightTrigger = event.state / self.MAX_TRIG_VAL
        elif event.code == 'BTN_TL':
            self.LeftBumper = event.state
        elif event.code == 'BTN_TR':
            self.RightBumper = event.state
        elif event.code == 'BTN_SOUTH':
            self.A = event.state
        elif event.code == 'BTN_NORTH':
            self.Y = event.state
        elif event.code == 'BTN_WEST':
            self.X = event.state
        elif event.code == 'BTN_EAST':
            self.B = event.state
        elif event.code == 'BTN_THUMBL':
            self.LeftThumb = event.state
        elif event.code == 'BTN_THUMBR':
            self.RightThumb = event.state
        elif event.code == 'BTN_SELECT':
            self.Back = event.state
        elif event.code == 'BTN_START':
            self.Start = event.state
        elif event.code == 'BTN_TRIGGER_HAPPY1':
            self.LeftDPad = event.state
        elif event.code == 'BTN_TRIGGER_HAPPY2':
            self.RightDPad = event.state
        elif event.code == 'BTN_TRIGGER_HAPPY3':
            self.UpDPad = event.state
        elif event.code == 'BTN_TRIGGER_HAPPY4':
            self.DownDPad = event.state

    def _attempt_reconnect(self):
        wait_delay = 3
        attempt = 0
        while not self._stop_event.is_set():
            try:
                get_gamepad()
                print("[JOYSTICK] Controller reconnected successfully!")
                self._connected = True
                return
            except UnpluggedError:
                attempt += 1
                print(f"[JOYSTICK] Reconnection attempt {attempt} failed. Retrying in {wait_delay} seconds...")
                time.sleep(wait_delay)


    def is_connected(self):
        return self._connected

    def __del__(self):
        self.stop_monitoring()

# Example usage:
"""
if __name__ == "__main__":
    # initialize the controller
    controller = XboxController()

    while True:
        # read values
        print(controller.read())
        # check connection status
        print(f"Connected: {controller.is_connected()}")

        time.sleep(0.1)
"""