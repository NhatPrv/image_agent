import React, { useState, useEffect, useRef } from 'react'
import { useGenerationStore } from '../stores/useGenerationStore'
import { useModelStore } from '../stores/useModelStore'
import { useSystemStore } from '../stores/useSystemStore'
import {
  Sparkles,
  Sliders,
  Image,
  Zap,
  RefreshCw,
  XCircle,
  FileImage,
  Upload,
  Maximize2,
  Download,
  Terminal,
  AlertTriangle,
  ShieldAlert,
  CheckCircle,
  Info,
  Wand2
} from 'lucide-react'
import { CanvasMaskEditor } from '../components/CanvasMaskEditor'

export function GenerateView(): React.JSX.Element {
  const connected = useSystemStore((state) => state.connected)

  // Zustand State hooks
  const prompt = useGenerationStore((state) => state.prompt)
  const negativePrompt = useGenerationStore((state) => state.negativePrompt)
  const width = useGenerationStore((state) => state.width)
  const height = useGenerationStore((state) => state.height)
  const steps = useGenerationStore((state) => state.steps)
  const cfgScale = useGenerationStore((state) => state.cfgScale)
  const seed = useGenerationStore((state) => state.seed)
  const sampler = useGenerationStore((state) => state.sampler)
  const selectedModelId = useGenerationStore((state) => state.modelId)
  const type = useGenerationStore((state) => state.type)
  const inputImagePath = useGenerationStore((state) => state.inputImagePath)
  const denoiseStrength = useGenerationStore((state) => state.denoiseStrength)

  const generating = useGenerationStore((state) => state.generating)
  const progress = useGenerationStore((state) => state.progress)
  const currentStep = useGenerationStore((state) => state.currentStep)
  const totalSteps = useGenerationStore((state) => state.totalSteps)
  const previewImage = useGenerationStore((state) => state.previewImage)
  const currentGenId = useGenerationStore((state) => state.currentGenerationId)
  const history = useGenerationStore((state) => state.history)

  const setPrompt = useGenerationStore((state) => state.setPrompt)
  const setNegativePrompt = useGenerationStore((state) => state.setNegativePrompt)
  const setParams = useGenerationStore((state) => state.setParams)
  const addHistoryItem = useGenerationStore((state) => state.addHistoryItem)

  const models = useModelStore((state) => state.models)
  const setModels = useModelStore((state) => state.setModels)
  const setLoadingModelId = useModelStore((state) => state.setLoadingModelId)

  // UI states
  const [samplers] = useState(['Euler', 'Euler A', 'DPM++ 2M', 'DPM++ 2M Karras', 'Heun', 'UniPC'])
  const [outputImage, setOutputImage] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [tempMaskBase64, setTempMaskBase64] = useState<string | null>(null)
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<'editor' | 'output'>('editor')
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Loop Generation States (Persisted in Zustand store)
  const loopEnabled = useGenerationStore((state) => state.loopEnabled)
  const setLoopEnabled = useGenerationStore((state) => state.setLoopEnabled)
  const loopCount = useGenerationStore((state) => state.loopCount)
  const setLoopCount = useGenerationStore((state) => state.setLoopCount)
  const [remainingLoops, setRemainingLoops] = useState<number>(0)
  const isLoopRunning = useRef(false)
  const prevGenerating = useRef(false)
  const remainingLoopsRef = useRef(0)
  const [optimizingPrompt, setOptimizingPrompt] = useState(false)

  interface ActiveLoRA {
    modelId: string
    weight: number
  }
  const [activeLoras, setActiveLoras] = useState<ActiveLoRA[]>([])

  // Realtime Log States
  const [serverLogs, setServerLogs] = useState<string[]>([])
  const [warningLogs, setWarningLogs] = useState<string[]>([])
  const [errorLogs, setErrorLogs] = useState<string[]>([])

  // Subscribe to backend stdout/stderr log relays
  useEffect(() => {
    const unsub = window.api.onBackendLog((data) => {
      const line = data.text.trim()
      if (!line) return

      // Classify log lines by check markers or level strings
      const isError =
        line.includes('| ERROR    |') ||
        line.includes('| ERROR |') ||
        line.toLowerCase().includes('error:') ||
        data.type === 'stderr'

      const isWarning =
        line.includes('| WARNING  |') ||
        line.includes('| WARNING |') ||
        line.toLowerCase().includes('warning:')

      // Filter out progress lines (e.g. "10%|#") to keep server terminal clean
      if (line.match(/^\s*\d+%\s*\|/)) {
        return
      }

      if (isError) {
        setErrorLogs((prev) => [...prev.slice(-99), line])
      } else if (isWarning) {
        setWarningLogs((prev) => [...prev.slice(-99), line])
      } else {
        setServerLogs((prev) => [...prev.slice(-99), line])
      }
    })
    return () => {
      unsub()
    }
  }, [])

  // Automatically display the latest generated image when history is updated
  useEffect(() => {
    if (history.length > 0) {
      const latest = history[0]
      if (latest.status === 'completed' && latest.images.length > 0) {
        const imagePath = latest.images[0].path.replace(/\\/g, '/')
        setTimeout(() => {
          setOutputImage(`http://127.0.0.1:8000/outputs/${imagePath}`)
          setActiveWorkspaceTab('output')
        }, 0)
      }
    }
  }, [history])

  // Fetch models on component mount
  useEffect(() => {
    let active = true
    const fetchModels = async (): Promise<void> => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/v1/models')
        if (res.ok && active) {
          const data = await res.json()
          setModels(data)
        }
      } catch (err) {
        console.error('Failed to fetch available models:', err)
      }
    }
    fetchModels()
    return () => {
      active = false
    }
  }, [setModels])

  async function handleScanModels(): Promise<void> {
    setIsScanning(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/models/scan', { method: 'POST' })
      if (response.ok) {
        const data = await response.json()
        setModels(data)
      }
    } catch (err) {
      console.error('Failed scanning models folder:', err)
    } finally {
      setIsScanning(false)
    }
  }

  async function handleLoadModel(modelId: string): Promise<void> {
    setLoadingModelId(modelId)
    setParams({ modelId })
    try {
      await fetch('http://127.0.0.1:8000/api/v1/models/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      })
    } catch (err) {
      console.error('Failed requesting model load:', err)
    }
  }

  async function handleDownloadImage(): Promise<void> {
    if (!outputImage) return
    setErrorMsg(null)
    setSuccessMsg(null)
    try {
      const relativePath = outputImage.replace('http://127.0.0.1:8000/outputs/', '')
      const savedPath = await window.api.saveImageAs(relativePath)
      if (savedPath) {
        setSuccessMsg(`Image successfully saved to: ${savedPath}`)
        setTimeout(() => setSuccessMsg(null), 5000)
      }
    } catch (err) {
      console.error('Failed to export image:', err)
      setErrorMsg(`Failed to export image: ${(err as Error).message}`)
    }
  }

  async function handleGenerateSubmit(): Promise<void> {
    if (!connected) return
    setErrorMsg(null)
    setOutputImage(null)

    // Fallback: If no model selected, alert user
    const targetModel = selectedModelId || (models.length > 0 ? models[0].id : '')
    if (!targetModel) {
      setErrorMsg('No model selected. Please scan or select a diffusion model checkpoint.')
      return
    }

    // Map UI sampler labels to backend scheduler keys
    const samplerMap: Record<string, string> = {
      Euler: 'euler',
      'Euler A': 'euler_a',
      'DPM++ 2M': 'dpm_pp_2m',
      'DPM++ 2M Karras': 'dpm_pp_2m_karras',
      Heun: 'heun',
      UniPC: 'unipc'
    }

    let finalInputPath: string | undefined = undefined
    let finalMaskPath: string | undefined = undefined

    if (type === 'img2img') {
      if (!inputImagePath) {
        setErrorMsg('Please select an input image first.')
        return
      }
      finalInputPath = inputImagePath
    } else if (type === 'inpaint') {
      if (!inputImagePath || !tempMaskBase64) {
        setErrorMsg('Please select an image and draw a mask first.')
        return
      }
      try {
        // Save base64 mask drawing to temporary file path via Electron IPC
        const savedMaskPath = await window.api.saveTempImage(
          tempMaskBase64,
          `mask_${Date.now()}.png`
        )
        finalInputPath = inputImagePath
        finalMaskPath = savedMaskPath
      } catch (err) {
        setErrorMsg('Failed to save drawn mask: ' + (err as Error).message)
        return
      }
    }

    const payload = {
      prompt,
      negative_prompt: negativePrompt,
      width,
      height,
      steps,
      cfg_scale: cfgScale,
      seed: seed === -1 ? Math.floor(Math.random() * 9999999) : seed,
      sampler: samplerMap[sampler] ?? sampler.toLowerCase(),
      model_id: targetModel,
      type,
      input_image_path: finalInputPath,
      mask_image_path: finalMaskPath,
      denoise_strength: type !== 'txt2img' ? denoiseStrength : undefined,
      priority: 'normal',
      loras: activeLoras.map((lora) => ({
        model_id: lora.modelId,
        weight: lora.weight
      }))
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/generations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!response.ok) {
        const errDetail = await response.json()
        let errorString = 'Failed submission.'
        if (errDetail && errDetail.detail) {
          if (Array.isArray(errDetail.detail)) {
            errorString = errDetail.detail
              .map((e: { loc: (string | number)[]; msg: string }) => `${e.loc.join('.')}: ${e.msg}`)
              .join(', ')
          } else {
            errorString = String(errDetail.detail)
          }
        }
        throw new Error(errorString)
      }
      const data = await response.json()
      addHistoryItem(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed connecting to API endpoint.'
      setErrorMsg(msg)
    }
  }

  // Loop Generation effect watching generating status
  useEffect(() => {
    const wentFromTrueToFalse = prevGenerating.current === true && generating === false
    prevGenerating.current = generating

    let cleanupFn: (() => void) | undefined = undefined

    if (wentFromTrueToFalse && isLoopRunning.current) {
      const currentRemaining = remainingLoopsRef.current
      if (currentRemaining === -1 || currentRemaining > 0) {
        let nextRemaining = currentRemaining
        if (currentRemaining !== -1) {
          nextRemaining = currentRemaining - 1
          remainingLoopsRef.current = nextRemaining
          setRemainingLoops(nextRemaining)
        }

        if (nextRemaining === -1 || nextRemaining > 0) {
          const timer = setTimeout(() => {
            handleGenerateSubmit()
          }, 1000)
          cleanupFn = () => clearTimeout(timer)
        } else {
          isLoopRunning.current = false
          setSuccessMsg('Loop generation completed successfully!')
          setTimeout(() => setSuccessMsg(null), 3000)
        }
      }
    }

    return cleanupFn
  }, [generating])

  async function handleStartGenerate(): Promise<void> {
    if (loopEnabled) {
      let count = loopCount
      if (count < 1) {
        count = -1
      }
      remainingLoopsRef.current = count
      setRemainingLoops(count)
      isLoopRunning.current = true
      await handleGenerateSubmit()
    } else {
      isLoopRunning.current = false
      remainingLoopsRef.current = 0
      setRemainingLoops(0)
      await handleGenerateSubmit()
    }
  }

  async function handleStopLoop(): Promise<void> {
    isLoopRunning.current = false
    remainingLoopsRef.current = 0
    setRemainingLoops(0)
    await handleCancelGeneration()
  }

  async function handleCancelGeneration(): Promise<void> {
    isLoopRunning.current = false
    remainingLoopsRef.current = 0
    setRemainingLoops(0)
    if (!currentGenId) return
    try {
      await fetch(`http://127.0.0.1:8000/api/v1/queue/${currentGenId}/cancel`, {
        method: 'POST'
      })
    } catch (err) {
      console.error('Failed to request cancellation:', err)
    }
  }

  async function handleOptimizePrompt(): Promise<void> {
    if (!prompt.trim()) return
    setOptimizingPrompt(true)
    setErrorMsg(null)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/generations/optimize-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt })
      })
      if (response.ok) {
        const data = await response.json()
        setPrompt(data.optimized_prompt)
      } else {
        const errData = await response.json()
        setErrorMsg(errData.detail || 'Failed to optimize prompt via Ollama.')
      }
    } catch (err) {
      console.error('Failed to request prompt optimization:', err)
      setErrorMsg('Lỗi kết nối tới Ollama backend.')
    } finally {
      setOptimizingPrompt(false)
    }
  }

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* ─── Left Configuration Panel ─── */}
      <div className="w-80 border-r border-slate-900 bg-slate-950 p-6 overflow-y-auto space-y-6 flex-shrink-0">
        <div className="flex items-center justify-between border-b border-slate-900 pb-4">
          <div className="flex items-center space-x-2">
            <Sliders className="h-4.5 w-4.5 text-violet-400" />
            <h2 className="text-sm font-semibold tracking-wide text-slate-200">
              TUNING PARAMETERS
            </h2>
          </div>
          <button
            onClick={handleScanModels}
            disabled={isScanning}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition disabled:opacity-50"
            title="Scan Models Directory"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isScanning ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Generation Mode Tabs */}
        <div className="grid grid-cols-3 gap-1 bg-slate-900/50 p-1 rounded-xl border border-slate-900">
          {(['txt2img', 'img2img', 'inpaint'] as const).map((m) => {
            const labels = { txt2img: 'Text', img2img: 'Image', inpaint: 'Inpaint' }
            const active = type === m
            return (
              <button
                key={m}
                type="button"
                disabled={generating}
                onClick={() => setParams({ type: m })}
                className={`py-1.5 text-[10px] font-bold rounded-lg uppercase tracking-wider transition cursor-pointer ${
                  active
                    ? 'bg-violet-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                }`}
              >
                {labels[m]}
              </button>
            )
          })}
        </div>

        {/* Model Selection Dropdown */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 tracking-wider">
            CHECKPOINT MODEL
          </label>
          <select
            value={selectedModelId}
            onChange={(e) => handleLoadModel(e.target.value)}
            disabled={generating}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition cursor-pointer"
          >
            <option value="" disabled>
              Select model checkpoint...
            </option>
            {models.filter(m => m.component_type === 'checkpoint').map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} ({model.architecture.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        {/* LoRA Configuration Section */}
        <div className="space-y-3 bg-slate-900/40 border border-slate-800/60 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-300 tracking-wider flex items-center gap-1.5">
              🎨 LORA STYLES
            </label>
            <button
              type="button"
              disabled={generating}
              onClick={() => {
                const availableLoras = models.filter(m => m.component_type === 'lora');
                const unusedLora = availableLoras.find(l => !activeLoras.some(al => al.modelId === l.id));
                if (unusedLora) {
                  setActiveLoras([...activeLoras, { modelId: unusedLora.id, weight: 1.0 }]);
                } else if (availableLoras.length > 0) {
                  setActiveLoras([...activeLoras, { modelId: availableLoras[0].id, weight: 1.0 }]);
                }
              }}
              className="text-[10px] font-semibold text-violet-400 hover:text-violet-300 transition flex items-center gap-0.5"
            >
              + ADD LORA
            </button>
          </div>

          {activeLoras.length === 0 ? (
            <div className="text-[11px] text-slate-500 italic py-1.5 text-center bg-slate-950/30 border border-dashed border-slate-800/80 rounded-xl">
              No LoRA models applied
            </div>
          ) : (
            <div className="space-y-3">
              {activeLoras.map((activeLora, idx) => {
                const availableLoras = models.filter(m => m.component_type === 'lora');
                return (
                  <div key={idx} className="space-y-2 bg-slate-950/40 border border-slate-800/80 rounded-xl p-3 relative group">
                    <button
                      type="button"
                      onClick={() => setActiveLoras(activeLoras.filter((_, i) => i !== idx))}
                      className="absolute top-2 right-2 text-slate-500 hover:text-red-400 text-xs transition"
                    >
                      ×
                    </button>
                    
                    <div className="space-y-1">
                      <select
                        value={activeLora.modelId}
                        onChange={(e) => {
                          const newLoras = [...activeLoras];
                          newLoras[idx].modelId = e.target.value;
                          setActiveLoras(newLoras);
                        }}
                        className="w-full bg-slate-900 border border-slate-850 rounded-lg px-2 py-1 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-violet-500/50"
                      >
                        {availableLoras.map((lora) => (
                          <option key={lora.id} value={lora.id}>
                            {lora.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] text-slate-400">
                        <span>Weight</span>
                        <span className="font-mono text-violet-400 font-medium">
                          {activeLora.weight.toFixed(2)}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="-2"
                        max="2"
                        step="0.05"
                        value={activeLora.weight}
                        onChange={(e) => {
                          const newLoras = [...activeLoras];
                          newLoras[idx].weight = parseFloat(e.target.value);
                          setActiveLoras(newLoras);
                        }}
                        className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-violet-500"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Aspect Ratio Config */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-400 tracking-wider">
            IMAGE DIMENSIONS (UP TO 8K)
          </label>

          {/* Preset Dropdown */}
          <div className="space-y-1">
            <select
              value={
                [
                  '512x512',
                  '512x768',
                  '768x512',
                  '720x1280',
                  '1080x1920',
                  '1080x2340',
                  '768x1024',
                  '1024x768',
                  '1280x720',
                  '1600x900',
                  '1920x1080',
                  '1920x1200',
                  '2560x1440',
                  '1440x2560',
                  '2560x1600',
                  '3440x1440',
                  '2880x1800',
                  '3000x2000',
                  '3200x2000',
                  '3840x2160',
                  '2160x3840',
                  '7680x4320',
                  '4320x7680'
                ].includes(`${width}x${height}`)
                  ? `${width}x${height}`
                  : 'custom'
              }
              onChange={(e) => {
                const val = e.target.value
                if (val !== 'custom') {
                  const [w, h] = val.split('x').map(Number)
                  setParams({ width: w, height: h })
                }
              }}
              disabled={generating}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition cursor-pointer"
            >
              <option value="custom">-- Custom Resolution --</option>
              <optgroup label="Standard SD 1.5 Presets" className="bg-slate-950 text-slate-400">
                <option value="512x512">Square (512x512 - 1:1)</option>
                <option value="512x768">Portrait (512x768 - 2:3)</option>
                <option value="768x512">Landscape (768x512 - 3:2)</option>
              </optgroup>
              <optgroup label="Mobile Devices (Portrait)" className="bg-slate-950 text-slate-400">
                <option value="720x1280">Mobile HD (720x1280 - 9:16)</option>
                <option value="1080x1920">Mobile FHD (1080x1920 - 9:16)</option>
                <option value="1080x2340">Mobile Ultra (1080x2340 - 19.5:9)</option>
              </optgroup>
              <optgroup label="Tablet & iPad Devices" className="bg-slate-950 text-slate-400">
                <option value="768x1024">Tablet Portrait (768x1024 - 3:4)</option>
                <option value="1024x768">Tablet Landscape (1024x768 - 4:3)</option>
              </optgroup>
              <optgroup label="Desktop FHD Screen Presets" className="bg-slate-950 text-slate-400">
                <option value="1280x720">Desktop HD (1280x720 - 16:9)</option>
                <option value="1600x900">Desktop HD+ (1600x900 - 16:9)</option>
                <option value="1920x1080">Desktop FHD (1920x1080 - 16:9)</option>
                <option value="1920x1200">Desktop Wide (1920x1200 - 16:10)</option>
              </optgroup>
              <optgroup
                label="Desktop 2K / 3K Screen Presets"
                className="bg-slate-950 text-slate-400"
              >
                <option value="2560x1440">2K QHD Desktop (2560x1440 - 16:9)</option>
                <option value="1440x2560">2K QHD Mobile (1440x2560 - 9:16)</option>
                <option value="2560x1600">Laptop WQXGA / Legion 5 Pro (2560x1600 - 16:10)</option>
                <option value="3440x1440">Ultrawide QHD (3440x1440 - 21:9)</option>
                <option value="2880x1800">3K Retina Laptop (2880x1800 - 16:10)</option>
                <option value="3000x2000">3K Surface / Display (3000x2000 - 3:2)</option>
                <option value="3200x2000">3.2K Laptop Screen (3200x2000 - 16:10)</option>
              </optgroup>
              <optgroup label="UHD 4K / 8K Presets" className="bg-slate-950 text-slate-400">
                <option value="3840x2160">UHD 4K Landscape (3840x2160)</option>
                <option value="2160x3840">UHD 4K Portrait (2160x3840)</option>
                <option value="7680x4320">UHD 8K Landscape (7680x4320)</option>
                <option value="4320x7680">UHD 8K Portrait (4320x7680)</option>
              </optgroup>
            </select>
          </div>

          {/* Custom Width/Height inputs side-by-side */}
          <div className="grid grid-cols-2 gap-3.5">
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase">Width</span>
              <input
                type="number"
                min="128"
                max="8192"
                step="8"
                value={width}
                disabled={generating}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 512
                  setParams({ width: val })
                }}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition"
              />
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase">Height</span>
              <input
                type="number"
                min="128"
                max="8192"
                step="8"
                value={height}
                disabled={generating}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 512
                  setParams({ height: val })
                }}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition"
              />
            </div>
          </div>

          {/* VRAM Warning for high resolutions */}
          {width > 2048 || height > 2048 ? (
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-[10px] leading-relaxed text-rose-400 font-medium">
              🚨 <strong>CRITICAL OOM RISK (4K/8K):</strong> Generating at resolutions above 2K
              requires substantial GPU VRAM. Ensure both <strong>Model CPU Offloading</strong> and{' '}
              <strong>VAE Tiling</strong> are enabled in Settings to prevent OOM crashes.
            </div>
          ) : (
            (width > 1024 || height > 1024) && (
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[10px] leading-relaxed text-amber-400 font-medium">
                ⚠️ <strong>High Resolution Warning:</strong> Generating at FHD speeds requires more
                VRAM. Make sure VRAM optimizations are enabled if you run into OOM errors.
              </div>
            )
          )}
        </div>

        {/* Sampling Steps Slider */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-400">
            <span>SAMPLING STEPS</span>
            <span className="text-violet-400">{steps}</span>
          </div>
          <input
            type="range"
            min="5"
            max="100"
            step="1"
            value={steps}
            disabled={generating}
            onChange={(e) => setParams({ steps: parseInt(e.target.value) })}
            className="w-full accent-violet-500 h-1 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* CFG Scale Slider */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-400">
            <span>CFG SCALE</span>
            <span className="text-violet-400">{cfgScale.toFixed(1)}</span>
          </div>
          <input
            type="range"
            min="1"
            max="20"
            step="0.5"
            value={cfgScale}
            disabled={generating}
            onChange={(e) => setParams({ cfgScale: parseFloat(e.target.value) })}
            className="w-full accent-violet-500 h-1 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>

        {/* Sampler Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 tracking-wider">
            SAMPLER METHOD
          </label>
          <select
            value={sampler}
            disabled={generating}
            onChange={(e) => setParams({ sampler: e.target.value })}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition cursor-pointer"
          >
            {samplers.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Custom Seed Field */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 tracking-wider">
            CUSTOM SEED (-1 for Random)
          </label>
          <input
            type="number"
            value={seed}
            disabled={generating}
            onChange={(e) => setParams({ seed: parseInt(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs font-semibold text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition"
          />
        </div>

        {/* Loop Generation Settings */}
        <div className="space-y-3 border-t border-slate-900 pt-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-400 tracking-wider">
              LOOP GENERATION
            </label>
            <input
              type="checkbox"
              checked={loopEnabled}
              disabled={isLoopRunning.current}
              onChange={(e) => setLoopEnabled(e.target.checked)}
              className="accent-violet-500 h-4 w-4 rounded border-slate-800 bg-slate-900 cursor-pointer"
            />
          </div>
          {loopEnabled && (
            <div className="space-y-1.5 animate-fade-in">
              <span className="text-[10px] font-bold text-slate-500 uppercase">
                Number of Loops (Enter &lt; 1 for Infinite)
              </span>
              <input
                type="number"
                value={loopCount}
                disabled={isLoopRunning.current}
                onChange={(e) => {
                  const val = parseInt(e.target.value)
                  setLoopCount(isNaN(val) ? 1 : val)
                }}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-200 focus:outline-none focus:ring-1 focus:ring-violet-500/50 transition"
              />
            </div>
          )}
        </div>

        {/* Image to Image settings */}
        {type === 'img2img' && (
          <div className="space-y-4 border-t border-slate-900 pt-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 tracking-wider">
                INPUT IMAGE
              </label>
              {inputImagePath ? (
                <div className="relative rounded-xl border border-slate-800 bg-slate-900 p-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2 truncate max-w-[180px]">
                    <FileImage className="h-4 w-4 text-violet-400 flex-shrink-0" />
                    <span className="text-[10px] text-slate-200 truncate font-semibold">
                      {inputImagePath.split(/[\\/]/).pop()}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setParams({ inputImagePath: null })}
                    className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition cursor-pointer"
                  >
                    <XCircle className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={async () => {
                    const img = await window.api.selectImage()
                    if (img) setParams({ inputImagePath: img })
                  }}
                  className="w-full py-2.5 px-3 border border-dashed border-slate-800 rounded-xl hover:border-slate-700 bg-slate-900/30 flex items-center justify-center space-x-2 hover:bg-slate-900/50 transition cursor-pointer text-slate-400 hover:text-slate-200"
                >
                  <Upload className="h-3.5 w-3.5" />
                  <span className="text-xs font-semibold">Select Input Image</span>
                </button>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>DENOISING STRENGTH</span>
                <span className="text-violet-400">{denoiseStrength.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.05"
                value={denoiseStrength}
                disabled={generating}
                onChange={(e) => setParams({ denoiseStrength: parseFloat(e.target.value) })}
                className="w-full accent-violet-500 h-1 bg-slate-800 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* Inpaint settings */}
        {type === 'inpaint' && (
          <div className="space-y-4 border-t border-slate-900 pt-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-semibold text-slate-400">
                <span>DENOISING STRENGTH</span>
                <span className="text-violet-400">{denoiseStrength.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.05"
                max="1.0"
                step="0.05"
                value={denoiseStrength}
                disabled={generating}
                onChange={(e) => setParams({ denoiseStrength: parseFloat(e.target.value) })}
                className="w-full accent-violet-500 h-1 bg-slate-800 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>

      {/* ─── Right Content Panel (Wrapper for Center View & Bottom Logs) ─── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* ─── Center Prompt & Preview Panel ─── */}
        <div className="flex-1 flex flex-col p-8 overflow-hidden justify-between space-y-6">
          {/* Prompts Input Section */}
          <div className="space-y-4 flex-shrink-0">
            {/* Positive Prompt */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <div className="flex items-center space-x-2">
                  <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                  <span>POSITIVE PROMPT</span>
                </div>
                <button
                  type="button"
                  onClick={handleOptimizePrompt}
                  disabled={generating || optimizingPrompt || !prompt.trim()}
                  className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-violet-600/10 border border-violet-500/20 text-[10px] font-bold text-violet-400 hover:bg-violet-600/20 hover:text-violet-300 disabled:opacity-50 disabled:cursor-not-allowed transition cursor-pointer"
                >
                  <Wand2 className={`h-3 w-3 ${optimizingPrompt ? 'animate-pulse' : ''}`} />
                  <span>{optimizingPrompt ? 'OPTIMIZING...' : 'ENHANCE VIA OLLAMA'}</span>
                </button>
              </div>
              <textarea
                value={prompt}
                disabled={generating}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your creative vision in details..."
                className="w-full h-24 bg-slate-900 border border-slate-850 rounded-xl p-4 text-sm font-medium text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-violet-500/30 transition resize-none"
              />
            </div>

            {/* Negative Prompt */}
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-slate-400 tracking-wider">
                NEGATIVE PROMPT
              </span>
              <input
                type="text"
                value={negativePrompt}
                disabled={generating}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="What to exclude from the generated image..."
                className="w-full bg-slate-900 border border-slate-850 rounded-xl px-4 py-2.5 text-xs font-medium text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-violet-500/30 transition"
              />
            </div>
          </div>

          {/* Center Workspace (Image Preview Box) */}
          <div className="flex-1 border border-slate-900 rounded-2xl bg-slate-900/10 flex items-center justify-center p-6 overflow-hidden relative">
            {generating ? (
              <div className="flex flex-col items-center justify-center space-y-5 max-w-sm w-full">
                {/* WS Image Preview Frame */}
                <div className="relative h-64 w-64 rounded-xl border border-slate-800 bg-slate-950 flex items-center justify-center overflow-hidden shadow-2xl">
                  {previewImage ? (
                    <img
                      src={previewImage}
                      alt="Generation step preview"
                      className="h-full w-full object-cover animate-pulse"
                    />
                  ) : (
                    <Image className="h-10 w-10 text-slate-700 animate-pulse" />
                  )}
                  {/* Overlay step indicator */}
                  <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md text-[10px] font-bold text-violet-400 border border-slate-800">
                    Step {currentStep} / {totalSteps}
                  </div>
                </div>

                {/* Progress bar info */}
                <div className="w-full space-y-2">
                  <div className="flex justify-between text-xs font-bold text-slate-300">
                    <span>Generating image...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden border border-slate-900">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>

                {/* Cancel Button */}
                <button
                  onClick={handleCancelGeneration}
                  className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                >
                  <XCircle className="h-4 w-4 text-rose-500" />
                  <span>Cancel Generation</span>
                </button>
              </div>
            ) : type === 'inpaint' && activeWorkspaceTab === 'editor' ? (
              <CanvasMaskEditor
                imagePath={inputImagePath}
                width={width}
                height={height}
                onMaskChange={(maskBase64) => {
                  setTempMaskBase64(maskBase64)
                }}
                onImageSelected={(path) => {
                  setParams({ inputImagePath: path })
                }}
              />
            ) : outputImage ? (
              <div className="flex flex-col items-center justify-center space-y-3">
                <div className="relative group rounded-xl overflow-hidden border border-slate-850 shadow-2xl">
                  <img
                    src={outputImage}
                    alt="Generated Output"
                    className="max-h-[380px] max-w-full object-contain cursor-zoom-in"
                    onClick={() => setIsFullscreen(true)}
                  />
                  {/* Hover overlay button to trigger fullscreen */}
                  <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center pointer-events-none">
                    <button className="p-3 rounded-full bg-slate-900/80 border border-slate-850 text-white shadow-lg flex items-center justify-center">
                      <Maximize2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                <div className="flex items-center space-x-3 text-xs">
                  <span className="text-[11px] font-medium text-slate-500">Seed: {seed}</span>

                  <button
                    type="button"
                    onClick={() => setIsFullscreen(true)}
                    className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-slate-200 text-[10px] font-bold text-violet-400 uppercase tracking-wider transition cursor-pointer flex items-center space-x-1"
                  >
                    <Maximize2 className="h-3 w-3" />
                    <span>Fullscreen</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleDownloadImage}
                    className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-slate-200 text-[10px] font-bold text-emerald-400 uppercase tracking-wider transition cursor-pointer flex items-center space-x-1"
                  >
                    <Download className="h-3 w-3" />
                    <span>Save Image</span>
                  </button>

                  {type === 'inpaint' && (
                    <button
                      type="button"
                      onClick={() => setActiveWorkspaceTab('editor')}
                      className="px-2.5 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-slate-200 text-[10px] font-bold text-violet-400 uppercase tracking-wider transition cursor-pointer"
                    >
                      Draw Mask
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center space-y-3">
                <div className="mx-auto h-12 w-12 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-center">
                  <Image className="h-6 w-6 text-slate-600" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-slate-400">Workspace is empty</h4>
                  <p className="text-xs text-slate-500 max-w-xs leading-normal">
                    Configure parameters on the left and enter your prompt to generate your local AI
                    image.
                  </p>
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="absolute top-4 left-4 right-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-400">
                {errorMsg}
              </div>
            )}

            {successMsg && (
              <div className="absolute top-4 left-4 right-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400 z-10 animate-fade-in">
                {successMsg}
              </div>
            )}
          </div>

          {/* Generate Trigger Button Container */}
          <div className="flex-shrink-0">
            {(() => {
              const isLoopActive = isLoopRunning.current
              const buttonText = isLoopActive
                ? remainingLoops === -1
                  ? 'STOP INFINITE LOOP'
                  : `STOP LOOP (${remainingLoops} LEFT)`
                : generating
                  ? 'GENERATING AI IMAGE...'
                  : 'GENERATE AI IMAGE'

              return (
                <button
                  onClick={isLoopActive ? handleStopLoop : handleStartGenerate}
                  disabled={!isLoopActive && (generating || !connected)}
                  className={`w-full py-4 rounded-xl font-bold text-sm tracking-wider flex items-center justify-center space-x-2.5 transition-all duration-300 shadow-xl ${
                    !isLoopActive && (generating || !connected)
                      ? 'bg-slate-900 border border-slate-850 text-slate-500 cursor-not-allowed'
                      : isLoopActive
                        ? 'bg-gradient-to-r from-rose-600 to-red-600 text-white hover:from-rose-500 hover:to-red-500 shadow-rose-500/10 hover:shadow-rose-500/20 cursor-pointer'
                        : 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:from-violet-500 hover:to-indigo-500 shadow-violet-500/10 hover:shadow-violet-500/20 cursor-pointer'
                  }`}
                >
                  {isLoopActive ? (
                    <XCircle className="h-4 w-4 animate-pulse" />
                  ) : (
                    <Zap className={`h-4 w-4 ${generating ? 'animate-bounce' : ''}`} />
                  )}
                  <span>{buttonText}</span>
                </button>
              )
            })()}
          </div>
        </div>

        {/* ─── Bottom Split Log Terminals ─── */}
        <div className="border-t border-slate-900 bg-slate-950/80 p-4 space-y-3 flex-shrink-0 select-none">
          <div className="flex items-center justify-between border-b border-slate-900 pb-2">
            <div className="flex items-center space-x-2">
              <Terminal className="h-4 w-4 text-violet-400" />
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                SYSTEM DIAGNOSTICS & LOG PANELS
              </h3>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 h-40">
            {/* 1. Progress Terminal */}
            <div className="bg-slate-900/50 border border-slate-850 rounded-xl p-3 flex flex-col justify-between font-mono text-[10px] overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5 mb-2 text-violet-400 font-bold uppercase tracking-wider">
                <span>🚀 CURRENT PROGRESS</span>
                <span
                  className={`h-1.5 w-1.5 rounded-full ${generating ? 'bg-violet-500 animate-ping' : 'bg-slate-700'}`}
                />
              </div>
              {generating ? (
                <div className="space-y-2.5 flex-1 flex flex-col justify-center">
                  <div className="flex justify-between font-semibold text-slate-200">
                    <span>Generating...</span>
                    <span className="text-violet-400">{progress}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <div className="text-slate-400 text-right">
                    Step {currentStep} / {totalSteps}
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-500 space-y-1">
                  <Info className="h-4 w-4 opacity-50" />
                  <span>Idle - No active generation</span>
                </div>
              )}
            </div>

            {/* 2. Realtime Server Logs Terminal */}
            <div className="bg-slate-900/50 border border-slate-850 rounded-xl p-3 flex flex-col font-mono text-[10px] overflow-hidden">
              <div className="flex items-center space-x-1.5 border-b border-slate-800 pb-1.5 mb-1.5 text-emerald-400 font-bold uppercase tracking-wider">
                <CheckCircle className="h-3 w-3" />
                <span>Realtime Server</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-1 scrollbar-thin text-slate-300 pr-1 select-text">
                {serverLogs.length === 0 ? (
                  <span className="text-slate-600 italic">Listening for server events...</span>
                ) : (
                  serverLogs.map((log, idx) => (
                    <div key={idx} className="truncate" title={log}>
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 3. Warnings Terminal */}
            <div className="bg-slate-900/50 border border-slate-850 rounded-xl p-3 flex flex-col font-mono text-[10px] overflow-hidden">
              <div className="flex items-center space-x-1.5 border-b border-slate-800 pb-1.5 mb-1.5 text-amber-400 font-bold uppercase tracking-wider">
                <AlertTriangle className="h-3 w-3" />
                <span>Warnings</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-1 scrollbar-thin text-amber-300/80 pr-1 select-text">
                {warningLogs.length === 0 ? (
                  <span className="text-slate-600 italic">No system warnings.</span>
                ) : (
                  warningLogs.map((log, idx) => (
                    <div key={idx} className="break-all" title={log}>
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* 4. Errors Terminal */}
            <div className="bg-slate-900/50 border border-slate-850 rounded-xl p-3 flex flex-col font-mono text-[10px] overflow-hidden">
              <div className="flex items-center space-x-1.5 border-b border-slate-800 pb-1.5 mb-1.5 text-rose-400 font-bold uppercase tracking-wider">
                <ShieldAlert className="h-3 w-3" />
                <span>Diagnostics Errors</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-1 scrollbar-thin text-rose-300/80 pr-1 select-text">
                {errorLogs.length === 0 ? (
                  <span className="text-slate-600 italic">No diagnostic errors.</span>
                ) : (
                  errorLogs.map((log, idx) => (
                    <div key={idx} className="break-all" title={log}>
                      {log}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fullscreen Image Preview Modal */}
      {isFullscreen && outputImage && (
        <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-md flex flex-col items-center justify-center p-6 transition-all duration-300">
          <button
            onClick={() => setIsFullscreen(false)}
            className="absolute top-6 right-6 p-2 rounded-full bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
            title="Close Fullscreen"
          >
            <XCircle className="h-6 w-6" />
          </button>

          <img
            src={outputImage}
            alt="Fullscreen Preview"
            className="max-h-[85vh] max-w-full rounded-2xl object-contain border border-slate-900 shadow-2xl animate-fade-in"
          />

          <div className="mt-4 px-4 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-xs font-medium text-slate-300 flex items-center space-x-4">
            <span>
              <strong>Prompt:</strong> {prompt}
            </span>
            <span className="text-slate-600">|</span>
            <span>
              <strong>Seed:</strong> {seed}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
