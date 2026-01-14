import { useState, useEffect, useCallback, useRef } from 'react'

export interface EventRatePoint {
  timestamp: number
  count: number
  byType: Record<string, number>
}

interface UseEventRateTrackerReturn {
  rateHistory: EventRatePoint[]
  currentRate: number // events per minute
  rateByType: Record<string, number>
  isConnected: boolean
  error: string | null
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// How many time buckets to keep (each bucket is 10 seconds)
const MAX_BUCKETS = 30 // 5 minutes of history
const BUCKET_SIZE_MS = 10000 // 10 seconds per bucket

/**
 * Hook for tracking event rates over time.
 * Aggregates events into time buckets for sparkline visualization.
 *
 * Implements DASH-16: Event rate sparklines
 */
export function useEventRateTracker(): UseEventRateTrackerReturn {
  const [rateHistory, setRateHistory] = useState<EventRatePoint[]>([])
  const [currentRate, setCurrentRate] = useState(0)
  const [rateByType, setRateByType] = useState<Record<string, number>>({})
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const currentBucketRef = useRef<{ count: number; byType: Record<string, number> }>({
    count: 0,
    byType: {},
  })
  const bucketStartRef = useRef(Math.floor(Date.now() / BUCKET_SIZE_MS) * BUCKET_SIZE_MS)

  // Flush current bucket and start a new one
  const flushBucket = useCallback(() => {
    const now = Date.now()
    const currentBucketStart = Math.floor(now / BUCKET_SIZE_MS) * BUCKET_SIZE_MS

    // Only flush if we've moved to a new bucket
    if (currentBucketStart > bucketStartRef.current) {
      const bucket: EventRatePoint = {
        timestamp: bucketStartRef.current,
        count: currentBucketRef.current.count,
        byType: { ...currentBucketRef.current.byType },
      }

      setRateHistory((prev) => {
        const newHistory = [...prev, bucket].slice(-MAX_BUCKETS)

        // Calculate current rate (events per minute) from last 6 buckets (1 minute)
        const recentBuckets = newHistory.slice(-6)
        const totalEvents = recentBuckets.reduce((sum, b) => sum + b.count, 0)
        const minutes = (recentBuckets.length * BUCKET_SIZE_MS) / 60000
        const rate = minutes > 0 ? totalEvents / minutes : 0
        setCurrentRate(Math.round(rate * 10) / 10)

        // Calculate rate by type
        const typeRates: Record<string, number> = {}
        for (const b of recentBuckets) {
          for (const [type, count] of Object.entries(b.byType)) {
            typeRates[type] = (typeRates[type] || 0) + count
          }
        }
        // Convert to per-minute rates
        for (const type of Object.keys(typeRates)) {
          typeRates[type] = Math.round((typeRates[type] / minutes) * 10) / 10
        }
        setRateByType(typeRates)

        return newHistory
      })

      // Reset current bucket
      currentBucketRef.current = { count: 0, byType: {} }
      bucketStartRef.current = currentBucketStart
    }
  }, [])

  // Handle incoming event
  const handleEvent = useCallback((eventType: string) => {
    currentBucketRef.current.count += 1
    currentBucketRef.current.byType[eventType] =
      (currentBucketRef.current.byType[eventType] || 0) + 1
  }, [])

  // Periodic bucket flush
  useEffect(() => {
    const interval = setInterval(flushBucket, BUCKET_SIZE_MS)
    return () => clearInterval(interval)
  }, [flushBucket])

  // Connect to SSE stream
  useEffect(() => {
    const url = `${API_URL}/api/stream`

    const connect = () => {
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        setIsConnected(true)
        setError(null)
      }

      eventSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)

          // Skip heartbeat events
          if (data.type === 'heartbeat') return
          // Skip tick events (they're regular and would skew the rate)
          if (data.type === 'tick') return

          handleEvent(data.type)
        } catch (err) {
          console.error('Failed to parse SSE event:', err)
        }
      }

      eventSource.onerror = () => {
        setIsConnected(false)
        setError('Connection lost. Reconnecting...')
        eventSource.close()

        setTimeout(() => {
          if (eventSourceRef.current === eventSource) {
            connect()
          }
        }, 3000)
      }
    }

    connect()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [handleEvent])

  return {
    rateHistory,
    currentRate,
    rateByType,
    isConnected,
    error,
  }
}
