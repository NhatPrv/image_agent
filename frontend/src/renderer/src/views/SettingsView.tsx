import React, { useEffect, useState } from 'react'
import { Save, FolderOpen, ShieldCheck, Zap, HardDrive } from 'lucide-react'

interface SettingsPayload {
  app: {
    name: string
    version: string
    debug: boolean
  }
  server: {
    host: string
    port: number
    cors_origins: string[]
  }
  paths: {
    models_dir: string
    outputs_dir: string
    logs_dir: string
  }
  gpu: {
    device: string
    dtype: string
    xformers: boolean
    attention_slicing: boolean
    vae_slicing: boolean
    vae_tiling: boolean
    cpu_offload: boolean
    sequential_cpu_offload: boolean
    torch_compile: boolean
    max_vram_usage_mb: number
  }
}

export function SettingsView(): React.JSX.Element {
  const [settings, setSettings] = useState<SettingsPayload | null>(null)
  const [loading, setLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  useEffect(() => {
    let active = true
    const fetchSettings = async (): Promise<void> => {
      setLoading(true)
      try {
        const response = await fetch('http://127.0.0.1:8000/api/v1/settings')
        if (response.ok && active) {
          const data = await response.json()
          setSettings(data)
        }
      } catch (err) {
        console.error('Failed to load settings:', err)
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }
    fetchSettings()
    return () => {
      active = false
    }
  }, [])

  async function handleBrowseFolder(
    field: 'models_dir' | 'outputs_dir' | 'logs_dir'
  ): Promise<void> {
    if (!settings) return
    try {
      // Invoke native Electron file chooser through preload IPC bridge
      const chosenPath = await window.api.selectDirectory()
      if (chosenPath) {
        setSettings({
          ...settings,
          paths: {
            ...settings.paths,
            [field]: chosenPath
          }
        })
      }
    } catch (err) {
      console.error('Failed opening directory chooser:', err)
    }
  }

  async function handleSaveSettings(): Promise<void> {
    if (!settings) return
    setSuccessMsg(null)
    setErrorMsg(null)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
      if (response.ok) {
        setSuccessMsg('Settings updated and saved to SQLite configuration storage successfully!')
        // Auto dismiss alert after 4 seconds
        setTimeout(() => setSuccessMsg(null), 4000)
      } else {
        throw new Error('Failed to update config on FastAPI server.')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Network connection issue.'
      setErrorMsg(msg)
    }
  }

  if (loading || !settings) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="flex flex-col items-center space-y-2">
          <span className="h-5 w-5 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
          <span className="text-xs font-semibold text-slate-500">Querying config registry...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8 pb-16">
      <div className="flex justify-between items-center border-b border-slate-900 pb-4">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
            SYSTEM SETTINGS
          </h2>
          <p className="text-[11px] text-slate-500">
            Configure file folders, CPU/VRAM load policies, and hardware acceleration.
          </p>
        </div>
        <button
          onClick={handleSaveSettings}
          className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-xs font-bold text-white shadow-lg shadow-violet-500/10 cursor-pointer transition-all duration-200"
        >
          <Save className="h-4 w-4" />
          <span>Save Changes</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400">
          {successMsg}
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-400">
          {errorMsg}
        </div>
      )}

      <div className="space-y-6">
        {/* ─── Paths Settings ─── */}
        <section className="bg-slate-900/10 border border-slate-900 rounded-2xl p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-400 flex items-center space-x-2">
            <HardDrive className="h-4 w-4 text-violet-400" />
            <span>STORAGE PATHS</span>
          </h3>

          <div className="space-y-4">
            {/* Models Folder */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Models Directory
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={settings.paths.models_dir}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      paths: { ...settings.paths, models_dir: e.target.value }
                    })
                  }
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-300 focus:outline-none"
                />
                <button
                  onClick={() => handleBrowseFolder('models_dir')}
                  className="px-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 flex items-center justify-center transition cursor-pointer"
                >
                  <FolderOpen className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Outputs Folder */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Outputs Directory
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={settings.paths.outputs_dir}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      paths: { ...settings.paths, outputs_dir: e.target.value }
                    })
                  }
                  className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-300 focus:outline-none"
                />
                <button
                  onClick={() => handleBrowseFolder('outputs_dir')}
                  className="px-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 flex items-center justify-center transition cursor-pointer"
                >
                  <FolderOpen className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ─── GPU & VRAM Memory Optimizations ─── */}
        <section className="bg-slate-900/10 border border-slate-900 rounded-2xl p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-400 flex items-center space-x-2">
            <Zap className="h-4 w-4 text-violet-400" />
            <span>ACCELERATION & MEMORY OPTIMIZATIONS</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* GPU Device */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Device
              </label>
              <select
                value={settings.gpu.device}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    gpu: { ...settings.gpu, device: e.target.value }
                  })
                }
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-300 focus:outline-none"
              >
                <option value="cuda">CUDA (Nvidia GPU)</option>
                <option value="cpu">CPU (Slow fallback)</option>
              </select>
            </div>

            {/* Floating precision Dtype */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Precision Weight
              </label>
              <select
                value={settings.gpu.dtype}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    gpu: { ...settings.gpu, dtype: e.target.value }
                  })
                }
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-300 focus:outline-none"
              >
                <option value="float16">FP16 (Recommended for RTX)</option>
                <option value="float32">FP32 (High precision, high memory)</option>
              </select>
            </div>
          </div>

          {/* Toggle Switches */}
          <div className="pt-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                id: 'xformers',
                label: 'Enable xFormers Cross-Attention',
                desc: 'Saves VRAM and increases rendering speed'
              },
              {
                id: 'attention_slicing',
                label: 'Enable Attention Slicing',
                desc: 'Processes attention blocks sequentially'
              },
              {
                id: 'vae_slicing',
                label: 'Enable VAE Slicing',
                desc: 'Splits VRAM frames for large image decoding'
              },
              {
                id: 'vae_tiling',
                label: 'Enable VAE Tiling',
                desc: 'Processes VAE tiles sequentially (prevents OOM on high resolutions)'
              },
              {
                id: 'cpu_offload',
                label: 'Enable Sequential CPU Offload',
                desc: 'Sends idle pipeline steps to host system memory'
              }
            ].map((opt) => (
              <div
                key={opt.id}
                className="flex items-start space-x-3.5 p-3 rounded-xl border border-slate-900/60 bg-slate-900/5"
              >
                <input
                  type="checkbox"
                  id={opt.id}
                  checked={settings.gpu[opt.id as keyof typeof settings.gpu] as boolean}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      gpu: {
                        ...settings.gpu,
                        [opt.id]: e.target.checked
                      }
                    })
                  }
                  className="mt-1 accent-violet-500 h-4 w-4 rounded cursor-pointer"
                />
                <div className="space-y-0.5">
                  <label
                    htmlFor={opt.id}
                    className="text-xs font-bold text-slate-300 cursor-pointer"
                  >
                    {opt.label}
                  </label>
                  <p className="text-[10px] text-slate-500 leading-normal">{opt.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ─── App Info ─── */}
        <section className="bg-slate-900/10 border border-slate-900 rounded-2xl p-6 space-y-4">
          <h3 className="text-xs font-bold text-slate-400 flex items-center space-x-2">
            <ShieldCheck className="h-4 w-4 text-violet-400" />
            <span>APPLICATION INFO</span>
          </h3>

          <div className="grid grid-cols-2 gap-4 text-xs font-semibold text-slate-400">
            <div>
              <p className="text-[10px] text-slate-500 uppercase">App Name</p>
              <p className="text-slate-300 font-bold">{settings.app.name}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">Version</p>
              <p className="text-slate-300 font-bold">{settings.app.version}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">Port Server</p>
              <p className="text-slate-300 font-bold">{settings.server.port}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase">Debug Mode</p>
              <p className="text-slate-300 font-bold">
                {settings.app.debug ? 'Active' : 'Disabled'}
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
