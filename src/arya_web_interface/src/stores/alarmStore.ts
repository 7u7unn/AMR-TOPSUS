import { create } from 'zustand'

export type AlarmSeverity = 'info' | 'warning' | 'error' | 'critical'

export interface Alarm {
  id: string
  message: string
  severity: AlarmSeverity
  timestamp: number
  acknowledged: boolean
}

interface AlarmStore {
  alarms: Alarm[]
  addAlarm: (message: string, severity: AlarmSeverity) => void
  acknowledgeAlarm: (id: string) => void
  removeAlarm: (id: string) => void
  clearAll: () => void
}

export const useAlarmStore = create<AlarmStore>((set) => ({
  alarms: [],

  addAlarm: (message, severity) => set((state) => ({
    alarms: [
      {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        message,
        severity,
        timestamp: Date.now(),
        acknowledged: false,
      },
      ...state.alarms,
    ].slice(0, 100), // Keep max 100 alarms
  })),

  acknowledgeAlarm: (id) => set((state) => ({
    alarms: state.alarms.map((a) =>
      a.id === id ? { ...a, acknowledged: true } : a
    ),
  })),

  removeAlarm: (id) => set((state) => ({
    alarms: state.alarms.filter((a) => a.id !== id),
  })),

  clearAll: () => set({ alarms: [] }),
}))