"""Launch the line_follower node.

Usage:
    ros2 launch magnetic_line_follower line_follower_launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='magnetic_line_follower',
            executable='line_follower',
            name='line_follower_node',
            output='screen',
            parameters=[
                {'port': '/dev/ttyUSB3'},
                {'baud': 9600},
                {'slave': 1},
                {'scale': 1.0},
                {'topic': 'line_data_mm'},
                {'period': 0.1},
            ],
        ),
    ])
