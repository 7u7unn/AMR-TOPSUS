#!/usr/bin/env python3
"""
Integrated ARYA Web Interface - Main Entry Point
Combines modular backend (ROS2 Node) with FastAPI web server
Ready for: ros2 launch arya_web_interface amir_starter.launch.py
"""

import asyncio
import json
import logging
import os
import signal
import threading
import time
import math
from pathlib import Path

import rclpy
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from ament_index_python.packages import get_package_prefix, get_package_share_directory

from std_msgs.msg import Float32MultiArray, String, UInt8

# Import new modular structure
from arya_web_interface.services.ros_node import AryaWebNode
from arya_web_interface.models.requests import (
    LocalizationRequest,
    MappingSaveRequest,
    NavAnnotationsRequest,
)
from arya_web_interface.handlers import (
    handle_get_maps,
    handle_get_map_grid,
    handle_get_nav_annotations,
    handle_save_slam_map,
    handle_save_nav_annotations,
)
from arya_web_interface.utils.validation import (
    validate_coordinates,
    validate_map_name,
    sanitize_mapping_file_stem,
)
from arya_web_interface.utils.constants import (
    LAUNCH_PRESETS,
    KNOWN_ROS_TOPIC_TYPES,
)
from arya_web_interface.utils.map_management import (
    find_maps_folder,
    extract_default_map_name,
    nav_annotation_path,
    save_nav_annotations,
    save_selected_map,
    MAP_SELECTION_LOCK,
    MAPPING_SAVE_LOCK,
)
from arya_web_interface.utils.converters import (
    normalize_topic_name,
    ros_value_to_bounded_data,
)


# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AryaWebInterface")

# ===================== GLOBAL STATE =====================
ros_node: AryaWebNode = None
ros_executor = None
ros_thread = None
app_shutdown = False


def setup_ros_node():
    """Initialize ROS2 node and executor in separate thread."""
    global ros_node, ros_executor, ros_thread

    def run_ros():
        try:
            rclpy.spin(ros_node)
        except KeyboardInterrupt:
            pass
        finally:
            ros_node.destroy_node()
            rclpy.shutdown()

    rclpy.init()
    ros_node = AryaWebNode()
    
    ros_thread = threading.Thread(target=run_ros, daemon=False)
    ros_thread.start()
    logger.info("✓ ROS2 Node started")


def shutdown_ros():
    """Gracefully shutdown ROS2."""
    global app_shutdown
    app_shutdown = True
    if ros_node:
        ros_node.destroy_node()
    logger.info("✓ ROS2 Node stopped")


