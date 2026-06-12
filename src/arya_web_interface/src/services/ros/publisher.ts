import { rosConnection } from './connection'
import type {
  CmdVelCommand,
  GoalPoseCommand,
  InitialPoseCommand,
  LaunchStartCommand,
  LaunchStopCommand,
  IOSetSingleCommand,
  IOMaskCommand,
  ModeCommand,
  ResetOdomCommand,
  SaveMapCommand,
  LoadMapCommand,
} from '@/types/ros'

// ============ Velocity Commands ============

export function publishCmdVel(linear: number, angular: number): boolean {
  return rosConnection.send({ type: 'cmd_vel', linear, angular } as CmdVelCommand)
}

// ============ Navigation Commands ============

export function publishGoalPose(x: number, y: number, theta: number): boolean {
  return rosConnection.send({ type: 'goal_pose', x, y, theta } as GoalPoseCommand)
}

export function publishInitialPose(x: number, y: number, theta: number): boolean {
  return rosConnection.send({ type: 'initial_pose', x, y, theta } as InitialPoseCommand)
}

export function publishResetOdom(): boolean {
  return rosConnection.send({ type: 'reset_odom' } as ResetOdomCommand)
}

// ============ Launch Management ============

export function publishLaunchStart(name: string): boolean {
  return rosConnection.send({ type: 'launch_start', name } as LaunchStartCommand)
}

export function publishLaunchStop(name: string): boolean {
  return rosConnection.send({ type: 'launch_stop', name } as LaunchStopCommand)
}

// ============ I/O Commands ============

export function publishIOSetSingle(pin: number, value: boolean): boolean {
  return rosConnection.send({ type: 'io_set_single', pin, value } as IOSetSingleCommand)
}

export function publishIOMask(mask: number, value: number): boolean {
  return rosConnection.send({ type: 'io_mask', mask, value } as IOMaskCommand)
}

// ============ Mode Commands ============

export function publishMode(mode: 'auto' | 'manual' | 'emergency'): boolean {
  return rosConnection.send({ type: 'mode', mode } as ModeCommand)
}

// ============ Map Commands ============

export function publishSaveMap(name: string): boolean {
  return rosConnection.send({ type: 'save_map', name } as SaveMapCommand)
}

export function publishLoadMap(name: string): boolean {
  return rosConnection.send({ type: 'load_map', name } as LoadMapCommand)
}