import React, { useEffect, useState } from 'react'
import {
  Download,
  Play,
  X,
  CheckCircle2,
  AlertCircle,
  FileType,
  RefreshCw,
  Globe,
  HelpCircle
} from 'lucide-react'
import { useDownloadStore } from '../stores/useDownloadStore'

// catalog list of recommended models
interface RecommendedModel {
  name: string
  filename: string
  url: string
  size: string
  description: string
  type: string
}

const RECOMMENDED_MODELS: RecommendedModel[] = [
  {
    name: 'Stable Diffusion 1.5 Pruned Checkpoint',
    filename: 'v1-5-pruned-emaonly.safetensors',
    url: 'https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors',
    size: '4.27 GB',
    type: 'checkpoint',
    description:
      'Official base Stable Diffusion 1.5 checkpoint. Ideal for general-purpose creations, photorealism, or anime base styles.'
  },
  {
    name: 'DreamShaper v8',
    filename: 'DreamShaper_8_pruned.safetensors',
    url: 'https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors',
    size: '2.13 GB',
    type: 'checkpoint',
    description:
      'Highly versatile checkpoint combining photo-realism, anime, and oil painting styles. Excels at generating rich detail and illustrations.'
  },
  {
    name: 'Realistic Vision v6.0 B1',
    filename: 'Realistic_Vision_V6.0_B1_noVAE.safetensors',
    url: 'https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE/resolve/main/Realistic_Vision_V6.0_B1_noVAE.safetensors',
    size: '2.13 GB',
    type: 'checkpoint',
    description:
      'Best-in-class realistic model. Specializes in producing natural human skin textures, realistic eyes, fashion, landscapes, and animals.'
  }
]

