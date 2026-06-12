import { create } from 'zustand'

export interface KeepoutZone {
  id: string
  name: string
  points: { x: number; y: number }[]
}

export interface MapInfo {
  name: string
  timestamp: string
  loaded: boolean
}

interface MapStore {
  availableMaps: MapInfo[]
  selectedMapName: string
  loadedMapData: string | null
  mapResolution: number
  mapWidth: number
  mapHeight: number
  mapOrigin: { x: number; y: number; theta: number }
  keepoutZones: KeepoutZone[]
  setAvailableMaps: (maps: MapInfo[]) => void
  setSelectedMapName: (name: string) => void
  setLoadedMapData: (data: string, resolution: number, width: number, height: number, origin: { x: number; y: number; theta: number }) => void
  addKeepoutZone: (zone: KeepoutZone) => void
  removeKeepoutZone: (id: string) => void
  reset: () => void
}

export const useMapStore = create<MapStore>((set) => ({
  availableMaps: [],
  selectedMapName: '',
  loadedMapData: null,
  mapResolution: 0,
  mapWidth: 0,
  mapHeight: 0,
  mapOrigin: { x: 0, y: 0, theta: 0 },
  keepoutZones: [],

  setAvailableMaps: (availableMaps) => set({ availableMaps }),
  setSelectedMapName: (selectedMapName) => set({ selectedMapName }),
  setLoadedMapData: (loadedMapData, mapResolution, mapWidth, mapHeight, mapOrigin) =>
    set({ loadedMapData, mapResolution, mapWidth, mapHeight, mapOrigin }),
  addKeepoutZone: (zone) => set((state) => ({ keepoutZones: [...state.keepoutZones, zone] })),
  removeKeepoutZone: (id) => set((state) => ({
    keepoutZones: state.keepoutZones.filter((z) => z.id !== id)
  })),
  reset: () => set({
    availableMaps: [],
    selectedMapName: '',
    loadedMapData: null,
    mapResolution: 0,
    mapWidth: 0,
    mapHeight: 0,
    mapOrigin: { x: 0, y: 0, theta: 0 },
    keepoutZones: [],
  }),
}))