# Repository Guidelines

This repository contains ROS 2 workspace source packages for the Autonomous Mobile Robot (AMR).

## Project Structure & Module Organization

All ROS 2 packages reside in `D:\MagangUnair26\Program\src`.
- `amr_bringup`: Core launch files, configurations, maps, and RViz profiles.
- `amr_bringup_headless`: Launch configurations for headless execution.
- `arya_web_interface`: Frontend/backend interface files.
- `magnetic_line_follower`: Package for line tracking sensors and logic.
- Sensor drivers: `ccf_laser_sensor`, `ros2_wheeltec_n100_imu`, `sllidar_ros2`, `serial-ros2`.
- Actuator drivers: `arya_motor_driver`, `waveshare_modbus_io`.

Each Python package follows standard ROS 2 Python structure:
- `amr_bringup/amr_bringup/` for source Python code.
- `amr_bringup/launch/` for launch files.
- `amr_bringup/config/` for parameters and configurations.
- `amr_bringup/test/` for unit tests.

## Build, Test, and Development Commands

Commands must be executed from the ROS 2 workspace root (`D:\MagangUnair26\Program`):

- **Build Workspace**:
  ```bash
  colcon build --symlink-install
  ```
- **Build Specific Package**:
  ```bash
  colcon build --packages-select <package_name>
  ```
- **Source Workspace**:
  ```bash
  source install/setup.bash
  ```
- **Run Tests**:
  ```bash
  colcon test --packages-select <package_name>
  ```
- **Check Test Results**:
  ```bash
  colcon test-result --all
  ```

## Coding Style & Naming Conventions

- **Python**: Follow PEP 8 style guide. Set indentations to 4 spaces. Keep variable names in snake_case.
- **C++**: Follow ROS 2 developer guide (indentation: 2 spaces, camelCase for variables).
- **ROS Nodes**: Use snake_case for node names and topic names.
- **Launch Files**: Keep launch filenames in snake_case ending with `.launch.py`.

## Testing Guidelines

- Place test scripts inside the `test/` directory of each package.
- Use `pytest` for Python packages and `ament_cmake_gtest` for C++ packages.
- Test files must start with the `test_` prefix (e.g., `test_node.py`).

## Commit & Pull Request Guidelines

- **Commit Messages**: Use clean, descriptive messages describing changes (e.g., `feat: add laser driver node`, `fix: correct motor speed conversion`).
- **Pull Requests**: Explain modifications, list updated packages, and confirm successful compilation.


## Remote Connection & Robot Deployment

The workspace is on a remote development PC. To access the physical robot, use SSH:
- **SSH Command**: `ssh arya@192.168.1.101`
- **Password**: `12345678`
