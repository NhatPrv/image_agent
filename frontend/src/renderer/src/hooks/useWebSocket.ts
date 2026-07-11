import { useEffect, useRef } from 'react'
import { useSystemStore } from '../stores/useSystemStore'
import { useGenerationStore } from '../stores/useGenerationStore'
import { useModelStore } from '../stores/useModelStore'
import { useQueueStore } from '../stores/useQueueStore'
import { useDownloadStore } from '../stores/useDownloadStore'

export function useWebSocket(): void {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null)

  const setConnected = useSystemStore((state) => state.setConnected)
  const setStats = useSystemStore((state) => state.setStats)

  const setGenerating = useGenerationStore((state) => state.setGenerating)
  const setProgress = useGenerationStore((state) => state.setProgress)
  const resetProgress = useGenerationStore((state) => state.resetProgress)
  const updateHistoryItem = useGenerationStore((state) => state.updateHistoryItem)

  const setActiveModel = useModelStore((state) => state.setActiveModel)
  const setLoadingModelId = useModelStore((state) => state.setLoadingModelId)
  const setLoadingProgress = useModelStore((state) => state.setLoadingProgress)
  const setLoadingError = useModelStore((state) => state.setLoadingError)

  const removeQueueItem = useQueueStore((state) => state.removeQueueItem)

  const addOrUpdateTask = useDownloadStore((state) => state.addOrUpdateTask)
  const updateTaskProgress = useDownloadStore((state) => state.updateTaskProgress)
  const updateTaskStatus = useDownloadStore((state) => state.updateTaskStatus)

  useEffect(() => {
    function connect(): void {
      if (ws.current) return

      console.log('Connecting to WebSocket api channel: ws://127.0.0.1:8000/ws')
      const socket = new WebSocket('ws://127.0.0.1:8000/ws')

      socket.onopen = () => {
        console.log('WebSocket channel connected.')
        setConnected(true)
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current)
          reconnectTimeout.current = null
        }
      }

      socket.onmessage = (event) => {
        try {
          const packet = JSON.parse(event.data)
          const { event: eventType, data } = packet

          switch (eventType) {
            case 'system.monitor':
              setStats(data)
              break

            case 'generation.started':
              setGenerating(true, data.generation_id)
              setProgress(0, 0, data.total_steps || 25, null)
              break

            case 'generation.progress':
              setProgress(
                data.progress_percentage || 0,
                data.step || 0,
                data.total_steps || 25,
                data.preview_base64 ? `data:image/jpeg;base64,${data.preview_base64}` : null
              )
              break

            case 'generation.completed':
              updateHistoryItem(data.generation_id, {
                status: 'completed',
                completed_at: data.completed_at,
                duration_ms: data.duration_ms,
                images: data.images
              })
              removeQueueItem(data.queue_item_id)
              resetProgress()
              break

            case 'generation.failed':
              updateHistoryItem(data.generation_id, {
                status: 'failed',
                error_message: data.error
              })
              removeQueueItem(data.queue_item_id)
              resetProgress()
              break

            case 'model.loading':
              setLoadingModelId(data.model_id)
              setLoadingProgress(data.progress || 0)
              break

            case 'model.loaded':
              setActiveModel(data.model_info)
              break

            case 'model.error':
              setLoadingError(data.error)
              break

            case 'model.unloaded':
              setActiveModel(null)
              break

            case 'download.started':
              addOrUpdateTask({
                task_id: data.task_id,
                url: data.url,
                filename: data.filename,
                component_type: 'checkpoint',
                bytes_downloaded: 0,
                bytes_total: 0,
                speed_mb: 0.0,
                eta_seconds: 0.0,
                status: 'pending',
                file_path: ''
              })
              break

            case 'download.progress':
              updateTaskProgress(
                data.task_id,
                data.bytes_downloaded,
                data.bytes_total,
                data.speed_mb,
                data.eta_seconds
              )
              break

            case 'download.completed':
              updateTaskStatus(data.task_id, 'completed')
              break

            case 'download.failed':
              updateTaskStatus(data.task_id, 'failed', data.error_message)
              break

            default:
              // Custom unhandled event
              break
          }
        } catch (err) {
          console.error('Failed to parse websocket message packet:', err)
        }
      }

      socket.onclose = () => {
        console.log('WebSocket channel disconnected. Reconnecting in 3s...')
        setConnected(false)
        ws.current = null
        reconnectTimeout.current = setTimeout(() => {
          connect()
        }, 3000)
      }

      socket.onerror = (err) => {
        console.error('WebSocket connection error:', err)
        socket.close()
      }

      ws.current = socket
    }

    connect()

    return () => {
      if (ws.current) {
        ws.current.close()
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}
