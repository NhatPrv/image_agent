import { contextBridge } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

import { ipcRenderer } from 'electron'

// Custom APIs for renderer
const api = {
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  selectImage: () => ipcRenderer.invoke('select-image'),
  saveTempImage: (base64Data: string, filename: string) =>
    ipcRenderer.invoke('save-temp-image', base64Data, filename),
  saveImageAs: (sourcePath: string) => ipcRenderer.invoke('save-image-as', sourcePath),
  onBackendLog: (
    callback: (data: { type: 'stdout' | 'stderr'; text: string }) => void
  ): (() => void) => {
    const listener = (_event: unknown, data: { type: 'stdout' | 'stderr'; text: string }): void =>
      callback(data)
    ipcRenderer.on('backend-log', listener)
    return () => {
      ipcRenderer.removeListener('backend-log', listener)
    }
  }
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
