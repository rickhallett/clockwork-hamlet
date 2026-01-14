import { useState, useEffect, useCallback, useRef } from 'react'

export interface VillageEvent {
  id: string
  type: 'movement' | 'dialogue' | 'action' | 'relationship' | 'goal' | 'system'
  summary: string
  timestamp: string
  agent_id?: string
  agent_name?: string
  location_id?: string
  location_name?: string
  details?: Record<string, unknown>
  significance: 1 | 2 | 3
}

interface StreamFilters {
  types?: string[]
  agent?: string
  location?: string
}

interface UseVillageStreamOptions {
  filters?: StreamFilters
  maxEvents?: number
  autoConnect?: boolean
}

interface UseVillageStreamReturn {
  events: VillageEvent[]
  isConnected: boolean
  isPaused: boolean
  error: string | null
  pause: () => void
  resume: () => void
  clearEvents: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useVillageStream(options: UseVillageStreamOptions = {}): UseVillageStreamReturn {
  const { filters = {}, maxEvents = 100, autoConnect = true } = options

  const [events, setEvents] = useState<VillageEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const pausedEventsRef = useRef<VillageEvent[]>([])

  const buildStreamUrl = useCallback(() => {
    const params = new URLSearchParams()

    if (filters.types && filters.types.length > 0) {
      params.set('types', filters.types.join(','))
    }
    if (filters.agent) {
      params.set('agent', filters.agent)
    }
    if (filters.location) {
      params.set('location', filters.location)
    }

    const queryString = params.toString()
    return `${API_URL}/api/stream${queryString ? `?${queryString}` : ''}`
  }, [filters])

  const addEvent = useCallback((event: VillageEvent) => {
    if (isPaused) {
      pausedEventsRef.current.push(event)
    } else {
      setEvents((prev) => {
        const newEvents = [event, ...prev]
        return newEvents.slice(0, maxEvents)
      })
    }
  }, [isPaused, maxEvents])

  const pause = useCallback(() => {
    setIsPaused(true)
    pausedEventsRef.current = []
  }, [])

  const resume = useCallback(() => {
    setIsPaused(false)
    // Add any events that came in while paused
    if (pausedEventsRef.current.length > 0) {
      setEvents((prev) => {
        const newEvents = [...pausedEventsRef.current.reverse(), ...prev]
        return newEvents.slice(0, maxEvents)
      })
      pausedEventsRef.current = []
    }
  }, [maxEvents])

  const clearEvents = useCallback(() => {
    setEvents([])
    pausedEventsRef.current = []
  }, [])

  useEffect(() => {
    if (!autoConnect) return

    const url = buildStreamUrl()

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

          // Transform backend format to frontend format
          // Backend sends: actors (string[]), timestamp (int), detail (string)
          // Frontend expects: agent_id, agent_name, timestamp (ISO string), details
          const primaryAgent = data.actors?.[0] || data.agent_id
          const timestamp = typeof data.timestamp === 'number'
            ? new Date(data.timestamp * 1000).toISOString()
            : data.timestamp || new Date().toISOString()

          const event: VillageEvent = {
            id: data.id || crypto.randomUUID(),
            type: data.type || 'system',
            summary: data.summary || data.description || 'Unknown event',
            timestamp,
            agent_id: primaryAgent,
            agent_name: data.agent_name || primaryAgent,
            location_id: data.location_id,
            location_name: data.location_name || data.location_id,
            details: data.details || (data.detail ? { detail: data.detail } : data.data),
            significance: (data.significance >= 1 && data.significance <= 3 ? data.significance : 1) as 1 | 2 | 3,
          }

          addEvent(event)
        } catch (err) {
          console.error('Failed to parse SSE event:', err)
        }
      }

      eventSource.onerror = () => {
        setIsConnected(false)
        setError('Connection lost. Reconnecting...')
        eventSource.close()

        // Reconnect after a delay
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
  }, [autoConnect, buildStreamUrl, addEvent])

  return {
    events,
    isConnected,
    isPaused,
    error,
    pause,
    resume,
    clearEvents,
  }
}
