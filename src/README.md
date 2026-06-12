# AMR (Autonomous Mobile Robot) - Arya AMR System

ROS 2-based autonomous mobile robot platform for indoor navigation, line following, and web interface control.

## Overview

This repository contains the complete software stack for the Arya AMR, featuring:
- **Navigation 2** for autonomous path planning and localization
- **SLAM** for simultaneous localization and mapping
- **Magnetic line follower** for guided path following
- **Web interface** for remote monitoring and control
- **Sensor fusion** for IMU, LiDAR, and obstacle detection

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Web Interface (arya_web_interface)           │
│  - REST API & WebSocket server                                      │
│  - Mission control & telemetry                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Navigation Stack (Nav2)                          │
│  - Planner Server (MPPI/Smac)                                       │
│  - Controller Server (MPPI)                                         │
│  - Behavior Server (Spin/Backup/Wait)                               │
│  - BT Navigator (Behavior Trees)                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Sensor Fusion & Drivers                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  SLLiDAR A2M7│  │  CCF Laser   │  │  IMU N100    │               │
│  │  (2D LiDAR)  │  │  (Obstacle)  │  │ (Orientation)│               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                              │                                      │
│                              ▼                                      │
│                    ┌──────────────────────┐                         │
│                    │  Robot Localization  │                         │
│                    │  (EKF Filter)        │                         │
│                    └──────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Motor & Actuator Control                         │
│  - Motor Driver (ZLAC1525)                                          │
│  - Modbus I/O (WaveShare)                                           │
│  - Odometry Bridge                                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Magnetic Line Follower                           │
│  - CCF-NS16 Sensor (Modbus RTU)                                     │
│  - Line Keeper (PD + Stanley + SLAM Recovery)                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
src/
├── amr_bringup/              # Core navigation & launch files
│   ├── launch/               # Main launch files
│   │   ├── amir_starter.launch.py    # Full system startup
│   │   ├── navigation.launch.py      # Nav2 only
│   │   ├── mapping.launch.py         # SLAM mapping
│   │   └── localization.launch.py    # Localization only
│   ├── config/               # Nav2, AMCL, EKF parameters
│   └── rviz/                 # RViz visualization configs
├── amr_bringup_headless/     # Headless navigation (no RViz)
├── arya_motor_driver/        # Motor control & odometry
│   ├── motor_node.py         # ZLAC motor driver
│   ├── odom_bridge.py        # Odometry to TF publisher
│   └── twist_mux.yaml        # Velocity arbitration
├── arya_web_interface/       # Web control interface
│   ├── services/ros_node.py  # ROS2 node for web bridge
│   └── handlers/             # HTTP/WebSocket handlers
├── ccf_laser_sensor/         # Front obstacle detection
│   └── ccf_laser_node.py     # CCF-LAS6-4M sensor driver
├── magnetic_line_follower/   # Line following system
│   ├── line_follower_node.py   # Modbus sensor reader
│   ├── mag_line_keeper.py      # Steering controller
│   └── path_recorder.py        # Path recording utility
├── sensor_tf_fusion/         # Sensor TF bridge
│   └── robot_bridge.py       # Odometry + TF publisher
├── sllidar_ros2/             # LiDAR driver (SLLiDAR A2M7)
├── ros2_wheeltec_n100_imu/   # IMU driver
├── waveshare_modbus_io/      # Modbus I/O expansion
└── serial-ros2/              # Serial communication utilities
```

## Quick Start

### Prerequisites
- ROS 2 Humble (Ubuntu 22.04)
- Python 3.10+
- SSH access to robot: `ssh arya@192.168.1.101` (password: `12345678`)

### Build & Setup

```bash
# Clone and build
cd ~/arya_ws/src
git clone <this-repo>
cd ..
colcon build --symlink-install
source install/setup.bash
```

### Launch Full System

```bash
# From remote PC (192.168.1.101)
ros2 launch amr_bringup amir_starter.launch.py \
  enable_lidar:=true \
  enable_ekf:=true \
  enable_web:=true \
  enable_lidar_rviz:=true
