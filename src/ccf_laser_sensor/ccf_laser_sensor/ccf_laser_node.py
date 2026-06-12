#!/usr/bin/env python3
"""
ccf_laser_sensor.ccf_laser_node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
ROS2 driver node for the CCF-LAS4-4M 5-channel laser obstacle avoidance
sensor (Beijing Xintuo Future Technology Co., Ltd.).

Sensor specs
------------
- 5 valid distance channels, 180° horizontal × 25° vertical FOV
- Effective range: 1 – 700 cm
- Interface: RS485, Modbus RTU
- Default slave address: 2
- Default baud rate: 9600
- Response time: ~30 ms

Register map (FC=0x03, starting at 0x0000)
------------------------------------------
  Reg 0x0000  Channel 1 distance  (cm or raw unit, see datasheet)
  Reg 0x0001  Channel 2 distance
  Reg 0x0002  Channel 3 distance
  Reg 0x0003  Channel 4 distance
  Reg 0x0004  Channel 5 distance

  Registers 0x0005 and 0x0006 are non-distance values and are ignored.

  Value 0xFFFF (65535) → out-of-range / no detection

Published topics
----------------
  ~/front_laser   (std_msgs/Float32MultiArray)
      Raw distance register values for the 5 valid channels.
      Out-of-range channels → float('inf').

  ~/front_laser_scan   (sensor_msgs/LaserScan)
      Best-effort LaserScan built from the 5 discrete beams.
      Angles span –90° … +90° (5 evenly-spaced beams, step = 45°).
      frame_id = 'ccf_laser_link'

Parameters
----------
  port        string   '/dev/serial/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-port0'
  baud        int      9600
  slave       int      2
  period      double   0.05      poll interval [s]
  topic_dist  string   '/front_laser'
  topic_scan  string   '/front_laser_scan'
  frame_id    string   'ccf_laser_link'
  num_channels int     5
  start_reg   int      0         first Modbus register (0x0000)
  range_max_m double   7.0       sensor max range in metres
  range_scale double   0.001     raw unit → metres  (1 raw unit = 1 mm → 0.001)
"""

import math
import serial
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, MultiArrayLayout
from sensor_msgs.msg import LaserScan

from ccf_laser_sensor.modbus_rtu import build_fc03, parse_fc03_response, query, ModbusError

# Treat zero and the 0xFFFF no-detection sentinel as invalid. Extra
# non-distance registers are ignored by limiting the published channel count.
_OUT_OF_RANGE = 0xFFFF
_INVALID_RAW_VALUES = {0, _OUT_OF_RANGE}

# 5 distance beams spread across 180° → step = 45°
# Beam 1 = –90°, Beam 3 = 0° (centre), Beam 5 = +90°
_NUM_BEAMS = 5
_ANGLE_MIN = -math.pi / 2          # –90°
_ANGLE_MAX =  math.pi / 2          # +90°
_ANGLE_INCREMENT = math.pi / (_NUM_BEAMS - 1)   # 45° between beams


