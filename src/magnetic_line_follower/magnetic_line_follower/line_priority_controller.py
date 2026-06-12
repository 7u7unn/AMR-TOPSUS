#!/usr/bin/env python3
"""Priority line-following controller with laser braking.

This node subscribes to the raw magnetic line sensor values and the laser
raw distance array, converts the line readings into a twist command, and
publishes it to the manual control topic so it has priority over Nav2 via
`twist_mux`.
"""

import math

from geometry_msgs.msg import PoseStamped, Twist
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class LinePriorityController(Node):
    def __init__(self):
        super().__init__('line_priority_controller')

        self.declare_parameter('line_topic', 'line_data')
        self.declare_parameter('laser_topic', '/front_laser')
        self.declare_parameter('goal_topic', '/goal_pose')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel_manual')
        self.declare_parameter('publish_period', 0.033)  # 30 Hz for faster response
        self.declare_parameter('base_linear', 0.12)
        self.declare_parameter('angular_gain', 0.08)
        self.declare_parameter('line_timeout', 0.5)
        self.declare_parameter('goal_timeout', 1.0)

        line_topic = self.get_parameter('line_topic').get_parameter_value().string_value
        laser_topic = self.get_parameter('laser_topic').get_parameter_value().string_value
        goal_topic = self.get_parameter('goal_topic').get_parameter_value().string_value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value
        publish_period = self.get_parameter('publish_period').get_parameter_value().double_value
        self.base_linear = self.get_parameter('base_linear').get_parameter_value().double_value
        self.angular_gain = self.get_parameter('angular_gain').get_parameter_value().double_value
        self.line_timeout = self.get_parameter('line_timeout').get_parameter_value().double_value
        self.goal_timeout = self.get_parameter('goal_timeout').get_parameter_value().double_value

        self._line_data = []
        self._laser_data = []
        self._last_line_update = self.get_clock().now()
        self._last_laser_update = self.get_clock().now()
        self._last_goal_update = self.get_clock().now()

        self.create_subscription(Float32MultiArray, line_topic, self._line_callback, 10)
        self.create_subscription(Float32MultiArray, laser_topic, self._laser_callback, 10)
        self.create_subscription(PoseStamped, goal_topic, self._goal_callback, 10)
        self._cmd_pub = self.create_publisher(Twist, cmd_vel_topic, 10)

        self.create_timer(publish_period, self._timer_callback)
        self.get_logger().info(
            f'Line priority controller ready | line_topic={line_topic} '
            f'laser_topic={laser_topic} cmd_vel_topic={cmd_vel_topic}'
        )

    def _line_callback(self, msg: Float32MultiArray) -> None:
        self._line_data = list(msg.data)
        self._last_line_update = self.get_clock().now()

    def _laser_callback(self, msg: Float32MultiArray) -> None:
        self._laser_data = list(msg.data)
        self._last_laser_update = self.get_clock().now()

    def _goal_callback(self, msg: PoseStamped) -> None:
        self._last_goal_update = self.get_clock().now()

    def _nav_target_active(self) -> bool:
        now = self.get_clock().now()
        elapsed = (now - self._last_goal_update).nanoseconds / 1e9
        return elapsed <= self.goal_timeout

    def _brake_active(self) -> bool:
        if len(self._laser_data) < 4:
            return False
        ch1 = float(self._laser_data[0])
        ch2 = float(self._laser_data[1])
        ch3 = float(self._laser_data[2])
        ch4 = float(self._laser_data[3])
        ch5 = float(self._laser_data[4])
        return (
            (math.isfinite(ch1) and ch1 < 50.0)
            or (math.isfinite(ch2) and ch2 < 70.0)
            or (math.isfinite(ch3) and ch3 < 70.0)
            or (math.isfinite(ch4) and ch4 < 70.0)
            or (math.isfinite(ch5) and ch5 < 50.0)
        )

    def _timer_callback(self) -> None:
        cmd = Twist()

        now = self.get_clock().now()
        line_stale = (now - self._last_line_update).nanoseconds / 1e9 > self.line_timeout
        laser_stale = (now - self._last_laser_update).nanoseconds / 1e9 > self.line_timeout

        if not self._nav_target_active():
            self._cmd_pub.publish(cmd)
            return

        if line_stale or laser_stale:
            self._cmd_pub.publish(cmd)
            return

        if self._brake_active():
            self.get_logger().warning('Brake condition active, stopping motion')
            self._cmd_pub.publish(cmd)
            return

        if len(self._line_data) < 2:
            self._cmd_pub.publish(cmd)
            return

        # Line data format: [bitmap (16-bit position), deviation_mm (filtered deviation)]
        bitmap = int(self._line_data[0])
        deviation_mm = float(self._line_data[1])

        # If no tape detected (bitmap == 0), stop
        if bitmap == 0:
            self.get_logger().debug('No magnetic tape detected, stopping')
            self._cmd_pub.publish(cmd)
            return

        # Check if deviation is within reasonable range (tape is being tracked)
        if abs(deviation_mm) > 100.0:  # Beyond sensor range
            self.get_logger().warning(f'Deviation out of range: {deviation_mm}mm, stopping')
            self._cmd_pub.publish(cmd)
            return

        # Convert deviation to normalized error (-1.0 to +1.0)
        # Deviation range is approximately -85mm to +85mm (8.5 points * 10mm spacing)
        # Positive deviation = right of center, Negative = left of center
        error = deviation_mm / 85.0  # Normalize to [-1.0, 1.0]

        cmd.linear.x = max(0.0, self.base_linear)
        cmd.angular.z = max(-1.0, min(1.0, self.angular_gain * error))
        self._cmd_pub.publish(cmd)

        self.get_logger().debug(
            f'Line following: bitmap={bitmap}, deviation={deviation_mm:.1f}mm, '
            f'error={error:.3f}, angular_z={cmd.angular.z:.3f}'
        )


def main(args=None):
    import rclpy

    rclpy.init(args=args)
    node = LinePriorityController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
