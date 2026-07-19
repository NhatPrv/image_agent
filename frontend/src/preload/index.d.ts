import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      selectDirectory: () => Promise<string | null>
      getBackendStatus: () => Promise<{ running: boolean; pid?: number; error?: string }>
      selectImage: () => Promise<string | null>
      readImageBase64: (filePath: string) => Promise<string | null>
      saveTempImage: (base64Data: string, filename: string) => Promise<string>
      saveImageAs: (sourcePath: string) => Promise<string | null>
      onBackendLog: (
        callback: (data: { type: 'stdout' | 'stderr'; text: string }) => void
      ) => () => void
    }
  }
}
