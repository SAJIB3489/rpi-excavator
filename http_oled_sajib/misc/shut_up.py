# stop the beeping at startup
import sys
#import os

# Get the absolute path of the directory containing the module
#module_path = os.path.abspath(os.path.join('..', 'main', 'control_modules'))

module_path = 'home/pi/Documents/masi/main/control_modules'

# Add it to the Python path
if module_path not in sys.path:
    sys.path.append(module_path)

# Now you can import the module
from PWM_controller import PWM_hat

path = '../main/configuration_files/excavator_channel_configs.yaml'

pwm = PWM_hat(
    config_file=path,
    simulation_mode=False,
	input_rate_threshold=0,	# set rate to 0 (or None) to disable rate monitoring
)

# no need to explicitly call pwm.reset() as it is called in the constructor
# also no need to call pwm.stop_monitoring() as input threshold is set to 0