import React from 'react'
import { useSystemStore } from '../stores/useSystemStore'
import { useModelStore } from '../stores/useModelStore'
import { useQueueStore } from '../stores/useQueueStore'
import { Cpu, HardDrive, Cpu as GpuIcon, Activity, Wifi, WifiOff } from 'lucide-react'

interface MainLayoutProps {
  children: React.ReactNode
  currentView: string
  setCurrentView: (view: string) => void
}

export function MainLayout({
  children,
  currentView,
  setCurrentView
}: MainLayoutProps): React.JSX.Element {
  const connected = useSystemStore((state) => state.connected)
  const stats = useSystemStore((state) => state.stats)
  const activeModel = useModelStore((state) => state.activeModel)
  const loadingModelId = useModelStore((state) => state.loadingModelId)
  const loadingProgress = useModelStore((state) => state.loadingProgress)
  const queueItems = useQueueStore((state) => state.queueItems)

  const cpuUsage = stats?.cpu.usage_percent ?? 0
  const ramUsage = stats?.ram.usage_percent ?? 0
  const ramUsedGb = stats ? (stats.ram.used_mb / 1024).toFixed(1) : '0'
  const ramTotalGb = stats ? (stats.ram.total_mb / 1024).toFixed(0) : '0'

  const vramUsage = stats?.gpu.vram_usage_percent ?? 0
  const vramUsedMb = stats?.gpu.vram_used_mb ?? 0
  const vramTotalMb = stats?.gpu.vram_total_mb ?? 0

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans select-none">
      {/* ─── Sidebar Navigation ─── */}
      <aside className="w-64 border-r border-slate-900 bg-slate-900/40 backdrop-blur-md flex flex-col justify-between">
        <div>
          {/* Logo Brand Header */}
          <div className="p-6 border-b border-slate-900 flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Activity className="h-5 w-5 text-white animate-pulse-glow" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Image Agent
              </h1>
              <p className="text-[10px] text-slate-500 font-medium">LOCAL AI PLATFORM</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5">
            {[
              { id: 'generate', label: 'Generate View', icon: GpuIcon },
              { id: 'history', label: 'Gallery & History', icon: HardDrive },
              { id: 'settings', label: 'Settings', icon: Activity }
            ].map((item) => {
              const Icon = item.icon
              const active = currentView === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 text-sm font-medium ${
                    active
                      ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-600/10'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                  }`}
                >
                  <Icon className="h-4.5 w-4.5" />
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* ─── Hardware Telemetry Dashboard ─── */}
        <div className="p-4 border-t border-slate-900 bg-slate-900/10 space-y-4">
          <h3 className="text-xs font-semibold text-slate-500 tracking-wider px-2">
            SYSTEM TELEMETRY
          </h3>

          <div className="space-y-3.5 px-2">
            {/* CPU Metric */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-[11px] font-medium text-slate-400">
                <span className="flex items-center">
                  <Cpu className="h-3 w-3 mr-1.5 text-slate-500" /> CPU Usage
                </span>
                <span>{cpuUsage.toFixed(1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-violet-600 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(cpuUsage, 100)}%` }}
                />
              </div>
            </div>

            {/* RAM Metric */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-[11px] font-medium text-slate-400">
                <span className="flex items-center">
                  <HardDrive className="h-3 w-3 mr-1.5 text-slate-500" /> Host RAM
                </span>
                <span>
                  {ramUsedGb}/{ramTotalGb} GB
                </span>
              </div>
              <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(ramUsage, 100)}%` }}
                />
              </div>
            </div>

            {/* VRAM Metric */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-[11px] font-medium text-slate-400">
                <span className="flex items-center">
                  <GpuIcon className="h-3 w-3 mr-1.5 text-indigo-400 animate-pulse" /> VRAM Memory
                </span>
                <span>
                  {(vramUsedMb / 1024).toFixed(1)}/{(vramTotalMb / 1024).toFixed(0)} GB
                </span>
              </div>
              <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-violet-500 to-pink-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(vramUsage, 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Connection Indicator */}
          <div className="flex items-center justify-between px-2 pt-2 border-t border-slate-900/50">
            <span className="text-[11px] font-medium text-slate-500">Service Status</span>
            <div className="flex items-center space-x-1.5">
              {connected ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-md shadow-emerald-500/50 animate-ping" />
                  <span className="h-2 w-2 rounded-full bg-emerald-500 absolute" />
                  <span className="text-[11px] font-medium text-emerald-400 flex items-center">
                    <Wifi className="h-3 w-3 mr-1" /> ONLINE
                  </span>
                </>
              ) : (
                <>
                  <span className="h-2 w-2 rounded-full bg-rose-500 shadow-md shadow-rose-500/50" />
                  <span className="text-[11px] font-medium text-rose-400 flex items-center">
                    <WifiOff className="h-3 w-3 mr-1" /> OFFLINE
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* ─── Right Content Column ─── */}
      <div className="flex-1 flex flex-col justify-between overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-900 bg-slate-900/10 backdrop-blur-md flex items-center justify-between px-8 flex-shrink-0">
          <div className="flex items-center space-x-4">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Active Model
            </span>
            {activeModel ? (
              <div className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-2 text-xs font-semibold">
                <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
                <span className="text-slate-200">{activeModel.name}</span>
                <span className="text-slate-500 text-[10px]">
                  ({activeModel.architecture.toUpperCase()})
                </span>
              </div>
            ) : loadingModelId ? (
              <div className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center space-x-3 text-xs font-semibold">
                <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" />
                <span className="text-slate-400">Swapping to Model...</span>
                <span className="text-indigo-400 text-[10px]">{loadingProgress}%</span>
              </div>
            ) : (
              <span className="text-xs font-medium text-slate-400 italic">No model loaded</span>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {/* Active Queue Size */}
            {queueItems.length > 0 && (
              <div className="px-3 py-1 rounded-full bg-violet-600/10 border border-violet-500/20 text-[11px] font-semibold text-violet-400 flex items-center">
                Queue tasks: {queueItems.length}
              </div>
            )}
            <span className="text-xs text-slate-400 font-semibold">v0.1.0 Alpha</span>
          </div>
        </header>

        {/* Dynamic View Panel */}
        <main className="flex-1 overflow-y-auto bg-slate-950/90 relative">{children}</main>
      </div>
    </div>
  )
}
