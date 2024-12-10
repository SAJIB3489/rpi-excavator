# OLED Network and System Status Display

This project provides a Python script to display real-time network and system status information on an SSD1306 OLED display. The script fetches data such as the active network interface, IP address, SSID, Wi-Fi signal strength (RSSI), and CPU temperature. The information is displayed dynamically and toggles between network information and CPU temperature every few seconds.

## Features

- **Network Interface Detection**: Automatically detects the active network interface (wired or wireless).
- **IP Address Display**: Shows the IP address associated with the active interface.
- **Wi-Fi Signal Strength**: Displays a signal strength indicator for wireless connections.
- **CPU Temperature**: Optionally displays the CPU temperature in Celsius.
- **Dynamic Display Toggle**: Alternates between network information and CPU temperature.

## Requirements

### Hardware:
- Raspberry Pi
- SSD1306 OLED Display (128x64 pixels)

### Software:
- Python 3.x
- Required Python libraries:
  - adafruit-circuitpython-ssd1306
  - PIL (Pillow)
  - pyyaml

## Installation

1. **Install Required Libraries**: Run the following command to install the necessary Python libraries:

   ```bash
   pip install adafruit-circuitpython-ssd1306 Pillow pyyaml
   ```

2. **Wiring**:
   - Connect the SSD1306 OLED display to the Raspberry Pi using I2C.
   - Ensure the correct I2C address (default is 0x3D) and reset pin (D4) are specified in the script.

3. **Configuration**:
   - Update the `font_path` in the script to point to a valid .ttf font file on your Raspberry Pi.
   - Ensure I2C is enabled on your Raspberry Pi. You can enable I2C via `raspi-config` under "Interfacing Options."

## Usage

1. **Run the Script**: Execute the script using Python 3:

   ```bash
   python3 oled.py
   ```

2. **Display Information**:
   - The OLED display will start showing the SSID, IP address, and Wi-Fi signal strength if connected wirelessly.
   - For wired connections, it will display "Wired" as the network name.
   - Every 5 seconds, the display toggles between the network information and CPU temperature.

3. **Automatic Startup** (Recommended):
   To run the script automatically at system startup after the network is available, you can set up a systemd service:

   a. Create a new service file:
      ```bash
      sudo nano /etc/systemd/system/oled-display.service
      ```

   b. Add the following content to the file (adjust paths as necessary):
      ```
      [Unit]
      Description=OLED Network and System Status Display
      After=network.target

      [Service]
      ExecStart=/usr/bin/python3 /path/to/your/oled.py
      Restart=always
      User=pi

      [Install]
      WantedBy=multi-user.target
      ```

   c. Save and close the file, then enable and start the service:
      ```bash
      sudo systemctl enable oled-display.service
      sudo systemctl start oled-display.service
      ```

   This will ensure that your OLED display script runs automatically after the network is available on system startup.

## Customization

- **Toggle Interval**: Adjust the interval at which the display toggles between network information and CPU temperature by modifying the `if current_time - last_toggle_time >= 5:` line. Change `5` to your desired interval in seconds.
- **Display Layout**: Modify the `update_display` function to change how information is displayed on the OLED screen.

## Troubleshooting

- **No Display Output**:
  - Ensure the I2C address is correct. Run `i2cdetect -y 1` to find the correct address.
  - Verify that I2C is enabled on the Raspberry Pi.
- **Font Not Found**:
  - Make sure the `font_path` points to a valid font file. You can download a font like Montserrat from Google Fonts and place it in your project directory.