export function DownloadManagerView(): React.JSX.Element {
  const tasks = useDownloadStore((state) => state.tasks)
  const setTasks = useDownloadStore((state) => state.setTasks)
  const addOrUpdateTask = useDownloadStore((state) => state.addOrUpdateTask)

  // Form states
  const [customUrl, setCustomUrl] = useState('')
  const [customFilename, setCustomFilename] = useState('')
  const [customType, setCustomType] = useState('checkpoint')

  const [loading, setLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Fetch downloads list on mount
  useEffect(() => {
    let active = true
    const fetchTasks = async (): Promise<void> => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/v1/downloads')
        if (response.ok && active) {
          const data = await response.json()
          setTasks(data)
        }
      } catch (err) {
        console.error('Failed to retrieve downloads registry list:', err)
      }
    }
    fetchTasks()
    return () => {
      active = false
    }
  }, [setTasks])

  // URL extraction of filename is handled on change to prevent cascading renders

  async function triggerDownload(url: string, filename: string, type: string): Promise<void> {
    setSuccessMsg(null)
    setErrorMsg(null)
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/downloads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          filename,
          component_type: type
        })
      })

      if (response.ok) {
        const newTask = await response.json()
        addOrUpdateTask(newTask)
        setSuccessMsg(`Download task queued for ${filename}!`)
        setTimeout(() => setSuccessMsg(null), 3000)
      } else {
        const errDetail = await response.json()
        throw new Error(errDetail.detail || 'Server rejected download task request.')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connection failed.'
      setErrorMsg(msg)
      setTimeout(() => setErrorMsg(null), 5000)
    } finally {
      setLoading(false)
    }
  }

  async function cancelTask(taskId: string): Promise<void> {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/downloads/${taskId}/cancel`, {
        method: 'POST'
      })
      if (response.ok) {
        setSuccessMsg('Download task has been cancelled.')
        setTimeout(() => setSuccessMsg(null), 3000)
      }
    } catch (err) {
      console.error('Failed to cancel download task:', err)
    }
  }

  function handleCustomSubmit(e: React.FormEvent): void {
    e.preventDefault()
    if (!customUrl || !customFilename) {
      setErrorMsg('Please input both download URL and target filename.')
      return
    }
    triggerDownload(customUrl, customFilename, customType)
    setCustomUrl('')
    setCustomFilename('')
  }

  function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  function formatEta(seconds: number): string {
    if (!seconds || seconds === Infinity) return 'Calculating...'
    if (seconds < 60) return `${Math.round(seconds)}s`
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}m ${secs}s`
  }

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-8 pb-20">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-slate-900 pb-4">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
            MODEL DOWNLOAD MANAGER
          </h2>
          <p className="text-[11px] text-slate-500">
            Browse recommended offline models or paste custom URLs to download checkpoints directly.
          </p>
        </div>
      </div>

      {/* Alerts */}
      {successMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400 flex items-center space-x-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-400 flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recommended Models list (Left 2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <Globe className="h-4 w-4 text-violet-400" />
              <span>Recommended Models (1-Click Tải)</span>
            </h3>
            <p className="text-[10px] text-slate-500">
              Curation of stable base models optimal for local GPU rendering.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {RECOMMENDED_MODELS.map((model) => {
              const activeTask = tasks.find(
                (t) => t.url === model.url && (t.status === 'downloading' || t.status === 'pending')
              )
              const completedTask = tasks.find(
                (t) => t.url === model.url && t.status === 'completed'
              )

              return (
                <div
                  key={model.name}
                  className="p-5 rounded-2xl bg-slate-950 border border-slate-900 hover:border-slate-800 transition-all duration-300 flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="flex justify-between items-start">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-violet-950 text-violet-300 border border-violet-800/30">
                          {model.type}
                        </span>
                        <h4 className="text-xs font-bold text-slate-200 mt-2">{model.name}</h4>
                      </div>
                      <span className="text-[10px] font-medium text-slate-400 font-mono">
                        {model.size}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      {model.description}
                    </p>
                    <div className="text-[10px] text-slate-500 font-mono select-all bg-slate-900/50 p-2 rounded-lg break-all">
                      File: {model.filename}
                    </div>
                  </div>

                  <div className="flex justify-end pt-2">
                    {activeTask ? (
                      <button
                        disabled
                        className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 text-slate-500 text-[10px] font-semibold"
                      >
                        <RefreshCw className="h-3 w-3 animate-spin" />
                        <span>Downloading...</span>
                      </button>
                    ) : completedTask ? (
                      <span className="flex items-center space-x-1.5 text-[10px] font-semibold text-emerald-400 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Đã Tải Xong</span>
                      </span>
                    ) : (
                      <button
                        disabled={loading}
                        onClick={() => triggerDownload(model.url, model.filename, model.type)}
                        className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-[10px] font-bold text-white transition-all cursor-pointer shadow-md shadow-violet-600/10"
                      >
                        <Download className="h-3.5 w-3.5" />
                        <span>Download to Local</span>
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Custom URL Downloader (Right Column) */}
        <div className="space-y-6">
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <FileType className="h-4 w-4 text-violet-400" />
              <span>Tải URL Tùy Chọn</span>
            </h3>
            <p className="text-[10px] text-slate-500">
              Download any checkpoint/LoRA directly from HuggingFace, CivitAI or elsewhere.
            </p>
          </div>

          <form
            onSubmit={handleCustomSubmit}
            className="p-5 rounded-2xl bg-slate-950 border border-slate-900 space-y-4"
          >
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Direct Download Link URL
              </label>
              <input
                type="url"
                required
                value={customUrl}
                onChange={(e) => {
                  const url = e.target.value
                  setCustomUrl(url)
                  try {
                    const urlObj = new URL(url)
                    const pathname = urlObj.pathname
                    const lastPart = pathname.substring(pathname.lastIndexOf('/') + 1)
                    if (lastPart && lastPart.includes('.')) {
                      setCustomFilename(lastPart)
                    }
                  } catch {
                    // Ignore invalid url extraction
                  }
                }}
                placeholder="https://huggingface.co/..."
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-200 placeholder-slate-600 focus:outline-none focus:border-violet-500 transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Save Filename
              </label>
              <input
                type="text"
                required
                value={customFilename}
                onChange={(e) => setCustomFilename(e.target.value)}
                placeholder="my_favorite_model.safetensors"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-200 placeholder-slate-600 focus:outline-none focus:border-violet-500 transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Model Category
              </label>
              <select
                value={customType}
                onChange={(e) => setCustomType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-[11px] text-slate-200 focus:outline-none focus:border-violet-500 transition-all"
              >
                <option value="checkpoint">Checkpoint (Model Base)</option>
                <option value="lora">LoRA Model</option>
                <option value="vae">VAE Weights</option>
                <option value="controlnet">ControlNet Weights</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-xs font-bold text-white transition-all cursor-pointer shadow-md shadow-violet-600/10 mt-6"
            >
              <Play className="h-4 w-4" />
              <span>Queue Download Task</span>
            </button>
          </form>

          {/* Help Tips */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-900 space-y-2.5">
            <h4 className="text-[10px] font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
              <HelpCircle className="h-3.5 w-3.5 text-violet-400" />
              <span>Lưu ý khi dán URL</span>
            </h4>
            <ul className="list-disc list-inside text-[10px] text-slate-500 space-y-1.5 leading-relaxed">
              <li>
                <strong>HuggingFace:</strong> Sử dụng liên kết copy từ nút{' '}
                <code className="text-slate-300">download</code> chính thức (có chữ{' '}
                <code className="text-violet-400">/resolve/</code> trong URL).
              </li>
              <li>
                <strong>CivitAI:</strong> Copy liên kết download, nếu model yêu cầu đăng nhập, hãy
                thêm tham số API Key của bạn vào sau URL.
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Active & History downloads dashboard */}
      <div className="space-y-4 border-t border-slate-900 pt-8">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Download Telemetry Dashboard ({tasks.length} tasks)
        </h3>

        {tasks.length === 0 ? (
          <div className="p-8 rounded-2xl bg-slate-950 border border-slate-900 border-dashed text-center">
            <span className="text-[11px] text-slate-500 font-medium">
              No active or history downloads registered yet. Start one above!
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tasks.map((task) => {
              const percent =
                task.bytes_total > 0 ? (task.bytes_downloaded / task.bytes_total) * 100 : 0
              const isCompleted = task.status === 'completed'
              const isFailed = task.status === 'failed'
              const isCancelled = task.status === 'cancelled'
              const isDownloading = task.status === 'downloading'

              return (
                <div
                  key={task.task_id}
                  className={`p-4 rounded-xl bg-slate-950 border ${
                    isCompleted
                      ? 'border-emerald-500/10'
                      : isFailed
                        ? 'border-rose-500/10'
                        : 'border-slate-900'
                  } space-y-3.5`}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-0.5">
                      <h4 className="text-xs font-bold text-slate-200 truncate max-w-[280px]">
                        {task.filename}
                      </h4>
                      <p className="text-[9px] text-slate-500 font-mono truncate max-w-[280px]">
                        {task.url}
                      </p>
                    </div>

                    {isDownloading && (
                      <button
                        onClick={() => cancelTask(task.task_id)}
                        className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-rose-400 cursor-pointer transition-colors"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>

                  {/* Progress telemetry */}
                  {!isCompleted && !isFailed && !isCancelled && (
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-[9px] font-mono text-slate-400">
                        <span>
                          {formatBytes(task.bytes_downloaded)} / {formatBytes(task.bytes_total)}
                        </span>
                        <span>{task.speed_mb.toFixed(2)} MB/s</span>
                      </div>

                      <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 transition-all duration-300"
                          style={{ width: `${percent}%` }}
                        />
                      </div>

                      <div className="flex justify-between text-[9px] text-slate-500">
                        <span>ETA: {formatEta(task.eta_seconds)}</span>
                        <span>{percent.toFixed(1)}%</span>
                      </div>
                    </div>
                  )}

                  {/* Completed status banner */}
                  {isCompleted && (
                    <div className="flex items-center space-x-2 text-[10px] text-emerald-400 font-semibold">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                      <span>Download completed successfully and model auto-registered!</span>
                    </div>
                  )}

                  {/* Failed status banner */}
                  {isFailed && (
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2 text-[10px] text-rose-400 font-semibold">
                        <AlertCircle className="h-4 w-4 text-rose-500 shrink-0" />
                        <span>Download failed</span>
                      </div>
                      <p className="text-[9px] text-rose-500 leading-normal pl-6">
                        Reason: {task.error_message || 'Unknown network error.'}
                      </p>
                    </div>
                  )}

                  {/* Cancelled status banner */}
                  {isCancelled && (
                    <div className="flex items-center space-x-2 text-[10px] text-slate-500 font-semibold">
                      <AlertCircle className="h-4 w-4 text-slate-600 shrink-0" />
                      <span>Download cancelled and temp files scrubbed.</span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
