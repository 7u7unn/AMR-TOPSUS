# MIGRATE.md

# AMR/AGV Web HMI Modernization Plan

## Objective

Migrate existing ROS2 web interface from current JavaScript architecture to a scalable, maintainable, production-grade HMI platform.

The new platform should gradually replace daily operator usage of:

* RViz (monitoring tasks)
* rqt
* Terminal-based operations
* Manual ROS topic commands
* Ad-hoc debugging dashboards

while keeping ROS2 as the robot middleware and navigation backbone.

---

# Target Architecture

```text
ROS2
│
├── Nav2
├── SLAM
├── Localization
├── Drivers
├── Diagnostics
├── Mission Manager
│
└── Web HMI (FastAPI Backend)
     │
     ├── WebSocket API
     └── REST API
          │
          └── Web HMI (React Frontend)
               ├── Dashboard
               ├── Fleet
               ├── Map
               ├── Mission
               ├── Teleop
               ├── Cameras
               ├── Diagnostics
               ├── Logs
               └── Settings
```

**Note:** The existing FastAPI backend (`web_node.py`) with rclpy integration is production-ready and will be kept unchanged. Only the frontend is modernized.

---

# Technology Stack

## Frontend

* React
* TypeScript
* Vite

## UI

* TailwindCSS
* shadcn/ui

## State Management

* Zustand

## Data Fetching

* TanStack Query

## ROS Communication

* Custom WebSocket service layer (wraps existing FastAPI WebSocket protocol)
* rclpy (Python ROS2 client library) - already in use via FastAPI backend

## Visualization

* React Three Fiber
* Three.js

## Terminal

* xterm.js

## Desktop Packaging

* Tauri (optional)

---

# Project Structure

```text
src/

app/
pages/
components/

features/
  dashboard/
  map/
  mission/
  teleop/
  fleet/
  diagnostics/
  logs/
  settings/

services/
  ros/
  api/

stores/

hooks/

types/

utils/

assets/
```

---

# Migration Strategy

## Phase 1

### Build System Modernization

Goal:

Replace ad-hoc frontend structure with a modern React build system.

Tasks:

* Install Vite
* Enable TypeScript
* Configure ESLint
* Configure Prettier
* Configure Path Alias
* Configure React Router

Example:

```text
@/components
@/features
@/services
```

Success Criteria:

* New React application runs under Vite
* All existing functionality accessible from new frontend

---

## Phase 2

### ROS Communication Layer

Goal:

Centralize all frontend communication with the FastAPI backend.

Architecture:

```text
Browser (React)
    ↓ WebSocket / fetch
FastAPI (web_node.py) ← NO CHANGE
    ↓ rclpy
ROS2 Topics/Services
```

Create:

```text
services/ros/
├── connection.ts       ← WebSocket connect/disconnect/reconnect with auto-retry
├── protocol.ts         ← Message type definitions
├── publisher.ts        ← Send commands (cmd_vel, goal_pose, etc.)
├── subscriber.ts       ← Subscribe to topics via WebSocket
└── services.ts         ← Call REST endpoints
```

Message Types to Support (from existing web_node.py):

```typescript
// Publishers (send from browser)
interface CmdVelCommand { type: 'cmd_vel'; linear: number; angular: number }
interface GoalPoseCommand { type: 'goal_pose'; x: number; y: number; theta: number }
interface InitialPoseCommand { type: 'initial_pose'; x: number; y: number; theta: number }
interface LaunchCommand { type: 'launch_start' | 'launch_stop'; name: string }
interface IOCommand { type: 'io_set_single' | 'io_mask'; pin: number; value: boolean }
interface ModeCommand { type: 'mode'; mode: 'auto' | 'manual' | 'emergency' }
interface ResetOdomCommand { type: 'reset_odom' }

// Subscribers (receive from robot)
interface RobotPoseData { type: 'robot_pose'; x: number; y: number; theta: number }
interface BatteryData { type: 'battery'; percentage: number; charging: boolean }
interface AmclData { type: 'amcl_pose'; x: number; y: number; theta: number; available: boolean }
interface LaunchStateData { type: 'launch_state'; name: string; running: boolean }
interface I/OData { type: 'io_state'; di: boolean[]; do: boolean[] }
```

Rules:

* Components never directly call WebSocket
* Components consume service APIs only
* Services are the only entry point to ROS communication

Success Criteria:

* Single ROS entry point in frontend
* Easier testing
* Easier maintenance
* Protocol documentation

---

## Phase 3

### State Management

Install:

```text
zustand
```

Stores:

```text
robotStore      ← pose, velocity, mode, connection status
batteryStore    ← percentage, charging state
missionStore    ← current mission, queue, stations, waypoints
mapStore        ← available maps, selected map, keepout zones
alarmStore      ← warnings, errors, critical alerts
fleetStore      ← all robots (future), fleet health
teleopStore     ← velocity commands, safety states
ioStore         ← digital inputs/outputs
```

