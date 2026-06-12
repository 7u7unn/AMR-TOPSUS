#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   AGV Sensor Auto-Detector — Beijing Xintuo Future Technology   ║
║   Detects:                                                       ║
║     • Laser Obstacle Avoidance Sensor (1-400cm, RS485 Modbus)   ║
║     • 16-bit Magnetic Navigation Sensor (CCF-NS16, RS485 Modbus)║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    python3 detect_agv_sensors.py
    python3 detect_agv_sensors.py --addr 1           # specific Modbus address
    python3 detect_agv_sensors.py --baud 9600        # try single baud only
    python3 detect_agv_sensors.py --exclude ttyUSB0 ttyUSB1 ttyS1 ttyS3
"""

import serial
import serial.tools.list_ports
import struct
import time
import argparse
import sys
from dataclasses import dataclass
from typing import Optional

# ═══════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════

DEFAULT_EXCLUDED  = ["ttyS1", "ttyS3"]
DEFAULT_BAUDS     = [9600, 19200, 115200, 38400, 4800]
DEFAULT_ADDRESSES = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]          # Add more e.g. [0x01, 0x02] if needed
TIMEOUT_SEC       = 1.0

# ═══════════════════════════════════════════════════════════════
#  COLORS (ANSI)
# ═══════════════════════════════════════════════════════════════

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"
    BLUE   = "\033[94m"
    PURPLE = "\033[95m"

def ok(msg):    print(f"  {C.GREEN}✅ {msg}{C.RESET}")
def fail(msg):  print(f"  {C.GRAY}   {msg}{C.RESET}")
def warn(msg):  print(f"  {C.YELLOW}⚠  {msg}{C.RESET}")
def info(msg):  print(f"  {C.CYAN}ℹ  {msg}{C.RESET}")

# ═══════════════════════════════════════════════════════════════
#  MODBUS RTU UTILITIES
# ═══════════════════════════════════════════════════════════════

def crc16_modbus(data: bytes) -> bytes:
    """Calculate CRC16 for Modbus RTU."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)

def build_request(addr: int, func: int, reg: int, count: int) -> bytes:
    """Build a Modbus RTU read request frame."""
    frame = struct.pack('>BBHH', addr, func, reg, count)
    return frame + crc16_modbus(frame)

def verify_crc(frame: bytes) -> bool:
    """Validate CRC of received frame."""
    if len(frame) < 4:
        return False
    data, recv_crc = frame[:-2], frame[-2:]
    return crc16_modbus(data) == recv_crc

def modbus_query(ser: serial.Serial, request: bytes,
                 expected_len: int) -> Optional[bytes]:
    """Send Modbus request and read response. Returns None on failure."""
    try:
        ser.reset_input_buffer()
        ser.write(request)
        time.sleep(0.05)

        response = ser.read(expected_len)
        if len(response) < expected_len:
            # Try to read remaining bytes
            response += ser.read(expected_len - len(response))

        if len(response) == expected_len and verify_crc(response):
            return response
        return None
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════
#  SENSOR DEFINITIONS
# ═══════════════════════════════════════════════════════════════

@dataclass
class SensorResult:
    sensor_type: str
    port: str
    baud: int
    addr: int
    raw_data: dict

# ───────────────────────────────────────────────
#  LASER OBSTACLE AVOIDANCE SENSOR
#  FC=04, Register 0x0000 → distance (cm)
#  Response: [addr][04][02][hi][lo][crc_lo][crc_hi]
# ───────────────────────────────────────────────

LASER_NAME     = "Laser Obstacle Avoidance Sensor"
LASER_FC       = 0x04
LASER_REG      = 0x0000
LASER_COUNT    = 0x0001
LASER_RESP_LEN = 7   # addr(1)+fc(1)+bytecount(1)+data(2)+crc(2)

def probe_laser(ser: serial.Serial, addr: int) -> Optional[dict]:
    """
    Query laser sensor. Returns dict with distance if valid.
    Laser sensor: FC04, reg 0x0000 → 16-bit distance in cm (1–400).
    """
    req = build_request(addr, LASER_FC, LASER_REG, LASER_COUNT)
    resp = modbus_query(ser, req, LASER_RESP_LEN)

    if resp is None:
        return None
    if resp[0] != addr or resp[1] != LASER_FC or resp[2] != 0x02:
        return None

    distance_cm = struct.unpack('>H', resp[3:5])[0]

    # Sanity check: laser range is 1–400 cm
    if 0 <= distance_cm <= 400:
        return {
            "distance_cm": distance_cm,
            "raw_hex": resp.hex(' ').upper(),
        }
    return None

# ───────────────────────────────────────────────
#  16-BIT MAGNETIC NAVIGATION SENSOR
#  FC=03, Register 0x0000 → 16-bit bitmap (which elements detect tape)
#         Register 0x0001 → deviation (signed, mm offset from center)
#  Response: [addr][03][04][r0_hi][r0_lo][r1_hi][r1_lo][crc_lo][crc_hi]
# ───────────────────────────────────────────────

