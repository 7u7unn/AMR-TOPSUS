#!/usr/bin/env python3
"""Node to auto-detect two 7-channel obstacle sensors and publish their distances.

Searches serial ports (auto or via param), validates by parsing 7 numeric values
from the device output, and publishes each sensor's 7-channel distances along
with a single `OBSTCLE_INT` flag set to 1 when any channel is < 1.0 m.
"""

import sys
import glob
import os
import time
import re
import serial
import serial.tools.list_ports

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Int32, String

EXCLUDED_PORTS = ['/dev/ttyS1', '/dev/ttyS3', '/dev/ttyUSB0', '/dev/ttyUSB1']  # S1 ZLAC S3 WAVESHARE

FLOATS_RE = re.compile(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")


def list_candidate_ports():
    """Return a sorted list of candidate serial port device names."""
    ports = []
    for p in serial.tools.list_ports.comports():
        ports.append(p.device)

    if not sys.platform.startswith('win'):
        ports.extend(glob.glob('/dev/ttyUSB*'))
        ports.extend(glob.glob('/dev/ttyACM*'))
        ports.extend(glob.glob('/dev/ttyS*'))
        ports.extend(glob.glob('/dev/serial/by-id/*'))
        ports.extend(glob.glob('/dev/serial/by-path/*'))

    # Remove duplicates while preserving sort order
    seen = set()
    unique_ports = []
    for port in sorted(ports):
        if port not in seen:
            seen.add(port)
            unique_ports.append(port)
    return unique_ports


def list_port_infos():
    """Return detailed serial port records for debugging and USB hub detection."""
    infos = list(serial.tools.list_ports.comports())
    return sorted(infos, key=lambda p: p.device)


def list_serial_symlinks():
    """Return by-id and by-path symlink entries for additional debugging."""
    symlinks = []
    if not sys.platform.startswith('win'):
        for path in sorted(glob.glob('/dev/serial/by-id/*')) + sorted(glob.glob('/dev/serial/by-path/*')):
            try:
                target = os.path.realpath(path)
            except Exception:
                target = None
            symlinks.append((path, target))
    return symlinks


def try_parse_seven_floats(s):
    """Return list of 7 floats if found in string `s`, else None."""
    nums = FLOATS_RE.findall(s)
    if len(nums) >= 7:
        try:
            vals = [float(x) for x in nums[:7]]
            return vals
        except Exception:
            return None
    return None


def validate_port_for_sensor(port, baudrates=(9600, 115200), timeout=0.5, attempts=10, logger=None):
    """Try to open `port` at provided baudrates and parse 7 floats from its output.
    Returns (baud, values) on success, or (None, None).
    """
    for baud in baudrates:
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=timeout)
        except Exception as e:
            if logger:
                logger.debug(f"Cannot open {port}@{baud}: {e}")
            continue

        try:
            # Flush unread data and give the device a chance to emit fresh output
            try:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
            except Exception:
                pass
            # Try a few reads to allow device to output a line
            for _ in range(attempts):
                line = ser.readline()
                if not line:
                    # try a short raw read
                    line = ser.read(128)
                try:
                    text = line.decode('utf-8', errors='ignore')
                except Exception:
                    text = ''
                if text:
                    vals = try_parse_seven_floats(text)
                    if vals:
                        ser.close()
                        if logger:
                            logger.info(f"Validated sensor on {port}@{baud}: {vals}")
                        return baud, vals
                time.sleep(0.02)
        finally:
            try:
                ser.close()
            except Exception:
                pass

    return None, None