class CcfLaserNode(Node):
    """ROS2 node that polls the CCF-LAS4-4M sensor and publishes laser data."""

    def __init__(self):
        super().__init__('ccf_laser_node')

        # ------------------------------------------------------------------
        # Declare & read parameters
        # ------------------------------------------------------------------
        self.declare_parameter(
            'port',
            '/dev/serial/by-path/pci-0000:00:14.0-usb-0:3.3:1.0-port0',
        )
        self.declare_parameter('baud', 9600)
        self.declare_parameter('slave', 2)
        self.declare_parameter('period', 0.05)
        self.declare_parameter('topic_dist', '/front_laser')
        self.declare_parameter('topic_scan', '/front_laser_scan')
        self.declare_parameter('frame_id', 'ccf_laser_link')
        self.declare_parameter('num_channels', _NUM_BEAMS)
        self.declare_parameter('start_reg', 0)
        self.declare_parameter('range_max_m', 7.0)
        self.declare_parameter('range_scale', 0.001)   # 1 raw unit = 1 mm
        self.declare_parameter('serial_timeout', 0.05)

        port = self.get_parameter('port').get_parameter_value().string_value
        baud = self.get_parameter('baud').get_parameter_value().integer_value
        self._slave = self.get_parameter('slave').get_parameter_value().integer_value
        period = self.get_parameter('period').get_parameter_value().double_value
        topic_dist = self.get_parameter('topic_dist').get_parameter_value().string_value
        topic_scan = self.get_parameter('topic_scan').get_parameter_value().string_value
        self._frame_id = self.get_parameter('frame_id').get_parameter_value().string_value
        requested_num_ch = self.get_parameter('num_channels').get_parameter_value().integer_value
        self._num_ch = min(requested_num_ch, _NUM_BEAMS)
        if requested_num_ch != self._num_ch:
            self.get_logger().warning(
                f'num_channels={requested_num_ch} exceeds hardware capacity {_NUM_BEAMS}; using {_NUM_BEAMS} valid distance channels'
            )
        self._start_reg = self.get_parameter('start_reg').get_parameter_value().integer_value
        self._range_max = self.get_parameter('range_max_m').get_parameter_value().double_value
        self._scale = self.get_parameter('range_scale').get_parameter_value().double_value
        serial_timeout = self.get_parameter('serial_timeout').get_parameter_value().double_value

        # Pre-build the Modbus request frame (won't change at runtime)
        self._request = build_fc03(self._slave, self._start_reg, self._num_ch)

        # ------------------------------------------------------------------
        # Publishers
        # ------------------------------------------------------------------
        self._pub_dist = self.create_publisher(Float32MultiArray, topic_dist, 10)
        self._pub_scan = self.create_publisher(LaserScan, topic_scan, 10)

        # ------------------------------------------------------------------
        # Serial port
        # ------------------------------------------------------------------
        self._ser = None
        self._open_serial(port, baud, serial_timeout)

        # ------------------------------------------------------------------
        # Poll timer
        # ------------------------------------------------------------------
        self._timer = self.create_timer(period, self._timer_callback)
        self.get_logger().info(
            f'CCF-LAS4-4M node started | port={port} baud={baud} '
            f'slave={self._slave} period={period:.3f}s channels={self._num_ch}'
        )

    # ------------------------------------------------------------------
    # Serial helpers
    # ------------------------------------------------------------------

    def _open_serial(self, port: str, baud: int, timeout: float) -> None:
        try:
            self._ser = serial.Serial(port, baud, timeout=timeout)
            self.get_logger().info(f'Opened serial port {port} @ {baud} baud (timeout={timeout}s)')
        except serial.SerialException as exc:
            self._ser = None
            self.get_logger().error(
                f'Cannot open serial port {port}: {exc}\n'
                '  → Check the port path and that the user has access to it.\n'
                '  → Run:  sudo usermod -aG dialout $USER  (then re-login)'
            )

    # ------------------------------------------------------------------
    # Timer callback
    # ------------------------------------------------------------------

    def _timer_callback(self) -> None:
        if self._ser is None or not self._ser.is_open:
            self.get_logger().warning('Serial port not available; skipping poll', throttle_duration_sec=5.0)
            return

        # --- query sensor -----------------------------------------------
        try:
            raw_bytes = query(self._ser, self._request, wait_s=0.08)
        except Exception as exc:
            self.get_logger().error(f'Serial write/read error: {exc}', throttle_duration_sec=2.0)
            return

        if not raw_bytes:
            self.get_logger().debug('No response from sensor (timeout)')
            return

        # --- parse Modbus response --------------------------------------
        try:
            registers = parse_fc03_response(raw_bytes, self._num_ch)
        except ModbusError as exc:
            self.get_logger().warning(
                f'Modbus parse error: {exc}  raw={raw_bytes.hex().upper()}',
                throttle_duration_sec=1.0,
            )
            return

        if len(registers) < self._num_ch:
            self.get_logger().warning(
                f'Expected {self._num_ch} registers, got {len(registers)}'
            )
            return

        # --- publish raw register values (no normalization) ------------
        distances_raw: list[float] = []
        distances_m: list[float] = []
        for raw in registers[: self._num_ch]:
            if raw in _INVALID_RAW_VALUES:
                distances_raw.append(float('inf'))
                distances_m.append(float('inf'))
            else:
                raw_float = float(raw)
                distances_raw.append(raw_float)
                distances_m.append(raw_float * self._scale)

        now = self.get_clock().now().to_msg()

        dist_msg = Float32MultiArray()
        dist_msg.layout = MultiArrayLayout(
            dim=[MultiArrayDimension(label='channel', size=self._num_ch, stride=self._num_ch)],
            data_offset=0,
        )
        dist_msg.data = distances_raw
        self._pub_dist.publish(dist_msg)

        # --- publish LaserScan ------------------------------------------
        scan_msg = LaserScan()
        scan_msg.header.stamp = now
        scan_msg.header.frame_id = self._frame_id
        scan_msg.angle_min = _ANGLE_MIN
        scan_msg.angle_max = _ANGLE_MAX
        scan_msg.angle_increment = _ANGLE_INCREMENT
        scan_msg.time_increment = 0.0
        scan_msg.scan_time = float(self.get_parameter('period').get_parameter_value().double_value)
        scan_msg.range_min = 0.01   # 1 cm
        scan_msg.range_max = self._range_max
        scan_msg.ranges = [
            min(d, self._range_max) if math.isfinite(d) else self._range_max
            for d in distances_m
        ]
        scan_msg.intensities = []   # not provided by this sensor
        self._pub_scan.publish(scan_msg)

        self.get_logger().debug(
            'raw distances: ' + '  '.join(
                f'ch{i+1}={d:.1f}' if math.isfinite(d) else f'ch{i+1}=OOR'
                for i, d in enumerate(distances_raw)
            )
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def destroy_node(self) -> None:
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
                self.get_logger().info('Serial port closed')
            except Exception:
                pass
        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = CcfLaserNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
