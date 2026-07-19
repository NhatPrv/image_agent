import React, { useState } from 'react'
import { MainLayout } from './layouts/MainLayout'
import { GenerateView } from './views/GenerateView'
import { HistoryView } from './views/HistoryView'
import { SettingsView } from './views/SettingsView'
import { DownloadManagerView } from './views/DownloadManagerView'
import { useWebSocket } from './hooks/useWebSocket'

function App(): React.JSX.Element {
  // Start WebSocket client listener channel on mount
  useWebSocket()

  // Track active view state
  const [currentView, setCurrentView] = useState<string>('generate')

  return (
    <MainLayout currentView={currentView} setCurrentView={setCurrentView}>
      <div className={currentView === 'generate' ? 'h-full w-full' : 'hidden'}>
        <GenerateView />
      </div>
      <div className={currentView === 'history' ? 'h-full w-full' : 'hidden'}>
        <HistoryView />
      </div>
      <div className={currentView === 'downloads' ? 'h-full w-full' : 'hidden'}>
        <DownloadManagerView />
      </div>
      <div className={currentView === 'settings' ? 'h-full w-full' : 'hidden'}>
        <SettingsView />
      </div>
    </MainLayout>
  )
}

export default App
