import { create } from 'zustand'

export interface Station {
  id: string
  name: string
  x: number
  y: number
  theta: number
  wait: number
}

export interface Mission {
  id: string
  name: string
  waypoints: Station[]
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed'
}

interface MissionStore {
  currentMission: Mission | null
  missionQueue: Mission[]
  stations: Station[]
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'success' | 'error'
  addStation: (station: Station) => void
  removeStation: (id: string) => void
  setCurrentMission: (mission: Mission | null) => void
  setMissionQueue: (queue: Mission[]) => void
  addToQueue: (mission: Mission) => void
  removeFromQueue: (id: string) => void
  setStations: (stations: Station[]) => void
  setStatus: (status: 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'success' | 'error') => void
  reset: () => void
}

export const useMissionStore = create<MissionStore>((set) => ({
  currentMission: null,
  missionQueue: [],
  stations: [],
  status: 'idle',

  addStation: (station) => set((state) => ({ stations: [...state.stations, station] })),
  removeStation: (id) => set((state) => ({ stations: state.stations.filter((s) => s.id !== id) })),
  setCurrentMission: (currentMission) => set({ currentMission }),
  setMissionQueue: (missionQueue) => set({ missionQueue }),
  addToQueue: (mission) => set((state) => ({ missionQueue: [...state.missionQueue, mission] })),
  removeFromQueue: (id) => set((state) => ({
    missionQueue: state.missionQueue.filter((m) => m.id !== id)
  })),
  setStations: (stations) => set({ stations }),
  setStatus: (status) => set({ status }),
  reset: () => set({ currentMission: null, missionQueue: [], stations: [], status: 'idle' }),
}))