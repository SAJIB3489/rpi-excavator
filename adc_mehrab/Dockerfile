FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgpiod2 python3-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install \
    Adafruit-Blinka==8.50.0 \
    adafruit-circuitpython-busdevice==5.2.10 \
    adafruit-circuitpython-connectionmanager==3.1.2 \
    adafruit-circuitpython-motor==3.4.14 \
    adafruit-circuitpython-pca9685==3.4.16 \
    adafruit-circuitpython-register==1.10.1 \
    adafruit-circuitpython-requests==4.1.8 \
    adafruit-circuitpython-servokit==1.3.18 \
    adafruit-circuitpython-typing==1.11.2 \
    Adafruit-PlatformDetect==3.75.0 \
    Adafruit-PureIO==1.1.11 \
    binho-host-adapter==0.1.6 \
    evdev==1.7.1 \
    inputs==0.5 \
    pyftdi==0.56.0 \
    pyserial==3.5 \
    pyusb==1.2.1 \
    PyYAML==6.0.2 \
    RPi.GPIO==0.7.1 \
    rpi-ws281x==5.0.0 \
    setuptools==66.1.1 \
    sysv-ipc==1.1.0 \
    typing_extensions==4.12.2 && \
    rm -rf /var/lib/apt/lists/*

# Copy all files from the current folder to the container
COPY . /app

# Set the working directory
WORKDIR /app

# Set the command to run the main script
CMD ["python", "main.py"]
