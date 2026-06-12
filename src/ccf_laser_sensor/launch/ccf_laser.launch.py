"""
launch/ccf_laser.launch.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Launches the CCF-LAS4-4M 5-channel laser obstacle avoidance sensor node.

Usage examples
--------------
# Default (port comes from config/ccf_laser_params.yaml):
  ros2 launch ccf_laser_sensor ccf_laser.launch.py

# Override port at launch time:
  ros2 launch ccf_laser_sensor ccf_laser.launch.py port:=/dev/ttyUSB0

# Override multiple params:
  ros2 launch ccf_laser_sensor ccf_laser.launch.py slave:=2 baud:=115200
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('ccf_laser_sensor')

    # ------------------------------------------------------------------
    # Launch arguments (all optional – defaults come from the YAML file)
    # ------------------------------------------------------------------
    declare_port = DeclareLaunchArgument(
        'port',
        default_value='/dev/serial/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-port0',
        description='Serial port for the CCF-LAS4-4M sensor',
    )
    declare_baud = DeclareLaunchArgument(
        'baud',
        default_value='9600',
        description='Baud rate',
    )
    declare_slave = DeclareLaunchArgument(
        'slave',
        default_value='2',
        description='Modbus slave (device) address',
    )
    declare_period = DeclareLaunchArgument(
        'period',
        default_value='0.05',
        description='Polling period in seconds',
    )
    declare_frame_id = DeclareLaunchArgument(
        'frame_id',
        default_value='ccf_laser_link',
        description='TF frame id for the LaserScan header',
    )

    params_file = PathJoinSubstitution([pkg_share, 'config', 'ccf_laser_params.yaml'])

    # ------------------------------------------------------------------
    # Node
    # ------------------------------------------------------------------
    ccf_laser_node = Node(
        package='ccf_laser_sensor',
        executable='ccf_laser_node',
        name='ccf_laser_node',
        output='screen',
        parameters=[
            params_file,
            {
                # Launch-argument overrides take priority over the YAML file
                'port':     LaunchConfiguration('port'),
                'baud':     LaunchConfiguration('baud'),
                'slave':    LaunchConfiguration('slave'),
                'period':   LaunchConfiguration('period'),
                'frame_id': LaunchConfiguration('frame_id'),
            },
        ],
        remappings=[],
    )

    return LaunchDescription([
        declare_port,
        declare_baud,
        declare_slave,
        declare_period,
        declare_frame_id,
        ccf_laser_node,
    ])
