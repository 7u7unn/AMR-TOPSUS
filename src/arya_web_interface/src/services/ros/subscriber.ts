import { rosConnection } from './connection'
import type { SubscriberData } from '@/types/ros'

type Unsubscribe = () => void

export function subscribeToAll(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage(handler)
}

export function subscribeRobotPose(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'robot_pose') handler(data)
  })
}

export function subscribeBattery(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'battery') handler(data)
  })
}

export function subscribeAmclPose(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'amcl_pose') handler(data)
  })
}

export function subscribeLaunchState(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'launch_state') handler(data)
  })
}

export function subscribeIOState(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'io_state') handler(data)
  })
}

export function subscribeLaser(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'laser') handler(data)
  })
}

export function subscribeVelocity(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'velocity') handler(data)
  })
}

export function subscribeModeState(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'mode_state') handler(data)
  })
}

export function subscribeMap(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'map') handler(data)
  })
}

export function subscribeMissionState(handler: (data: SubscriberData) => void): Unsubscribe {
  return rosConnection.onMessage((data) => {
    if (data.type === 'mission_state') handler(data)
  })
}