#!/usr/bin/env python3
import math
import json
import os
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray, Bool, String
from tf2_ros import Buffer, TransformListener

class MagLineKeeper(Node):
    def __init__(self):
        super().__init__('mag_line_keeper')
        
        # Declare parameters
        self.declare_parameter('path_file', 'recorded_path.json')
        self.declare_parameter('kp_mag', 0.05)         # Proportional gain for magnetic deviation
        self.declare_parameter('kd_mag', 0.02)         # Derivative gain for magnetic deviation
        self.declare_parameter('kp_heading', 0.8)      # Heading error gain during SLAM recovery
        self.declare_parameter('kp_slam', 0.6)         # Lateral offset gain during SLAM recovery
        self.declare_parameter('linear_speed', 0.20)   # Safe forward speed during line following
        self.declare_parameter('recovery_timeout', 3.0)# Max seconds allowed in SLAM dead reckoning
        self.declare_parameter('recovery_max_dist', 0.6)# Max distance (meters) allowed in recovery
        self.declare_parameter('mag_topic', 'line_data')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('effective_wheelbase', 0.35) # Effective wheelbase (distance from wheels to sensor)
        self.declare_parameter('laser_topic', '/front_laser') # Laser obstacle sensor topic
        self.declare_parameter('laser_min_dist', 70.0)      # Stop robot if obstacle is under 70cm
        self.declare_parameter('checkpoint_bits', 8)      # Min active bits to detect a transverse checkpoint line

        # Load parameter values
        self.kp_mag = self.get_parameter('kp_mag').get_parameter_value().double_value
        self.kd_mag = self.get_parameter('kd_mag').get_parameter_value().double_value
        self.kp_heading = self.get_parameter('kp_heading').get_parameter_value().double_value
        self.kp_slam = self.get_parameter('kp_slam').get_parameter_value().double_value
        self.default_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        self.recovery_timeout = self.get_parameter('recovery_timeout').get_parameter_value().double_value
        self.recovery_max_dist = self.get_parameter('recovery_max_dist').get_parameter_value().double_value
        mag_topic = self.get_parameter('mag_topic').get_parameter_value().string_value
        self.L_eff = self.get_parameter('effective_wheelbase').get_parameter_value().double_value
        laser_topic = self.get_parameter('laser_topic').get_parameter_value().string_value
        self.laser_min_dist = self.get_parameter('laser_min_dist').get_parameter_value().double_value
        self.checkpoint_bits = self.get_parameter('checkpoint_bits').get_parameter_value().integer_value
        self.map_frame = self.get_parameter('map_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value
        
        path_filepath = self.get_parameter('path_file').get_parameter_value().string_value

        # Load Pre-recorded Path
        self.path_points = []
        self.load_path(path_filepath)

        # State tracking variables
        self.current_pose = None  # Struct in map frame resolved by TF
        self.current_speed = 0.0  # Linear speed from EKF
        self.last_deviation = 0.0
        self.line_active = False
        self.checkpoint_active = False
        self.bitmap_history = [0, 0, 0] # 3-sample sliding window for active bit count
        
        # PD tracking
        self.prev_cte = 0.0
        
        # Recovery state variables
        self.recovery_start_time = None
        self.recovery_start_pose = None  # Pos in map frame at recovery start
        self.fault_active = False
        self.laser_stop_active = False   # Laser interrupt stop flag

        # TF Buffer and Listener to lookup 'map -> base_link' for geometric recovery
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Publishers / Subscribers
        self.pub_vel = self.create_publisher(Twist, '/cmd_vel_raw', 10)
        self.pub_laser_obstacle = self.create_publisher(Bool, '/mag_line_keeper/laser_obstacle', 10)
        self.pub_state = self.create_publisher(String, '/mag_line_keeper/state', 10)
        self.sub_mag = self.create_subscription(
            Float32MultiArray, 
            mag_topic, 
            self.mag_callback, 
            10
        )
        self.sub_odom = self.create_subscription(
            Odometry, 
            '/odometry/filtered', 
            self.odom_callback, 
            10
        )
        self.sub_nav2 = self.create_subscription(
            Twist, 
            '/cmd_vel_raw_nav2', 
            self.nav2_callback, 
            10
        )
        self.sub_laser = self.create_subscription(
            Float32MultiArray,
            laser_topic,
            self.laser_callback,
            10
        )

        # Timer to publish diagnostics at 5 Hz (every 0.2 seconds)
        self.create_timer(0.2, self.publish_diagnostics)

        self.get_logger().info(
            f"✅ MagLineKeeper active. Subscribing to: Mag={mag_topic}, Nav2=/cmd_vel_raw_nav2, Laser={laser_topic}.\n"
            f"Fitted for static 'map' frame recovery using TF lookup.\n"
            f"Publishing to: /cmd_vel_raw. Path file: {path_filepath}"
        )

    def load_path(self, filepath):
        if not os.path.exists(filepath):
            self.get_logger().warning(f"⚠️ Recorded path file '{filepath}' not found. SLAM recovery will be unavailable.")
            return
        try:
            with open(filepath, 'r') as f:
                self.path_points = json.load(f)
            self.get_logger().info(f"✅ Loaded {len(self.path_points)} path points for SLAM recovery.")
        except Exception as e:
            self.get_logger().error(f"Failed to load recorded path file: {e}")

    def odom_callback(self, msg: Odometry):
        # We only use odom_callback for velocity tracking
        self.current_speed = msg.twist.twist.linear.x

    def laser_callback(self, msg: Float32MultiArray):
        # Channel-specific safety thresholds in cm:
        # CH1: 35cm, CH2: 80cm, CH3: 90cm, CH4: 80cm, CH5: 35cm
        thresholds = [35.0, 80.0, 90.0, 80.0, 35.0]
        stop_triggered = False
        triggered_ch = -1
        triggered_val = 0.0
        triggered_thr = 0.0

        for i, val in enumerate(msg.data):
            if i < len(thresholds):
                thr = thresholds[i]
                # Sensor reading is already in cm (confirmed by user)
                if val < thr:
                    stop_triggered = True
                    triggered_ch = i + 1
                    triggered_val = val
                    triggered_thr = thr
                    break

        if stop_triggered:
            if not self.laser_stop_active:
                self.get_logger().warn(
                    f"🚨 Laser obstacle detected on CH{triggered_ch}! "
                    f"Distance {triggered_val:.1f}cm is below the safety threshold of {triggered_thr:.1f}cm! "
                    f"Halting robot safety interrupt."
                )
                self.laser_stop_active = True
            # Always publish stop command immediately when obstacle is active
            self.publish_zero_velocity()
        else:
            if self.laser_stop_active:
                self.get_logger().info("✅ All laser obstacle channels cleared. Resuming autonomous operation.")
                self.laser_stop_active = False

    def publish_diagnostics(self):
        # Publish current active state string
        state_str = String()
        if self.fault_active:
            state_str.data = "EMERGENCY_STOP_LIMIT_EXCEEDED"
        elif self.laser_stop_active:
            state_str.data = "LASER_OBSTACLE_STOP"
        elif self.checkpoint_active:
            state_str.data = "CHECKPOINT"
        elif self.line_active:
            state_str.data = "LINE_FOLLOWING"
        else:
            state_str.data = "SLAM_DEAD_RECKONING"
        self.pub_state.publish(state_str)

        # Publish safety obstacle flag
        obs_msg = Bool()
        obs_msg.data = self.laser_stop_active
        self.pub_laser_obstacle.publish(obs_msg)

    def mag_callback(self, msg: Float32MultiArray):
        if len(msg.data) < 2:
            return
        bitmap = int(msg.data[0])
        deviation_mm = float(msg.data[1])

        # 3-sample sliding window filter for active bit counts
        active_bits = bin(bitmap).count('1')
        self.bitmap_history.append(active_bits)
        if len(self.bitmap_history) > 3:
            self.bitmap_history.pop(0)

        # If all 3 samples in the sliding window have less than 3 active bits, consider the line lost
        if len(self.bitmap_history) == 3 and all(cnt < 3 for cnt in self.bitmap_history):
            self.line_active = False
            self.checkpoint_active = False
        elif active_bits >= 3:
            # If current reading has a solid tape signal, consider it active
            self.line_active = True
            
        # Update checkpoint flag
        self.checkpoint_active = self.line_active and active_bits >= self.checkpoint_bits

        if self.line_active:
            self.last_deviation = deviation_mm
            # Clear recovery states once tape is re-acquired
            if self.recovery_start_time is not None:
                self.get_logger().info("🎉 Magnetic line re-acquired! Resuming line following.")
                self.recovery_start_time = None
                self.recovery_start_pose = None

    def lookup_map_pose(self):
        """Lookup current robot pose in 'map' frame via TF."""
        try:
            now = Time()
            trans = self.tf_buffer.lookup_transform(self.map_frame, self.base_frame, now)
            return {
                'x': trans.transform.translation.x,
                'y': trans.transform.translation.y,
                'qx': trans.transform.rotation.x,
                'qy': trans.transform.rotation.y,
                'qz': trans.transform.rotation.z,
                'qw': trans.transform.rotation.w,
            }
        except Exception as e:
            # Silence TF warning to avoid spamming
            return None

    def nav2_callback(self, msg: Twist):
        # If in a persistent fault state or laser obstacle detected, force stop safety halt
        if self.fault_active or self.laser_stop_active:
            self.publish_zero_velocity()
            return

        out_msg = Twist()

        if self.line_active:
            # ──────────────────────────────────────────────────────────
            # STATE 1: LINE FOLLOWING (NORMAL PHYSICAL GUIDANCE)
            # ──────────────────────────────────────────────────────────
            # Cap forward linear velocity to configured safe line following speed, or follow Nav2 intent
            out_msg.linear.x = min(self.default_speed, abs(msg.linear.x)) if msg.linear.x > 0 else 0.0
            
            e_cte = self.last_deviation / 1000.0  # Convert mm to meters
            
            p_term = self.kp_mag * e_cte
            d_term = self.kd_mag * (e_cte - self.prev_cte)
            self.prev_cte = e_cte

            omega = p_term + d_term
            out_msg.angular.z = max(min(-omega, 0.4), -0.4) # Inverted for correct steering recovery direction
            
        else:
            # ──────────────────────────────────────────────────────────
            # STATE 2: NAV2 PASS-THROUGH (LOST LINE / FREE SPACE NAVIGATION)
            # ──────────────────────────────────────────────────────────
            # Directly pass through Nav2 commands so Nav2 drives the robot to navigate/recover
            out_msg = msg

        self.pub_vel.publish(out_msg)

    def find_closest_path_point(self, pose):
        if not self.path_points:
            return None
        closest = self.path_points[0]
        min_d = float('inf')
        for pt in self.path_points:
            d = math.sqrt((pose['x'] - pt['x'])**2 + (pose['y'] - pt['y'])**2)
            if d < min_d:
                min_d = d
                closest = pt
        return closest

    def compute_lateral_error(self, current, target):
        # Calculate signed cross-track error relative to the target pose yaw
        dx = current['x'] - target['x']
        dy = current['y'] - target['y']
        
        # Decode target yaw orientation from quaternion
        siny_cosp = 2 * (target['qw'] * target['qz'] + target['qx'] * target['qy'])
        cosy_cosp = 1 - 2 * (target['qy']**2 + target['qz']**2)
        target_yaw = math.atan2(siny_cosp, cosy_cosp)
        
        # Cross-track error orthogonal to path segment heading
        error = -dx * math.sin(target_yaw) + dy * math.cos(target_yaw)
        return error

    def compute_heading_error(self, current, target):
        # Decode current yaw orientation from quaternion
        siny_cosp = 2 * (current['qw'] * current['qz'] + current['qx'] * current['qy'])
        cosy_cosp = 1 - 2 * (current['qy']**2 + current['qz']**2)
        curr_yaw = math.atan2(siny_cosp, cosy_cosp)

        # Decode target yaw orientation from quaternion
        siny_cosp = 2 * (target['qw'] * target['qz'] + target['qx'] * target['qy'])
        cosy_cosp = 1 - 2 * (target['qy']**2 + target['qz']**2)
        target_yaw = math.atan2(siny_cosp, cosy_cosp)

        # Heading offset normalized within [-pi, pi]
        err = target_yaw - curr_yaw
        while err > math.pi: err -= 2 * math.pi
        while err < -math.pi: err += 2 * math.pi
        return err

    def publish_zero_velocity(self):
        stop_msg = Twist()
        self.pub_vel.publish(stop_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MagLineKeeper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
