## Explain your code here


### Docker

Build the image
```
sudo docker build --no-cache -t adc_app .
```

Create container

```
sudo docker run -it --restart=always -d --name adc \
  --privileged \
  --device /dev/gpiomem \
  --device /dev/ttyUSB0 \
  --device /dev/ttyUSB1 \
  --device /dev/video0 \
  --device /dev/input \
  --net=host \
  -v /var/run/dbus:/var/run/dbus \
  adc_app:latest
  ```


### Configuration_files

``Updated_Own_config.yaml`` contains channel configuration for components of the excvator.

### Control_modules

``PWM_controller.py`` This module implements a PWM (Pulse Width Modulation) controller for servo motors and other PWM-controlled devices.
``joystick_evdev.py`` Contains mapping for Xbox controler.
### main.py

``main.py`` execute ``Updated_Own_config.yaml`` ``PWM_controller.py`` ``joystick_evdev.py`` programmes for operating the excavator.

#### Contributor
Eetu Miettinen and Joni Hänninen
