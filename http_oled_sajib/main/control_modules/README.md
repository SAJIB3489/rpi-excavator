# Control Modules

This repository contains all the needed scripts to control the Excavator. The control modules are responsible for handling network communication, sensor data acquisition, and actuator control.
Please use the configuration files to set up the sensors and controllers according to your hardware setup, these files should not need any changes in the code.

## Modules

### 1. socket_manager.py
- Handles network communication using sockets
- Supports both client and server modes
- Implements data buffering and logging

### 2. PWM_controller.py
- Controls PWM (Pulse Width Modulation) outputs
- Manages servo motors and other PWM-controlled devices

### 3. IMU_sensors.py
- Interfaces with IMU (Inertial Measurement Unit) sensors
- Implements Kalman and Complementary filters for sensor fusion
- Provides real-time orientation data

### 4. GPIO_sensors.py
- Manages GPIO-based sensors, including RPM sensors
- Utilizes hardware interrupts for efficient data collection
- Supports various GPIO sensor types

### 5. ADC_sensors.py
- Interfaces with Analog-to-Digital Converter (ADC) sensors
- Supports pressure and angle sensors
- Implements calibration and filtering options

## Features
- Configurable using YAML files
- Simulation modes for testing without hardware
- Thread-safe operations
- Extensible architecture for adding new sensor types

## Requirements
- Python 3.x
- Additional libraries: PyYAML, NumPy, RPi.GPIO (for Raspberry Pi)
- Adafruit libraries for specific sensors

## Usage
1. Install required dependencies
2. Configure sensors and controllers using YAML files
3. Import and initialize relevant modules in your Python script
4. Use provided methods to read sensor data and control outputs


