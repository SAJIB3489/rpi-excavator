import numpy as np
#import time
from PID import PID

LOOP_HZ = 10.0

class FeedbackLinearization:
    def __init__(self, system_params):
        self.system_params = system_params
        self.pid1 = PID(P=system_params['Kp'], I=system_params['Ki'], D=system_params['Kd'],
                        max_output=system_params['max_control_input'])
        self.pid2 = PID(P=system_params['Kp'], I=system_params['Ki'], D=system_params['Kd'],
                        max_output=system_params['max_control_input'])
        self.pid3 = PID(P=system_params['Kp'], I=system_params['Ki'], D=system_params['Kd'],
                        max_output=system_params['max_control_input'])

        self.pid1.setSampleTime(1.0 / LOOP_HZ)
        self.pid1.setMaxOutput(1.0)
        self.pid1.setWindup(1.0)

        self.pid2.setSampleTime(1.0 / LOOP_HZ)
        self.pid2.setMaxOutput(1.0)
        self.pid2.setWindup(1.0)

        self.pid3.setSampleTime(1.0 / LOOP_HZ)
        self.pid3.setMaxOutput(1.0)
        self.pid3.setWindup(1.0)



    def custom_boom_linearization(self, pump_pressure, cylinder_pressures, boom_data, desired_angles):
        """
        Perform feedback linearization for a custom hydraulic boom system.

        Args:
        pump_pressure (float): Current pump pressure
        cylinder_pressures (np.array): Pressures for each hydraulic cylinder [p1_extend, p1_retract, p2_extend, p2_retract, p3_extend, p3_retract]
        boom_data (np.array): Accelerometer and gyro data for each boom [kal_angle_x1, kal_angle_x2, kal_angle_x3]
        desired_angles (np.array): Desired angles for each boom [angle1, angle2, angle3]

        Returns:
        np.array: Control inputs for each boom [u1, u2, u3]
        """
        # TODO: pressure calculation
        # combine extend and retract pressures, use the bigger one?????
        cylinder_pressures = np.array([max(cylinder_pressures[0], cylinder_pressures[1]),
                                       max(cylinder_pressures[2], cylinder_pressures[3],
                                       max(cylinder_pressures[4], cylinder_pressures[5]))])

        # Update PID controllers
        self.pid1.SetPoint = desired_angles[0]
        self.pid2.SetPoint = desired_angles[1]
        self.pid3.SetPoint = desired_angles[2]

        self.pid1.update(boom_data[0])
        self.pid2.update(boom_data[1])
        self.pid3.update(boom_data[2])

        # Get PID outputs
        v = np.array([self.pid1.output, self.pid2.output, self.pid3.output])

        # Nonlinear terms
        f = np.array([
            self.nonlinear_term(boom_data[0], cylinder_pressures[0], pump_pressure),
            self.nonlinear_term(boom_data[1], cylinder_pressures[1], pump_pressure),
            self.nonlinear_term(boom_data[2], cylinder_pressures[2], pump_pressure)
        ])

        # Control effectiveness
        g = np.array([
            self.control_effectiveness(boom_data[0], cylinder_pressures[0], pump_pressure),
            self.control_effectiveness(boom_data[1], cylinder_pressures[1], pump_pressure),
            self.control_effectiveness(boom_data[2], cylinder_pressures[2], pump_pressure)
        ])

        # Calculate control input
        u = (v - f) / g

        return u


    def nonlinear_term(self, boom_data, cylinder_pressure, pump_pressure):
        # Implement your nonlinear term calculation here
        # This is a placeholder implementation
        return 0.0

    def control_effectiveness(self, boom_data, cylinder_pressure, pump_pressure):
        # Implement your control effectiveness calculation here
        # This is a placeholder implementation
        return 1.0

# Example usage
if __name__ == "__main__":

    system_params = {
        'Kp': 1.0,
        'Ki': 0.0,
        'Kd': 0.0,
        'max_control_input': 1,  # -1 to 1
        # Add any other parameters your system needs
    }

    feedback_linearization = FeedbackLinearization(system_params)

    pump_pressure = 200.0  # psi
    cylinder_pressures = np.array([180.0, 175.0, 185.0])  # psi
    boom_data = np.array([30.0, 45.0, 60.0])  # degrees
    # ground data calculated in imu_sensors.py!!!!!!
    desired_angles = np.array([30.0, 45.0, 60.0])  # degrees

    control_signals = feedback_linearization.custom_boom_linearization(
        pump_pressure, cylinder_pressures, boom_data, desired_angles
    )

    print("Control signals:", control_signals)