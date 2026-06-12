"""ROS Node implementation with thread-safe state management."""

import threading
import time
import math
import os
import signal
import subprocess

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from rclpy.action import ActionClient
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

from std_msgs.msg import Float32MultiArray, UInt8, String
from geometry_msgs.msg import Twist, PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, OccupancyGrid, Path as NavPath
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import NavigateToPose
from std_srvs.srv import Empty
from action_msgs.msg import GoalStatus
from pathlib import Path
from ament_index_python.packages import get_package_prefix, get_package_share_directory

try:
    from lifecycle_msgs.srv import GetState
except Exception:
    GetState = None

try:
    from rosidl_runtime_py.utilities import get_message
except ImportError:
    get_message = None

from ..utils.constants import (
    NAV_GOAL_STATUS_LABELS,
    LAUNCH_PRESETS,
    MAX_LIDAR_POINTS,
)
from ..utils.converters import normalize_topic_name



class AryaWebNode(Node):
    """
    ROS2 Node for web interface control of autonomous mobile robot.
    
    Thread-safe by design with locks protecting shared state:
    - nav_goal_lock: Navigation goal state (current goal, seq, contexts)
    - mission_lock: Station queue mission state
    - drive_mode_lock: Drive mode selection
    - launch_lock: Launch process tracking
    - topic_echo_lock: Dynamic topic subscriptions
    - imu_restart_lock: IMU process restart
    - localization_reset_lock: Localization reset operations
    """
    
    def __init__(self):
        super().__init__('arya_web_node')
        self.get_logger().info("Initializing AryaWebNode...")
        
        # Node parameters
        self.declare_parameter("imu_serial_port", "/dev/ttyUSB0")
        self.declare_parameter("imu_serial_baud", 921600)
        self.declare_parameter("imu_respawn_wait_sec", 3.0)
        self.declare_parameter("imu_restart_fallback", True)
        self.declare_parameter("restart_ekf_on_reset_odom", True)
        self.declare_parameter("ekf_config", "~/arya_ws/src/sensor_tf_fusion/config/ekf.yaml")
        self.declare_parameter("ekf_respawn_wait_sec", 3.0)
        self.declare_parameter("ekf_restart_fallback", True)
        self.declare_parameter("lidar_motor_enabled", True)
        self.declare_parameter("cmd_vel_topic", "cmd_vel_manual")
        self.declare_parameter("drive_mode_default", "auto")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("laser_frame", "laser")
        
        # Load parameters
        self.imu_serial_port = self.get_parameter("imu_serial_port").value
        self.imu_serial_baud = int(self.get_parameter("imu_serial_baud").value)
        self.imu_respawn_wait_sec = float(self.get_parameter("imu_respawn_wait_sec").value)
        self.imu_restart_fallback = bool(self.get_parameter("imu_restart_fallback").value)
        self.restart_ekf_on_reset_odom = bool(self.get_parameter("restart_ekf_on_reset_odom").value)
        self.ekf_config = str(Path(self.get_parameter("ekf_config").value).expanduser())
        self.ekf_respawn_wait_sec = float(self.get_parameter("ekf_respawn_wait_sec").value)
        self.ekf_restart_fallback = bool(self.get_parameter("ekf_restart_fallback").value)
        self.lidar_motor_enabled = bool(self.get_parameter("lidar_motor_enabled").value)
        self.cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value).strip() or "cmd_vel_manual"
        drive_mode_default = str(self.get_parameter("drive_mode_default").value).strip().lower()
        self.drive_mode = "manual" if drive_mode_default == "manual" else "auto"
        self.base_frame = str(self.get_parameter("base_frame").value).strip() or "base_link"
        self.laser_frame = str(self.get_parameter("laser_frame").value).strip() or "laser"
        
        # Thread synchronization
        self.imu_restart_lock = threading.Lock()
        self.localization_reset_lock = threading.Lock()
        self.topic_echo_lock = threading.Lock()
        self.drive_mode_lock = threading.Lock()
        self.launch_lock = threading.Lock()
        
        # Launch process state
        self.launch_processes = {}
        self.launch_log_dir = Path.home() / ".arya_amr" / "logs"
        
        # TF2 buffer for transformations
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.last_lidar_tf_warn_time = 0.0
        self.last_grid_tf_warn_times = {}
        
        # Robot state
        self.telemetry = [0, 0, 0, 0, 0, 0]
        self.odom = [0, 0, 0]
        self.amcl_pose = None
        self.io_inputs_byte = 0
        self.io_outputs_byte = 0
        
        # Low battery warning / flashing state
        self.low_battery_threshold = 50.0  # V
        self.low_battery_flashing = False
        self.low_battery_flash_state = False
        
        # Navigation state
        self.nav_goal_lock = threading.Lock()
        self.nav_goal_seq = 0
        self.current_nav_goal_handle = None
        self.nav_goal_contexts = {}
        self.nav_goal_status = {
            "state": "idle",
            "message": "Belum ada goal dari web.",
            "seq": 0,
        }
        
        # Mission queue state
        self.mission_lock = threading.Lock()
        self.mission_seq = 0
        self.station_mission_status = {
            "state": "idle",
            "message": "Belum ada station mission.",
            "mode": "idle",
            "mission_id": 0,
            "current_index": -1,
            "total": 0,
            "station": None,
        }
        
        # Map data
        self.map_data = None
        self.map_dirty = False
        self.local_costmap_data = None
        self.local_costmap_dirty = False
        self.global_costmap_data = None
        self.global_costmap_dirty = False
        self.path_data = None
        self.path_dirty = False
        self.recorded_path_data = None
        self.recorded_path_dirty = False
        self.lidar_scan_data = None
        self.lidar_scan_dirty = False
        self.front_laser_data = None
        self.mag_line_data = None
        
        # QoS profiles
        qos_reliable = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )
        qos_transient = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        qos_best_effort = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )
        
        # Subscriptions
        self.sub_telemetry = self.create_subscription(
            Float32MultiArray, 'telemetry', self._cb_telemetry, 10
        )
        self.sub_odom = self.create_subscription(
            Odometry, '/odometry/filtered', self._cb_odom, 10
        )
        self.sub_amcl_pose = self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose', self._cb_amcl_pose, 10
        )
        self.sub_io_inputs = self.create_subscription(
            UInt8, 'io/inputs_raw', self._cb_io_inputs, 10
        )
        self.sub_io_outputs = self.create_subscription(
            UInt8, 'io/outputs_raw', self._cb_io_outputs, 10
        )
        self.sub_map = self.create_subscription(
            OccupancyGrid, '/map', self._cb_map, qos_transient
        )
        self.sub_local_costmap = self.create_subscription(
            OccupancyGrid, '/local_costmap/costmap', self._cb_local_costmap, qos_best_effort
        )
        self.sub_global_costmap = self.create_subscription(
            OccupancyGrid, '/global_costmap/costmap', self._cb_global_costmap, qos_transient
        )
        self.sub_path = self.create_subscription(
            NavPath, '/plan', self._cb_path, 1
        )
        self.sub_recorded_path = self.create_subscription(
            NavPath, '/path_recorder/path', self._cb_recorded_path, 1
        )
        self.sub_lidar_scan = self.create_subscription(
            LaserScan, '/scan', self._cb_lidar_scan, qos_best_effort
        )
        self.sub_front_laser = self.create_subscription(
            Float32MultiArray, '/front_laser', self._cb_front_laser, 10
        )
        self.sub_mag_line = self.create_subscription(
            Float32MultiArray, 'line_data', self._cb_mag_line, 10
        )
        
        # Publishers
        self.pub_cmd = self.create_publisher(Twist, self.cmd_vel_topic, qos_reliable)
        self.pub_reset_odom = self.create_publisher(Float32MultiArray, 'reset_odom', qos_reliable)
        self.pub_reset_encoder = self.create_publisher(Float32MultiArray, 'reset_encoder', qos_reliable)
        self.pub_io_cmd = self.create_publisher(String, 'io/cmd_single', 10)
        self.pub_io_mask = self.create_publisher(UInt8, 'io/cmd_mask', 10)
        self.pub_goal = self.create_publisher(PoseStamped, '/goal_pose', 1)
        self.pub_initial_pose = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 1)
        self.pub_path_recorder_control = self.create_publisher(String, '/path_recorder/control', 10)
        
        # Low battery safety warning timer (0.5s interval matches 2Hz toggle -> 1Hz blink)
        self.low_battery_timer = self.create_timer(0.5, self._cb_low_battery_timer)
        
        # Action clients
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.lidar_start_client = self.create_client(Empty, 'start_motor')
        self.lidar_stop_client = self.create_client(Empty, 'stop_motor')
        
        # Lifecycle state clients
        self.lifecycle_state_clients = {}
        if GetState is not None:
            for node_name in ("bt_navigator", "planner_server", "controller_server"):
                self.lifecycle_state_clients[node_name] = self.create_client(
                    GetState,
                    f"/{node_name}/get_state",
                )
        
        self.get_logger().info(
            f"AryaWebNode initialized. cmd_vel: {self.cmd_vel_topic}, mode: {self.drive_mode}"
        )
    
    # Callback methods (all prefixed with _cb_ to indicate they're callbacks)
    def _cb_telemetry(self, msg):
        self.telemetry = list(msg.data)
    
    def _cb_low_battery_timer(self):
        if not self.telemetry or len(self.telemetry) < 1:
            return
        voltage = self.telemetry[0]
        # Only activate alarm when telemetry is actively transmitting (> 10.0V) and voltage is < 50.0V
        if 10.0 < voltage < self.low_battery_threshold:
            self.low_battery_flashing = True
            self.low_battery_flash_state = not self.low_battery_flash_state
            cmd = "on" if self.low_battery_flash_state else "off"
            # Publish to DO 1 (Front Yellow Lamp) and DO 2 (Rear Yellow Lamp)
            self.pub_io_cmd.publish(String(data=f"{cmd} 1"))
            self.pub_io_cmd.publish(String(data=f"{cmd} 2"))
        else:
            if self.low_battery_flashing:
                # Turn off both yellow lights to reset DO state
                self.pub_io_cmd.publish(String(data="off 1"))
                self.pub_io_cmd.publish(String(data="off 2"))
                self.low_battery_flashing = False
                self.low_battery_flash_state = False
    
    def _cb_odom(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        theta = math.atan2(siny_cosp, cosy_cosp)
        theta = math.atan2(math.sin(theta), math.cos(theta))
        self.odom = [x, y, theta]
    
    def _cb_amcl_pose(self, msg: PoseWithCovarianceStamped):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        theta = math.atan2(siny_cosp, cosy_cosp)
        theta = math.atan2(math.sin(theta), math.cos(theta))
        self.amcl_pose = [x, y, theta]
    
    def _cb_io_inputs(self, msg):
        self.io_inputs_byte = int(msg.data)
    
    def _cb_io_outputs(self, msg):
        self.io_outputs_byte = int(msg.data)
    
    def _cb_map(self, msg):
        self.map_data = self._parse_grid(msg)
        self.map_dirty = True
    
    def _cb_local_costmap(self, msg):
        self.local_costmap_data = self._parse_grid(msg)
        self.local_costmap_dirty = True
    
    def _cb_global_costmap(self, msg):
        self.global_costmap_data = self._parse_grid(msg)
        self.global_costmap_dirty = True
    
    def _cb_path(self, msg):
        self.path_data = [[round(p.pose.position.x, 3), round(p.pose.position.y, 3)] for p in msg.poses]
        self.path_dirty = True
        
    def _cb_recorded_path(self, msg):
        self.recorded_path_data = [[round(p.pose.position.x, 3), round(p.pose.position.y, 3), round(p.pose.position.z, 1)] for p in msg.poses]
        self.recorded_path_dirty = True

    def _cb_front_laser(self, msg):
        self.front_laser_data = [round(x, 1) for x in msg.data]
    
    def _cb_mag_line(self, msg):
        if len(msg.data) >= 2:
            self.mag_line_data = [int(msg.data[0]), float(msg.data[1])]
        else:
            self.mag_line_data = None
    
    def _cb_lidar_scan(self, msg: LaserScan):
        """Process LiDAR scan and transform to base frame."""
        ranges = list(msg.ranges)
        if not ranges:
            return
        
        source_frame = msg.header.frame_id.strip() if msg.header.frame_id else self.laser_frame
        target_frame = self.base_frame
        tx = ty = yaw = 0.0
        transformed_frame = source_frame
        
        try:
            transform = self.tf_buffer.lookup_transform(target_frame, source_frame, Time())
            tx = transform.transform.translation.x
            ty = transform.transform.translation.y
            yaw = self._yaw_from_quaternion(transform.transform.rotation)
            transformed_frame = target_frame
        except Exception as exc:
            now = time.monotonic()
            if now - self.last_lidar_tf_warn_time > 5.0:
                self.get_logger().warn(
                    f"TF {target_frame} <- {source_frame} not available: {exc}"
                )
                self.last_lidar_tf_warn_time = now
        
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        step = max(1, math.ceil(len(ranges) / MAX_LIDAR_POINTS))
        points = []
        range_min = float(msg.range_min or 0.0)
        range_max = float(msg.range_max or 0.0)
        
        for i in range(0, len(ranges), step):
            r = float(ranges[i])
            if not math.isfinite(r):
                continue
            if r <= range_min:
                continue
            if range_max > 0.0 and r >= range_max:
                continue
            angle = float(msg.angle_min + (i * msg.angle_increment))
            lx = r * math.cos(angle)
            ly = r * math.sin(angle)
            bx = tx + cos_yaw * lx - sin_yaw * ly
            by = ty + sin_yaw * lx + cos_yaw * ly
            points.append([round(bx, 3), round(by, 3)])
        
        self.lidar_scan_data = {
            "frame_id": transformed_frame,
            "source_frame_id": source_frame,
            "points": points,
        }
        self.lidar_scan_dirty = True
    
    @staticmethod
    def _yaw_from_quaternion(q):
        """Extract yaw angle from quaternion."""
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        theta = math.atan2(siny_cosp, cosy_cosp)
        return math.atan2(math.sin(theta), math.cos(theta))
    
    def _parse_grid(self, msg):
        """Parse OccupancyGrid message with TF transformation."""
        import base64
        source_frame = (msg.header.frame_id or "").strip().lstrip("/") or "map"
        ox = float(msg.info.origin.position.x)
        oy = float(msg.info.origin.position.y)
        oyaw = self._yaw_from_quaternion(msg.info.origin.orientation)
        transformed = self._transform_grid_origin_to_map(source_frame, ox, oy, oyaw)
        
        return {
            "frame_id": transformed["frame_id"],
            "source_frame_id": source_frame,
            "target_frame_id": "map",
            "transform_ok": transformed["transform_ok"],
            "w": msg.info.width,
            "h": msg.info.height,
            "res": msg.info.resolution,
            "ox": transformed["ox"],
            "oy": transformed["oy"],
            "oyaw": transformed["oyaw"],
            "b64": base64.b64encode(bytes(msg.data)).decode('ascii')
        }
    
    def _transform_grid_origin_to_map(self, source_frame, ox, oy, oyaw):
        """Transform grid origin from source frame to map frame."""
        if source_frame == "map":
            return {
                "frame_id": "map",
                "transform_ok": True,
                "ox": ox,
                "oy": oy,
                "oyaw": oyaw,
            }
        
        try:
            transform = self.tf_buffer.lookup_transform("map", source_frame, Time())
            tx = float(transform.transform.translation.x)
            ty = float(transform.transform.translation.y)
            tyaw = self._yaw_from_quaternion(transform.transform.rotation)
            cos_yaw = math.cos(tyaw)
            sin_yaw = math.sin(tyaw)
            return {
                "frame_id": "map",
                "transform_ok": True,
                "ox": tx + cos_yaw * ox - sin_yaw * oy,
                "oy": ty + sin_yaw * ox + cos_yaw * oy,
                "oyaw": math.atan2(math.sin(tyaw + oyaw), math.cos(tyaw + oyaw)),
            }
        except Exception as exc:
            now = time.monotonic()
            last_warn = self.last_grid_tf_warn_times.get(source_frame, 0.0)
            if now - last_warn > 5.0:
                self.get_logger().warn(
                    f"TF map <- {source_frame} not available: {exc}"
                )
                self.last_grid_tf_warn_times[source_frame] = now
            return {
                "frame_id": source_frame,
                "transform_ok": False,
                "ox": ox,
                "oy": oy,
                "oyaw": oyaw,
            }

    def _make_goal_pose(self, x, y, theta):
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.orientation.z = math.sin(float(theta) / 2.0)
        msg.pose.orientation.w = math.cos(float(theta) / 2.0)
        return msg

    def _set_nav_goal_status(self, state, message, seq=None, **extra):
        with self.nav_goal_lock:
            active_seq = self.nav_goal_seq
            if seq is not None and seq != active_seq:
                return
            status = {
                "state": state,
                "message": message,
                "seq": active_seq if seq is None else seq,
            }
            status.update(extra)
            self.nav_goal_status = status

    def get_nav_goal_status(self):
        with self.nav_goal_lock:
            return dict(self.nav_goal_status)

    def _get_nav_goal_context(self, seq, remove=False):
        with self.nav_goal_lock:
            if remove:
                return self.nav_goal_contexts.pop(seq, {})
            return dict(self.nav_goal_contexts.get(seq, {}))

    def _set_station_mission_status(self, state, message, **extra):
        with self.mission_lock:
            status = {
                "state": state,
                "message": message,
                "mode": extra.pop("mode", self.station_mission_status.get("mode", "idle")),
                "mission_id": extra.pop("mission_id", self.station_mission_status.get("mission_id", 0)),
                "current_index": extra.pop("current_index", self.station_mission_status.get("current_index", -1)),
                "total": extra.pop("total", self.station_mission_status.get("total", 0)),
                "station": extra.pop("station", self.station_mission_status.get("station")),
            }
            status.update(extra)
            self.station_mission_status = status

    def get_station_mission_status(self):
        with self.mission_lock:
            return dict(self.station_mission_status)

    def _on_nav_goal_feedback(self, seq, feedback_msg):
        feedback = getattr(feedback_msg, "feedback", None)
        distance_remaining = getattr(feedback, "distance_remaining", None)
        extra = {}
        if distance_remaining is not None:
            extra["distance_remaining"] = round(float(distance_remaining), 3)
        context = self._get_nav_goal_context(seq)
        station = context.get("station")
        if context.get("source") == "queue":
            extra.update({
                "mission_mode": "queue",
                "mission_id": context.get("mission_id"),
                "mission_index": context.get("mission_index"),
                "station": station,
            })
            station_name = station.get("name", "station") if isinstance(station, dict) else "station"
            message = f"Menuju station {station_name}."
        else:
            message = "Goal sedang dieksekusi."
        self._set_nav_goal_status(seq=seq, state="executing", message=message, **extra)

    def _on_nav_goal_response(self, seq, future):
        try:
            goal_handle = future.result()
        except Exception as exc:
            self._set_nav_goal_status(
                seq=seq,
                state="failed",
                message=f"Gagal mengirim NavigateToPose goal: {exc}",
                mode="action",
            )
            self._handle_queue_goal_finished(seq, False, "failed", str(exc))
            return

        if not goal_handle.accepted:
            diagnostics = self.get_nav2_goal_diagnostics()
            hint = diagnostics.get("hint") or "Cek lifecycle bt_navigator dan log Nav2."
            self._set_nav_goal_status(
                seq=seq,
                state="rejected",
                message=f"NavigateToPose menolak goal dari web. {hint}",
                mode="action",
                diagnostics=diagnostics,
            )
            self._handle_queue_goal_finished(seq, False, "rejected", f"NavigateToPose menolak goal. {hint}")
            return

        with self.nav_goal_lock:
            if seq == self.nav_goal_seq:
                self.current_nav_goal_handle = goal_handle

        self._set_nav_goal_status(
            seq=seq,
            state="accepted",
            message="NavigateToPose menerima goal dari web.",
            mode="action",
        )
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(lambda done_future: self._on_nav_goal_result(seq, done_future))

    def _on_nav_goal_result(self, seq, future):
        try:
            result = future.result()
            status_code = int(result.status)
        except Exception as exc:
            self._set_nav_goal_status(
                seq=seq,
                state="failed",
                message=f"Gagal membaca hasil NavigateToPose: {exc}",
                mode="action",
            )
            self._handle_queue_goal_finished(seq, False, "failed", str(exc))
            return

        state = NAV_GOAL_STATUS_LABELS.get(status_code, f"status_{status_code}")
        message = f"NavigateToPose {state}."
        context = self._get_nav_goal_context(seq, remove=True)
        extra = {}
        if context.get("source") == "queue":
            extra.update({
                "mission_mode": "queue",
                "mission_id": context.get("mission_id"),
                "mission_index": context.get("mission_index"),
                "station": context.get("station"),
            })
        self._set_nav_goal_status(
            seq=seq,
            state=state,
            message=message,
            mode="action",
            result_status=status_code,
            **extra,
        )
        with self.nav_goal_lock:
            if seq == self.nav_goal_seq:
                self.current_nav_goal_handle = None
        self._handle_queue_goal_finished(
            seq,
            status_code == GoalStatus.STATUS_SUCCEEDED,
            state,
            message,
            context=context,
        )

    def get_lifecycle_state(self, node_name: str, timeout_sec: float = 0.15) -> dict:
        client = self.lifecycle_state_clients.get(node_name)
        if client is None or GetState is None:
            return {
                "node": node_name,
                "available": False,
                "state": "unknown",
                "message": "Lifecycle service client tidak tersedia.",
            }

        if not client.wait_for_service(timeout_sec=0.02):
            return {
                "node": node_name,
                "available": False,
                "state": "unknown",
                "message": f"Service /{node_name}/get_state belum tersedia.",
            }

        future = client.call_async(GetState.Request())
        deadline = time.monotonic() + max(0.02, timeout_sec)
        while not future.done() and time.monotonic() < deadline:
            time.sleep(0.01)

        if not future.done():
            return {
                "node": node_name,
                "available": True,
                "state": "unknown",
                "message": f"Timeout membaca lifecycle {node_name}.",
            }

        try:
            response = future.result()
            state = response.current_state
            label = str(getattr(state, "label", "") or "unknown")
            return {
                "node": node_name,
                "available": True,
                "state": label,
                "state_id": int(getattr(state, "id", 0)),
                "message": f"{node_name} lifecycle={label}.",
            }
        except Exception as exc:
            return {
                "node": node_name,
                "available": True,
                "state": "unknown",
                "message": f"Gagal membaca lifecycle {node_name}: {exc}",
            }

    def get_nav2_goal_diagnostics(self) -> dict:
        states = {
            node_name: self.get_lifecycle_state(node_name, timeout_sec=0.08)
            for node_name in ("bt_navigator", "planner_server", "controller_server")
        }
        bt_state = states.get("bt_navigator", {})
        bt_label = str(bt_state.get("state") or "unknown")

        if bt_state.get("available") and bt_label != "active":
            hint = f"bt_navigator belum active (state: {bt_label}). Tunggu Nav2 lifecycle aktif atau restart Nav2."
        elif self.amcl_pose is None:
            hint = "AMCL pose belum masuk; set initial pose dan pastikan localization aktif."
        else:
            hint = "bt_navigator aktif; cek log bt_navigator untuk BT XML atau goal yang tidak valid."

        return {
            "lifecycle": states,
            "amcl_pose_available": self.amcl_pose is not None,
            "map_available": self.map_data is not None,
            "hint": hint,
        }

    def wait_for_nav2_goal_ready(self, timeout_sec: float = 2.0) -> dict:
        deadline = time.monotonic() + max(0.0, timeout_sec)
        last_diagnostics = {}

        while time.monotonic() <= deadline:
            action_ready = self.nav_to_pose_client.wait_for_server(timeout_sec=0.05)
            diagnostics = self.get_nav2_goal_diagnostics()
            last_diagnostics = diagnostics

            bt_state = diagnostics.get("lifecycle", {}).get("bt_navigator", {})
            bt_available = bool(bt_state.get("available"))
            bt_label = str(bt_state.get("state") or "unknown")
            lifecycle_ok = (not bt_available) or bt_label == "active"

            if action_ready and lifecycle_ok:
                return {
                    "ok": True,
                    "action_ready": True,
                    "diagnostics": diagnostics,
                    "message": "NavigateToPose ready.",
                }

            time.sleep(0.1)

        hint = last_diagnostics.get("hint") or "Action navigate_to_pose belum ready."
        return {
            "ok": False,
            "action_ready": False,
            "diagnostics": last_diagnostics,
            "message": hint,
        }

    def send_goal(
        self,
        x,
        y,
        theta,
        *,
        source="single",
        mission_id=None,
        mission_index=None,
        station=None,
        clear_mission=True,
        allow_topic_fallback=True,
    ):
        msg = self._make_goal_pose(x, y, theta)
        self.set_drive_mode("auto")
        self.path_data = []
        self.path_dirty = True

        if clear_mission:
            self._set_station_mission_status(
                "idle",
                "Single mission aktif.",
                mode="single",
                mission_id=0,
                current_index=-1,
                total=0,
                station=station,
            )

        with self.nav_goal_lock:
            self.nav_goal_seq += 1
            seq = self.nav_goal_seq
            context = {
                "source": source,
                "mission_id": mission_id,
                "mission_index": mission_index,
                "station": station,
            }
            self.nav_goal_contexts[seq] = context
            self.nav_goal_status = {
                "state": "queued",
                "message": "Goal web disiapkan.",
                "seq": seq,
                "mode": "action",
            }
            if station:
                self.nav_goal_status["station"] = station
            if source == "queue":
                self.nav_goal_status["mission_mode"] = "queue"
                self.nav_goal_status["mission_id"] = mission_id
                self.nav_goal_status["mission_index"] = mission_index

        readiness = self.wait_for_nav2_goal_ready(timeout_sec=2.0)
        if not readiness.get("ok"):
            if not allow_topic_fallback:
                self._set_nav_goal_status(
                    seq=seq,
                    state="failed",
                    message=readiness.get("message", "Action navigate_to_pose belum ready."),
                    mode="action",
                    diagnostics=readiness.get("diagnostics", {}),
                )
                self._handle_queue_goal_finished(seq, False, "failed", readiness.get("message", "Action navigate_to_pose belum ready."))
                return {
                    "ok": False,
                    "mode": "action",
                    "seq": seq,
                    "message": readiness.get("message", "Action navigate_to_pose belum ready."),
                    "diagnostics": readiness.get("diagnostics", {}),
                }

            diagnostics = readiness.get("diagnostics", {})
            bt_state = diagnostics.get("lifecycle", {}).get("bt_navigator", {})
            if bt_state.get("available") and str(bt_state.get("state") or "unknown") != "active":
                message = readiness.get("message", "bt_navigator belum active.")
                self._set_nav_goal_status(
                    seq=seq,
                    state="failed",
                    message=message,
                    mode="action",
                    diagnostics=diagnostics,
                )
                return {
                    "ok": False,
                    "mode": "action",
                    "seq": seq,
                    "message": message,
                    "diagnostics": diagnostics,
                }

            self.pub_goal.publish(msg)
            self._set_nav_goal_status(
                seq=seq,
                state="fallback_published",
                message="Action navigate_to_pose belum ready; goal dipublish ke /goal_pose.",
                mode="topic",
                diagnostics=readiness.get("diagnostics", {}),
            )
            self.get_logger().warn("NavigateToPose action belum ready, fallback publish /goal_pose")
            return {
                "ok": True,
                "mode": "topic",
                "seq": seq,
                "message": "Goal dikirim via fallback /goal_pose.",
                "diagnostics": readiness.get("diagnostics", {}),
            }

        goal = NavigateToPose.Goal()
        goal.pose = msg
        send_future = self.nav_to_pose_client.send_goal_async(
            goal,
            feedback_callback=lambda feedback_msg: self._on_nav_goal_feedback(seq, feedback_msg),
        )
        send_future.add_done_callback(lambda future: self._on_nav_goal_response(seq, future))
        self._set_nav_goal_status(
            seq=seq,
            state="sent",
            message="Goal dikirim ke NavigateToPose action.",
            mode="action",
            mission_mode="queue" if source == "queue" else None,
            mission_id=mission_id,
            mission_index=mission_index,
            station=station,
        )
        self.get_logger().info(
            f"Goal pose dari web: x={float(x):.3f}, y={float(y):.3f}, theta={math.degrees(float(theta)):.1f} deg"
        )
        return {
            "ok": True,
            "mode": "action",
            "seq": seq,
            "message": "Goal dikirim ke NavigateToPose.",
        }

    def _normalize_mission_station(self, item, index=0):
        if not isinstance(item, dict):
            raise ValueError("Station mission harus berupa object.")

        station_id = str(item.get("id") or f"station_{index + 1}").strip()[:80]
        name = str(item.get("name") or f"Station {index + 1}").strip()[:80]
        try:
            x = float(item.get("x"))
            y = float(item.get("y"))
            theta = float(item.get("theta"))
            wait_sec = float(item.get("wait_sec", 0.0) or 0.0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Station {name} punya nilai koordinat tidak valid.") from exc
        enabled = bool(item.get("enabled", True))

        if not all(math.isfinite(value) for value in (x, y, theta, wait_sec)):
            raise ValueError(f"Station {name} punya nilai koordinat tidak valid.")
        if wait_sec < 0:
            raise ValueError(f"Station {name} punya wait_sec negatif.")
        if not enabled:
            raise ValueError(f"Station {name} tidak aktif.")

        return {
            "id": station_id,
            "name": name,
            "x": x,
            "y": y,
            "theta": theta,
            "wait_sec": wait_sec,
            "enabled": enabled,
        }

    def start_station_queue(self, stations):
        if not isinstance(stations, list):
            return {
                "ok": False,
                "message": "Payload stations harus list.",
            }

        try:
            queue = [
                self._normalize_mission_station(item, index)
                for index, item in enumerate(stations)
            ]
        except (TypeError, ValueError) as exc:
            return {
                "ok": False,
                "message": str(exc),
            }

        if not queue:
            return {
                "ok": False,
                "message": "Queue station masih kosong.",
            }

        self.cancel_current_nav_goal(update_status=False)
        with self.mission_lock:
            self.mission_seq += 1
            mission_id = self.mission_seq
            self.station_mission_status = {
                "state": "starting",
                "message": "Queue mission disiapkan.",
                "mode": "queue",
                "mission_id": mission_id,
                "queue": queue,
                "current_index": -1,
                "total": len(queue),
                "station": None,
                "stop_requested": False,
            }

        self._start_next_station_in_queue(mission_id)
        return {
            "ok": True,
            "message": f"Queue mission dimulai ({len(queue)} station).",
            "mission_status": self.get_station_mission_status(),
        }

    def cancel_current_nav_goal(self, update_status=True):
        with self.nav_goal_lock:
            goal_handle = self.current_nav_goal_handle
            seq = self.nav_goal_seq

        if goal_handle is not None:
            try:
                goal_handle.cancel_goal_async()
            except Exception as exc:
                self.get_logger().warn(f"Gagal cancel goal aktif: {exc}")

        if update_status:
            self._set_nav_goal_status(
                "canceling",
                "Cancel goal diminta dari web.",
                seq=seq,
                mode="action",
            )

    def cancel_station_queue(self):
        with self.mission_lock:
            status = self.station_mission_status
            if status.get("mode") != "queue" or status.get("state") not in ("starting", "running", "executing"):
                return {
                    "ok": True,
                    "message": "Tidak ada queue mission aktif.",
                    "mission_status": dict(status),
                }
            mission_id = status.get("mission_id", 0)
            self.station_mission_status = {
                **status,
                "state": "canceled",
                "message": "Queue mission dibatalkan dari web.",
                "stop_requested": True,
            }

        self.cancel_current_nav_goal(update_status=True)
        self.get_logger().info(f"Queue mission #{mission_id} dibatalkan dari web")
        return {
            "ok": True,
            "message": "Queue mission dibatalkan.",
            "mission_status": self.get_station_mission_status(),
        }

    def _start_next_station_in_queue(self, mission_id):
        with self.mission_lock:
            status = self.station_mission_status
            if status.get("mission_id") != mission_id or status.get("mode") != "queue":
                return
            if status.get("stop_requested"):
                return
            queue = list(status.get("queue") or [])
            next_index = int(status.get("current_index", -1)) + 1
            if next_index >= len(queue):
                self.station_mission_status = {
                    **status,
                    "state": "succeeded",
                    "message": "Queue mission selesai.",
                    "current_index": len(queue) - 1,
                    "total": len(queue),
                    "station": None,
                }
                self._set_nav_goal_status(
                    "succeeded",
                    "Queue mission selesai.",
                    mode="queue",
                    mission_id=mission_id,
                    mission_index=len(queue) - 1,
                )
                return

            station = queue[next_index]
            self.station_mission_status = {
                **status,
                "state": "executing",
                "message": f"Menuju station {station['name']}.",
                "current_index": next_index,
                "total": len(queue),
                "station": station,
            }

        result = self.send_goal(
            station["x"],
            station["y"],
            station["theta"],
            source="queue",
            mission_id=mission_id,
            mission_index=next_index,
            station=station,
            clear_mission=False,
            allow_topic_fallback=False,
        )
        if not result.get("ok"):
            self._abort_station_queue(mission_id, next_index, station, result.get("message", "Goal gagal dikirim."))

    def _abort_station_queue(self, mission_id, index, station, reason):
        with self.mission_lock:
            status = self.station_mission_status
            if status.get("mission_id") != mission_id:
                return
            self.station_mission_status = {
                **status,
                "state": "failed",
                "message": reason,
                "current_index": index,
                "station": station,
                "failed_index": index,
                "failed_station": station,
            }
        self.get_logger().warn(f"Queue mission #{mission_id} gagal di index {index}: {reason}")

    def _handle_queue_goal_finished(self, seq, success, state, message, context=None):
        if context is None:
            context = self._get_nav_goal_context(seq, remove=True)
        if context.get("source") != "queue":
            return

        mission_id = context.get("mission_id")
        index = context.get("mission_index")
        station = context.get("station")
        with self.mission_lock:
            status = self.station_mission_status
            if status.get("mission_id") != mission_id or status.get("mode") != "queue":
                return
            if status.get("stop_requested"):
                return

        if success:
            self._start_next_station_in_queue(mission_id)
        else:
            station_name = station.get("name", "station") if isinstance(station, dict) else "station"
            self._abort_station_queue(
                mission_id,
                int(index if index is not None else -1),
                station,
                f"Queue abort di {station_name}: {message or state}.",
            )

    def set_initial_pose(self, x, y, theta):
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.pose.position.x = float(x)
        msg.pose.pose.position.y = float(y)
        msg.pose.pose.orientation.z = math.sin(float(theta) / 2.0)
        msg.pose.pose.orientation.w = math.cos(float(theta) / 2.0)

        covariance = [0.0] * 36
        covariance[0] = 0.25
        covariance[7] = 0.25
        covariance[35] = 0.06853892326654787
        msg.pose.covariance = covariance

        self.pub_initial_pose.publish(msg)
        self.amcl_pose = [float(x), float(y), float(theta)]
        self.get_logger().info(
            f"Initial pose dari web: x={float(x):.3f}, y={float(y):.3f}, theta={math.degrees(float(theta)):.1f} deg"
        )
        return {
            "ok": True,
            "message": "Initial pose dipublish ke /initialpose.",
            "x": float(x),
            "y": float(y),
            "theta": float(theta),
        }

    def list_ros_topics(self):
        topic_map = {}
        try:
            topics = self.get_topic_names_and_types()
        except Exception as exc:
            self.get_logger().warn(f"Gagal membaca ROS topic list: {exc}")
            topics = []

        for name, types in topics:
            clean_name = normalize_topic_name(name)
            if not clean_name:
                continue
            topic_map[clean_name] = {
                "name": clean_name,
                "types": sorted(set(types)),
                "available": True,
                "source": "graph",
            }

        for name, types in self.known_ros_topic_types().items():
            if name in topic_map:
                merged_types = set(topic_map[name]["types"])
                merged_types.update(types)
                topic_map[name]["types"] = sorted(merged_types)
                topic_map[name]["known"] = True
            else:
                topic_map[name] = {
                    "name": name,
                    "types": sorted(set(types)),
                    "available": False,
                    "source": "known",
                    "known": True,
                }

        items = list(topic_map.values())
        return sorted(items, key=lambda item: item["name"].casefold())

    def known_ros_topic_types(self):
        topics = {
            normalize_topic_name(name): list(types)
            for name, types in KNOWN_ROS_TOPIC_TYPES.items()
        }
        configured_cmd_vel = normalize_topic_name(self.cmd_vel_topic)
        if configured_cmd_vel:
            topics.setdefault(configured_cmd_vel, [])
            if "geometry_msgs/msg/Twist" not in topics[configured_cmd_vel]:
                topics[configured_cmd_vel].append("geometry_msgs/msg/Twist")
        return topics

    def resolve_topic_types(self, topic_name: str) -> list[str]:
        clean_name = normalize_topic_name(topic_name)
        if not clean_name:
            return []

        try:
            for name, types in self.get_topic_names_and_types():
                if normalize_topic_name(name) == clean_name:
                    return sorted(set(types))
        except Exception as exc:
            self.get_logger().warn(f"Gagal resolve topic '{clean_name}' dari ROS graph: {exc}")

        return sorted(set(self.known_ros_topic_types().get(clean_name, [])))

    def create_echo_subscription(self, topic_name: str, callback):
        if get_message is None:
            raise RuntimeError("rosidl_runtime_py tidak tersedia untuk dynamic topic echo")

        clean_name = normalize_topic_name(topic_name)
        if not clean_name:
            raise ValueError("Nama topic tidak valid")

        msg_types = self.resolve_topic_types(clean_name)
        if not msg_types:
            raise ValueError(
                f"Topic '{clean_name}' tidak ditemukan di ROS graph dan belum ada tipe fallback."
            )

        msg_type = msg_types[0]
        msg_cls = get_message(msg_type)
        qos_echo = QoSProfile(
            depth=5,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        with self.topic_echo_lock:
            subscription = self.create_subscription(msg_cls, clean_name, callback, qos_echo)

        return subscription, msg_type

    def destroy_echo_subscription(self, subscription):
        if subscription is None:
            return
        with self.topic_echo_lock:
            self.destroy_subscription(subscription)

    def publish_cmd_vel(self, v, w):
        msg = Twist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)

        self.pub_cmd.publish(msg)

        # flush stop biar responsif
        if v == 0.0 and w == 0.0:
            self.pub_cmd.publish(msg)

    def send_cmd_vel(self, v, w):
        with self.drive_mode_lock:
            if self.drive_mode != "manual":
                return False

        self.publish_cmd_vel(v, w)
        return True

    def send_path_recorder_command(self, cmd: str) -> bool:
        try:
            msg = String()
            msg.data = str(cmd)
            self.pub_path_recorder_control.publish(msg)
            self.get_logger().info(f"Published path recorder control command: '{cmd}'")
            return True
        except Exception as e:
            self.get_logger().error(f"Failed to publish path recorder control command: {e}")
            return False

    def set_drive_mode(self, mode):
        next_mode = str(mode or "").strip().lower()
        if next_mode not in ("auto", "manual"):
            self.get_logger().warn(f"Mode drive tidak valid: {mode}")
            return self.drive_mode

        with self.drive_mode_lock:
            previous_mode = self.drive_mode
            if previous_mode == next_mode:
                return self.drive_mode

            if previous_mode == "manual" and next_mode == "auto":
                self.publish_cmd_vel(0.0, 0.0)

            self.drive_mode = next_mode

        self.get_logger().info(f"Drive mode: {previous_mode} -> {next_mode}")
        return next_mode

    def reset_odom_and_restart_imu(self):
        self.pub_reset_odom.publish(Float32MultiArray(data=[0.0, 0.0, 0.0]))
        threading.Thread(target=self.reset_localization_nodes, daemon=True).start()

    def reset_localization_nodes(self):
        if not self.localization_reset_lock.acquire(blocking=False):
            self.get_logger().warn("Reset localization masih berjalan, request baru diabaikan")
            return

        try:
            self.restart_imu_node()
            if self.restart_ekf_on_reset_odom:
                self.restart_ekf_node()
        finally:
            self.localization_reset_lock.release()

    def restart_imu_node(self):
        if not self.imu_restart_lock.acquire(blocking=False):
            self.get_logger().warn("Restart IMU masih berjalan, request baru diabaikan")
            return

        try:
            old_pids = self.get_process_pids("/wheeltec_n100_imu/imu_node")
            killed = self.stop_process("/wheeltec_n100_imu/imu_node", "IMU")
            if killed:
                self.get_logger().info("Reset odom dikirim, menunggu imu_node respawn")
                self.wait_for_old_pids_to_exit("/wheeltec_n100_imu/imu_node", old_pids, 2.0)
            else:
                self.get_logger().warn("Reset odom dikirim, tapi proses imu_node tidak ditemukan")

            deadline = time.monotonic() + max(0.0, self.imu_respawn_wait_sec)
            while time.monotonic() < deadline:
                time.sleep(0.25)
                pids = self.get_process_pids("/wheeltec_n100_imu/imu_node")
                if (pids - old_pids) or (not old_pids and pids):
                    self.get_logger().info("imu_node sudah aktif kembali")
                    return

            if not self.imu_restart_fallback:
                self.get_logger().warn("imu_node belum respawn and fallback start dimatikan")
                return

            self.start_imu_process()
        finally:
            self.imu_restart_lock.release()

    def restart_ekf_node(self):
        old_pids = self.get_process_pids("/robot_localization/ekf_node")
        killed = self.stop_process("/robot_localization/ekf_node", "EKF")
        if killed:
            self.get_logger().info("Menunggu ekf_node respawn agar yaw kembali 0")
            self.wait_for_old_pids_to_exit("/robot_localization/ekf_node", old_pids, 2.0)
        else:
            self.get_logger().warn("Proses ekf_node tidak ditemukan saat reset odom")

        deadline = time.monotonic() + max(0.0, self.ekf_respawn_wait_sec)
        while time.monotonic() < deadline:
            time.sleep(0.25)
            pids = self.get_process_pids("/robot_localization/ekf_node")
            if (pids - old_pids) or (not old_pids and pids):
                self.get_logger().info("ekf_node sudah aktif kembali")
                return

        if not self.ekf_restart_fallback:
            self.get_logger().warn("ekf_node belum respawn and fallback start dimatikan")
            return

        self.start_ekf_process()

    def stop_process(self, pattern, label):
        try:
            result = subprocess.run(
                ["pkill", "-TERM", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
        except FileNotFoundError:
            self.get_logger().error(f"Gagal stop {label}: command 'pkill' tidak ditemukan")
            return False
        except subprocess.TimeoutExpired:
            self.get_logger().error(f"Gagal stop {label}: timeout saat menghentikan proses")
            return False

        if result.returncode in (0, 1):
            return result.returncode == 0

        stderr = result.stderr.strip()
        self.get_logger().error(f"Gagal menghentikan {label}: {stderr}")
        return False

    def get_process_pids(self, pattern):
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode != 0:
                return set()
            return {int(pid) for pid in result.stdout.split() if pid.strip().isdigit()}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return set()

    def wait_for_old_pids_to_exit(self, pattern, old_pids, timeout_sec):
        deadline = time.monotonic() + max(0.0, timeout_sec)
        while old_pids and time.monotonic() < deadline:
            if not (self.get_process_pids(pattern) & old_pids):
                return True
            time.sleep(0.1)
        return not old_pids

    def start_imu_process(self):
        try:
            imu_executable = Path(get_package_prefix("wheeltec_n100_imu")) / "lib" / "wheeltec_n100_imu" / "imu_node"
        except Exception as exc:
            self.get_logger().error(f"Gagal mencari package wheeltec_n100_imu: {exc}")
            return

        if not imu_executable.exists():
            self.get_logger().error(f"Executable imu_node tidak ditemukan: {imu_executable}")
            return

        cmd = [
            str(imu_executable),
            "--ros-args",
            "-p", f"serial_port:={self.imu_serial_port}",
            "-p", f"serial_baud:={self.imu_serial_baud}",
        ]

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except Exception as exc:
            self.get_logger().error(f"Gagal start ulang imu_node: {exc}")
            return

        self.get_logger().info(f"imu_node distart ulang manual di {self.imu_serial_port}")

    def start_ekf_process(self):
        try:
            ekf_executable = Path(get_package_prefix("robot_localization")) / "lib" / "robot_localization" / "ekf_node"
        except Exception as exc:
            self.get_logger().error(f"Gagal mencari package robot_localization: {exc}")
            return

        if not ekf_executable.exists():
            self.get_logger().error(f"Executable ekf_node tidak ditemukan: {ekf_executable}")
            return

        if not Path(self.ekf_config).exists():
            self.get_logger().error(f"Config EKF tidak ditemukan: {self.ekf_config}")
            return

        cmd = [
            str(ekf_executable),
            "--ros-args",
            "-r", "__node:=ekf_filter_node",
            "--params-file", self.ekf_config,
        ]

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except Exception as exc:
            self.get_logger().error(f"Gagal start ulang ekf_node: {exc}")
            return

        self.get_logger().info("ekf_node distart ulang manual")

    def set_lidar_motor(self, enabled):
        client = self.lidar_start_client if enabled else self.lidar_stop_client
        service_name = 'start_motor' if enabled else 'stop_motor'

        if not client.wait_for_service(timeout_sec=0.2):
            self.get_logger().warn(f"Service LIDAR '{service_name}' belum tersedia")
            return

        future = client.call_async(Empty.Request())
        future.add_done_callback(
            lambda done_future: self._on_lidar_motor_response(done_future, enabled, service_name)
        )

    def _on_lidar_motor_response(self, future, enabled, service_name):
        try:
            future.result()
        except Exception as exc:
            self.get_logger().error(f"Gagal memanggil service LIDAR '{service_name}': {exc}")
            return

        self.lidar_motor_enabled = bool(enabled)
        state = "ON" if enabled else "OFF"
        self.get_logger().info(f"Motor LIDAR {state}")

    def is_localization_ready(self):
        if self.amcl_pose is not None:
            return True

        try:
            topic_names = {name for name, _types in self.get_topic_names_and_types()}
        except Exception:
            return False

        return "/map" in topic_names and "/amcl_pose" in topic_names

    def is_hardware_ready(self):
        try:
            topic_names = {name for name, _types in self.get_topic_names_and_types()}
        except Exception:
            return False

        return "/scan" in topic_names and "/odometry/filtered" in topic_names

    def _default_launch_status(self, name):
        preset = LAUNCH_PRESETS[name]
        return {
            "name": name,
            "label": preset["label"],
            "status": "stopped",
            "running": False,
            "pid": None,
            "returncode": None,
            "log_path": "",
            "message": "Stopped",
        }

    def _launch_status_locked(self, name):
        status = self._default_launch_status(name)
        state = self.launch_processes.get(name)
        if not state:
            return status

        process = state.get("process")
        returncode = process.poll() if process else state.get("returncode")
        running = returncode is None
        stop_requested = bool(state.get("stop_requested"))

        status.update({
            "running": running,
            "pid": process.pid if process else state.get("pid"),
            "returncode": returncode,
            "log_path": str(state.get("log_path") or ""),
        })

        if running:
            status["status"] = state.get("status", "running")
            status["message"] = state.get("message", "Running")
        else:
            state["returncode"] = returncode
            if returncode == 0 or stop_requested:
                status["status"] = "stopped"
                status["message"] = "Stopped"
            else:
                status["status"] = "failed"
                status["message"] = f"Exited with code {returncode}"
            state["status"] = status["status"]
            state["message"] = status["message"]

        return status

    def get_launch_statuses(self):
        with self.launch_lock:
            return [
                self._launch_status_locked(name)
                for name in LAUNCH_PRESETS.keys()
            ]

    def _is_launch_running_locked(self, name):
        state = self.launch_processes.get(name)
        process = state.get("process") if state else None
        return bool(process and process.poll() is None)

    def start_launch_preset(self, name):
        clean_name = str(name or "").strip()
        if clean_name not in LAUNCH_PRESETS:
            return {
                "ok": False,
                "name": clean_name,
                "action": "start",
                "message": "Launch preset tidak dikenal.",
            }

        if clean_name == "local_hdl":
            with self.launch_lock:
                hardware_running = self._is_launch_running_locked("amir_hdl")
            if not hardware_running and not self.is_hardware_ready():
                return {
                    "ok": False,
                    "name": clean_name,
                    "action": "start",
                    "message": "Hardware belum terdeteksi. Jalankan amir_hdl dulu.",
                }

        if clean_name == "nav_hdl":
            with self.launch_lock:
                local_running = self._is_launch_running_locked("local_hdl")
            if not local_running and not self.is_localization_ready():
                return {
                    "ok": False,
                    "name": clean_name,
                    "action": "start",
                    "message": "Localization belum terdeteksi. Jalankan local_hdl dulu.",
                }

        preset = LAUNCH_PRESETS[clean_name]
        with self.launch_lock:
            current = self._launch_status_locked(clean_name)
            if current["running"]:
                return {
                    "ok": True,
                    "name": clean_name,
                    "action": "start",
                    "message": f"{preset['label']} sudah running.",
                    "status": current,
                }

            try:
                self.launch_log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                return {
                    "ok": False,
                    "name": clean_name,
                    "action": "start",
                    "message": f"Gagal membuat folder log: {exc}",
                }

            stamp = time.strftime("%Y%m%d_%H%M%S")
            log_path = self.launch_log_dir / f"{clean_name}_{stamp}.log"
            cmd = ["bash", "-ic", preset["alias"]]

            try:
                with log_path.open("ab") as log_file:
                    header = (
                        f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"START {clean_name}: {preset['alias']} ===\n"
                    )
                    log_file.write(header.encode("utf-8"))
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
            except Exception as exc:
                self.get_logger().error(f"Gagal start {clean_name}: {exc}")
                return {
                    "ok": False,
                    "name": clean_name,
                    "action": "start",
                    "message": f"Gagal start {preset['label']}: {exc}",
                }

            self.launch_processes[clean_name] = {
                "process": process,
                "pid": process.pid,
                "log_path": log_path,
                "status": "running",
                "message": "Running",
                "stop_requested": False,
            }
            time.sleep(0.2)
            status = self._launch_status_locked(clean_name)

        if status["status"] == "failed":
            message = f"{preset['label']} gagal start. Cek log: {log_path}"
            self.get_logger().error(message)
            return {
                "ok": False,
                "name": clean_name,
                "action": "start",
                "message": message,
                "status": status,
            }

        self.get_logger().info(f"{preset['label']} started via alias {preset['alias']} pid={process.pid}")
        return {
            "ok": True,
            "name": clean_name,
            "action": "start",
            "message": f"{preset['label']} started.",
            "status": status,
        }

    def _send_launch_signal(self, process, sig):
        try:
            if os.name == "nt":
                if sig == signal.SIGINT:
                    process.terminate()
                else:
                    process.kill()
            else:
                os.killpg(process.pid, sig)
            return True
        except ProcessLookupError:
            return True
        except Exception as exc:
            self.get_logger().warn(f"Gagal mengirim signal ke launch pid={process.pid}: {exc}")
            return False

    def stop_launch_preset(self, name):
        clean_name = str(name or "").strip()
        if clean_name not in LAUNCH_PRESETS:
            return {
                "ok": False,
                "name": clean_name,
                "action": "stop",
                "message": "Launch preset tidak dikenal.",
            }

        if clean_name == "amir_hdl":
            cascade_results = []
            for dependent_name in ("nav_hdl", "local_hdl", "mapping"):
                result = self.stop_launch_preset(dependent_name)
                cascade_results.append(result)
                if not result.get("ok"):
                    return {
                        "ok": False,
                        "name": clean_name,
                        "action": "stop",
                        "message": f"Gagal stop {dependent_name} sebelum stop Hardware.",
                        "cascade": cascade_results,
                    }

        preset = LAUNCH_PRESETS[clean_name]
        with self.launch_lock:
            state = self.launch_processes.get(clean_name)
            process = state.get("process") if state else None
            if not process or process.poll() is not None:
                status = self._launch_status_locked(clean_name)
                return {
                    "ok": True,
                    "name": clean_name,
                    "action": "stop",
                    "message": f"{preset['label']} sudah stopped.",
                    "status": status,
                }

            state["stop_requested"] = True
            state["status"] = "stopping"
            state["message"] = "Stopping"

        self._send_launch_signal(process, signal.SIGINT)
        try:
            process.wait(timeout=8.0)
        except subprocess.TimeoutExpired:
            self._send_launch_signal(process, signal.SIGTERM)
            try:
                process.wait(timeout=4.0)
            except subprocess.TimeoutExpired:
                self._send_launch_signal(process, signal.SIGKILL)
                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    pass

        with self.launch_lock:
            status = self._launch_status_locked(clean_name)

        self.get_logger().info(f"{preset['label']} stop requested, status={status['status']}")
        return {
            "ok": status["status"] != "failed",
            "name": clean_name,
            "action": "stop",
            "message": f"{preset['label']} stopped." if status["status"] != "failed" else status["message"],
            "status": status,
        }