class AGVObstacleSensorNode(Node):
    def __init__(self):
        super().__init__('agv_obstacle_sensor')

        # Parameters: optional ports to force, otherwise auto-detect
        self.declare_parameter('front_port', '')
        self.declare_parameter('back_port', '')
        self.declare_parameter('baudrates', [9600, 115200])
        self.declare_parameter('scan_retry_sec', 5.0)

        self.front_port = self.get_parameter('front_port').value
        self.back_port = self.get_parameter('back_port').value
        self.baudrates = tuple(self.get_parameter('baudrates').value)
        self.scan_retry_sec = float(self.get_parameter('scan_retry_sec').value)

        # Publishers
        self.front_pub = self.create_publisher(Float32MultiArray, '/agv_obstacle/front', 10)
        self.back_pub = self.create_publisher(Float32MultiArray, '/agv_obstacle/back', 10)
        self.ports_pub = self.create_publisher(String, '/agv_obstacle/ports', 10)
        self.int_pub = self.create_publisher(Int32, '/agv_obstacle/OBSTCLE_INT', 10)

        # Serial connections
        self.front_ser = None
        self.back_ser = None
        self.front_baud = None
        self.back_baud = None

        # Start detection
        self.detect_timer = None
        self.start_detection()

    def start_detection(self):
        self.get_logger().info('Starting sensor detection...')
        self.detect_sensors()

    def detect_sensors(self):
        valid_ports = []

        # If explicit ports provided, validate them first
        if self.front_port:
            baud, vals = validate_port_for_sensor(self.front_port, baudrates=self.baudrates, logger=self.get_logger())
            if baud:
                valid_ports.append(('front', self.front_port, baud, vals))
            else:
                self.get_logger().warn(f'Configured front_port {self.front_port} did not validate.')

        if self.back_port:
            baud, vals = validate_port_for_sensor(self.back_port, baudrates=self.baudrates, logger=self.get_logger())
            if baud:
                valid_ports.append(('back', self.back_port, baud, vals))
            else:
                self.get_logger().warn(f'Configured back_port {self.back_port} did not validate.')

        if len(valid_ports) < 2:
            # Scan candidate ports
            ports = [p for p in list_candidate_ports() if p not in EXCLUDED_PORTS]
            port_infos = list_port_infos()
            symlinks = list_serial_symlinks()
            self.get_logger().info(f'Candidate ports: {ports}')
            for info in port_infos:
                msg = f"port={info.device} desc={info.description} hwid={info.hwid}"
                self.get_logger().info(msg)
            for path, target in symlinks:
                self.get_logger().info(f"serial symlink: {path} -> {target}")

            for port in ports:
                # Skip if already validated above or duplicates
                if any(port == vp[1] for vp in valid_ports):
                    continue
                baud, vals = validate_port_for_sensor(port, baudrates=self.baudrates, logger=self.get_logger())
                if baud:
                    role = 'front' if not any(v[0] == 'front' for v in valid_ports) else 'back'
                    valid_ports.append((role, port, baud, vals))
                if len(valid_ports) >= 2:
                    break

        # Assign detected ports
        for role, port, baud, vals in valid_ports:
            if role == 'front' and not self.front_ser:
                try:
                    self.front_ser = serial.Serial(port, baudrate=baud, timeout=0.2)
                    self.front_baud = baud
                    self.get_logger().info(f'Front sensor assigned to {port}@{baud}')
                except Exception as e:
                    self.get_logger().error(f'Failed to open front port {port}: {e}')
            elif role == 'back' and not self.back_ser:
                try:
                    self.back_ser = serial.Serial(port, baudrate=baud, timeout=0.2)
                    self.back_baud = baud
                    self.get_logger().info(f'Back sensor assigned to {port}@{baud}')
                except Exception as e:
                    self.get_logger().error(f'Failed to open back port {port}: {e}')

        # If any sensor still missing, retry after delay
        if (not self.front_ser) or (not self.back_ser):
            self.get_logger().warn('Could not detect both sensors yet, retrying...')
            self.detect_timer = self.create_timer(self.scan_retry_sec, self.detect_retry)
        else:
            # Publish ports info and start polling timers
            ports_msg = String()
            ports_msg.data = f"front({self.front_ser.port}) back({self.back_ser.port})"
            self.ports_pub.publish(ports_msg)
            self.get_logger().info(f"Sensors ready: {ports_msg.data}")
            # Poll at 10 Hz
            self.poll_timer = self.create_timer(0.1, self.poll_sensors)

    def detect_retry(self):
        if self.detect_timer:
            self.detect_timer.cancel()
        self.detect_sensors()

    def poll_sensors(self):
        ob_int = 0
        # Front
        if self.front_ser and self.front_ser.is_open:
            vals = self.read_sensor_once(self.front_ser)
            if vals:
                self.publish_values(self.front_pub, vals)
                if any(v < 1.0 for v in vals):
                    ob_int = 1

        # Back
        if self.back_ser and self.back_ser.is_open:
            vals = self.read_sensor_once(self.back_ser)
            if vals:
                self.publish_values(self.back_pub, vals)
                if any(v < 1.0 for v in vals):
                    ob_int = 1

        int_msg = Int32()
        int_msg.data = ob_int
        self.int_pub.publish(int_msg)

    def read_sensor_once(self, ser):
        try:
            line = ser.readline()
            if not line:
                line = ser.read(128)
            try:
                text = line.decode('utf-8', errors='ignore')
            except Exception:
                text = ''
            vals = try_parse_seven_floats(text)
            if vals:
                self.get_logger().debug(f'Read from {ser.port}: {vals}')
                return vals
        except Exception as e:
            self.get_logger().error(f'Error reading from {getattr(ser, "port", "?")}: {e}')
        return None

    def publish_values(self, pub, vals):
        msg = Float32MultiArray()
        msg.data = [float(x) for x in vals]
        pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = AGVObstacleSensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down agv_obstacle_sensor node.')
    finally:
        # Close serial ports
        try:
            if node.front_ser and node.front_ser.is_open:
                node.front_ser.close()
        except Exception:
            pass
        try:
            if node.back_ser and node.back_ser.is_open:
                node.back_ser.close()
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
