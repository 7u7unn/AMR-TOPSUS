// ROS Message Types - Protocol definitions matching web_node.py

// ============ Publisher Commands (Browser -> Robot) ============

export interface CmdVelCommand {
  type: 'cmd_vel'
  linear: number
  angular: number
}

export interface GoalPoseCommand {
  type: 'goal_pose'
  x: number
  y: number
  theta: number
}

export interface InitialPoseCommand {
  type: 'initial_pose'
  x: number
  y: number
  theta: number
}

export interface LaunchStartCommand {
  type: 'launch_start'
  name: string
}

export interface LaunchStopCommand {
  type: 'launch_stop'
  name: string
}

export interface IOSetSingleCommand {
  type: 'io_set_single'
  pin: number
  value: boolean
}

export interface IOMaskCommand {
  type: 'io_mask'
  mask: number
  value: number
}

export interface ModeCommand {
  type: 'mode'
  mode: 'auto' | 'manual' | 'emergency'
}

export interface ResetOdomCommand {
  type: 'reset_odom'
}

export interface SaveMapCommand {
  type: 'save_map'
  name: string
}

export interface LoadMapCommand {
  type: 'load_map'
  name: string
}

// Union type for all publisher commands
export type PublisherCommand =
  | CmdVelCommand
  | GoalPoseCommand
  | InitialPoseCommand
  | LaunchStartCommand
  | LaunchStopCommand
  | IOSetSingleCommand
  | IOMaskCommand
  | ModeCommand
  | ResetOdomCommand
  | SaveMapCommand
  | LoadMapCommand

// ============ Subscriber Data (Robot -> Browser) ============

export interface RobotPoseData {
  type: 'robot_pose'
  x: number
  y: number
  theta: number
}

export interface BatteryData {
  type: 'battery'
  percentage: number
  charging: boolean
}

export interface AmclPoseData {
  type: 'amcl_pose'
  x: number
  y: number
  theta: number
  available: boolean
}

export interface LaunchStateData {
  type: 'launch_state'
  name: string
  running: boolean
}

export interface IOStateData {
  type: 'io_state'
  di: boolean[]
  do: boolean[]
}

export interface LaserData {
  type: 'laser'
  distances: number[]
}

export interface VelocityData {
  type: 'velocity'
  linear: number
  angular: number
}

export interface ModeStateData {
  type: 'mode_state'
  mode: 'auto' | 'manual' | 'emergency'
}

export interface MapData {
  type: 'map'
  data: string // base64 encoded
  resolution: number
  width: number
  height: number
  origin: { x: number; y: number; theta: number }
}

export interface MissionStateData {
  type: 'mission_state'
  current: string | null
  queue: string[]
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed'
}

// Union type for all subscriber data
export type SubscriberData =
  | RobotPoseData
  | BatteryData
  | AmclPoseData
  | LaunchStateData
  | IOStateData
  | LaserData
  | VelocityData
  | ModeStateData
  | MapData
  | MissionStateData

// ============ REST API Types ============

export interface TopicInfo {
  name: string
  type: string
}

export interface ServiceInfo {
  name: string
  type: string
}

export interface MapListItem {
  name: string
  timestamp: string
  size: number
}

export interface LaunchConfig {
  name: string
  display_name: string
  description: string
}

export interface StationInfo {
  name: string
  x: number
  y: number
  theta: number
}

// ============ Connection State ============

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface ConnectionState {
  status: ConnectionStatus
  lastError: string | null
  reconnectAttempts: number
}