```

### Launch Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_lidar` | true | Enable SLLiDAR A2M7 |
| `enable_ekf` | true | Enable robot localization |
| `enable_web` | true | Enable web interface |
| `enable_lidar_rviz` | true | Visualize LiDAR in RViz |
| `imu_port` | /dev/ttyUSB1 | IMU serial port |
| `lidar_port` | /dev/ttyUSB0 | LiDAR serial port |

## Key Topics & Services

### Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/scan` | sensor_msgs/LaserScan | LiDAR scan data |
| `/front_laser` | std_msgs/Float32MultiArray | CCF laser distances |
| `/front_laser_scan` | sensor_msgs/LaserScan | CCF laser as LaserScan |
| `/line_data` | std_msgs/Float32MultiArray | Magnetic line sensor data |
| `/odometry/filtered` | nav_msgs/Odometry | EKF-processed odometry |
| `/amcl_pose` | geometry_msgs/PoseWithCovarianceStamped | AMCL pose estimate |
| `/map` | nav_msgs/OccupancyGrid | SLAM map |

### Subscribed Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/cmd_vel` | geometry_msgs/Twist | Velocity commands |
| `/cmd_vel_auto` | geometry_msgs/Twist | Auto navigation commands |
| `/cmd_vel_manual` | geometry_msgs/Twist | Manual control commands |
| `/initialpose` | geometry_msgs/PoseWithCovarianceStamped | Pose initialization |

### Services

| Service | Type | Description |
|---------|------|-------------|
| `/navigate_to_pose` | NavigateToPose (action) | Navigate to pose |
| `/localize_pose` | Empty | Initialize localization |
| `/web/launch/start` | String | Start launch preset |
| `/web/launch/stop` | String | Stop launch preset |

## Navigation Stack Configuration

- **Local Planner**: MPPI (Model Predictive Path Integral)
- **Global Planner**: Smac Planner (2D Dijkstra)
- **Localization**: AMCL with particle filter
- **Mapping**: SLAM Toolbox (online async)
- **Recovery Behaviors**: Spin, Backup, DriveOnHeading, Wait

## Web Interface

Access the web interface at `http://<robot-ip>:8080` (default port).

### Features
- Real-time telemetry (pose, velocity, battery)
- Mission control (waypoints, navigation)
- Launch control (start/stop ROS2 nodes)
- Map management (load/save maps)
- Drive mode switching (manual/auto)
- Localization reset

## Magnetic Line Following

The line follower system uses:
- **CCF-NS16** magnetic sensor (Modbus RTU)
- **PD + Stanley** controller for steering
- **SLAM-based recovery** when line lost

Launch: `ros2 launch magnetic_line_follower magnetic_line_follower_integrated.launch.py`

## Remote Access

```bash
# SSH to robot
ssh arya@192.168.1.101
# Password: 12345678

# Build on robot
cd ~/arya_ws
colcon build --symlink-install
source install/setup.bash

# Run tests
colcon test --packages-select arya_motor_driver
colcon test-result --all
```

## Troubleshooting

### Common Issues

1. **LiDAR not detected**: Check `/dev/ttyUSB0` permissions
   ```bash
   sudo usermod -aG dialout $USER
   ```

2. **TF tree broken**: Verify static transforms in `amir_starter.launch.py`

3. **Navigation stuck**: Increase `transform_tolerance` in `nav2_params.yaml`

4. **Web interface not connecting**: Check firewall and port 8080

## Development

### Adding New Nodes

1. Create package: `ros2 pkg create <package_name>`
2. Add to `amir_starter.launch.py` with appropriate delays
3. Test individually before full system launch

### Testing

```bash
# Run tests for specific package
colcon test --packages-select <package_name>

# Check coverage
colcon test-result --all
```

## License

TODO: License declaration

## Maintainer
- Jundi Al-Maghribi @7u7unn
- Shultan Al-Zainuddin @mochshultan
- Alvin Attirmidzi @Lvynzz
