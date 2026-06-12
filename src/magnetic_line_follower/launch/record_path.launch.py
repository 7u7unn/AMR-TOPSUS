"""Launch the path_recorder node.

This launch file starts:
1. The path_recorder node, which listens for control topics (/path_recorder/control)
   and saves recorded static map coordinate tracks to the resource path file.

Usage:
    ros2 launch magnetic_line_follower record_path.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # Retrieve default file location inside package share or source home
    default_path_file = os.path.join(
        get_package_share_directory('magnetic_line_follower'),
        'resource',
        'recorded_path.json'
    )

    # Declare arguments
    output_file_arg = DeclareLaunchArgument(
        'output_file', 
        default_value=default_path_file,
        description='Path to save the recorded JSON poses'
    )
    min_dist_arg = DeclareLaunchArgument(
        'min_dist', 
        default_value='0.08',
        description='Minimum distance (m) between successive recorded points'
    )
    mag_topic_arg = DeclareLaunchArgument(
        'mag_topic', 
        default_value='line_data',
        description='Magnetic line follower sensor topic'
    )

    # 1. Path Recorder Node
    recorder_node = Node(
        package='magnetic_line_follower',
        executable='path_recorder',
        name='path_recorder_node',
        output='screen',
        parameters=[{
            'output_file': LaunchConfiguration('output_file'),
            'min_dist': LaunchConfiguration('min_dist'),
            'mag_topic': LaunchConfiguration('mag_topic'),
            'control_topic': '/path_recorder/control',
            'path_pub_topic': '/path_recorder/path'
        }]
    )

    return LaunchDescription([
        output_file_arg,
        min_dist_arg,
        mag_topic_arg,
        recorder_node
    ])
