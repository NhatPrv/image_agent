import { create } from 'zustand'

export interface QueueItem {
  id: string
  generation_id: string
  priority: 'low' | 'normal' | 'high'
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  position: number
  created_at: string
}

interface QueueState {
  queueItems: QueueItem[]
  setQueueItems: (items: QueueItem[]) => void
  addQueueItem: (item: QueueItem) => void
  removeQueueItem: (itemId: string) => void
}

export const useQueueStore = create<QueueState>((set) => ({
  queueItems: [],
  setQueueItems: (queueItems) => set({ queueItems }),
  addQueueItem: (item) => set((state) => ({ queueItems: [...state.queueItems, item] })),
  removeQueueItem: (itemId) =>
    set((state) => ({ queueItems: state.queueItems.filter((item) => item.id !== itemId) }))
}))
