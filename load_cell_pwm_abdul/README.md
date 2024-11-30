#######Weight Measurement with HX711 and Raspberry Pi
This Python script interfaces with an HX711 load cell amplifier to measure weight using a load cell and a Raspberry Pi. The code captures the raw data from the HX711 and converts it to a meaningful weight value (in grams) by calibrating the scale with a known weight. The script continuously reads and prints the weight on the scale until it is interrupted.

Prerequisites
Before running the script, ensure that the following requirements are met:

Raspberry Pi: Any model with GPIO pins (tested on Raspberry Pi 3/4).
HX711 Load Cell Amplifier: Used to read the output from the load cell.
Load Cell: The sensor used to measure weight.
Python Libraries: The script requires the following libraries:
RPi.GPIO: For interacting with the Raspberry Pi’s GPIO pins.
hx711: The HX711 library for communicating with the HX711 load cell amplifier.
You can install the necessary libraries using pip:

bash
Copy code
pip install RPi.GPIO hx711
Wiring Diagram
The HX711 is connected to the Raspberry Pi via the GPIO pins:

DOUT: Pin 21 (GPIO21)
PD_SCK: Pin 20 (GPIO20)
Make sure the load cell is connected to the HX711 amplifier module 

***********************************************************************
#This is the code for example.py

************************************************************************************************************************

#!/usr/bin/env python3
import RPi.GPIO as GPIO  # import GPIO
from hx711 import HX711  # import the class HX711

try:
    GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering
    # Create an object hx which represents your real hx711 chip
    # Required input parameters are only 'dout_pin' and 'pd_sck_pin'
    hx = HX711(dout_pin=21, pd_sck_pin=20)
    # measure tare and save the value as offset for current channel
    # and gain selected. That means channel A and gain 128
    err = hx.zero()
    # check if successful
    if err:
        raise ValueError('Tare is unsuccessful.')

    reading = hx.get_raw_data_mean()
    if reading:  # always check if you get correct value or only False
        # now the value is close to 0
        print('Data subtracted by offset but still not converted to units:',
              reading)
    else:
        print('invalid data', reading)

    # In order to calculate the conversion ratio to some units, in my case I want grams,
    # you must have known weight.
    input('Put known weight on the scale and then press Enter')
    reading = hx.get_data_mean()
    if reading:
        print('Mean value from HX711 subtracted by offset:', reading)
        known_weight_grams = input(
            'Write how many grams it was and press Enter: ')
        try:
            value = float(known_weight_grams)
            print(value, 'grams')
        except ValueError:
            print('Expected integer or float and I have got:',
                  known_weight_grams)

        # set scale ratio for particular channel and gain which is
        # used to calculate the conversion to units. Required argument is only
        # scale ratio. Without arguments 'channel' and 'gain_A' it sets
        # the ratio for current channel and gain.
        ratio = reading / value  # calculate the ratio for channel A and gain 128
        hx.set_scale_ratio(ratio)  # set ratio for current channel
        print('Ratio is set.')
    else:
        raise ValueError('Cannot calculate mean value. Try debug mode. Variable reading:', reading)

    # Read data several times and return mean value
    # subtracted by offset and converted by scale ratio to
    # desired units. In my case in grams.
    print("Now, I will read data in infinite loop. To exit press 'CTRL + C'")
    input('Press Enter to begin reading')
    print('Current weight on the scale in grams is: ')
    while True:
        print(hx.get_weight_mean(20), 'g')

except (KeyboardInterrupt, SystemExit):
    print('Bye :)')

finally:
    GPIO.cleanup()


************************************************************************************************


    

