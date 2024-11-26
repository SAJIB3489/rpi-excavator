import asyncio
import time
from control_modules import PWM_controller, socket_manager #ADC_sensors #IMU_sensors

addr = '192.168.0.136'
port = 5111

identification_number = 0  # 0 excavator, 1 Mevea, 2 Motion Platform, more can be added...
inputs = 20  # Number of inputs received from the other end
outputs = 0  # Number of outputs I'm going to send.

# Initialize PWM controller
pwm = PWM_controller.PWM_hat(
    config_file='configuration_files/excavator_channel_configs.yaml',
    simulation_mode=False,
    pump_variable=True,
    tracks_disabled=True,
    deadzone=0.8,
    input_rate_threshold=5
)

# Initialize socket
socket = socket_manager.MasiSocketManager()

# Set up Excavator as server
if not socket.setup_socket(addr, port, identification_number, inputs, outputs, socket_type='server'):
    raise Exception("Could not set up socket!")

# Receive handshake and extra arguments
handshake_result, extra_args = socket.handshake(example_arg_you_could_send_here=69)

if not handshake_result:
    raise Exception("Could not make handshake!")

loop_frequency, int_scale = extra_args[0], extra_args[1]
print(f"Received extra arguments: Loop_freq ({loop_frequency}), int_scale ({int_scale})")

# Update the PWM-controller safety threshold to be 10% of the loop_frequency
pwm.set_threshold(loop_frequency * 0.10)

# Switch socket communication to UDP (to save bandwidth)
socket.tcp_to_udp()



def int_to_float(int_data, decimals=2, scale=int_scale):
    return [round((value / scale), decimals) for value in int_data]

class ButtonState:
    # Button state tracking
    def __init__(self):
        self.states = {}

    def check_button(self, button_index, value, threshold=0.8):
        # check rising edge. Return True if button is pressed and was not pressed before
        # threshold 0.8 because we mangled the data with int_scale
        current_state = value > threshold
        previous_state = self.states.get(button_index, False)
        self.states[button_index] = current_state
        return current_state and not previous_state

async def async_main():
    control_task = asyncio.create_task(control_signal_loop(20))
    # add more non-blocking tasks here (e.g. sensor reading and sending)
    await asyncio.gather(control_task) # remember to add task names here as well

async def control_signal_loop(frequency):
    interval = 1.0 / frequency
    step = 0
    button_state = ButtonState()

    while True:
        start_time = time.time()

        value_list = socket.get_latest_received()

        if value_list is not None:
            float_values = int_to_float(value_list)

            control_values = float_values[:8]
            pwm.update_values(control_values)

            # print average input rate roughly every second
            if step % loop_frequency == 0:
                print(f"Avg rate: {pwm.get_average_input_rate():.2f} Hz")
            step += 1

            """
            TODO: systems for buttons
            pwm.set_threshold(num_hz)                        # change the safety state threshold. Int/float
            pwm.set_tracks(bool)                             # enable/disable tracks
            pwm.set_pump(bool)                               # enable/disable pump
            pwm.toggle_pump_variable(bool)                   # set pump to variable/fixed speed
            pwm.reload_config(file)                          # reload the configuration file
            pwm.print_input_mappings()                       # print the used input mappings
            channel_types = pwm.get_defined_channel_types()  # get the channel types used
            hz_rate = pwm.get_average_input_rate()           # get the average input rate in Hz. Last 30 seconds measured.
            UNTESTED: pwm.update_pump(adjustment)            # increase/decrease pump base speed (please be careful, untested!)
            pwm.reset_pump_load()                            # reset the manual pump adjustment
            """


            # Button checks (mostly placeholders)
            if button_state.check_button(8, float_values[8]):
                print("Right stick rocker up pressed")


            if button_state.check_button(9, float_values[9]):
                print("Right stick rocker down pressed")

            if button_state.check_button(10, float_values[10]):
                print("Right stick button rear pressed")


            if button_state.check_button(11, float_values[11]):
                print("Right stick button bottom pressed")


            if button_state.check_button(12, float_values[12]):
                print("Reloading PWM controller configuration...")
                pwm.reload_config(config_file='configuration_files/excavator_channel_configs.yaml')

            if button_state.check_button(13, float_values[13]):
                print("Right stick button mid pressed")


            if button_state.check_button(14, float_values[14]):
                print("Left stick rocker up pressed")


            if button_state.check_button(15, float_values[15]):
                print("Left stick rocker down pressed")


            if button_state.check_button(16, float_values[16]):
                print("Left stick button rear pressed")


            if button_state.check_button(17, float_values[17]):
                print("Left stick button top pressed")


            if button_state.check_button(18, float_values[18]):
                print("Left stick button bottom pressed")


            if button_state.check_button(19, float_values[19]):
                print("Left stick button mid pressed")


        elapsed_time = time.time() - start_time
        await asyncio.sleep(max(0, interval - elapsed_time))

def run():
    socket.start_data_recv_thread()
    asyncio.run(async_main())

if __name__ == "__main__":
    try:
        run()
    finally:
        pwm.reset()
        socket.stop_all()
        pwm.stop_monitoring()