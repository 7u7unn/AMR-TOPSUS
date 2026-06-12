from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    """Launch the node using `python -m` to avoid depending on installed lib exec path."""
    # The node is run as a module; parameters can be passed via ROS params or remappings.
    cmd = ['python3', '-m', 'agv_obstacle_sensor.obstacle_node']
    return LaunchDescription([
        ExecuteProcess(cmd=cmd, output='screen')
    ])