MAG_NAME     = "16-bit Magnetic Navigation Sensor"
MAG_FC       = 0x03
MAG_REG      = 0x0000
MAG_COUNT    = 0x0002     # Read 2 registers: bitmap + deviation
MAG_RESP_LEN = 9          # addr(1)+fc(1)+bytecount(1)+data(4)+crc(2)

def probe_magnetic(ser: serial.Serial, addr: int) -> Optional[dict]:
    """
    Query magnetic navigation sensor.
    Register 0: 16-bit detection bitmap (each bit = 1 sensor element).
    Register 1: signed deviation from center (mm or raw unit).
    """
    req = build_request(addr, MAG_FC, MAG_REG, MAG_COUNT)
    resp = modbus_query(ser, req, MAG_RESP_LEN)

    if resp is None:
        return None
    if resp[0] != addr or resp[1] != MAG_FC or resp[2] != 0x04:
        return None

    bitmap    = struct.unpack('>H', resp[3:5])[0]
    deviation = struct.unpack('>h', resp[5:7])[0]   # signed

    # Decode bitmap: which of the 16 elements are active
    active_bits = [i + 1 for i in range(16) if (bitmap >> i) & 1]

    return {
        "bitmap":       bitmap,
        "bitmap_bin":   format(bitmap, '016b'),
        "active_bits":  active_bits,
        "deviation":    deviation,
        "raw_hex":      resp.hex(' ').upper(),
    }

def render_bitmap(bitmap_bin: str) -> str:
    """Render 16-bit bitmap as visual bar."""
    bar = ""
    for ch in bitmap_bin:
        bar += f"{C.GREEN}█{C.RESET}" if ch == '1' else f"{C.GRAY}░{C.RESET}"
    return bar

# ═══════════════════════════════════════════════════════════════
#  MAIN DETECTOR
# ═══════════════════════════════════════════════════════════════

def scan_ports(excluded: list, bauds: list, addresses: list) -> list:
    """Scan all available serial ports, try both sensor types."""
    results = []
    available_ports = list(serial.tools.list_ports.comports())

    if not available_ports:
        print(f"\n{C.RED}No serial ports found on this system.{C.RESET}")
        print("Check: ls /dev/tty*\n")
        return results

    print(f"\n{C.BOLD}{C.BLUE}{'═'*62}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}  Scanning {len(available_ports)} port(s) | "
          f"Bauds: {bauds} | Addr: {[hex(a) for a in addresses]}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{'═'*62}{C.RESET}\n")

    for port_info in available_ports:
        name   = port_info.name
        device = port_info.device
        desc   = port_info.description or "Unknown"

        if name in excluded:
            print(f"{C.GRAY}[SKIP] {device} — excluded{C.RESET}")
            continue

        print(f"{C.BOLD}[PORT] {device}{C.RESET}  {C.GRAY}{desc}{C.RESET}")

        found_on_port = False

        for baud in bauds:
            if found_on_port:
                break
            for addr in addresses:
                try:
                    ser = serial.Serial(
                        port=device,
                        baudrate=baud,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=TIMEOUT_SEC
                    )
                except serial.SerialException as e:
                    warn(f"Cannot open {device}: {e}")
                    break

                # ── Try LASER first ──────────────────────────
                laser_data = probe_laser(ser, addr)
                if laser_data:
                    ok(f"{C.BOLD}{LASER_NAME}{C.RESET}")
                    info(f"Port={device}  Baud={baud}  Addr={hex(addr)}")
                    info(f"📏 Distance : {laser_data['distance_cm']} cm")
                    info(f"Raw HEX    : {laser_data['raw_hex']}")
                    results.append(SensorResult(
                        sensor_type="laser",
                        port=device, baud=baud, addr=addr,
                        raw_data=laser_data
                    ))
                    found_on_port = True
                    ser.close()
                    break

                # ── Try MAGNETIC second ──────────────────────
                mag_data = probe_magnetic(ser, addr)
                if mag_data:
                    ok(f"{C.BOLD}{MAG_NAME}{C.RESET}")
                    info(f"Port={device}  Baud={baud}  Addr={hex(addr)}")
                    info(f"🧲 Bitmap   : {render_bitmap(mag_data['bitmap_bin'])}")
                    info(f"   Bits     : {mag_data['bitmap_bin']}  (0x{mag_data['bitmap']:04X})")
                    info(f"   Active   : {mag_data['active_bits'] if mag_data['active_bits'] else 'None (no tape detected)'}")
                    info(f"   Deviation: {mag_data['deviation']}")
                    info(f"Raw HEX    : {mag_data['raw_hex']}")
                    results.append(SensorResult(
                        sensor_type="magnetic",
                        port=device, baud=baud, addr=addr,
                        raw_data=mag_data
                    ))
                    found_on_port = True
                    ser.close()
                    break

                fail(f"Baud={baud} Addr={hex(addr)} — no response")
                ser.close()

        if not found_on_port:
            print(f"  {C.YELLOW}No sensor detected on {device}{C.RESET}")
        print()

    return results