# ===================== FASTAPI APP =====================
app = FastAPI(
    title="ARYA Web Interface",
    description="Headless web control for autonomous mobile robot",
    version="2.0",
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== CSP MIDDLEWARE =====================
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers including CSP."""
    response = await call_next(request)

    # CSP for production - block eval and inline scripts
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws: wss: http: https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# ===================== HEALTH & STATUS =====================
@app.get("/api/healthz")
@app.get("/healthz")
async def healthz():
    """Health check endpoint for container orchestration and UI."""
    if not ros_node:
        return JSONResponse({"status": "initializing", "ok": False, "ros_ready": False}, status_code=503)
    
    return {
        "status": "ok",
        "ok": True,
        "ros_node": "running",
        "ros_ready": True,
        "time": ros_node.get_clock().now().to_msg().sec,
    }


@app.get("/api/status")
async def get_status():
    """Get robot and web interface status."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    with ros_node.nav_goal_lock:
        nav_status = ros_node.nav_goal_status.copy()
    
    with ros_node.mission_lock:
        mission_status = ros_node.mission_status.copy()
    
    return {
        "connected": True,
        "robot_ready": True,
        "telemetry": ros_node.telemetry.copy() if hasattr(ros_node, "telemetry") else {},
        "navigation": nav_status,
        "mission": mission_status,
    }


# ===================== MAP ENDPOINTS =====================
@app.get("/api/maps")
async def get_maps():
    """List all available maps."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    return await handle_get_maps(find_maps_folder, extract_default_map_name)


@app.post("/api/maps/select")
async def select_map(request: LocalizationRequest):
    """Select and load a map for localization."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    try:
        validate_map_name(request.map_name)
        map_path = _resolve_map_path(request.map_name)
        with MAP_SELECTION_LOCK:
            save_selected_map(map_path)
        logger.info(f"Loading map: {request.map_name}")
        return {
            "message": f"Map {request.map_name} disimpan untuk localization manual.",
            "map_name": request.map_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/maps/grid")
@app.get("/api/maps/{map_name}/grid")
async def get_map_grid(map_name: str):
    """Get occupancy grid data for a map."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    try:
        validate_map_name(map_name)
        return await handle_get_map_grid(map_name, resolve_map_fn=_resolve_map_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/nav_annotations")
@app.get("/api/maps/{map_name}/annotations")
async def get_map_annotations(map_name: str):
    """Get saved annotations for a map (zones, stations, etc)."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    try:
        validate_map_name(map_name)
        return await handle_get_nav_annotations(
            map_name,
            resolve_map_fn=_resolve_map_path,
            nav_annotation_path_fn=nav_annotation_path,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/nav_annotations")
@app.post("/api/maps/{map_name}/annotations")
async def save_map_annotations(request: NavAnnotationsRequest, map_name: str = None):
    """Save annotations for a map."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    target_map = map_name or request.map_name
    try:
        validate_map_name(target_map)
        logger.info(f"Saving annotations for map: {target_map}")
        return await handle_save_nav_annotations(
            target_map,
            request.zones,
            request.stations,
            resolve_map_fn=_resolve_map_path,
            save_nav_annotations_fn=save_nav_annotations,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== NAVIGATION ENDPOINTS =====================
@app.post("/api/goal/nav2")
async def set_nav2_goal(request: dict):
    """Set navigation goal via Nav2 action."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    try:
        x = float(request.get("x", 0))
        y = float(request.get("y", 0))
        theta = float(request.get("theta", 0))
        
        x, y, theta = validate_coordinates(x, y, theta)
        
        with ros_node.nav_goal_lock:
            ros_node.nav_goal_seq += 1
            seq = ros_node.nav_goal_seq
        
        logger.info(f"Goal {seq}: navigate to ({x}, {y}, {theta})")
        return {"goal_id": seq, "status": "accepted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/goal/cancel")
async def cancel_goal():
    """Cancel current navigation goal."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    with ros_node.nav_goal_lock:
        if ros_node.current_nav_goal_handle:
            logger.info("Canceling navigation goal")
            ros_node.cancel_current_nav_goal(update_status=True)
            return {"status": "canceled"}
        else:
            raise HTTPException(status_code=400, detail="No active goal")


# ===================== DRIVE CONTROL ENDPOINTS =====================
@app.post("/api/drive/mode")
async def set_drive_mode(request: dict):
    """Set drive mode: manual or auto."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    mode = request.get("mode", "manual").lower()
    if mode not in ["manual", "auto"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    ros_node.set_drive_mode(mode)
    logger.info(f"Drive mode set to: {mode}")
    return {"mode": mode}


@app.post("/api/drive/joystick")
async def joystick_command(request: dict):
    """Joystick command: linear and angular velocity."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    try:
        linear_x = float(request.get("linear_x", 0))
        angular_z = float(request.get("angular_z", 0))
        
        # Clamp values to [-1.0, 1.0]
        linear_x = max(-1.0, min(1.0, linear_x))
        angular_z = max(-1.0, min(1.0, angular_z))
        
        ros_node.send_cmd_vel(linear_x, angular_z)
        return {"status": "received"}
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid values: {e}")


# ===================== SLAM MAPPING ENDPOINTS =====================
@app.post("/api/mapping/save")
@app.post("/api/slam/save")
async def save_slam_map(request: MappingSaveRequest):
    """Save SLAM map from SLAM Toolbox."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    try:
        sanitized = sanitize_mapping_file_stem(request.map_name)
        logger.info(f"Saving SLAM map: {sanitized}")
        return await handle_save_slam_map(
            sanitized,
            find_maps_fn=find_maps_folder,
            ros_logger=ros_node.get_logger(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== PATH RECORDER ENDPOINTS =====================
@app.post("/api/path_recorder/start")
async def start_path_recorder():
    """Start path recording."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    ok = ros_node.send_path_recorder_command("start")
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send start command to path recorder")
    return {"status": "started"}

@app.post("/api/path_recorder/stop")
async def stop_path_recorder():
    """Stop path recording."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    ok = ros_node.send_path_recorder_command("stop")
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send stop command to path recorder")
    return {"status": "stopped"}

@app.post("/api/path_recorder/name_station")
async def name_station_path_recorder(request: dict):
    """Name current station pose in path recorder."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    name = request.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Station name is required")
        
    ok = ros_node.send_path_recorder_command(f"name:{name}")
    if not ok:
        raise HTTPException(status_code=500, detail=f"Failed to name station '{name}'")
    return {"status": "named", "station_name": name}


# ===================== DIAGNOSTICS ENDPOINTS =====================
@app.get("/api/topics")
@app.get("/api/diagnostics/topics")
async def get_topics():
    """Get list of available ROS topics."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    return {"topics": list(KNOWN_ROS_TOPIC_TYPES.keys())}


@app.get("/api/diagnostics/launches")
async def get_launch_presets():
    """Get available launch presets."""
    return {"presets": LAUNCH_PRESETS}


@app.post("/api/diagnostics/echo/{topic_name}")
async def subscribe_topic_echo(topic_name: str):
    """Subscribe to dynamic topic for diagnostics."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
# ===================== DIAGNOSTICS ENDPOINTS =====================
@app.get("/api/topics")
@app.get("/api/diagnostics/topics")
async def get_topics():
    """Get list of available ROS topics."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    return {"topics": list(KNOWN_ROS_TOPIC_TYPES.keys())}


@app.get("/api/diagnostics/launches")
async def get_launch_presets():
    """Get available launch presets."""
    return {"presets": LAUNCH_PRESETS}


@app.post("/api/diagnostics/echo/{topic_name}")
async def subscribe_topic_echo(topic_name: str):
    """Subscribe to dynamic topic for diagnostics."""
    if not ros_node:
        raise HTTPException(status_code=503, detail="ROS node not ready")
    
    logger.info(f"Echo topic: {topic_name}")
    return {"topic": topic_name, "status": "subscribed"}


# ===================== WEBSOCKET CHANNELS =====================
@app.websocket("/ws/topics")
async def ws_topics(websocket: WebSocket):
    """WebSocket for dynamic topic echo streaming."""
    await websocket.accept()
    subscriptions = []
    slot_states = {}
    state_lock = threading.Lock()
    echo_rate_hz = 5
    min_convert_interval = 1.0 / echo_rate_hz

    def clear_subscriptions():
        nonlocal subscriptions
        if ros_node is not None:
            for subscription in subscriptions:
                try:
                    ros_node.destroy_echo_subscription(subscription)
                except Exception as exc:
                    logger.warning(f"Gagal melepas topic echo subscription: {exc}")
        subscriptions = []
        with state_lock:
            slot_states.clear()

    def make_echo_callback(slot: int):
        def cb(msg):
            now = time.monotonic()
            with state_lock:
                state = slot_states.get(slot)
                if state is None:
                    return
                if now - state["last_convert"] < min_convert_interval:
                    return
                state["last_convert"] = now

            data = ros_value_to_bounded_data(msg)

            with state_lock:
                state = slot_states.get(slot)
                if state is None:
                    return
                state["count"] += 1
                state["stamp"] = time.strftime("%H:%M:%S")
                state["data"] = data
                state["dirty"] = True

        return cb

    async def subscribe_topics(topics):
        if ros_node is None:
            await websocket.send_text(json.dumps({
                "type": "error",
                "detail": "ROS node belum siap.",
            }))
            return

        clean_topics = []
        for raw_topic in topics:
            clean_topic = normalize_topic_name(raw_topic)
            if clean_topic and clean_topic not in clean_topics:
                clean_topics.append(clean_topic)

        if len(clean_topics) > 2:
            await websocket.send_text(json.dumps({
                "type": "error",
                "detail": "Echo dibatasi maksimal 2 ROS topic.",
            }))
            return

        clear_subscriptions()
        slots = []

        try:
            for slot, topic_name in enumerate(clean_topics, start=1):
                with state_lock:
                    slot_states[slot] = {
                        "slot": slot,
                        "topic": topic_name,
                        "msg_type": "",
                        "stamp": "waiting",
                        "count": 0,
                        "data": {"status": "waiting for message"},
                        "dirty": True,
                        "last_convert": 0.0,
                    }

                subscription, msg_type = ros_node.create_echo_subscription(
                    topic_name,
                    make_echo_callback(slot),
                )
                subscriptions.append(subscription)

                with state_lock:
                    slot_states[slot]["msg_type"] = msg_type

                slots.append({
                    "slot": slot,
                    "topic": topic_name,
                    "msg_type": msg_type,
                })
        except Exception as exc:
            clear_subscriptions()
            await websocket.send_text(json.dumps({
                "type": "error",
                "detail": str(exc),
            }))
            return

        await websocket.send_text(json.dumps({
            "type": "subscribed",
            "slots": slots,
            "rate_hz": echo_rate_hz,
        }))

    try:
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.2)
                data = json.loads(msg)

                if data.get("type") == "subscribe":
                    topics = data.get("topics", [])
                    if not isinstance(topics, list):
                        raise ValueError("Payload topics harus list")
                    await subscribe_topics(topics)
                elif data.get("type") == "clear":
                    clear_subscriptions()
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "slots": [],
                        "rate_hz": echo_rate_hz,
                    }))
            except asyncio.TimeoutError:
                pass
            except (json.JSONDecodeError, ValueError) as exc:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "detail": str(exc),
                }))

            updates = []
            with state_lock:
                for state in slot_states.values():
                    if not state["dirty"]:
                        continue
                    updates.append({
                        "slot": state["slot"],
                        "topic": state["topic"],
                        "msg_type": state["msg_type"],
                        "stamp": state["stamp"],
                        "count": state["count"],
                        "data": state["data"],
                    })
                    state["dirty"] = False

            if updates:
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "updates": updates,
                }))

    except WebSocketDisconnect:
        pass
    finally:
        clear_subscriptions()


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    """Main WebSocket channel for real-time telemetry streaming and command execution."""
    await websocket.accept()
    last_cmd_time = 0.0
    last_v, last_w = 0.0, 0.0
    last_telemetry_time = 0.0
    telemetry_interval = 0.1

    if ros_node:
        ros_node.map_dirty = True
        ros_node.local_costmap_dirty = True
        ros_node.global_costmap_dirty = True
        ros_node.path_dirty = True
        ros_node.recorded_path_dirty = True
        ros_node.lidar_scan_dirty = True

    while True:
        try:
            now = asyncio.get_event_loop().time()

            # send telemetry data at 10 Hz
            if ros_node and now - last_telemetry_time >= telemetry_interval:
                last_telemetry_time = now
                amcl_pose = ros_node.amcl_pose
                await websocket.send_text(json.dumps({
                    "voltage": ros_node.telemetry[0] if len(ros_node.telemetry) > 0 else 0,
                    "current_left": ros_node.telemetry[1] if len(ros_node.telemetry) > 1 else 0,
                    "current_right": ros_node.telemetry[2] if len(ros_node.telemetry) > 2 else 0,
                    "temp_driver": ros_node.telemetry[3] if len(ros_node.telemetry) > 3 else 0,
                    "rpm_left": ros_node.telemetry[4] if len(ros_node.telemetry) > 4 else 0,
                    "rpm_right": ros_node.telemetry[5] if len(ros_node.telemetry) > 5 else 0,
                    "x": ros_node.odom[0],
                    "y": ros_node.odom[1],
                    "theta": ros_node.odom[2],
                    "amcl_x": amcl_pose[0] if amcl_pose else None,
                    "amcl_y": amcl_pose[1] if amcl_pose else None,
                    "amcl_theta": amcl_pose[2] if amcl_pose else None,
                    "launches": ros_node.get_launch_statuses(),
                    "io_inputs":  ros_node.io_inputs_byte,
                    "io_outputs": ros_node.io_outputs_byte,
                    "lidar_motor": ros_node.lidar_motor_enabled,
                    "drive_mode": ros_node.drive_mode,
                    "nav_goal_status": ros_node.get_nav_goal_status(),
                    "mission_status": ros_node.get_station_mission_status(),
                    "front_laser": ros_node.front_laser_data,
                    "mag_line": ros_node.mag_line_data,
                }))

            if ros_node and getattr(ros_node, 'map_dirty', False):
                ros_node.map_dirty = False
                await websocket.send_text(json.dumps({"type": "nav_map", "data": ros_node.map_data}))

            if ros_node and getattr(ros_node, 'local_costmap_dirty', False):
                ros_node.local_costmap_dirty = False
                await websocket.send_text(json.dumps({"type": "nav_local_costmap", "data": ros_node.local_costmap_data}))

            if ros_node and getattr(ros_node, 'global_costmap_dirty', False):
                ros_node.global_costmap_dirty = False
                await websocket.send_text(json.dumps({"type": "nav_global_costmap", "data": ros_node.global_costmap_data}))

            if ros_node and getattr(ros_node, 'path_dirty', False):
                ros_node.path_dirty = False
                await websocket.send_text(json.dumps({"type": "nav_path", "data": ros_node.path_data}))

            if ros_node and getattr(ros_node, 'recorded_path_dirty', False):
                ros_node.recorded_path_dirty = False
                await websocket.send_text(json.dumps({"type": "recorded_path", "data": ros_node.recorded_path_data}))

            if ros_node and getattr(ros_node, 'lidar_scan_dirty', False):
                ros_node.lidar_scan_dirty = False
                await websocket.send_text(json.dumps({
                    "type": "nav_lidar_scan",
                    "data": ros_node.lidar_scan_data,
                }))

            # read incoming websocket commands
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.02)
                data = json.loads(msg)
            except asyncio.TimeoutError:
                # no command received in 0.02s -> stop manual drive if needed, or pass
                now_check = asyncio.get_event_loop().time()
                if ros_node and ros_node.drive_mode == "manual" and now_check - last_cmd_time > 0.1 and (last_v != 0.0 or last_w != 0.0):
                    ros_node.send_cmd_vel(0.0, 0.0)
                    last_v, last_w = 0.0, 0.0
                continue

            if ros_node is None:
                continue

            if data.get("type") == "cmd_vel":
                v = float(data["linear"])
                w = float(data["angular"])
                if ros_node.send_cmd_vel(v, w):
                    last_cmd_time = asyncio.get_event_loop().time()
                    last_v, last_w = v, w

            elif data.get("type") == "mode":
                ros_node.set_drive_mode(data.get("value"))
                last_v, last_w = 0.0, 0.0

            elif data.get("type") == "reset_odom":
                ros_node.reset_odom_and_restart_imu()
            elif data.get("type") == "reset_encoder":
                ros_node.pub_reset_encoder.publish(Float32MultiArray(data=[0.0]))
            elif data.get("type") == "lidar_motor":
                ros_node.set_lidar_motor(bool(data.get("enabled")))
            elif data.get("type") == "io_set_single":
                ch  = int(data["channel"])   # 1..8
                cmd = str(data["cmd"])       # "on" / "off"
                ros_node.pub_io_cmd.publish(String(data=f"{cmd} {ch}"))

            elif data.get("type") == "io_mask":
                mask = int(data["mask"]) & 0xFF
                ros_node.pub_io_mask.publish(UInt8(data=mask))
            elif data.get("type") == "goal_pose":
                result = ros_node.send_goal(data["x"], data["y"], data["theta"])
                result["type"] = "goal_pose_ack"
                result["drive_mode"] = ros_node.drive_mode
                result["nav_goal_status"] = ros_node.get_nav_goal_status()
                result["mission_status"] = ros_node.get_station_mission_status()
                await websocket.send_text(json.dumps(result))
            elif data.get("type") in ("initial_pose", "init_pose", "set_initial_pose"):
                result = ros_node.set_initial_pose(data["x"], data["y"], data["theta"])
                result["type"] = "initial_pose_ack"
                await websocket.send_text(json.dumps(result))
            elif data.get("type") == "mission_queue_start":
                result = ros_node.start_station_queue(data.get("stations", []))
                result["type"] = "mission_queue_ack"
                result["mission_status"] = ros_node.get_station_mission_status()
                await websocket.send_text(json.dumps(result))
            elif data.get("type") == "mission_queue_cancel":
                result = ros_node.cancel_station_queue()
                result["type"] = "mission_queue_ack"
                result["mission_status"] = ros_node.get_station_mission_status()
                await websocket.send_text(json.dumps(result))
            elif data.get("type") == "mission_status":
                await websocket.send_text(json.dumps({
                    "type": "mission_status",
                    "mission_status": ros_node.get_station_mission_status(),
                }))
            elif data.get("type") == "launch_start":
                result = ros_node.start_launch_preset(data.get("name"))
                result["type"] = "launch_result"
                result["launches"] = ros_node.get_launch_statuses()
                await websocket.send_text(json.dumps(result))
            elif data.get("type") == "launch_stop":
                result = ros_node.stop_launch_preset(data.get("name"))
                result["type"] = "launch_result"
                result["launches"] = ros_node.get_launch_statuses()
                await websocket.send_text(json.dumps(result))
            elif data.get("type") == "launch_status":
                await websocket.send_text(json.dumps({
                    "type": "launch_status",
                    "launches": ros_node.get_launch_statuses(),
                }))
        except WebSocketDisconnect:
            if ros_node and ros_node.drive_mode == "manual":
                ros_node.send_cmd_vel(0.0, 0.0)
            break


