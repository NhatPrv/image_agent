import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      selectDirectory: () => Promise<string | null>
      getBackendStatus: () => Promise<{ running: boolean; pid?: number; error?: string }>
    }
  }
}
