import React, { useState, useEffect } from 'react'
import { useGenerationStore } from '../stores/useGenerationStore'
import { useModelStore } from '../stores/useModelStore'
import { useSystemStore } from '../stores/useSystemStore'
import { Sparkles, Sliders, Image, Zap, RefreshCw, XCircle, FileImage, Upload } from 'lucide-react'
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
  const [isScanning, setIsScanning] = useState(false)
  const [tempMaskBase64, setTempMaskBase64] = useState<string | null>(null)
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<'editor' | 'output'>('editor')

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
      priority: 'normal'
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/generations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!response.ok) {
        const errDetail = await response.json()
        throw new Error(errDetail.detail || 'Failed submission.')
      }
      const data = await response.json()
      addHistoryItem(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed connecting to API endpoint.'
      setErrorMsg(msg)
    }
  }

  async function handleCancelGeneration(): Promise<void> {
    if (!currentGenId) return
    try {
      await fetch(`http://127.0.0.1:8000/api/v1/queue/${currentGenId}/cancel`, {
        method: 'POST'
      })
    } catch (err) {
      console.error('Failed to request cancellation:', err)
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
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} ({model.architecture.toUpperCase()})
              </option>
            ))}
          </select>
        </div>

        {/* Aspect Ratio Config */}
        <div className="space-y-3">
          <label className="text-xs font-semibold text-slate-400 tracking-wider">
            IMAGE DIMENSIONS
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'Square', w: 512, h: 512 },
              { label: 'Portrait', w: 512, h: 768 },
              { label: 'Landscape', w: 768, h: 512 }
            ].map((preset) => {
              const active = width === preset.w && height === preset.h
              return (
                <button
                  key={preset.label}
                  disabled={generating}
                  onClick={() => setParams({ width: preset.w, height: preset.h })}
                  className={`py-2 px-1 text-[11px] font-semibold border rounded-lg transition-all duration-200 ${
                    active
                      ? 'bg-violet-600/10 border-violet-500 text-violet-400'
                      : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                  }`}
                >
                  <div className="font-bold">
                    {preset.w}x{preset.h}
                  </div>
                  <div className="text-[9px] opacity-60 font-medium">{preset.label}</div>
                </button>
              )
            })}
          </div>
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

      {/* ─── Center Prompt & Preview Panel ─── */}
      <div className="flex-1 flex flex-col p-8 overflow-hidden justify-between space-y-6">
        {/* Prompts Input Section */}
        <div className="space-y-4 flex-shrink-0">
          {/* Positive Prompt */}
          <div className="space-y-1.5">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400">
              <Sparkles className="h-3.5 w-3.5 text-violet-400" />
              <span>POSITIVE PROMPT</span>
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
              width={width}
              height={height}
              onMaskChange={(inputImg, maskBase64) => {
                setParams({ inputImagePath: inputImg })
                setTempMaskBase64(maskBase64)
              }}
            />
          ) : outputImage ? (
            <div className="flex flex-col items-center justify-center space-y-3">
              <img
                src={outputImage}
                alt="Generated Output"
                className="max-h-[380px] max-w-full rounded-xl object-contain border border-slate-850 shadow-2xl"
              />
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-[11px] font-medium text-slate-500">Seed used: {seed}</span>
                {type === 'inpaint' && (
                  <button
                    type="button"
                    onClick={() => setActiveWorkspaceTab('editor')}
                    className="ml-4 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 hover:text-slate-200 text-[10px] font-bold text-violet-400 uppercase tracking-wider transition cursor-pointer"
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
        </div>

        {/* Generate Trigger Button Container */}
        <div className="flex-shrink-0">
          <button
            onClick={handleGenerateSubmit}
            disabled={generating || !connected}
            className={`w-full py-4 rounded-xl font-bold text-sm tracking-wider flex items-center justify-center space-x-2.5 transition-all duration-300 shadow-xl ${
              generating || !connected
                ? 'bg-slate-900 border border-slate-850 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:from-violet-500 hover:to-indigo-500 shadow-violet-500/10 hover:shadow-violet-500/20 cursor-pointer'
            }`}
          >
            <Zap className={`h-4 w-4 ${generating ? 'animate-bounce' : ''}`} />
            <span>{generating ? 'GENERATING AI IMAGE...' : 'GENERATE AI IMAGE'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}
