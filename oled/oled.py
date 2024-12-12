import subprocess
import os
import board
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from time import sleep, time

FONT_PATH = '/home/savonia/Music/Excavator/misc/oled/Montserrat-VariableFont_wght.ttf'
TIME_DELAY = 5  # switch between screens every 5 seconds


# OLED setup
RESET_PIN = digitalio.DigitalInOut(board.D4)
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3D, reset=RESET_PIN)

def clear_display():
    oled.fill(0)
    oled.show()

def get_active_interface():
    try:
        cmd = "ip route get 1.1.1.1 | awk '{print $5}' | head -n 1"
        interface = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return interface
    except subprocess.CalledProcessError:
        return None

def get_ip_address(interface):
    try:
        cmd = f"ip addr show {interface} | grep 'inet ' | awk '{{print $2}}' | cut -d'/' -f1"
        IP = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return IP
    except subprocess.CalledProcessError:
        return "No IP Found"

def get_ssid(interface):
    try:
        cmd = f"iwgetid -r {interface}"
        SSID = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return SSID
    except subprocess.CalledProcessError:
        return "Not Connected"

def get_rssi(interface):
    try:
        cmd = f"iwconfig {interface} | grep 'Signal level' | awk '{{print $4}}' | cut -d'=' -f2"
        rssi = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
        return int(rssi)
    except subprocess.CalledProcessError:
        return None

def get_cpu_temperature():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_str = f.read().strip()
            temp = float(temp_str) / 1000.0  # Convert from millidegree Celsius to Celsius
            return temp
    except IOError:
        return None

def draw_wifi_signal(draw, rssi, x, y):
    if rssi is None:
        return

    bars = 0
    if rssi > -50:
        bars = 3
    elif rssi > -60:
        bars = 2
    elif rssi > -70:
        bars = 1

    bar_width = 5
    bar_height = 3
    spacing = 2

    for i in range(bars):
        draw.rectangle((x, y - i * (bar_height + spacing), x + bar_width, y - i * (bar_height + spacing) + bar_height), outline=255, fill=255)

def update_display(interface, network_name, IP, rssi=None, show_cpu_temp=False):
    width = oled.width
    height = oled.height
    image = Image.new("1", (width, height))
    draw = ImageDraw.Draw(image)

    font_size = 12
    font_size_ip = 19
    font_savonia = ImageFont.truetype(FONT_PATH, font_size)
    font_savonia_ip = ImageFont.truetype(FONT_PATH, font_size_ip)

    if show_cpu_temp:
        cpu_temp = get_cpu_temperature()
        if cpu_temp is not None:
            cpu_temp_str = f"CPU: {cpu_temp:.0f}C"
            cpu_temp_width = draw.textlength(cpu_temp_str, font=font_savonia)
            cpu_temp_x = (width - cpu_temp_width) // 2
            draw.text((cpu_temp_x, 0), cpu_temp_str, font=font_savonia, fill=255)
    else:
        network_label = "SSID:" if "wlan" in interface else "Network:"
        network_label_width = draw.textlength(network_label, font=font_savonia)
        network_label_x = (width - network_label_width) // 2
        draw.text((network_label_x, 0), network_label, font=font_savonia, fill=255)

    network_name_width = draw.textlength(network_name, font=font_savonia)
    IP_width = draw.textlength(IP, font=font_savonia_ip)

    network_name_x = (width - network_name_width) // 2
    IP_x = (width - IP_width) // 2

    draw.text((network_name_x, 16), network_name, font=font_savonia, fill=255)
    draw.text((IP_x, 32), IP, font=font_savonia_ip, fill=255)
    draw.line((0, 14, width, 14), fill=255)

    if rssi:
        draw_wifi_signal(draw, rssi, width - 10, 10)

    oled.image(image)
    oled.show()

clear_display()

previous_network_name, previous_IP, previous_rssi = None, None, None
toggle_display = False
last_toggle_time = time()

while True:
    current_time = time()
    if current_time - last_toggle_time >= TIME_DELAY:
        toggle_display = not toggle_display
        last_toggle_time = current_time

    interface = get_active_interface()
    IP = get_ip_address(interface) if interface else "NONE"
    network_name = get_ssid(interface) if "wlan" in interface else "Wired" if interface else ""
    rssi = get_rssi(interface) if "wlan" in interface else None

    if network_name != previous_network_name or IP != previous_IP or (rssi and previous_rssi != rssi) or toggle_display != previous_toggle_display:
        update_display(interface, network_name, IP, rssi, show_cpu_temp=toggle_display)
        previous_network_name, previous_IP, previous_rssi, previous_toggle_display = network_name, IP, rssi, toggle_display

    sleep(1)
