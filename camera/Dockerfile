FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgpiod2 \
    libglib2.0-0 \
    python3-dev \
    gcc \
    build-essential \
    libusb-1.0-0-dev \
    libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir \
    Adafruit-Blinka==8.50.0 \
    adafruit-circuitpython-busdevice==5.2.10 \
    adafruit-circuitpython-connectionmanager==3.1.2 \
    adafruit-circuitpython-framebuf==1.6.6 \
    adafruit-circuitpython-requests==4.1.8 \
    adafruit-circuitpython-ssd1306==2.12.18 \
    adafruit-circuitpython-typing==1.11.1 \
    Adafruit-PlatformDetect==3.75.0 \
    Adafruit-PureIO==1.1.11 \
    azure-core==1.32.0 \
    azure-storage-blob==12.23.1 \
    binho-host-adapter==0.1.6 \
    blinker==1.9.0 \
    certifi==2024.8.30 \
    cffi==1.17.1 \
    charset-normalizer==3.4.0 \
    click==8.1.7 \
    colorzero==2.0 \
    cryptography==43.0.3 \
    Flask==3.0.3 \
    gpiod==2.2.2 \
    gpiozero==2.0.1 \
    hx711==1.1.2.3 \
    idna==3.10 \
    isodate==0.7.2 \
    itsdangerous==2.2.0 \
    Jinja2==3.1.4 \
    lgpio==0.2.2.0 \
    MarkupSafe==3.0.2 \
    numpy==2.1.3 \
    opencv-python==4.10.0.84 \
    pillow==11.0.0 \
    pycparser==2.22 \
    pyftdi==0.55.4 \
    pyserial==3.5 \
    pyusb==1.2.1 \
    PyYAML==6.0.2 \
    requests==2.32.3 \
    RPi.GPIO==0.7.1 \
    rpi-lgpio==0.6 \
    rpi-ws281x==5.0.0 \
    setuptools==66.1.1 \
    six==1.16.0 \
    sysv-ipc==1.1.0 \
    typing_extensions==4.12.2 \
    urllib3==2.2.3 \
    Werkzeug==3.1.3 && \
    rm -rf /var/lib/apt/lists/*

# Copy all files from the current folder to the container
COPY . /app

# Set the working directory
WORKDIR /app

# Set the command to run the main script
CMD ["python", "web.py"]
