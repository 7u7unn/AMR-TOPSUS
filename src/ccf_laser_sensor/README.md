# ccf_laser_sensor

ROS2 driver package for the **CCF-LAS4-4M** 5-channel laser obstacle avoidance
sensor by Beijing Xintuo Future Technology Co., Ltd.

| Spec | Value |
|------|-------|
| Model | CCF-LAS4-4M |
| Valid distance channels | 5 laser beams |
| Range | 1 – 700 cm |
| Horizontal FOV | ≤ 180° |
| Vertical FOV | ≤ 25° |
| Interface | RS485, Modbus RTU |
| Supply voltage | DC 6 – 30 V |
| Default baud | 9600 |
| Default slave | 1 |
| Response time | ~30 ms |

---

## Package layout

```
ccf_laser_sensor/
├── ccf_laser_sensor/
│   ├── __init__.py
│   ├── modbus_rtu.py       # CRC, frame builder, frame parser, serial query
│   └── ccf_laser_node.py   # ROS2 Node
├── config/
│   └── ccf_laser_params.yaml
├── launch/
│   └── ccf_laser.launch.py
├── package.xml
├── setup.cfg
└── setup.py
```

---

## Installation

```bash
# 1. Copy package into your ROS2 workspace src/
cp -r ccf_laser_sensor ~/ros2_ws/src/

# 2. Install Python dependency
pip install pyserial

# 3. Build
cd ~/ros2_ws
colcon build --packages-select ccf_laser_sensor
source install/setup.bash
```

### Serial port permissions
```bash
sudo usermod -aG dialout $USER
# Log out and back in, or run:
newgrp dialout
```

Verify the sensor port is visible:
```bash
ls -l /dev/serial/by-path/ | grep "3.3:1.0"
```

---

## Running

```bash
# Default – uses config/ccf_laser_params.yaml
ros2 launch ccf_laser_sensor ccf_laser.launch.py

# Override slave address and port at launch time
ros2 launch ccf_laser_sensor ccf_laser.launch.py slave:=2 port:=/dev/ttyUSB0

# Or run the node directly
ros2 run ccf_laser_sensor ccf_laser_node \
  --ros-args \
  -p port:='/dev/serial/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-port0' \
  -p slave:=1 \
  -p baud:=9600
```

---

## Published topics

| Topic | Type | Description |
|-------|------|-------------|
| `~/front_laser` | `std_msgs/Float32MultiArray` | 5 raw distance values; `inf` = out of range |
| `~/front_laser_scan` | `sensor_msgs/LaserScan` | 5-beam scan, angles –90° … +90° (45° step) |

### Viewing data
```bash
ros2 topic echo /ccf_laser_node/front_laser
ros2 topic echo /ccf_laser_node/front_laser_scan
# Visualise in RViz2:
ros2 run rviz2 rviz2   # Add → LaserScan → topic /ccf_laser_node/front_laser_scan
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | string | `/dev/serial/by-path/…` | Serial device path |
| `baud` | int | `9600` | Baud rate |
| `slave` | int | `1` | Modbus slave address |
| `period` | double | `0.05` | Poll interval (s) → 20 Hz |
| `num_channels` | int | `5` | Number of valid distance channels to read |
| `start_reg` | int | `0` | First Modbus register (0x0000) |
| `range_scale` | double | `0.001` | Raw unit → metres (1 raw = 1 mm) |
| `range_max_m` | double | `7.0` | Maximum range in metres |
| `frame_id` | string | `ccf_laser_link` | TF frame for LaserScan |
| `topic_dist` | string | `/front_laser` | Float32MultiArray topic name |
| `topic_scan` | string | `/front_laser_scan` | LaserScan topic name |

---

## Modbus register map

| Register | Channel | Description |
|----------|---------|-------------|
| 0x0000 | 1 | Leftmost beam (–90°) |
| 0x0001 | 2 | –45° |
| 0x0002 | 3 | 0° |
| 0x0003 | 4 | +45° |
| 0x0004 | 5 | Rightmost beam (+90°) |

Registers 0x0005 and 0x0006 are non-distance values and are ignored.

> `0xFFFF` (65535) and `0` are treated as no detection / out of range and published as `inf`. Raw value `255` is preserved as a valid reading because it sits in the non-distance register area that is ignored by the driver.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `Cannot open serial port` | Permission denied | `sudo usermod -aG dialout $USER` |
| `Cannot open serial port` | Wrong path | Check `ls /dev/serial/by-path/` |
| `CRC mismatch` | Wrong baud rate | Confirm baud in YAML matches sensor config |
| `Modbus exception code` | Wrong slave address | Change `slave` parameter |
| All channels = `inf` | Sensor out of range or object too close (<1 cm) | Normal operation |
| Short frames | USB cable / RS485 adapter issue | Check wiring; try lower baud |
