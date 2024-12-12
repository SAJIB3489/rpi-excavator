### Docker

Build the image
```
sudo docker build --no-cache -t load_cell_app .
```

Create container

```
sudo docker run -it --restart=always -d --name load_cell \
  --device /dev/gpiomem \
  --device /dev/ttyUSB0 \
  --device /dev/ttyUSB1 \
  --device /dev/video0 \
  load_cell_app:latest
  ```

![image3](/attachment/load_cell.png)

Weight Measurement with HX711 and Raspberry Pi
----------------------------------------------
This Python script interfaces with an HX711 load cell amplifier to measure weight using a load cell and a Raspberry Pi. The code captures the raw data from the HX711 and converts it to a meaningful weight value (in grams) by calibrating the scale with a known weight. The script continuously reads and prints the weight on the scale until it is interrupted.

Prerequisites
Before running the script, ensure that the following requirements are met:

Raspberry Pi: Any model with GPIO pins (tested on Raspberry Pi 3/4).
HX711 Load Cell Amplifier: Used to read the output from the load cell.
Load Cell: The sensor used to measure weight.
Python Libraries: The script requires the following libraries:
RPi.GPIO: For interacting with the Raspberry Pi’s GPIO pins.
hx711: The HX711 library for communicating with the HX711 load cell amplifier.

*****************************************************

How the Code Works
------------------
Setup GPIO: The script sets the GPIO pin numbering mode to BCM using GPIO.setmode(GPIO.BCM) to use the BCM pin numbers.

HX711 Initialization: The script creates an instance of the HX711 class, passing the GPIO pins used for data (DOUT) and clock (PD_SCK).

Taring the Scale: The script calls the hx.zero() method to tare the scale. This establishes a baseline by setting the current reading (with no weight) as the offset.

Getting Initial Data: It then takes a raw data reading using hx.get_raw_data_mean(). This reading is subtracted by the offset, but is not yet converted to weight units.

Calibration: The user is prompted to place a known weight on the scale. The script then calculates the scale ratio by comparing the reading to the known weight (in grams) and sets this ratio in the HX711 object.

Continuous Measurement: After calibration, the script enters an infinite loop where it continuously reads the weight on the scale using hx.get_weight_mean(20), which returns the mean weight based on 20 readings. The weight is displayed in grams.

Exit: To exit the program, press CTRL + C.


***********************************************************************

How the Data is output:
------------------------

Data subtracted by offset but still not converted to units: 1050
Mean value from HX711 subtracted by offset: 1050
Write how many grams it was and press Enter: 500
500.0 grams
Ratio is set.
Now, I will read data in infinite loop. To exit press 'CTRL + C'
Press Enter to begin reading
Current weight on the scale in grams is:
47.00 g
46.00 g
-17.98 g
...


# How i made it work?
-------------------

Under my Folder - Abduls_Part, I created a virtual environment abdul_venv.

```
python3 -m venv abdul_venv
```

Then i had to activate it to get into my virtual env.

```
source abdul_venv/bin/activate
```

In my folder consisits of another folder hx711py within the folder Python_examples.

Then i uninstalled the current gpio package and libraries assosicated with it.

After further reasearch and finding the root cause of the issue that i was facing since the raspberry pi 5 was not compatible with the raspberry pi 4.

The source link where I found it:

https://stackoverflow.com/questions/78330125/gpio-programming-issues-in-python-3-for-raspberry-pi-5


These were the commands i used: 

```
sudo apt remove python3-rpi.gpio 
sudo apt install python3-rpi-lgpio
```

Then i made some changes in my final.py code for the new library to run which i cant recall exactly. I have Calibrated the load cell first with the another code: Calibrate.py

#Measuring a phone of roughly measuring: 105 grams.


![WhatsApp Image 2024-12-03 at 17 38 22](https://github.com/user-attachments/assets/58bde09b-2df8-4f40-9f05-66eedec4ced3)


#The results printed using the raspberry pi 5 with the code run:

    
![WhatsApp Image 2024-12-03 at 17 38 24](https://github.com/user-attachments/assets/cece2b5d-bf6b-4571-acca-53bccbd0d6d8)


