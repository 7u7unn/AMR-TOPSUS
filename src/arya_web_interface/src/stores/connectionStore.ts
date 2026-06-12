import { create } from 'zustand'
import type { ConnectionState, ConnectionStatus } from '@/types/ros'

interface ConnectionStore extends ConnectionState {
  setStatus: (status: ConnectionStatus) => void
  setError: (error: string | null) => void
  incrementReconnectAttempts: () => void
  reset: () => void
}

export const useConnectionStore = create<ConnectionStore>((set) => ({
  status: 'disconnected',
  lastError: null,
  reconnectAttempts: 0,

  setStatus: (status) => set({ status }),
  setError: (lastError) => set({ lastError }),
  incrementReconnectAttempts: () => set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),
  reset: () => set({ status: 'disconnected', lastError: null, reconnectAttempts: 0 }),
}))