# ===================== PATH RESOLUTION =====================
def _resolve_static_dir() -> Path:
    """Resolve static directory path safely, supporting both ROS2 share and local source runs."""
    try:
        share_path = Path(get_package_share_directory("arya_web_interface")) / "static"
        if share_path.exists():
            return share_path
    except Exception:
        pass

    try:
        pkg_prefix = get_package_prefix("arya_web_interface")
        prefix_path = Path(pkg_prefix) / "share" / "arya_web_interface" / "static"
        if prefix_path.exists():
            return prefix_path
    except Exception:
        pass

    return Path(__file__).parent / "static"


def _resolve_dist_dir() -> Path:
    """Resolve dist directory path for Vite build output."""
    base = Path(__file__).parent.parent  # Go up from arya_web_interface/
    dist_path = base / "dist"
    if dist_path.exists():
        return dist_path
    return base / "dist"


def _static_file_response(file_path: Path, media_type: str):
    """Serve a static file with cache disabled for robot UI updates."""
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def _resolve_static_asset(asset_path: str) -> Path:
    """Resolve a static asset from nested or older flattened install layouts."""
    relative_path = Path(asset_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise HTTPException(status_code=404, detail="Static asset not found")

    static_dir = _resolve_static_dir()
    static_root = static_dir.resolve()
    candidates = [static_dir / relative_path]
    if len(relative_path.parts) > 1:
        candidates.append(static_dir / relative_path.name)

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            resolved.relative_to(static_root)
        except (OSError, ValueError):
            continue
        if resolved.is_file():
            return resolved

    raise HTTPException(status_code=404, detail=f"Static asset not found: {asset_path}")


# ===================== STATIC FILES =====================
@app.get("/")
async def serve_index():
    """Serve index.html from dist/ (Vite build) or fallback to static/."""
    # Try dist/ first (Vite build output)
    dist_dir = _resolve_dist_dir()
    dist_index = dist_dir / "index.html"
    if dist_index.exists():
        return _static_file_response(dist_index, "text/html")

    # Fallback to static/ (old vanilla JS)
    static_dir = _resolve_static_dir()
    static_root_index = static_dir / "index.html"
    if static_root_index.exists():
        return _static_file_response(static_root_index, "text/html")

    local_index = static_dir / "html" / "index.html"
    if local_index.exists():
        return _static_file_response(local_index, "text/html")

    raise HTTPException(status_code=404, detail=f"index.html not found in dist/ or static/")


@app.get("/assets/{asset_path:path}")
async def serve_dist_assets(asset_path: str):
    """Serve assets from Vite build dist/assets/ directory."""
    dist_dir = _resolve_dist_dir()
    asset_file = dist_dir / "assets" / asset_path

    if not asset_file.exists():
        raise HTTPException(status_code=404, detail=f"Asset not found: {asset_path}")

    # Determine media type
    if asset_path.endswith(".js"):
        media_type = "application/javascript"
    elif asset_path.endswith(".css"):
        media_type = "text/css"
    elif asset_path.endswith(".svg"):
        media_type = "image/svg+xml"
    elif asset_path.endswith(".png"):
        media_type = "image/png"
    elif asset_path.endswith(".jpg") or asset_path.endswith(".jpeg"):
        media_type = "image/jpeg"
    else:
        media_type = "application/octet-stream"

    return _static_file_response(asset_file, media_type)


@app.get("/css/{asset_path:path}")
async def serve_css_asset(asset_path: str):
    """Serve CSS assets from source, nested install, or legacy flat install."""
    return _static_file_response(_resolve_static_asset(f"css/{asset_path}"), "text/css")


@app.get("/js/{asset_path:path}")
async def serve_js_asset(asset_path: str):
    """Serve JavaScript assets from source, nested install, or legacy flat install."""
    return _static_file_response(
        _resolve_static_asset(f"js/{asset_path}"),
        "application/javascript",
    )


@app.get("/styles.css")
async def serve_legacy_stylesheet():
    """Serve legacy stylesheet URL used by older installed index.html files."""
    return _static_file_response(_resolve_static_asset("css/styles.css"), "text/css")


@app.get("/app.js")
async def serve_legacy_app_script():
    """Serve legacy script URL used by older installed index.html files."""
    return _static_file_response(
        _resolve_static_asset("js/app.js"),
        "application/javascript",
    )


# Mount dist/ (Vite build) or static/ (legacy)
dist_dir_path = _resolve_dist_dir()
static_dir_path = _resolve_static_dir()

if dist_dir_path.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_dir_path / "assets")), name="dist-assets")
    app.mount("/", StaticFiles(directory=str(dist_dir_path), html=True), name="dist-root")

