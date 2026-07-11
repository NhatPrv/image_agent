import { create } from 'zustand'

export interface SystemStats {
  platform: string
  platform_version: string
  python_version: string
  cpu: {
    usage_percent: number
    cores: number
  }
  ram: {
    used_mb: number
    total_mb: number
    usage_percent: number
  }
  disk: {
    used_gb: number
    total_gb: number
    usage_percent: number
  }
  gpu: {
    cuda_available: boolean
    device_name: string
    vram_used_mb: number
    vram_total_mb: number
    vram_usage_percent: number
  }
}

interface SystemState {
  connected: boolean
  stats: SystemStats | null
  setConnected: (connected: boolean) => void
  setStats: (stats: SystemStats | null) => void
}

export const useSystemStore = create<SystemState>((set) => ({
  connected: false,
  stats: null,
  setConnected: (connected) => set({ connected }),
  setStats: (stats) => set({ stats })
}))
