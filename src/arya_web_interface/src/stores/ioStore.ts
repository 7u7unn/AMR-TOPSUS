import { create } from 'zustand'

interface IOStore {
  digitalInputs: boolean[]
  digitalOutputs: boolean[]
  setDigitalInputs: (inputs: boolean[]) => void
  setDigitalOutputs: (outputs: boolean[]) => void
  setOutput: (index: number, value: boolean) => void
  reset: () => void
}

const initialInputs = Array(8).fill(false)
const initialOutputs = Array(8).fill(false)

export const useIOStore = create<IOStore>((set) => ({
  digitalInputs: [...initialInputs],
  digitalOutputs: [...initialOutputs],

  setDigitalInputs: (digitalInputs) => set({ digitalInputs }),
  setDigitalOutputs: (digitalOutputs) => set({ digitalOutputs }),
  setOutput: (index, value) => set((state) => {
    const newOutputs = [...state.digitalOutputs]
    newOutputs[index] = value
    return { digitalOutputs: newOutputs }
  }),
  reset: () => set({ digitalInputs: [...initialInputs], digitalOutputs: [...initialOutputs] }),
}))