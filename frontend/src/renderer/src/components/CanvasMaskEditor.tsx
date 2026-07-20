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
  X,
  RotateCcw
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

  // Natural image dimensions (e.g. 3840x2160)
  const [naturalSize, setNaturalSize] = useState<{ width: number; height: number }>({
    width: 512,
    height: 512
  })

  // Fullscreen Pan & Zoom state
  const [zoom, setZoom] = useState<number>(1.0)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState<boolean>(false)
  const [isSpacePressed, setIsSpacePressed] = useState<boolean>(false)
  const panStartRef = useRef<{ x: number; y: number; panX: number; panY: number }>({
    x: 0,
    y: 0,
    panX: 0,
    panY: 0
  })

  const containerRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const isDrawingRef = useRef<boolean>(false)
  const lastPosRef = useRef<{ x: number; y: number } | null>(null)
  const historyRef = useRef<string[]>([]) // Store base64 snapshots for undo
  const [canUndo, setCanUndo] = useState(false)

  // Listen for ESC key to close Fullscreen Mode & Spacebar for pan drag
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape' && isFullscreenModal) {
        setIsFullscreenModal(false)
      }
      if (e.code === 'Space' && !e.repeat && isFullscreenModal) {
        setIsSpacePressed(true)
      }
    }

    const handleKeyUp = (e: KeyboardEvent): void => {
      if (e.code === 'Space' && isFullscreenModal) {
        setIsSpacePressed(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [isFullscreenModal])

  // Reset zoom & pan when exiting fullscreen or changing image
  useEffect(() => {
    if (!isFullscreenModal) {
      setZoom(1.0)
      setPan({ x: 0, y: 0 })
    }
  }, [isFullscreenModal, imagePath])

  // Calculate 100% exact canvas pixel coordinates (0 to naturalSize.width/height)
  const getCanvasCoordinates = useCallback(
    (clientX: number, clientY: number): { x: number; y: number } | null => {
      const container = containerRef.current
      if (!container || naturalSize.width === 0 || naturalSize.height === 0) return null

      const rect = container.getBoundingClientRect()
      const containerW = rect.width
      const containerH = rect.height
      if (containerW === 0 || containerH === 0) return null

      // Object-contain scale factor inside container
      const baseScale = Math.min(containerW / naturalSize.width, containerH / naturalSize.height)
      const currentZoom = isFullscreenModal ? zoom : 1.0
      const currentPan = isFullscreenModal ? pan : { x: 0, y: 0 }
      const effectiveScale = baseScale * currentZoom

      // Center of container
      const containerCenterX = containerW / 2
      const containerCenterY = containerH / 2

      // Displayed image center (with pan offset)
      const imageCenterX = containerCenterX + currentPan.x
      const imageCenterY = containerCenterY + currentPan.y

      // Top-left of rendered image inside container
      const imageLeft = imageCenterX - (naturalSize.width * effectiveScale) / 2
      const imageTop = imageCenterY - (naturalSize.height * effectiveScale) / 2

      // Mouse relative to container top-left
      const mouseX = clientX - rect.left
      const mouseY = clientY - rect.top

      // Map to actual canvas pixel (0 to naturalSize.width, 0 to naturalSize.height)
      const canvasX = (mouseX - imageLeft) / effectiveScale
      const canvasY = (mouseY - imageTop) / effectiveScale

      return { x: canvasX, y: canvasY }
    },
    [naturalSize, zoom, pan, isFullscreenModal]
  )

  // Trigger mask export
  const exportMask = useCallback((): void => {
    const canvas = canvasRef.current
    if (!canvas || !imagePath) return

    const exportW = naturalSize.width > 0 ? naturalSize.width : width
    const exportH = naturalSize.height > 0 ? naturalSize.height : height

    const exportCanvas = document.createElement('canvas')
    exportCanvas.width = exportW
    exportCanvas.height = exportH
    const exportCtx = exportCanvas.getContext('2d')

    if (exportCtx) {
      exportCtx.fillStyle = 'black'
      exportCtx.fillRect(0, 0, exportW, exportH)
      exportCtx.drawImage(canvas, 0, 0, exportW, exportH)

      const imgData = exportCtx.getImageData(0, 0, exportW, exportH)
      const data = imgData.data
      for (let i = 0; i < data.length; i += 4) {
        const alpha = data[i + 3]
        if (alpha > 10) {
          data[i] = 255
          data[i + 1] = 255
          data[i + 2] = 255
          data[i + 3] = 255
        } else {
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
  }, [imagePath, width, height, naturalSize, onMaskChange])

  // Handle select image click
  const handleSelectImage = async (): Promise<void> => {
    try {
      const selected = await window.api.selectImage()
      if (selected) {
        onImageSelected(selected)
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

  // Convert local imagePath to base64 data URL via IPC & set natural resolution
  useEffect(() => {
    if (imagePath) {
      window.api.readImageBase64(imagePath).then((base64) => {
        setImageSrc(base64)
        if (base64) {
          const img = new Image()
          img.onload = (): void => {
            const nw = img.naturalWidth || 512
            const nh = img.naturalHeight || 512
            setNaturalSize({ width: nw, height: nh })

            const canvas = canvasRef.current
            if (canvas) {
              canvas.width = nw
              canvas.height = nh
              const ctx = canvas.getContext('2d')
              if (ctx) {
                ctx.lineCap = 'round'
                ctx.lineJoin = 'round'
              }
              saveHistory()
            }
          }
          img.src = base64
        }
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

  // Mouse wheel zoom centered at crosshair cursor location
  const handleWheel = (e: React.WheelEvent<HTMLDivElement>): void => {
    if (!isFullscreenModal) return
    e.preventDefault()
    const container = containerRef.current
    if (!container) return
    const rect = container.getBoundingClientRect()

    // Cursor position relative to container center
    const mouseX = e.clientX - rect.left - rect.width / 2
    const mouseY = e.clientY - rect.top - rect.height / 2

    const zoomFactor = e.deltaY < 0 ? 1.2 : 0.833
    const newZoom = Math.min(Math.max(zoom * zoomFactor, 0.5), 10.0)

    if (newZoom === zoom) return

    // Keep point under crosshairs stationary while zooming
    const scaleRatio = newZoom / zoom
    const newPanX = mouseX - (mouseX - pan.x) * scaleRatio
    const newPanY = mouseY - (mouseY - pan.y) * scaleRatio

    setZoom(newZoom)
    setPan({ x: newPanX, y: newPanY })
  }

  // Mouse Down for drawing or pan dragging
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>): void => {
    // Right click (2) or middle click (1) or holding Space key triggers pan drag
    if (e.button === 2 || e.button === 1 || isSpacePressed) {
      setIsPanning(true)
      panStartRef.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y }
      return
    }

    if (e.button !== 0) return // Only left click draws

    const canvas = canvasRef.current
    if (!canvas) return
    const coords = getCanvasCoordinates(e.clientX, e.clientY)
    if (!coords) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.beginPath()
    ctx.moveTo(coords.x, coords.y)
    lastPosRef.current = { x: coords.x, y: coords.y }
    isDrawingRef.current = true

    // Scaled brush size relative to natural image resolution
    const scaleFactor = naturalSize.width > 0 ? naturalSize.width / 1000 : 1.0
    const effectiveBrushSize = Math.max(2, brushSize * scaleFactor)

    ctx.lineWidth = effectiveBrushSize
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    if (tool === 'eraser') {
      ctx.globalCompositeOperation = 'destination-out'
    } else {
      ctx.globalCompositeOperation = 'source-over'
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.65)' // semi-transparent red stroke
    }

    ctx.lineTo(coords.x, coords.y)
    ctx.stroke()
  }

  // Mouse Move for drawing or pan dragging
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>): void => {
    if (isPanning) {
      const dx = e.clientX - panStartRef.current.x
      const dy = e.clientY - panStartRef.current.y
      setPan({
        x: panStartRef.current.panX + dx,
        y: panStartRef.current.panY + dy
      })
      return
    }

    if (!isDrawingRef.current) return
    const canvas = canvasRef.current
    if (!canvas) return
    const coords = getCanvasCoordinates(e.clientX, e.clientY)
    if (!coords) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    if (lastPosRef.current) {
      ctx.beginPath()
      ctx.moveTo(lastPosRef.current.x, lastPosRef.current.y)
      ctx.lineTo(coords.x, coords.y)
      ctx.stroke()
    }
    lastPosRef.current = { x: coords.x, y: coords.y }
  }

  // Mouse Up / Leave
  const handleMouseUp = (): void => {
    if (isPanning) {
      setIsPanning(false)
      return
    }

    if (isDrawingRef.current) {
      isDrawingRef.current = false
      lastPosRef.current = null
      saveHistory()
      exportMask()
    }
  }

  const content = (
    <div
      className={`flex flex-col space-y-3 w-full items-center ${
        isFullscreenModal ? 'h-full justify-between' : ''
      }`}
    >
      {/* ─── Toolbar Row ─── */}
      <div className="flex items-center justify-between w-full bg-slate-950 border border-slate-900 rounded-xl p-3 flex-wrap gap-3 shrink-0">
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

        {/* Zoom Controls & Brush Size Slider */}
        {imagePath && (
          <div className="flex items-center space-x-4 text-xs">
            {isFullscreenModal && (
              <div className="flex items-center space-x-2 bg-slate-900 border border-slate-850 rounded-lg px-2.5 py-1 text-[11px]">
                <span className="text-slate-400">Zoom:</span>
                <span className="font-mono text-violet-400 font-bold">{Math.round(zoom * 100)}%</span>
                {zoom !== 1.0 && (
                  <button
                    type="button"
                    onClick={() => {
                      setZoom(1.0)
                      setPan({ x: 0, y: 0 })
                    }}
                    className="text-[10px] text-slate-400 hover:text-slate-200 transition ml-1"
                    title="Reset Zoom & Pan"
                  >
                    <RotateCcw className="h-3 w-3" />
                  </button>
                )}
              </div>
            )}

            <div className="flex items-center space-x-2">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">
                Brush: <span className="text-violet-400">{brushSize}px</span>
              </span>
              <input
                type="range"
                min="2"
                max={isFullscreenModal ? '120' : '80'}
                step="1"
                value={brushSize}
                onChange={(e) => setBrushSize(parseInt(e.target.value))}
                className="accent-violet-500 h-1 w-24 sm:w-28 bg-slate-800 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>

      {/* ─── Canvas Workspace Container ─── */}
      <div
        ref={containerRef}
        onWheel={handleWheel}
        className={`relative w-full rounded-xl border border-slate-900 bg-slate-950 flex items-center justify-center overflow-hidden shadow-inner transition-all duration-300 ${
          isFullscreenModal
            ? 'w-full h-full max-h-[82vh] border-violet-500/40 shadow-2xl shadow-violet-500/10 cursor-crosshair'
            : 'max-w-[720px] h-[360px] sm:h-[400px]'
        }`}
      >
        {imagePath ? (
          <div
            className="relative w-full h-full flex items-center justify-center pointer-events-auto"
            style={{
              transform: isFullscreenModal ? `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` : 'none',
              transformOrigin: 'center center',
              transition: isPanning ? 'none' : 'transform 0.05s ease-out'
            }}
            onContextMenu={(e) => e.preventDefault()}
          >
            {/* Base Image under the drawing canvas */}
            <img
              src={imageSrc || ''}
              alt="Base for inpaint"
              className="absolute inset-0 w-full h-full object-contain pointer-events-none select-none"
            />

            {/* Drawing Layer */}
            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="absolute inset-0 w-full h-full object-contain cursor-crosshair z-10 opacity-85"
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
        <div className="flex items-center justify-between w-full text-[10px] text-slate-400 shrink-0">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold uppercase tracking-wider bg-emerald-500/5 px-3 py-1 rounded-full border border-emerald-500/10">
            <CheckCircle2 className="h-3 w-3" />
            <span>
              Mask Layer Ready ({naturalSize.width} × {naturalSize.height} px)
            </span>
          </div>
          {isFullscreenModal && (
            <span className="text-slate-500 italic">
              💡 Lăn chuột để Zoom theo tâm cọ | Giữ chuột phải hoặc phím Space để kéo ảnh | Nhấn ESC để đóng
            </span>
          )}
        </div>
      )}
    </div>
  )

  if (isFullscreenModal) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-2xl flex flex-col items-center justify-between p-6 animate-in fade-in duration-200 overflow-hidden">
        {/* Top Fullscreen Header */}
        <div className="w-full max-w-6xl flex items-center justify-between border-b border-slate-900 pb-3 mb-2 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-violet-600/20 border border-violet-500/30 text-violet-400">
              <Maximize2 className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                BẢNG VẼ MẶT NẠ TOÀN MÀN HÌNH (PIXEL-PERFECT INPAINT STUDIO)
              </h3>
              <p className="text-[11px] text-slate-500">
                Độ phân giải thực: {naturalSize.width} × {naturalSize.height} px | Cuộn chuột để Zoom theo tâm cọ
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setIsFullscreenModal(false)}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="h-4 w-4 text-rose-400" />
            <span>Đóng / Hoàn tất (ESC)</span>
          </button>
        </div>

        {/* Content Container */}
        <div className="w-full max-w-6xl flex-1 flex items-center justify-center overflow-hidden">
          {content}
        </div>
      </div>
    )
  }

  return content
}
