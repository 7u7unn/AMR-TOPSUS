from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='magnetic_line_follower',
            executable='line_follower',
            name='magnetic_line_follower',
            output='screen',
            parameters=[{
                'linear_speed': 0.15,
                'kp': 0.08,
                'kd': 0.05,
                'lost_timeout': 2.0,
            }]
        )
    ])
