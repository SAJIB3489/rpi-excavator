# OLED Network and System Status Display

![image](/attachment/oled.png)

This project provides a Python script to display real-time network and system status information on an SSD1306 OLED display. The script fetches data such as the active network interface, IP address, SSID, Wi-Fi signal strength (RSSI), and CPU temperature. The information is displayed dynamically and toggles between network information and CPU temperature every few seconds.

## Features

- **Network Interface Detection**: Automatically detects the active network interface (wired or wireless).
- **IP Address Display**: Shows the IP address associated with the active interface.
- **Wi-Fi Signal Strength**: Displays a signal strength indicator for wireless connections.
- **CPU Temperature**: Optionally displays the CPU temperature in Celsius.
- **Dynamic Display Toggle**: Alternates between network information and CPU temperature.

## Requirements

### Hardware:
- Raspberry Pi (Including Raspberry Pi 5)
- SSD1306 OLED Display (128x64 pixels)

### Software:
- Python 3.x
- Required Python libraries (will be installed in virtual environment):
  - adafruit-circuitpython-ssd1306
  - PIL (Pillow)
  - rpi-lgpio (for Raspberry Pi 5 only)

## Installation

1. **Enable I2C**:
   ```bash
   sudo raspi-config
   ```
   Navigate to: Interface Options → I2C → Enable

2. **Create and Activate Virtual Environment**:
   ```bash
   # Navigate to your project directory
   cd /path/to/oled.py

   # Create virtual environment
   python3 -m venv oled_screen_venv

   # Activate virtual environment
   source oled_screen_venv/bin/activate
   ```

3. **Install Required Libraries**:
   ```bash
   # Install base requirements
   pip install adafruit-circuitpython-ssd1306 Pillow

   # For Raspberry Pi 5 only
   pip install rpi-lgpio
   ```

4. **Wiring**:
   - Connect the SSD1306 OLED display to the Raspberry Pi using I2C.
     ![WhatsApp Image 2024-11-26 at 18 57_edited](https://github.com/user-attachments/assets/5e1ff0fb-b704-4cd6-b4a3-3521ce9d9232)

   - Ensure the correct I2C address (default is 0x3D) and reset pin (D4) are specified in the script.

5. **Configuration**:
   - Update the `font_path` in the script to point to a valid .ttf font file on your Raspberry Pi.
   - Verify I2C is working by running: `i2cdetect -y 1`

## Usage

1. **Run the Script**: Make sure your virtual environment is activated, then execute:

   ```bash
   python3 oled.py
   ```

2. **Display Information**:
   - The OLED display will start showing the SSID, IP address, and Wi-Fi signal strength if connected wirelessly.
   - For wired connections, it will display "Wired" as the network name.
   - Every 5 seconds, the display toggles between the network information and CPU temperature.

3. **Automatic Startup (Using Virtual Environment)**:
   To run the script automatically at system startup with the virtual environment:

   a. Create a new service file:
      ```bash
      sudo nano /etc/systemd/system/oled-display.service
      ```

   b. Add the following content (adjust paths as necessary):
      ```
      [Unit]
      Description=OLED Network and System Status Display
      After=network.target

      [Service]
      Type=simple
      User=pi
      WorkingDirectory=/path/to/your/project
      Environment=PATH=/path/to/your/oled_screen_venv/bin:$PATH
      ExecStart=/path/to/your/oled_screen_venv/bin/python3 /path/to/your/oled.py
      Restart=always

      [Install]
      WantedBy=multi-user.target
      ```

   c. Enable and start the service:
      ```bash
      sudo systemctl enable oled-display.service
      sudo systemctl start oled-display.service
      ```

## Customization

- **Toggle Interval**: Adjust the interval at which the display toggles between network information and CPU temperature by modifying the `if current_time - last_toggle_time >= 5:` line. Change `5` to your desired interval in seconds.
- **Display Layout**: Modify the `update_display` function to change how information is displayed on the OLED screen.

## Troubleshooting

- **No Display Output**:
  - Ensure the I2C address is correct. Run `i2cdetect -y 1` to find the correct address.
  - Verify that I2C is enabled on the Raspberry Pi.
- **Font Not Found**:
  - Make sure the `font_path` points to a valid font file. You can download a font like Montserrat from Google Fonts and place it in your project directory.
- **Virtual Environment Issues**:
  - Ensure the virtual environment is activated before running pip install commands
  - Check that the paths in the systemd service file match your actual installation paths


  ### Contributor
  Eetu Miettinen, and Joni Hänninen
