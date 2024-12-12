
# import PWM (servo controller)
import control_modules.PWM_controller as PWM_controller
# import joystick module (evdev-version)
import control_modules.joystick_evdev as joystick_module
#import time for sleep
from time import sleep


def main(pwm, controller):
    step = 0

    pwm.print_input_mappings()
    sleep(5)

    while True:

        if not controller.is_connected():
            # controller not connected, do nothing
            pass
        else:
            # read all the joystick values
            joy_values = controller.read()
            #print(f"joystick values: {joy_values}")


            # we should modify the trigger values so that they can be flipped with bumper values

            # flip the LeftTrigger and if the LeftBumper is pressed
            if joy_values['LeftBumper']:
                joy_values['LeftTrigger'] = -joy_values['LeftTrigger']

            # flip the RightTrigger and if the RightBumper is pressed
            if joy_values['RightBumper']:
                joy_values['RightTrigger'] = -joy_values['RightTrigger']
                
                
            if joy_values['A']:
                # example, replace with your own logic
                # enable tracks with A button
                pwm.set_tracks(True)
                
            if joy_values['B']:
                # example, replace with your own logic
                # disable tracks with B button
                pwm.set_tracks(False)
                
                
            # example, increa pump stock speed
            #if joy_values['DPadY']:
                #pwm.update_pump(0.01, debug=True)
                
                


            # map the joystick values to the servo controller
            controller_list = [
                joy_values['RightJoystickX'], # scoop, index 0
                joy_values['LeftJoystickY'],  # lift boom, index 1
                joy_values['LeftJoystickX'],  # rotate cabin, index 2
                joy_values['RightJoystickY'],  # tilt boom, index 3
                joy_values['RightTrigger'],    # track R, index 4
                joy_values['LeftTrigger'],   # track L, index 5
            ]

            #print(f"giving input: {joy_values['LeftJoystickX']}")
            print(controller_list)
            # update the servo controller with the new values
            pwm.update_values(controller_list)

            # print every 20 steps
            if step % 20 == 0:
                rate = pwm.get_average_input_rate()
                print(f"average input rate: {rate}")
                step = 0

        step += 1
        sleep(0.01) # rough estimate of the loop time (100Hz)


if __name__ == '__main__':

    # initialize the servo controller
    # you don't need to give all those arguments, but you can if you want to change the default values
    pwm = PWM_controller.PWM_hat(
        config_file='configuration_files/Updated_Own_config.yaml', # where your servo configuration is stored
        simulation_mode=False,                             # set to True if you want to test without a servo controller
        input_rate_threshold=10,                           # minimum input rate needed to enable the servo movement. Set to 0 to disable
        deadzone=20,                                       # deadzone for the input values (% of the input range)
        tracks_disabled=False,                             # set to true if you want to disable the tracked driving
        pump_variable=True                                # set to true if you want to use the automatic pump control
    )


    controller = joystick_module.XboxController()

    try:
        # run the mainloop
        main(pwm, controller)
    except (KeyboardInterrupt, SystemExit):
        print("Exiting...")
        pwm.reset()
