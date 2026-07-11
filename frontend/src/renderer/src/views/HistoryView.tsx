import React, { useEffect, useState } from 'react'
import { useGenerationStore, GenerationRecord } from '../stores/useGenerationStore'
import { Image as ImageIcon, Calendar, Clock, Compass, Layers } from 'lucide-react'

export function HistoryView(): React.JSX.Element {
  const history = useGenerationStore((state) => state.history)
  const setHistory = useGenerationStore((state) => state.setHistory)
  const [selectedRecord, setSelectedRecord] = useState<GenerationRecord | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    const fetchHistory = async (): Promise<void> => {
      setLoading(true)
      try {
        const response = await fetch(
          'http://127.0.0.1:8000/api/v1/generations/history?limit=50&offset=0'
        )
        if (response.ok && active) {
          const data = await response.json()
          setHistory(data)
        }
      } catch (err) {
        console.error('Failed to load generation logs history:', err)
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }
    fetchHistory()
    return () => {
      active = false
    }
  }, [setHistory])

  return (
    <div className="h-full w-full flex overflow-hidden">
      {/* ─── Gallery Grid list ─── */}
      <div className="flex-1 p-8 overflow-y-auto space-y-6">
        <div className="flex justify-between items-center border-b border-slate-900 pb-4">
          <h2 className="text-sm font-semibold tracking-wide text-slate-200 uppercase">
            LOCAL GALLERY HISTORY
          </h2>
          <span className="text-xs text-slate-400 font-semibold">
            {history.length} generated images
          </span>
        </div>

        {loading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="flex flex-col items-center space-y-2">
              <span className="h-5 w-5 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
              <span className="text-xs font-semibold text-slate-500">
                Loading gallery records...
              </span>
            </div>
          </div>
        ) : history.length === 0 ? (
          <div className="h-64 border border-dashed border-slate-800 rounded-2xl flex flex-col items-center justify-center text-center p-6">
            <ImageIcon className="h-8 w-8 text-slate-700 mb-2" />
            <h4 className="text-sm font-semibold text-slate-400">No images found</h4>
            <p className="text-xs text-slate-500 max-w-xs leading-normal">
              You haven&apos;t generated any images locally yet. Visit the Generate View to get
              started!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {history.map((record) => {
              // Get first generated image from record
              const img = record.images[0]
              if (!img) return null
              // Backend outputs directory is served static at http://localhost:8000/outputs/
              // The image.path saved in db is e.g. "txt2img/img_xxxx.png"
              // So URL is http://localhost:8000/outputs/txt2img/img_xxxx.png
              // Let's normalize backslashes for URL formatting
              const staticPath = img.path.replace(/\\/g, '/')
              const thumbnailPath = img.thumbnail_path
                ? img.thumbnail_path.replace(/\\/g, '/')
                : staticPath
              const thumbnailUrl = `http://127.0.0.1:8000/outputs/${thumbnailPath}`

              return (
                <div
                  key={record.id}
                  onClick={() => setSelectedRecord(record)}
                  className="group relative aspect-square rounded-xl border border-slate-900 bg-slate-900/10 overflow-hidden cursor-pointer shadow-lg hover:border-slate-700 transition-all duration-300"
                >
                  <img
                    src={thumbnailUrl}
                    alt={record.params.prompt}
                    className="h-full w-full object-cover group-hover:scale-105 transition duration-500"
                  />
                  {/* Subtle info overlay */}
                  <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-all duration-300 flex flex-col justify-end p-4 space-y-1">
                    <p className="text-xs font-semibold text-slate-200 line-clamp-2">
                      {record.params.prompt}
                    </p>
                    <span className="text-[9px] font-bold text-violet-400 uppercase">
                      {record.params.sampler} • {record.params.steps} steps
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ─── Right Details Inspection Panel ─── */}
      {selectedRecord && (
        <div className="w-80 border-l border-slate-900 bg-slate-950 p-6 overflow-y-auto space-y-6 flex-shrink-0 flex flex-col justify-between h-full">
          <div className="space-y-6">
            <div className="flex justify-between items-center border-b border-slate-900 pb-4">
              <h3 className="text-xs font-semibold text-slate-400 tracking-wider">
                IMAGE METADATA
              </h3>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-slate-500 hover:text-slate-300 text-xs font-bold"
              >
                Close
              </button>
            </div>

            {/* Inspect preview */}
            <div className="aspect-square rounded-xl overflow-hidden border border-slate-800 bg-slate-900/20 shadow-inner">
              <img
                src={`http://127.0.0.1:8000/outputs/${selectedRecord.images[0]?.path.replace(/\\/g, '/')}`}
                alt="Selected generation"
                className="h-full w-full object-cover cursor-zoom-in"
                onClick={() =>
                  window.open(
                    `http://127.0.0.1:8000/outputs/${selectedRecord.images[0]?.path.replace(/\\/g, '/')}`
                  )
                }
              />
            </div>

            {/* Info Metrics List */}
            <div className="space-y-4 text-xs font-medium">
              {/* Prompt */}
              <div className="space-y-1.5 bg-slate-900/30 border border-slate-900/60 p-3.5 rounded-xl leading-relaxed text-slate-300">
                <span className="text-[10px] font-bold text-slate-500 flex items-center">
                  <Compass className="h-3.5 w-3.5 mr-1.5 text-violet-400" /> PROMPT
                </span>
                <p className="font-semibold text-slate-200">{selectedRecord.params.prompt}</p>
              </div>

              {/* Negative Prompt */}
              {selectedRecord.params.negative_prompt && (
                <div className="space-y-1.5 bg-slate-900/30 border border-slate-900/60 p-3.5 rounded-xl text-slate-400">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">
                    Negative Prompt
                  </span>
                  <p>{selectedRecord.params.negative_prompt}</p>
                </div>
              )}

              {/* Parameters Table Grid */}
              <div className="grid grid-cols-2 gap-3.5 pt-2">
                <div className="space-y-1 bg-slate-900/20 p-2.5 rounded-xl border border-slate-900/40">
                  <span className="text-[9px] font-bold text-slate-500 uppercase flex items-center">
                    <Layers className="h-3 w-3 mr-1" /> Resolution
                  </span>
                  <span className="font-semibold text-slate-300">
                    {selectedRecord.params.width} x {selectedRecord.params.height}
                  </span>
                </div>
                <div className="space-y-1 bg-slate-900/20 p-2.5 rounded-xl border border-slate-900/40">
                  <span className="text-[9px] font-bold text-slate-500 uppercase flex items-center">
                    <Clock className="h-3 w-3 mr-1" /> Duration
                  </span>
                  <span className="font-semibold text-slate-300">
                    {selectedRecord.duration_ms
                      ? `${(selectedRecord.duration_ms / 1000).toFixed(1)}s`
                      : 'N/A'}
                  </span>
                </div>
                <div className="space-y-1 bg-slate-900/20 p-2.5 rounded-xl border border-slate-900/40">
                  <span className="text-[9px] font-bold text-slate-500 uppercase">Steps</span>
                  <span className="font-semibold text-slate-300">
                    {selectedRecord.params.steps}
                  </span>
                </div>
                <div className="space-y-1 bg-slate-900/20 p-2.5 rounded-xl border border-slate-900/40">
                  <span className="text-[9px] font-bold text-slate-500 uppercase">CFG Scale</span>
                  <span className="font-semibold text-slate-300">
                    {selectedRecord.params.cfg_scale}
                  </span>
                </div>
                <div className="space-y-1 bg-slate-900/20 p-2.5 rounded-xl border border-slate-900/40">
                  <span className="text-[9px] font-bold text-slate-500 uppercase">Sampler</span>
                  <span className="font-semibold text-slate-300 truncate block">
                    {selectedRecord.params.sampler}
                  </span>
                </div>
                <div className="space-y-1 bg-slate-900/20 p-2.5 rounded-xl border border-slate-900/40">
                  <span className="text-[9px] font-bold text-slate-500 uppercase">Seed</span>
                  <span className="font-semibold text-slate-300 select-all">
                    {selectedRecord.params.seed}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-900 flex items-center justify-between text-[10px] text-slate-500">
            <span className="flex items-center">
              <Calendar className="h-3 w-3 mr-1" />{' '}
              {new Date(selectedRecord.created_at).toLocaleDateString()}
            </span>
            <span>ID: {selectedRecord.id.substring(0, 8)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
