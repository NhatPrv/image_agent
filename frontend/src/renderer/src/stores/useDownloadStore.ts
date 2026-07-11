import { create } from 'zustand'

export interface DownloadTask {
  task_id: string
  url: string
  filename: string
  component_type: string
  bytes_downloaded: number
  bytes_total: number
  speed_mb: number
  eta_seconds: number
  status: 'pending' | 'downloading' | 'completed' | 'failed' | 'cancelled'
  error_message?: string | null
  file_path: string
}

interface DownloadState {
  tasks: DownloadTask[]
  setTasks: (tasks: DownloadTask[]) => void
  addOrUpdateTask: (task: DownloadTask) => void
  updateTaskProgress: (
    task_id: string,
    bytes_downloaded: number,
    bytes_total: number,
    speed_mb: number,
    eta_seconds: number
  ) => void
  updateTaskStatus: (
    task_id: string,
    status: DownloadTask['status'],
    errorMessage?: string | null
  ) => void
}

export const useDownloadStore = create<DownloadState>((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addOrUpdateTask: (task) =>
    set((state) => {
      const exists = state.tasks.some((t) => t.task_id === task.task_id)
      if (exists) {
        return {
          tasks: state.tasks.map((t) => (t.task_id === task.task_id ? { ...t, ...task } : t))
        }
      }
      return { tasks: [task, ...state.tasks] }
    }),
  updateTaskProgress: (task_id, bytes_downloaded, bytes_total, speed_mb, eta_seconds) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.task_id === task_id
          ? {
              ...t,
              bytes_downloaded,
              bytes_total,
              speed_mb,
              eta_seconds,
              status: 'downloading'
            }
          : t
      )
    })),
  updateTaskStatus: (task_id, status, errorMessage = null) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.task_id === task_id
          ? {
              ...t,
              status,
              error_message: errorMessage
            }
          : t
      )
    }))
}))