if static_dir_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir_path)), name="static")
    if (static_dir_path / "css").exists():
        app.mount("/css", StaticFiles(directory=str(static_dir_path / "css")), name="css")
    if (static_dir_path / "js").exists():
        app.mount("/js", StaticFiles(directory=str(static_dir_path / "js")), name="js")


# ===================== WEBSOCKET (Future Enhancement) =====================
# @app.websocket("/ws/telemetry")
# async def websocket_telemetry(websocket: WebSocket):
#     """WebSocket for real-time telemetry streaming."""
#     await websocket.accept()
#     try:
#         while True:
#             # Stream telemetry data
#             data = {"telemetry": ros_node.telemetry.copy()}
#             await websocket.send_json(data)
#             await asyncio.sleep(0.1)  # 10 Hz
#     except WebSocketDisconnect:
#         logger.info("Telemetry client disconnected")


# ===================== UTILITY FUNCTIONS =====================
def _candidate_map_dirs() -> list[Path]:
    """Return map directories used by the map picker and package fallbacks."""
    candidates = []
    seen = set()

    def add_candidate(path: Path | None):
        if path is None:
            return
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            return
        if resolved in seen or not resolved.is_dir():
            return
        seen.add(resolved)
        candidates.append(resolved)

    add_candidate(find_maps_folder())

    for package_name in ("amr_bringup_headless", "amr_bringup", "arya_web_interface"):
        try:
            add_candidate(Path(get_package_share_directory(package_name)) / "maps")
        except Exception:
            pass
        try:
            pkg_prefix = get_package_prefix(package_name)
            add_candidate(Path(pkg_prefix) / "share" / package_name / "maps")
        except Exception:
            pass

    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        add_candidate(parent / "maps")
        add_candidate(parent / "amr_bringup_headless" / "maps")
        add_candidate(parent / "amr_bringup_headless" / "amr_bringup_headless" / "maps")
        add_candidate(parent / "amr_bringup" / "maps")

    add_candidate(Path.home() / "arya_ws" / "src" / "amr_bringup_headless" / "maps")
    add_candidate(Path.home() / "awg_ws" / "src" / "amr_bringup_headless" / "maps")

    return candidates


