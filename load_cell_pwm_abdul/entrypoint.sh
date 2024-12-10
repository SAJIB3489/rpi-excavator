#!/bin/bash

# Execute oled.py and wait for 1 minute
echo "Starting oled.py to display Network and System Status..."
python3 oled.py
sleep 60

# Execute final1.py and keep it running until stopped
echo "Starting final1.py..."
exec python3 final1.py
