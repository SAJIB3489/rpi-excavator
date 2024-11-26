# Excavator Control System Configuration Files

This repository contains the configuration files for the excavator control system. These YAML files are used to set up and customize the behavior of various control modules.

## Files

1. `excavator_channel_configs.yaml`
   - Configures PWM channels for different components (e.g., pump, tracks, boom, scoop)
   - Defines input/output mappings, servo offsets, and response curves

2. `excavator_config.yaml`
   - Contains system-wide settings
   - Specifies network configuration, PWM controller settings, and sensor parameters
   - Sets logging levels and performance parameters

3. `excavator_sensor_configs.yaml`
   - Configures various sensors: ADC, RPM, pressure, and IMU
   - Defines filtering options and calibration values

## Key Configuration Areas

- **PWM Control**: Fine-tune servo and motor responses
- **Network Settings**: Set IP address and port for communication
- **Sensor Calibration**: Adjust sensor readings for accuracy
- **Filter Configuration**: Customize data filtering for smooth operation
- **Performance Tuning**: Set data send/receive frequencies

## Usage

1. Review and modify these YAML files to get wanted behaviour. You can add or remove settings as needed (e.g. add new sensors, or remove PWM channels).
2. Ensure these configuration files are placed in the `configuration_files/` directory of your project.
3. The control modules will read these configurations on startup to initialize the system correctly.

## Important Notes

- Be cautious when modifying these files, as incorrect settings can lead to unexpected behavior.

For detailed information on each setting, refer to the comments within the YAML files.