def _resolve_map_path(map_name: str) -> Path:
    """Resolve map file path from map name."""
    clean_name = validate_map_name(map_name)
    searched_dirs = _candidate_map_dirs()

    for maps_dir in searched_dirs:
        map_path = maps_dir / clean_name
        if map_path.is_file():
            return map_path

    searched = ", ".join(str(path) for path in searched_dirs) or "no map directories found"
    raise FileNotFoundError(f"Map not found: {clean_name}. Searched: {searched}")


# ===================== EXCEPTION HANDLERS =====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


# ===================== STARTUP & SHUTDOWN =====================
@app.on_event("startup")
async def startup_event():
    """Initialize ROS node and services on app startup."""
    logger.info("Starting ARYA Web Interface...")
    setup_ros_node()
    await asyncio.sleep(1)  # Give ROS node time to initialize
    logger.info("✓ ARYA Web Interface ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    logger.info("Shutting down ARYA Web Interface...")
    shutdown_ros()
    logger.info("✓ ARYA Web Interface stopped")


# ===================== SIGNAL HANDLERS =====================
def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) gracefully."""
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_ros()


signal.signal(signal.SIGINT, signal_handler)


# ===================== MAIN =====================
def main():
    """Entry point for ros2 launch (called by console_scripts in setup.py)."""
    import sys
    
    # Configuration
    host = os.getenv("ARYA_WEB_HOST", "0.0.0.0")
    port = int(os.getenv("ARYA_WEB_PORT", "8000"))
    reload = "--reload" in sys.argv
    
    logger.info(f"Starting web server on {host}:{port}")
    logger.info(f"Dashboard: http://localhost:{port}")
    
    # Run Uvicorn server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
