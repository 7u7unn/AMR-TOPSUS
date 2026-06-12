"""Integrated Line Follower and SLAM Recovery Launch.

This launch file starts:
1. The Modbus RTU reader node for the CCF-NS16 magnetic sensor (publishing on 'line_data').
2. The MagLineKeeper interceptor node which processes 'line_data', intercepts '/cmd_vel_raw_nav2',
   and applies PD steering or SLAM-based path recovery before publishing to '/cmd_vel_raw'.

Usage:
    ros2 launch magnetic_line_follower magnetic_line_follower_integrated.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    # Declare launch arguments
    port_arg = DeclareLaunchArgument('port', default_value='/dev/ttyUSB3')
    baud_arg = DeclareLaunchArgument('baud', default_value='9600')
    slave_arg = DeclareLaunchArgument('slave', default_value='1')
    path_file_arg = DeclareLaunchArgument('path_file', default_value='recorded_path.json')
    linear_speed_arg = DeclareLaunchArgument('linear_speed', default_value='0.20')

    # 1. Modbus RTU Reader Node
    sensor_node = Node(
        package='magnetic_line_follower',
        executable='line_follower',
        name='magnetic_sensor_node',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('port'),
            'baud': LaunchConfiguration('baud'),
            'slave': LaunchConfiguration('slave'),
            'topic': 'line_data',
            'period': 0.05  # Publish at 20 Hz
        }]
    )

    # 2. Interceptor Line-Keeper Node (with Stanley/PD & SLAM recovery)
    keeper_node = Node(
        package='magnetic_line_follower',
        executable='mag_line_keeper',
        name='mag_line_keeper_node',
        output='screen',
        parameters=[{
            'path_file': LaunchConfiguration('path_file'),
            'kp_mag': 0.05,
            'kd_mag': 0.02,
            'kp_heading': 0.8,
            'kp_slam': 0.6,
            'linear_speed': LaunchConfiguration('linear_speed'),
            'recovery_timeout': 3.0,
            'recovery_max_dist': 0.6,
            'mag_topic': 'line_data',
            'effective_wheelbase': 0.35,
            'laser_topic': '/front_laser',
            'laser_min_dist': 70.0
        }]
    )

    return LaunchDescription([
        port_arg,
        baud_arg,
        slave_arg,
        path_file_arg,
        linear_speed_arg,
        sensor_node,
        keeper_node
    ])
