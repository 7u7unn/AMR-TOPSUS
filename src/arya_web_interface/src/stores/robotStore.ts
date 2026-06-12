import { create } from 'zustand'

interface RobotState {
  x: number
  y: number
  theta: number
  linearVelocity: number
  angularVelocity: number
  mode: 'auto' | 'manual' | 'emergency'
  amclX: number
  amclY: number
  amclTheta: number
  amclAvailable: boolean
}

interface RobotStore extends RobotState {
  setPose: (x: number, y: number, theta: number) => void
  setVelocity: (linear: number, angular: number) => void
  setMode: (mode: 'auto' | 'manual' | 'emergency') => void
  setAmclPose: (x: number, y: number, theta: number, available: boolean) => void
  reset: () => void
}

const initialState: RobotState = {
  x: 0,
  y: 0,
  theta: 0,
  linearVelocity: 0,
  angularVelocity: 0,
  mode: 'manual',
  amclX: 0,
  amclY: 0,
  amclTheta: 0,
  amclAvailable: false,
}

export const useRobotStore = create<RobotStore>((set) => ({
  ...initialState,

  setPose: (x, y, theta) => set({ x, y, theta }),
  setVelocity: (linearVelocity, angularVelocity) => set({ linearVelocity, angularVelocity }),
  setMode: (mode) => set({ mode }),
  setAmclPose: (amclX, amclY, amclTheta, amclAvailable) => set({ amclX, amclY, amclTheta, amclAvailable }),
  reset: () => set(initialState),
}))