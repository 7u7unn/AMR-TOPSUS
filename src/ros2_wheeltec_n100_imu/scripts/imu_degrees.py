#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


def quaternion_to_euler(x, y, z, w):
    """Return roll, pitch, yaw in radians from a ROS quaternion."""
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class ImuDegrees(Node):
    def __init__(self):
        super().__init__("imu_degrees")

        self.declare_parameter("topic", "/imu")
        self.declare_parameter("print_hz", 5.0)

        self.topic = self.get_parameter("topic").value
        self.print_period = 1.0 / max(0.1, float(self.get_parameter("print_hz").value))

        self.last_print = self.get_clock().now()
        self.last_yaw = None
        self.yaw_unwrapped = 0.0
        self.initial_yaw_unwrapped = None
        self.message_count = 0

        self.create_subscription(Imu, self.topic, self.imu_callback, 20)
        self.create_timer(2.0, self.status_callback)
        self.get_logger().info(
            f"Reading {self.topic}; printing roll/pitch/yaw in degrees at {1.0 / self.print_period:.1f} Hz"
        )

    def status_callback(self):
        if self.message_count == 0:
            self.get_logger().warn(f"Still waiting for IMU messages on {self.topic}")

    def imu_callback(self, msg):
        self.message_count += 1
        q = msg.orientation
        roll, pitch, yaw = quaternion_to_euler(q.x, q.y, q.z, q.w)

        if self.last_yaw is None:
            self.last_yaw = yaw
            self.yaw_unwrapped = yaw
            self.initial_yaw_unwrapped = yaw
        else:
            self.yaw_unwrapped += normalize_angle(yaw - self.last_yaw)
            self.last_yaw = yaw

        now = self.get_clock().now()
        if (now - self.last_print).nanoseconds * 1e-9 < self.print_period:
            return
        self.last_print = now

        yaw_delta = self.yaw_unwrapped - self.initial_yaw_unwrapped
        self.get_logger().info(
            "roll={:8.2f} deg | pitch={:8.2f} deg | yaw={:8.2f} deg | yaw_delta={:9.2f} deg".format(
                math.degrees(roll),
                math.degrees(pitch),
                math.degrees(yaw),
                math.degrees(yaw_delta),
            )
        )


def main(args=None):
    rclpy.init(args=args)
    node = ImuDegrees()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
