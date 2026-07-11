import { create } from 'zustand'

export interface ModelInfo {
  id: string
  name: string
  filename: string
  path: string
  component_type: 'checkpoint' | 'lora' | 'vae' | 'controlnet'
  architecture: 'sd_1_5' | 'sdxl' | 'flux' | 'sd3'
  file_format: 'safetensors' | 'ckpt' | 'diffusers'
  size_bytes: number
  hash_sha256: string
  metadata: Record<string, unknown>
}

interface ModelState {
  models: ModelInfo[]
  activeModel: ModelInfo | null
  loadingModelId: string | null
  loadingProgress: number
  loadingError: string | null
  setModels: (models: ModelInfo[]) => void
  setActiveModel: (model: ModelInfo | null) => void
  setLoadingModelId: (id: string | null) => void
  setLoadingProgress: (progress: number) => void
  setLoadingError: (error: string | null) => void
}

export const useModelStore = create<ModelState>((set) => ({
  models: [],
  activeModel: null,
  loadingModelId: null,
  loadingProgress: 0,
  loadingError: null,
  setModels: (models) => set({ models }),
  setActiveModel: (activeModel) => set({ activeModel, loadingModelId: null, loadingProgress: 100 }),
  setLoadingModelId: (loadingModelId) =>
    set({ loadingModelId, loadingError: null, loadingProgress: 0 }),
  setLoadingProgress: (loadingProgress) => set({ loadingProgress }),
  setLoadingError: (loadingError) => set({ loadingError, loadingModelId: null, loadingProgress: 0 })
}))
