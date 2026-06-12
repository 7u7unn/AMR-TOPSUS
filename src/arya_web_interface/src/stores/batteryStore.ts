import { create } from 'zustand'

interface BatteryStore {
  percentage: number
  charging: boolean
  setBattery: (percentage: number, charging: boolean) => void
  reset: () => void
}

export const useBatteryStore = create<BatteryStore>((set) => ({
  percentage: 0,
  charging: false,

  setBattery: (percentage, charging) => set({ percentage, charging }),
  reset: () => set({ percentage: 0, charging: false }),
}))