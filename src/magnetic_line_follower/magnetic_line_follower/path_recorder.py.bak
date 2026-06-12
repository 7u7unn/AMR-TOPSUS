#!/usr/bin/env python3
import json
import math
import os
import rclpy
from rclpy.node import Node
from rclpy.time import Time
import threading
from std_msgs.msg import Float32MultiArray, String
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped
from tf2_ros import Buffer, TransformListener

class PathRecorder(Node):
    def __init__(self):
        super().__init__('path_recorder')
        
        # Declare parameters
        self.declare_parameter('output_file', 'recorded_path.json')
        self.declare_parameter('min_dist', 0.08)          # Record pose every 8cm
        self.declare_parameter('mag_topic', 'line_data')
        self.declare_parameter('control_topic', '/path_recorder/control')
        self.declare_parameter('path_pub_topic', '/path_recorder/path')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('checkpoint_bits', 8)      # Min active bits to detect a transverse checkpoint line

        self.filepath = self.get_parameter('output_file').get_parameter_value().string_value
        self.min_dist = self.get_parameter('min_dist').get_parameter_value().double_value
        mag_topic = self.get_parameter('mag_topic').get_parameter_value().string_value
        control_topic = self.get_parameter('control_topic').get_parameter_value().string_value
        path_pub_topic = self.get_parameter('path_pub_topic').get_parameter_value().string_value
        self.map_frame = self.get_parameter('map_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value
        self.checkpoint_bits = self.get_parameter('checkpoint_bits').get_parameter_value().integer_value

        # Path points and recording state
        self.path_points = []
        self._lock = threading.Lock()
        self.last_x = None
        self.last_y = None
        self.current_mag = [0.0, 0.0]
        self.recording = False

        # TF Buffer and Listener for static 'map' frame coordinate tracking
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Publishers
        self.pub_path = self.create_publisher(Path, path_pub_topic, 10)

        # Subscriptions
        self.sub_mag = self.create_subscription(
            Float32MultiArray, 
            mag_topic, 
            self.mag_callback, 
            10
        )
        self.sub_control = self.create_subscription(
            String, 
            control_topic, 
            self.control_callback, 
            10
        )

        # Timer to record poses at 10 Hz in 'map' frame if recording is active
        self.create_timer(0.1, self.record_timer_callback)

        self.get_logger().info(
            f"✅ Path Recorder active (referenced in static 'map' frame).\n"
            f"Subscribing to: Mag={mag_topic}, Control={control_topic}.\n"
            f"Publishing path to: {path_pub_topic}.\n"
            f"File destination: {self.filepath}"
        )

    def mag_callback(self, msg: Float32MultiArray):
        if len(msg.data) >= 2:
            self.current_mag = [float(msg.data[0]), float(msg.data[1])]

    def control_callback(self, msg: String):
        command = msg.data.strip()
        self.get_logger().info(f"Received control command: '{command}'")

        if command == "start":
            self.recording = True
            self.path_points = []
            self.last_x = None
            self.last_y = None
            self.get_logger().info("⏺️ Started path recording. Cleared previous path.")
            self.publish_path_msg()
            
        elif command == "stop":
            self.recording = False
            self.save_path()
            self.get_logger().info("⏹️ Stopped path recording and saved path file.")
            
        elif command.startswith("name:"):
            station_name = command[5:].strip()
            self.name_station(station_name)

    def record_timer_callback(self):
        if not self.recording:
            return

        try:
            # Look up transform from static 'map' frame to robot 'base_link' frame
            # use an unspecified (zero) time to request the latest available transform
            now = Time()
            trans = self.tf_buffer.lookup_transform(self.map_frame, self.base_frame, now)
            
            x = trans.transform.translation.x
            y = trans.transform.translation.y
            qx = trans.transform.rotation.x
            qy = trans.transform.rotation.y
            qz = trans.transform.rotation.z
            qw = trans.transform.rotation.w

            # Verify min distance step has been exceeded
            if self.last_x is not None:
                dist = math.sqrt((x - self.last_x)**2 + (y - self.last_y)**2)
                if dist < self.min_dist:
                    return

            self.last_x = x
            self.last_y = y

            bitmap = int(self.current_mag[0])
            active_bits = bin(bitmap).count('1')
            is_checkpoint = active_bits >= self.checkpoint_bits

            point = {
                'x': x,
                'y': y,
                'qx': qx,
                'qy': qy,
                'qz': qz,
                'qw': qw,
                'mag_bitmap': bitmap,
                'mag_deviation': float(self.current_mag[1]),
                'is_checkpoint': is_checkpoint
            }
            if is_checkpoint:
                self.get_logger().info(f"✨ Transverse magnetic checkpoint detected! ({active_bits} active bits)")
            with self._lock:
                self.path_points.append(point)
            self.get_logger().info(f"Recorded point {len(self.path_points)}: X={x:.3f}, Y={y:.3f} (map frame)")
            
            # Publish path update for Web UI rendering
            self.publish_path_msg()

        except Exception as e:
            # TF may be temporarily unavailable; warn without raising new exceptions
            self.get_logger().warning(f"TF {self.map_frame} -> {self.base_frame} lookup unavailable: {e}")

    def name_station(self, station_name):
        try:
            now = Time()
            trans = self.tf_buffer.lookup_transform(self.map_frame, self.base_frame, now)
            x = trans.transform.translation.x
            y = trans.transform.translation.y
            qx = trans.transform.rotation.x
            qy = trans.transform.rotation.y
            qz = trans.transform.rotation.z
            qw = trans.transform.rotation.w

            bitmap = int(self.current_mag[0])

            point = {
                'x': x,
                'y': y,
                'qx': qx,
                'qy': qy,
                'qz': qz,
                'qw': qw,
                'mag_bitmap': bitmap,
                'mag_deviation': float(self.current_mag[1]),
                'station_name': station_name
            }
            
            # Append as a distinct named station pose in path
            with self._lock:
                self.path_points.append(point)
            self.last_x = x
            self.last_y = y
            
            self.get_logger().info(f"🏷️ Station '{station_name}' named at: X={x:.3f}, Y={y:.3f} (map frame)")
            self.publish_path_msg()
            self.save_path()

        except Exception as e:
            self.get_logger().error(f"Cannot name station. TF {self.map_frame} -> {self.base_frame} failed: {e}")

    def publish_path_msg(self):
        path_msg = Path()
        now_msg = self.get_clock().now().to_msg()
        path_msg.header.stamp = now_msg
        path_msg.header.frame_id = 'map'

        # Snapshot points under lock to avoid concurrent modification
        with self._lock:
            pts = list(self.path_points)

        for pt in pts:
            pose = PoseStamped()
            pose.header.frame_id = path_msg.header.frame_id
            pose.header.stamp = now_msg
            pose.pose.position.x = pt['x']
            pose.pose.position.y = pt['y']
            pose.pose.position.z = 1.0 if pt.get('is_checkpoint', False) else 0.0
            pose.pose.orientation.x = pt['qx']
            pose.pose.orientation.y = pt['qy']
            pose.pose.orientation.z = pt['qz']
            pose.pose.orientation.w = pt['qw']
            path_msg.poses.append(pose)

        self.pub_path.publish(path_msg)

    def save_path(self):
        try:
            # Ensure folder exists (handle when filepath has no directory component)
            dirpath = os.path.dirname(self.filepath) or '.'
            os.makedirs(dirpath, exist_ok=True)
            with self._lock:
                data = list(self.path_points)
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=4)
                
            # Save persistent backup to home directory to prevent colcon build wipes
            home_dir = os.path.expanduser("~")
            backup_dir = os.path.join(home_dir, ".arya_amr")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, "recorded_path.json")
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=4)
            self.get_logger().info(f"[BACKUP] Persistent path backup saved to: {backup_file}")
        except Exception as e:
            self.get_logger().error(f"Failed to save path file: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PathRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
