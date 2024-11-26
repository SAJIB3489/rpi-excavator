"""
Use this script to test the bno08x sensor for errors
"""

from time import sleep, time
from collections import deque
import board
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import (
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
)

test_results = []

def test_bno08x(num_passes, frequency_hz):
    multiplied_num_passes = num_passes * 1000
    loop_period = 1.0 / frequency_hz

    i2c = board.I2C()
    bno08x = BNO08X_I2C(i2c, address=0x4a)
    bno08x.enable_feature(BNO_REPORT_MAGNETOMETER)
    bno08x.enable_feature(BNO_REPORT_ROTATION_VECTOR)

    loop_count = 0
    failed_measurements = []
    previous_measurements = deque(maxlen=20)
    bno_crashed = False

    print(f"Starting {frequency_hz}Hz test loop...")
    for _ in range(multiplied_num_passes):
        loop_start_time = time()
        try:
            mag_x, mag_y, mag_z = bno08x.magnetic  # pylint:disable=no-member
            quat_i, quat_j, quat_k, quat_real = bno08x.quaternion  # pylint:disable=no-member
            current_measurement = (mag_x, mag_y, mag_z, quat_i, quat_j, quat_k, quat_real)

            # Check for repeated measurements
            if all(current_measurement == previous_measurement for previous_measurement in previous_measurements):
                failed_measurements.append((loop_count, "Sensor data frozen"))
                bno_crashed = True
                break

            previous_measurements.append(current_measurement)
        except Exception as e:
            failed_measurements.append((loop_count, str(e)))

        loop_count += 1

        if loop_count % 1000 == 0 and loop_count != 0:
            fail_rate = (len(failed_measurements) / loop_count) * 100
            print(f"{int(loop_count / 1000)}k loop, failed passes: {len(failed_measurements)} ({fail_rate:.2f}%)")

        time_elapsed = time() - loop_start_time
        sleep_time = max(0, loop_period - time_elapsed)
        sleep(sleep_time)

    if bno_crashed:
        print("Sensor data appears to be frozen. Test loop stopped.")
    else:
        print(f"{frequency_hz}Hz tests done!")
    sleep(1)
    return failed_measurements

def save_test_results_to_file(test_results, num_passes, filename):
    with open(filename, 'w') as file:
        file.write("BNO08x Test Results\n")
        file.write("-----------------------------------------------------------\n")
        for test_name, failures in test_results:
            if failures:
                failure_rate = (len(failures) / (num_passes * 1000)) * 100
                file.write(f"{test_name} with {num_passes} passes - {len(failures)} Failed measurements ({failure_rate:.2f}%):\n")
                for failure in failures:
                    file.write(f"Loop {failure[0]}: Error - {failure[1]}\n")
                file.write("\n")
            else:
                file.write(f"{test_name} - No failures detected.\n")
        file.write("-----------------------------------------------------------\n")


num_passes = int(input("Enter the (thousand) number of measurements to perform: "))

test_results.append(('Test with 30 Hz', test_bno08x(num_passes, 30)))

"""
test_results.append(('Test with 20 Hz', test_bno08x(num_passes, 20)))
test_results.append(('Test with 50 Hz', test_bno08x(num_passes, 50)))
test_results.append(('Test with 100 Hz', test_bno08x(num_passes, 100)))
"""
save_test_results_to_file(test_results, num_passes, "log/bno08x_test_results.txt")
print("Test results saved to 'bno08x_test_results.txt'")

