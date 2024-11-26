import time

class PID:
    def __init__(self, P=1.0, I=0.0, D=0.0, current_time=None, max_output=1.0):
        self.Kp = P
        self.Ki = I
        self.Kd = D

        self.sample_time = 0.00
        self.current_time = current_time if current_time is not None else time.time()
        self.last_time = self.current_time

        self.max_output = max_output  # Maximum value for normalization
        self.clear()

        # Ramp-up related attributes
        self.ramp_up_enabled = False
        self.ramp_rate = 0.1  # Default ramp rate (output units per second)
        self.last_output = 0.0

    def clear(self):
        """Clears PID computations and coefficients"""
        self.SetPoint = 0.0

        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        # Windup Guard
        self.int_error = 0.0
        self.windup_guard = 1.0

        self.output = 0.0

    def update(self, feedback_value, current_time=None):
        """Calculates PID value for given reference feedback and normalizes the output"""
        error = self.SetPoint - feedback_value

        self.current_time = current_time if current_time is not None else time.time()
        delta_time = self.current_time - self.last_time
        delta_error = error - self.last_error

        if (delta_time >= self.sample_time):
            self.PTerm = self.Kp * error
            self.ITerm += error * delta_time

            if (self.ITerm < -self.windup_guard):
                self.ITerm = -self.windup_guard
            elif (self.ITerm > self.windup_guard):
                self.ITerm = self.windup_guard

            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            # Compute raw output
            raw_output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)

            # Normalize output
            if self.max_output != 0:
                normalized_output = max(-self.max_output, min(self.max_output, raw_output))
            else:
                normalized_output = raw_output

            # Apply ramp-up if enabled
            if self.ramp_up_enabled:
                max_change = self.ramp_rate * delta_time
                if abs(normalized_output) > abs(self.last_output):
                    # Ramping up
                    if normalized_output > self.last_output:
                        self.output = min(self.last_output + max_change, normalized_output)
                    else:
                        self.output = max(self.last_output - max_change, normalized_output)
                else:
                    # Allow immediate decrease
                    self.output = normalized_output
            else:
                self.output = normalized_output

            self.last_output = self.output

    def setKp(self, proportional_gain):
        """Sets Proportional Gain"""
        self.Kp = proportional_gain

    def setKi(self, integral_gain):
        """Sets Integral Gain"""
        self.Ki = integral_gain

    def setKd(self, derivative_gain):
        """Sets Derivative Gain"""
        self.Kd = derivative_gain

    def setWindup(self, windup):
        """Sets windup guard"""
        self.windup_guard = windup

    def setSampleTime(self, sample_time):
        """Sets sample time"""
        self.sample_time = sample_time

    def setMaxOutput(self, max_output):
        """Sets the maximum absolute value for normalized output"""
        self.max_output = max_output

    def set_rampup(self, enabled, rate=None):
        """
        Enables or disables the ramp-up feature.

        :param enabled: Boolean to enable or disable ramp-up
        :param rate: Optional parameter to set the ramp rate (output units per second)
        """
        self.ramp_up_enabled = enabled
        if rate is not None:
            self.ramp_rate = rate
        self.last_output = self.output  # Initialize last output to current output