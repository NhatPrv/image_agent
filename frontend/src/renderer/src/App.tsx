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

  // Render view conditionally based on sidebar selector
  function renderView(): React.JSX.Element {
    switch (currentView) {
      case 'generate':
        return <GenerateView />
      case 'history':
        return <HistoryView />
      case 'downloads':
        return <DownloadManagerView />
      case 'settings':
        return <SettingsView />
      default:
        return <GenerateView />
    }
  }

  return (
    <MainLayout currentView={currentView} setCurrentView={setCurrentView}>
      {renderView()}
    </MainLayout>
  )
}

export default App