Responsibilities:

robotStore

* pose (x, y, theta)
* velocity (linear, angular)
* mode (auto, manual, emergency)
* connection status

batteryStore

* percentage (0-100)
* charging state

alarmStore

* warning list
* error list
* critical list

Success Criteria:

* No global variables
* No duplicated subscriptions
* All state in typed stores

---

## Phase 4

### Reusable UI Components

Create common components.

Examples:

```text
BatteryCard
StatusCard
AlarmCard
CameraPanel
RobotCard
MissionTable
DiagnosticTable
Joystick
DPad
MapViewer
TopicEcho
Toast
Modal
```

Rules:

* Reusable across features
* Typed with TypeScript
* Independent (no direct ROS calls)
* Accessible (WCAG compliance)

Success Criteria:

* No duplicated UI code
* Consistent design language

---

## Phase 5

### Dashboard

Create operator dashboard.

Widgets:

* Battery
* Current Mission
* Robot State
* Velocity
* Connectivity
* Localization Status
* Charging Status
* Emergency Status

Success Criteria:

* Operator overview in one screen

---

## Phase 6

### Map Module

Goal:

Reduce dependency on RViz.

Features:

* Occupancy Grid
* Robot Pose
* Goal Position
* Planned Path
* Costmap Overlay
* Obstacle Overlay
* Localization Confidence

Technology:

```text
React Three Fiber
Three.js
```

Success Criteria:

* Daily monitoring performed from browser

---

## Phase 7

### Teleoperation

Features:

* Keyboard Control
* Joystick Control
* Mobile Control

Safety Features:

* Deadman Switch
* Velocity Limit
* Command Timeout
* Emergency Stop

Success Criteria:

* Teleoperation from browser

---

## Phase 8

### Mission Management

Features:

* Waypoint Creation
* Route Assignment
* Task Queue
* Docking Command
* Charging Command
* Pause Mission
* Resume Mission
* Cancel Mission

Success Criteria:

* No terminal-based mission commands

---

## Phase 9

### Diagnostics

Features:

* Hardware Status
* Sensor Status
* CPU Usage
* Memory Usage
* Network Status
* ROS Diagnostics

Severity Levels:

```text
INFO
WARNING
ERROR
CRITICAL
```

Success Criteria:

* Fast fault identification

---

## Phase 10

### Log Center

Features:

* ROS Logs
* Navigation Logs
* Mission Logs
* System Logs

Technology:

```text
xterm.js
```

Capabilities:

* Search
* Filter
* Export

Success Criteria:

* Reduced SSH access

---

## Phase 11

### Camera Module

Features:

* Front Camera
* Rear Camera
* Fork Camera
* Inspection Camera

Support:

* WebRTC
* MJPEG
* RTSP Gateway

Success Criteria:

* Camera access from browser

---

## Phase 12

### Fleet Management

Goal:

Support multiple robots.

Features:

```text
Fleet Overview
Fleet Health
Robot Assignment
Mission Distribution
Traffic Monitoring
Charging Queue
```

Future Robot Types:

* AMR
* AGV
* Forklift AGV
* Tugger AGV

Success Criteria:

* Architecture supports growth

---

## Phase 13

### Authentication

Roles:

```text
Operator
Supervisor
Engineer
Administrator
```

Permissions:

Operator

* Monitor
* Teleop

Supervisor

* Mission Management

Engineer

* Diagnostics
* Maintenance

Administrator

* System Configuration

Success Criteria:

* Production-ready access control

---

## Phase 14

### Production Hardening

Features:

* Auto Reconnect
* Offline Detection
* Error Boundary
* Logging
* Performance Monitoring
* Health Checks

Success Criteria:

* Stable industrial deployment

---

# Development Rules

## Do

* Use TypeScript everywhere
* Keep ROS access centralized in services/
* Create reusable components
* Use feature-based folders
* Write typed interfaces
* Wrap WebSocket communication in service layer

## Don't

* Direct DOM manipulation
* Global mutable variables (window.*)
* Direct WebSocket access in components
* Massive utility files
* Business logic inside UI components
* Skip TypeScript types

---

# Backend Notes

The existing FastAPI backend (`arya_web_interface/web_node.py`) is production-ready and will **not** be modified during this migration. It provides:

* WebSocket endpoint (`/ws`) for real-time bidirectional communication
* REST API endpoints (`/api/*`) for queries and non-realtime operations
* Direct rclpy integration with ROS2

The frontend migration is independent of backend changes.

---

# Long-Term Vision

Operator Workstation

```text
Browser
│
├── Dashboard
├── Map
├── Teleop
├── Cameras
├── Missions
├── Fleet
├── Diagnostics
└── Logs
```

ROS2 remains the robot middleware.

The web application becomes the primary Human Machine Interface for operators, supervisors, and maintenance engineers.