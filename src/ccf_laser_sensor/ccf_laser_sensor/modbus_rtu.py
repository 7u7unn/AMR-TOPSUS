"""
ccf_laser_sensor.modbus_rtu
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Minimal Modbus RTU helpers for the CCF-LAS4-4M sensor.
No external modbus library required – only pyserial.
"""

import time
import struct


# ---------------------------------------------------------------------------
# CRC-16 / Modbus
# ---------------------------------------------------------------------------

def crc16(data: bytes) -> int:
    """Return the Modbus CRC-16 for *data*."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc & 0xFFFF


def _append_crc(frame: bytearray) -> bytes:
    c = crc16(bytes(frame))
    frame += bytearray([c & 0xFF, c >> 8])
    return bytes(frame)


def build_fc03(slave: int, start_reg: int, num_regs: int) -> bytes:
    """Build a Modbus FC=0x03 (Read Holding Registers) request frame."""
    frame = bytearray([
        slave & 0xFF,
        0x03,
        (start_reg >> 8) & 0xFF,
        start_reg & 0xFF,
        (num_regs >> 8) & 0xFF,
        num_regs & 0xFF,
    ])
    return _append_crc(frame)


# ---------------------------------------------------------------------------
# Frame parsing
# ---------------------------------------------------------------------------

class ModbusError(Exception):
    pass


def parse_fc03_response(resp: bytes, expected_regs: int) -> list[int]:
    """
    Parse a Modbus FC=0x03 response and return a list of unsigned 16-bit
    register values.

    Expected frame layout:
        [0]  slave address
        [1]  function code (0x03)
        [2]  byte count  (= 2 * num_regs)
        [3 .. 3+bytecount-1]  register data, big-endian
        [-2] CRC low
        [-1] CRC high

    Raises ModbusError on short frames, CRC mismatch, or exception responses.
    """
    if len(resp) < 5:
        raise ModbusError(f'Frame too short: {len(resp)} bytes  hex={resp.hex().upper()}')

    # Check for Modbus exception response (FC | 0x80)
    if resp[1] & 0x80:
        raise ModbusError(f'Modbus exception code {resp[2]:#04x}')

    byte_count = resp[2]
    expected_len = 3 + byte_count + 2  # header + data + CRC
    if len(resp) < expected_len:
        raise ModbusError(
            f'Frame shorter than expected: got {len(resp)}, need {expected_len}'
        )

    # Verify CRC over everything except the last two bytes
    payload = resp[:3 + byte_count]
    calc_crc = crc16(payload)
    recv_crc = resp[3 + byte_count] | (resp[3 + byte_count + 1] << 8)
    if calc_crc != recv_crc:
        raise ModbusError(
            f'CRC mismatch: calculated {calc_crc:#06x}, received {recv_crc:#06x}'
        )

    # Unpack registers (big-endian unsigned 16-bit words)
    data = resp[3:3 + byte_count]
    num_regs = byte_count // 2
    registers = list(struct.unpack(f'>{num_regs}H', data))
    return registers


# ---------------------------------------------------------------------------
# Low-level serial transaction
# ---------------------------------------------------------------------------

def query(ser, request: bytes, wait_s: float = 0.15) -> bytes:
    """
    Flush the RX buffer, transmit *request*, wait *wait_s* seconds, then
    read whatever is available (up to 64 bytes).

    This implementation avoids blocking on `ser.read()` when no data has
    arrived by returning an empty bytes object after the wait period. It
    polls `in_waiting` during the wait window to detect incoming bytes.
    """
    ser.reset_input_buffer()
    ser.write(request)

    end = time.monotonic() + wait_s
    # Poll for incoming bytes until wait_s expires
    while time.monotonic() < end:
        if ser.in_waiting:
            # small delay to let the remaining bytes arrive
            time.sleep(0.001)
            break
        time.sleep(0.005)

    if not ser.in_waiting:
        return b''

    # Read only the available bytes to avoid blocking on serial timeout
    return ser.read(ser.in_waiting or 64)
