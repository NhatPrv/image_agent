import React, { useRef, useState, useEffect, useCallback } from 'react'
import {
  Paintbrush,
  Eraser,
  Trash2,
  Undo,
  Upload,
  CheckCircle2,
  Maximize2,
  Minimize2,
  X
} from 'lucide-react'

interface CanvasMaskEditorProps {
  imagePath: string | null
  width: number
  height: number
  onMaskChange: (maskBase64: string | null) => void
  onImageSelected: (path: string | null) => void
}

export function CanvasMaskEditor({
  imagePath,
  onMaskChange,
  onImageSelected,
  width = 512,
  height = 512
}: CanvasMaskEditorProps): React.JSX.Element {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [tool, setTool] = useState<'brush' | 'eraser'>('brush')
  const [brushSize, setBrushSize] = useState<number>(20)
  const [isFullscreenModal, setIsFullscreenModal] = useState<boolean>(false)

  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const isDrawingRef = useRef<boolean>(false)
  const historyRef = useRef<string[]>([]) // Store base64 snapshots for undo
  const [canUndo, setCanUndo] = useState(false)

  // Listen for ESC key to close Fullscreen Mode
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape' && isFullscreenModal) {
        setIsFullscreenModal(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isFullscreenModal])

  // Trigger mask export
  const exportMask = useCallback((): void => {
    const canvas = canvasRef.current
    if (!canvas || !imagePath) return

    // Create an offscreen canvas to export a black-and-white mask
    // matching the desired width/height configured for generation.
    const exportCanvas = document.createElement('canvas')
    exportCanvas.width = width
    exportCanvas.height = height
    const exportCtx = exportCanvas.getContext('2d')

    if (exportCtx) {
      // 1. Black background
      exportCtx.fillStyle = 'black'
      exportCtx.fillRect(0, 0, width, height)

      // 2. Scale and draw the drawing canvas strokes as white
      // Canvas is drawn overlaying the image, so we just draw the canvas content.
      // But wait: we draw the mask as white. The transparent canvas currently has red drawings.
      // To get a black and white mask, we can filter or draw using a composition or offscreen canvas.
      // Easiest way: the transparent canvas only holds the mask drawings.
      // We can draw the transparent canvas on the black export canvas, then convert any non-transparent
      // pixels to white.
      exportCtx.drawImage(canvas, 0, 0, width, height)

      const imgData = exportCtx.getImageData(0, 0, width, height)
      const data = imgData.data
      for (let i = 0; i < data.length; i += 4) {
        const alpha = data[i + 3]
        if (alpha > 10) {
          // If drawn (alpha > 10), convert pixel to solid white
          data[i] = 255 // R
          data[i + 1] = 255 // G
          data[i + 2] = 255 // B
          data[i + 3] = 255 // A
        } else {
          // Keep background solid black
          data[i] = 0
          data[i + 1] = 0
          data[i + 2] = 0
          data[i + 3] = 255
        }
      }
      exportCtx.putImageData(imgData, 0, 0)
      const base64Mask = exportCanvas.toDataURL('image/png')
      onMaskChange(base64Mask)
    }
  }, [imagePath, width, height, onMaskChange])

  // Handle select image click
  const handleSelectImage = async (): Promise<void> => {
    try {
      const selected = await window.api.selectImage()
      if (selected) {
        onImageSelected(selected)
        // Reset canvas drawings
        clearCanvas()
        historyRef.current = []
        setCanUndo(false)
      }
    } catch (err) {
      console.error('Failed to select input image:', err)
    }
  }

  // Clear Canvas Drawing
  const clearCanvas = (): void => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      saveHistory()
      onMaskChange(null)
    }
  }

  // Save history state for undo
  const saveHistory = (): void => {
    const canvas = canvasRef.current
    if (!canvas) return
    const snap = canvas.toDataURL()
    historyRef.current.push(snap)
    if (historyRef.current.length > 20) {
      historyRef.current.shift()
    }
    setCanUndo(historyRef.current.length > 1)
  }

  // Undo draw step
  const handleUndo = (): void => {
    const canvas = canvasRef.current
    if (!canvas || historyRef.current.length <= 1) return
    // Remove current state
    historyRef.current.pop()
    const previousState = historyRef.current[historyRef.current.length - 1]

    const ctx = canvas.getContext('2d')
    if (ctx && previousState) {
      const img = new Image()
      img.onload = (): void => {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        ctx.drawImage(img, 0, 0)
        exportMask()
      }
      img.src = previousState
    }
    setCanUndo(historyRef.current.length > 1)
  }

  // Set up transparent drawing canvas parameters
  useEffect(() => {
    const canvas = canvasRef.current
    if (canvas) {
      canvas.width = 512
      canvas.height = 512
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.lineCap = 'round'
        ctx.lineJoin = 'round'
      }
      // Save initial blank state
      saveHistory()
    }
  }, [imagePath])

  // Convert local imagePath to base64 data URL via IPC for webSecurity bypass
  useEffect(() => {
    if (imagePath) {
      window.api.readImageBase64(imagePath).then((base64) => {
        setImageSrc(base64)
      })
    } else {
      setImageSrc(null)
    }
  }, [imagePath])

  // Triggers export when drawing ends or tool updates
  useEffect(() => {
    if (imagePath) {
      exportMask()
    }
  }, [imagePath, exportMask])

  // Mouse event listeners for canvas
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>): void => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    // Scale coords to match the internal 512x512 resolution of the canvas
    const x = ((e.clientX - rect.left) / rect.width) * canvas.width
    const y = ((e.clientY - rect.top) / rect.height) * canvas.height

    ctx.beginPath()
    ctx.moveTo(x, y)
    isDrawingRef.current = true

    // Setup brush/eraser properties
    ctx.lineWidth = brushSize
    if (tool === 'eraser') {
      ctx.globalCompositeOperation = 'destination-out'
    } else {
      ctx.globalCompositeOperation = 'source-over'
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.6)' // semi-transparent red
    }

    // Draw single point
    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const draw = (e: React.MouseEvent<HTMLCanvasElement>): void => {
    if (!isDrawingRef.current) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * canvas.width
    const y = ((e.clientY - rect.top) / rect.height) * canvas.height

    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const stopDrawing = (): void => {
    if (isDrawingRef.current) {
      isDrawingRef.current = false
      saveHistory()
      exportMask()
    }
  }

  const content = (
    <div className={`flex flex-col space-y-4 w-full items-center ${isFullscreenModal ? 'h-full justify-between' : ''}`}>
      {/* ─── Toolbar Row ─── */}
      <div className="flex items-center justify-between w-full bg-slate-950 border border-slate-900 rounded-xl p-3 flex-wrap gap-3">
        <div className="flex items-center space-x-1.5">
          {/* Upload Button */}
          <button
            type="button"
            onClick={handleSelectImage}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-bold transition shadow-md shadow-violet-500/10 cursor-pointer"
          >
            <Upload className="h-3.5 w-3.5" />
            <span>Select Image</span>
          </button>

          {imagePath && (
            <>
              {/* Brush Tool */}
              <button
                type="button"
                onClick={() => setTool('brush')}
                className={`p-2 rounded-lg border transition ${
                  tool === 'brush'
                    ? 'bg-slate-900 border-violet-500 text-violet-400'
                    : 'bg-slate-900/50 border-slate-850 text-slate-400 hover:text-slate-200'
                }`}
                title="Mask Brush"
              >
                <Paintbrush className="h-3.5 w-3.5" />
              </button>

              {/* Eraser Tool */}
              <button
                type="button"
                onClick={() => setTool('eraser')}
                className={`p-2 rounded-lg border transition ${
                  tool === 'eraser'
                    ? 'bg-slate-900 border-violet-500 text-violet-400'
                    : 'bg-slate-900/50 border-slate-850 text-slate-400 hover:text-slate-200'
                }`}
                title="Eraser"
              >
                <Eraser className="h-3.5 w-3.5" />
              </button>

              {/* Undo Tool */}
              <button
                type="button"
                onClick={handleUndo}
                disabled={!canUndo}
                className="p-2 rounded-lg border border-slate-850 bg-slate-900/50 text-slate-400 hover:text-slate-200 disabled:opacity-40 disabled:hover:text-slate-400 transition"
                title="Undo Stroke"
              >
                <Undo className="h-3.5 w-3.5" />
              </button>

              {/* Clear Canvas */}
              <button
                type="button"
                onClick={clearCanvas}
                className="p-2 rounded-lg border border-slate-850 bg-slate-900/50 text-rose-500 hover:bg-rose-500/10 transition"
                title="Clear Mask"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>

              {/* Fullscreen Expand Tool */}
              <button
                type="button"
                onClick={() => setIsFullscreenModal(!isFullscreenModal)}
                className={`p-2 rounded-lg border transition ${
                  isFullscreenModal
                    ? 'bg-violet-600 border-violet-500 text-white'
                    : 'bg-slate-900/50 border-slate-850 text-violet-400 hover:bg-violet-500/10'
                }`}
                title={isFullscreenModal ? 'Thu nhỏ giao diện' : 'Phóng to toàn màn hình để tô chi tiết'}
              >
                {isFullscreenModal ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              </button>
            </>
          )}
        </div>

        {/* Brush Size Slider */}
        {imagePath && (
          <div className="flex items-center space-x-3 text-xs">
            <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
              Brush Size: <span className="text-violet-400">{brushSize}px</span>
            </span>
            <input
              type="range"
              min="5"
              max={isFullscreenModal ? '120' : '80'}
              step="1"
              value={brushSize}
              onChange={(e) => setBrushSize(parseInt(e.target.value))}
              className="accent-violet-500 h-1 w-28 bg-slate-800 rounded-lg cursor-pointer"
            />
          </div>
        )}
      </div>

      {/* ─── Canvas Workspace Container ─── */}
      <div
        className={`relative aspect-square w-full rounded-xl border border-slate-900 bg-slate-950 flex items-center justify-center overflow-hidden shadow-inner transition-all duration-300 ${
          isFullscreenModal
            ? 'max-h-[76vh] max-w-[76vh] border-violet-500/40 shadow-2xl shadow-violet-500/10'
            : 'max-h-[520px] max-w-[520px]'
        }`}
      >
        {imagePath ? (
          <div className="relative w-full h-full">
            {/* Base Image under the drawing canvas */}
            <img
              src={imageSrc || ''}
              alt="Base for inpaint"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none select-none"
            />

            {/* Drawing Layer */}
            <canvas
              ref={canvasRef}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              className="absolute inset-0 w-full h-full object-contain cursor-crosshair z-10 opacity-80"
            />
          </div>
        ) : (
          <div className="text-center p-6 space-y-2">
            <div className="mx-auto h-12 w-12 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-center">
              <Upload className="h-6 w-6 text-slate-600" />
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                No Image Loaded
              </h4>
              <p className="text-[11px] text-slate-500 max-w-xs leading-normal">
                Choose a base image to start drawing a mask zone for inpainting generation.
              </p>
            </div>
          </div>
        )}
      </div>

      {imagePath && (
        <div className="flex items-center justify-between w-full text-[10px] text-slate-400">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold uppercase tracking-wider bg-emerald-500/5 px-3 py-1 rounded-full border border-emerald-500/10">
            <CheckCircle2 className="h-3 w-3" />
            <span>Mask Layer Connected & Ready</span>
          </div>
          {isFullscreenModal && (
            <span className="text-slate-500 italic">Nhấn ESC hoặc nút Thu nhỏ để quay lại giao diện chính</span>
          )}
        </div>
      )}
    </div>
  )

  if (isFullscreenModal) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-2xl flex flex-col items-center justify-between p-8 animate-in fade-in duration-200 overflow-hidden">
        {/* Top Fullscreen Header */}
        <div className="w-full max-w-5xl flex items-center justify-between border-b border-slate-900 pb-3 mb-2">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-violet-600/20 border border-violet-500/30 text-violet-400">
              <Maximize2 className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                BẢNG VẼ MẶT NẠ CHUYÊN SÂU (FULLSCREEN INPAINT EDITOR)
              </h3>
              <p className="text-[11px] text-slate-500">
                Khung vẽ mở rộng hỗ trợ tô chi tiết cho ảnh nét cao. Nhấn ESC để đóng.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsFullscreenModal(false)}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="h-4 w-4 text-rose-400" />
            <span>Đóng / Hoàn tất</span>
          </button>
        </div>

        {/* Content */}
        <div className="w-full max-w-5xl flex-1 flex items-center justify-center overflow-hidden">
          {content}
        </div>
      </div>
    )
  }

  return content
}
