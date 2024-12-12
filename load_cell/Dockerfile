# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgpiod2 \
    python3-dev \
    gcc \
    build-essential \
    libusb-1.0-0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir \
    Adafruit-Blinka==8.50.0 \
    adafruit-circuitpython-busdevice==5.2.10 \
    adafruit-circuitpython-connectionmanager==3.1.2 \
    adafruit-circuitpython-framebuf==1.6.6 \
    adafruit-circuitpython-requests==4.1.8 \
    adafruit-circuitpython-ssd1306==2.12.18 \
    adafruit-circuitpython-typing==1.11.2 \
    Adafruit-GPIO==1.0.3 \
    Adafruit-PlatformDetect==3.75.0 \
    Adafruit-PureIO==1.1.11 \
    Adafruit-SSD1306==1.6.2 \
    binho-host-adapter==0.1.6 \
    colorzero==2.0 \
    gpiozero==2.0.1 \
    HX711==1.0.0 \
    hx711-multi==1.4.1 \
    lgpio==0.2.2.0 \
    numpy==2.1.3 \
    pillow==11.0.0 \
    pyftdi==0.56.0 \
    pyserial==3.5 \
    pyusb==1.2.1 \
    RPi.GPIO==0.7.1 \
    rpi-lgpio==0.6 \
    rpi-ws281x==5.0.0 \
    setuptools==66.1.1 \
    spidev==3.6 \
    sysv-ipc==1.1.0 \
    typing_extensions==4.12.2

# Copy all files from the current folder to the container
COPY . /app

# Set the working directory
WORKDIR /app

# Set the command to run the main script
CMD ["python", "final1.py"]