# ═══════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════

def print_summary(results: list):
    print(f"\n{C.BOLD}{'═'*62}")
    print(f"  SUMMARY — {len(results)} sensor(s) found")
    print(f"{'═'*62}{C.RESET}\n")

    if not results:
        print(f"{C.RED}  ❌ No sensors detected.{C.RESET}")
        print(f"{C.GRAY}  Tips:")
        print(f"  • Check RS485 A/B wiring (try swapping)")
        print(f"  • Verify sensor power (check LED)")
        print(f"  • Try different Modbus address (default: 0x01)")
        print(f"  • Run: ls /dev/tty* to verify port exists{C.RESET}\n")
        return

    lasers   = [r for r in results if r.sensor_type == "laser"]
    magnetics = [r for r in results if r.sensor_type == "magnetic"]

    if lasers:
        print(f"  {C.PURPLE}🔴 LASER OBSTACLE AVOIDANCE SENSOR(S):{C.RESET}")
        for r in lasers:
            print(f"     Port : {C.BOLD}{r.port}{C.RESET}")
            print(f"     Baud : {r.baud} | Addr: {hex(r.addr)}")
            print(f"     Dist : {r.raw_data['distance_cm']} cm\n")

    if magnetics:
        print(f"  {C.BLUE}🧲 MAGNETIC NAVIGATION SENSOR(S):{C.RESET}")
        for r in magnetics:
            active = r.raw_data['active_bits']
            print(f"     Port     : {C.BOLD}{r.port}{C.RESET}")
            print(f"     Baud     : {r.baud} | Addr: {hex(r.addr)}")
            print(f"     Bitmap   : {r.raw_data['bitmap_bin']}")
            print(f"     Active   : {active if active else 'None'}")
            print(f"     Deviation: {r.raw_data['deviation']}\n")

# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Auto-detect AGV sensors (Laser + Magnetic) via RS485 Modbus RTU"
    )
    parser.add_argument(
        "--exclude", nargs="+", default=DEFAULT_EXCLUDED,
        metavar="PORT",
        help=f"Ports to exclude (default: {DEFAULT_EXCLUDED})"
    )
    parser.add_argument(
        "--baud", nargs="+", type=int, default=DEFAULT_BAUDS,
        metavar="BAUD",
        help=f"Baud rates to try (default: {DEFAULT_BAUDS})"
    )
    parser.add_argument(
        "--addr", nargs="+", type=lambda x: int(x, 0),
        default=DEFAULT_ADDRESSES,
        metavar="ADDR",
        help="Modbus addresses to try e.g. 0x01 0x02 (default: 0x01)"
    )
    parser.add_argument(
        "--monitor", action="store_true",
        help="After detection, continuously monitor sensor values"
    )
    args = parser.parse_args()

    # Header
    print(f"\n{C.BOLD}{C.CYAN}")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║  AGV Sensor Detector — Xintuo Future Technology     ║")
    print("  ║  Laser Obstacle Avoidance + 16-bit Magnetic Nav     ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")
    print(f"  Excluded ports : {args.exclude}")
    print(f"  Baud rates     : {args.baud}")
    print(f"  Modbus addrs   : {[hex(a) for a in args.addr]}")

    results = scan_ports(args.exclude, args.baud, args.addr)
    print_summary(results)

    # ── MONITOR MODE ──────────────────────────────────────────
    if args.monitor and results:
        print(f"\n{C.BOLD}{C.YELLOW}📡 MONITOR MODE — Ctrl+C to stop{C.RESET}\n")
        try:
            sensors_open = []
            for r in results:
                ser = serial.Serial(
                    port=r.port, baudrate=r.baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=TIMEOUT_SEC
                )
                sensors_open.append((r, ser))

            while True:
                for r, ser in sensors_open:
                    if r.sensor_type == "laser":
                        req = build_request(r.addr, LASER_FC, LASER_REG, LASER_COUNT)
                        resp = modbus_query(ser, req, LASER_RESP_LEN)
                        if resp:
                            dist = struct.unpack('>H', resp[3:5])[0]
                            bar = "█" * int(dist / 10) if dist <= 400 else ""
                            print(f"\r  🔴 {r.port} | Distance: {C.BOLD}{dist:>4} cm{C.RESET}  {bar:<40}", end="")

                    elif r.sensor_type == "magnetic":
                        req = build_request(r.addr, MAG_FC, MAG_REG, MAG_COUNT)
                        resp = modbus_query(ser, req, MAG_RESP_LEN)
                        if resp:
                            bitmap    = struct.unpack('>H', resp[3:5])[0]
                            deviation = struct.unpack('>h', resp[5:7])[0]
                            bmap_str  = render_bitmap(format(bitmap, '016b'))
                            print(f"\r  🧲 {r.port} | {bmap_str} dev={deviation:+4}", end="")

                time.sleep(0.1)

        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}Monitor stopped.{C.RESET}")
        finally:
            for _, ser in sensors_open:
                ser.close()

if __name__ == "__main__":
    main()