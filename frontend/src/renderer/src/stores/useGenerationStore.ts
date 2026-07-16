import { create } from 'zustand'

export interface GenerationParams {
  prompt: string
  negative_prompt: string
  width: number
  height: number
  steps: number
  cfg_scale: number
  seed: number
  sampler: string
  model_id: string
  type: 'txt2img' | 'img2img' | 'inpaint'
  input_image_path?: string
  mask_image_path?: string
  denoise_strength?: number
}

export interface ImageRecord {
  id: string
  generation_id: string
  path: string
  thumbnail_path: string
  width: number
  height: number
  format: string
  size_bytes: number
  created_at: string
}

export interface GenerationRecord {
  id: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  completed_at: string | null
  duration_ms: number | null
  error_message: string | null
  params: GenerationParams
  images: ImageRecord[]
}

interface GenerationState {
  prompt: string
  negativePrompt: string
  width: number
  height: number
  steps: number
  cfgScale: number
  seed: number
  sampler: string
  modelId: string
  type: 'txt2img' | 'img2img' | 'inpaint'
  inputImagePath: string | null
  maskImagePath: string | null
  denoiseStrength: number

  // Active status
  generating: boolean
  currentGenerationId: string | null
  progress: number
  currentStep: number
  totalSteps: number
  previewImage: string | null // Base64 encoded or absolute file URL

  // Loop generation states
  loopEnabled: boolean
  loopCount: number

  // History list
  history: GenerationRecord[]

  setPrompt: (prompt: string) => void
  setNegativePrompt: (negativePrompt: string) => void
  setParams: (
    params: Partial<
      Omit<
        GenerationState,
        'history' | 'generating' | 'progress' | 'currentStep' | 'totalSteps' | 'previewImage'
      >
    >
  ) => void
  setGenerating: (generating: boolean, currentGenerationId?: string | null) => void
  setProgress: (
    progress: number,
    currentStep: number,
    totalSteps: number,
    previewImage?: string | null
  ) => void
  setHistory: (history: GenerationRecord[]) => void
  addHistoryItem: (item: GenerationRecord) => void
  updateHistoryItem: (id: string, updates: Partial<GenerationRecord>) => void
  removeHistoryItem: (id: string) => void
  resetProgress: () => void
  setLoopEnabled: (enabled: boolean) => void
  setLoopCount: (count: number) => void
}

export const useGenerationStore = create<GenerationState>((set) => ({
  prompt:
    'A beautiful masterpiece oil painting of a futuristic city with neon lights, highly detailed, 8k resolution',
  negativePrompt: 'blurry, low quality, bad anatomy, deformed, worst quality, monochrome, ugly',
  width: 512,
  height: 512,
  steps: 25,
  cfgScale: 7.0,
  seed: -1,
  sampler: 'Euler A',
  modelId: '',
  type: 'txt2img',
  inputImagePath: null,
  maskImagePath: null,
  denoiseStrength: 0.75,

  loopEnabled: false,
  loopCount: 5,

  generating: false,
  currentGenerationId: null,
  progress: 0,
  currentStep: 0,
  totalSteps: 25,
  previewImage: null,

  history: [],

  setPrompt: (prompt) => set({ prompt }),
  setNegativePrompt: (negativePrompt) => set({ negativePrompt }),
  setParams: (params) => set(params),
  setGenerating: (generating, currentGenerationId = null) =>
    set({ generating, currentGenerationId }),
  setProgress: (progress, currentStep, totalSteps, previewImage = null) =>
    set({ progress, currentStep, totalSteps, previewImage }),
  setHistory: (history) => set({ history }),
  addHistoryItem: (item) => set((state) => ({ history: [item, ...state.history] })),
  updateHistoryItem: (id, updates) =>
    set((state) => ({
      history: state.history.map((item) => (item.id === id ? { ...item, ...updates } : item))
    })),
  removeHistoryItem: (id) =>
    set((state) => ({
      history: state.history.filter((item) => item.id !== id)
    })),
  resetProgress: () =>
    set({
      progress: 0,
      currentStep: 0,
      previewImage: null,
      currentGenerationId: null,
      generating: false
    }),
  setLoopEnabled: (loopEnabled) => set({ loopEnabled }),
  setLoopCount: (loopCount) => set({ loopCount })
}))
