import { useEffect } from 'react'
import { rosConnection } from '@/services/ros'
import { useConnectionStore, useRobotStore, useBatteryStore, useLaunchStore, useIOStore } from '@/stores'
import type { SubscriberData } from '@/types/ros'

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export function useROSConnection() {
  const { setStatus, setError } = useConnectionStore()

  useEffect(() => {
    // Subscribe to connection status changes
    const unsubscribe = rosConnection.onStatusChange((state) => {
      setStatus(state.status)
      if (state.lastError) {
        setError(state.lastError)
      }
    })

    // Connect to WebSocket
    rosConnection.connect(WS_URL)

    return () => {
      unsubscribe()
      rosConnection.disconnect()
    }
  }, [setStatus, setError])

  return {
    connect: () => rosConnection.connect(WS_URL),
    disconnect: () => rosConnection.disconnect(),
    isConnected: rosConnection.isConnected(),
  }
}

export function useROSSubscriptions() {
  const { setPose, setVelocity, setMode, setAmclPose } = useRobotStore()
  const { setBattery } = useBatteryStore()
  const { setLaunchState } = useLaunchStore()
  const { setDigitalInputs, setDigitalOutputs } = useIOStore()

  useEffect(() => {
    const handleMessage = (data: SubscriberData) => {
      switch (data.type) {
        case 'robot_pose':
          setPose(data.x, data.y, data.theta)
          break
        case 'velocity':
          setVelocity(data.linear, data.angular)
          break
        case 'mode_state':
          setMode(data.mode)
          break
        case 'amcl_pose':
          setAmclPose(data.x, data.y, data.theta, data.available)
          break
        case 'battery':
          setBattery(data.percentage, data.charging)
          break
        case 'launch_state':
          setLaunchState(data.name, data.running)
          break
        case 'io_state':
          setDigitalInputs(data.di)
          setDigitalOutputs(data.do)
          break
      }
    }

    const unsubscribe = rosConnection.onMessage(handleMessage)
    return () => unsubscribe()
  }, [setPose, setVelocity, setMode, setAmclPose, setBattery, setLaunchState, setDigitalInputs, setDigitalOutputs])
}

export function useROS() {
  useROSConnection()
  useROSSubscriptions()
}