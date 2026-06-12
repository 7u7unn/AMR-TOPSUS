import { create } from 'zustand'

export interface LaunchState {
  name: string
  displayName: string
  running: boolean
}

interface LaunchStore {
  launchStates: LaunchState[]
  setLaunchState: (name: string, running: boolean) => void
  setAllLaunchStates: (states: LaunchState[]) => void
  reset: () => void
}

export const useLaunchStore = create<LaunchStore>((set) => ({
  launchStates: [],

  setLaunchState: (name, running) => set((state) => {
    const existing = state.launchStates.find((l) => l.name === name)
    if (existing) {
      return {
        launchStates: state.launchStates.map((l) =>
          l.name === name ? { ...l, running } : l
        ),
      }
    }
    return {
      launchStates: [...state.launchStates, { name, displayName: name, running }],
    }
  }),

  setAllLaunchStates: (launchStates) => set({ launchStates }),
  reset: () => set({ launchStates: [] }),
}))