# Startup Script Configuration (for shut_up.py)

This README explains how to set up the `shut_up.py` script to run automatically at system startup using systemctl.

## Why?

The constant ESC beeping is very annoying.

## Prerequisites

- Ensure `shut_up.py` is located at `/home/pi/Documents/masi/shut_up.py`
- Make sure the script has executable permissions: `chmod +x /home/pi/Documents/masi/shut_up.py`

## Setup Instructions

1. Create a new systemd service file:

```bash
sudo nano /etc/systemd/system/shut_up.service
```

2. Add the following content to the file:

```ini
[Unit]
Description=Shut Up Startup Script
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Documents/masi/shut_up.py
User=pi
WorkingDirectory=/home/pi/Documents/masi

[Install]
WantedBy=multi-user.target
```

3. Save and exit the editor (Ctrl+X, then Y, then Enter in nano)

4. Reload the systemd daemon:

```bash
sudo systemctl daemon-reload
```

5. Enable the service to run at startup:

```bash
sudo systemctl enable shut_up.service
```

6. Start the service immediately (optional):

```bash
sudo systemctl start shut_up.service
```

The script will now run automatically after the network target is reached during system startup.
You will hear the ESCs beep happily and then go silent, indicating that the script has successfully executed and network communication is established.
