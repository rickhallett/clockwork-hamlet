/**
 * Dashboard hook for real-time monitoring (DASH-11 through DASH-15)
 *
 * Provides:
 * - DASH-12: Real-time agent positions via SSE
 * - DASH-13: Live LLM cost tracking
 * - DASH-14: Simulation health indicators
 * - DASH-15: Event rate data for sparklines
 */

import { useState, useEffect, useCallback, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Types
export interface AgentPosition {
  id: string
  name: string
  location_id: string
  state: string
}

export interface HealthMetrics {
  uptime_seconds: number
  total_ticks: number
  ticks_per_minute: number
  error_count: number
  last_tick_duration_ms: number
  avg_tick_duration_ms: number
  agents_processed: number
  queue_depth: number
}

export interface LLMStats {
  total_calls: number
  cached_calls: number
  api_calls: number
  tokens_in: number
  tokens_out: number
  total_tokens: number
  total_cost_usd: number
  total_cost_display: string
  avg_latency_ms: number
}

export interface EventRates {
  events_per_bucket: number[]
  by_type: Record<string, number[]>
  bucket_size_minutes: number
  total_buckets: number
  total_events: number
  current_rate: number
  peak_rate: number
  avg_rate: number
}

interface UseDashboardReturn {
  // DASH-12: Agent positions
  positions: AgentPosition[]
  positionsByLocation: Record<string, AgentPosition[]>

  // DASH-13: LLM costs
  llmStats: LLMStats | null
  sessionCost: string

  // DASH-14: Health
  health: HealthMetrics | null
  healthStatus: 'healthy' | 'degraded' | 'unknown'

  // DASH-15: Event rates
  eventRates: EventRates | null

  // Connection state
  isConnected: boolean
  error: string | null

  // Actions
  refetch: () => Promise<void>
}

export function useDashboard(): UseDashboardReturn {
  // State
  const [positions, setPositions] = useState<AgentPosition[]>([])
  const [positionsByLocation, setPositionsByLocation] = useState<Record<string, AgentPosition[]>>({})
  const [llmStats, setLlmStats] = useState<LLMStats | null>(null)
  const [sessionCost, setSessionCost] = useState('$0.0000')
  const [health, setHealth] = useState<HealthMetrics | null>(null)
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'degraded' | 'unknown'>('unknown')
  const [eventRates, setEventRates] = useState<EventRates | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)

  // Update positions by location
  const updatePositionsByLocation = useCallback((newPositions: AgentPosition[]) => {
    const byLoc: Record<string, AgentPosition[]> = {}
    for (const pos of newPositions) {
      const locId = pos.location_id || 'unknown'
      if (!byLoc[locId]) byLoc[locId] = []
      byLoc[locId].push(pos)
    }
    setPositionsByLocation(byLoc)
  }, [])

  // Fetch initial data and event rates
  const fetchData = useCallback(async () => {
    try {
      // Fetch dashboard summary for initial state
      const summaryRes = await fetch(`${API_URL}/api/dashboard/summary`)
      if (summaryRes.ok) {
        const summary = await summaryRes.json()

        // Update positions
        if (summary.positions) {
          setPositions(summary.positions)
          updatePositionsByLocation(summary.positions)
        }

        // Update health
        if (summary.health) {
          setHealth(summary.health.metrics)
          setHealthStatus(summary.health.status)
        }
      }

      // Fetch LLM stats
      const llmRes = await fetch(`${API_URL}/api/llm/stats`)
      if (llmRes.ok) {
        const llm = await llmRes.json()
        if (llm.session) {
          setLlmStats(llm.session)
          setSessionCost(llm.session.total_cost_display || '$0.0000')
        }
      }

      // Fetch event rates for sparklines
      const ratesRes = await fetch(`${API_URL}/api/dashboard/event-rates?minutes=60&bucket_size=1`)
      if (ratesRes.ok) {
        const rates = await ratesRes.json()
        setEventRates(rates)
      }

      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data')
    }
  }, [updatePositionsByLocation])

  // Connect to SSE for real-time updates
  useEffect(() => {
    // Initial fetch
    fetchData()

    // SSE connection for positions, health, and LLM updates
    const url = `${API_URL}/api/stream?types=positions,health,llm_usage`

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

          // Skip heartbeats
          if (data.type === 'heartbeat') return

          // DASH-12: Position updates
          if (data.type === 'positions' && data.data?.positions) {
            setPositions(data.data.positions)
            updatePositionsByLocation(data.data.positions)
          }

          // DASH-14: Health updates
          if (data.type === 'health' && data.data) {
            setHealth(data.data)
            setHealthStatus(data.data.error_count === 0 ? 'healthy' : 'degraded')
          }

          // DASH-13: LLM usage updates
          if (data.type === 'llm_usage' && data.data?.totals) {
            setLlmStats(data.data.totals)
            setSessionCost(data.data.totals.total_cost_display || '$0.0000')
          }
        } catch (err) {
          console.error('Failed to parse SSE event:', err)
        }
      }

      eventSource.onerror = () => {
        setIsConnected(false)
        setError('Connection lost. Reconnecting...')
        eventSource.close()

        // Reconnect after delay
        setTimeout(() => {
          if (eventSourceRef.current === eventSource) {
            connect()
          }
        }, 3000)
      }
    }

    connect()

    // Refresh event rates periodically (every 30 seconds)
    const ratesInterval = setInterval(async () => {
      try {
        const ratesRes = await fetch(`${API_URL}/api/dashboard/event-rates?minutes=60&bucket_size=1`)
        if (ratesRes.ok) {
          const rates = await ratesRes.json()
          setEventRates(rates)
        }
      } catch {
        // Ignore periodic fetch errors
      }
    }, 30000)

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      clearInterval(ratesInterval)
    }
  }, [fetchData, updatePositionsByLocation])

  return {
    positions,
    positionsByLocation,
    llmStats,
    sessionCost,
    health,
    healthStatus,
    eventRates,
    isConnected,
    error,
    refetch: fetchData,
  }
}
