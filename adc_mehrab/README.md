## Explain your code here


### Docker

Build the image
```
docker build --no-cache -t adc_app .
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


## How your code will work