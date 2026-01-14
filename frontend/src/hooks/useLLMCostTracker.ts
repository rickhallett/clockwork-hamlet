import { useState, useEffect, useCallback, useRef } from 'react'

export interface LLMCall {
  model: string
  tokens_in: number
  tokens_out: number
  cost_usd: number
  latency_ms: number
  cached: boolean
  agent_id: string | null
  timestamp: number
}

export interface LLMTotals {
  total_calls: number
  total_tokens_in: number
  total_tokens_out: number
  total_cost_usd: number
  average_latency_ms: number
  cache_hit_rate: number
}

interface UseLLMCostTrackerReturn {
  recentCalls: LLMCall[]
  totals: LLMTotals
  isConnected: boolean
  error: string | null
  clearHistory: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const MAX_RECENT_CALLS = 50

/**
 * Hook for tracking LLM API costs in real-time.
 * Subscribes to llm_usage events via SSE.
 *
 * Implements DASH-14: Live LLM cost tracking widget
 */
export function useLLMCostTracker(): UseLLMCostTrackerReturn {
  const [recentCalls, setRecentCalls] = useState<LLMCall[]>([])
  const [totals, setTotals] = useState<LLMTotals>({
    total_calls: 0,
    total_tokens_in: 0,
    total_tokens_out: 0,
    total_cost_usd: 0,
    average_latency_ms: 0,
    cache_hit_rate: 0,
  })
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const totalLatencyRef = useRef(0)
  const cacheHitsRef = useRef(0)

  const clearHistory = useCallback(() => {
    setRecentCalls([])
    setTotals({
      total_calls: 0,
      total_tokens_in: 0,
      total_tokens_out: 0,
      total_cost_usd: 0,
      average_latency_ms: 0,
      cache_hit_rate: 0,
    })
    totalLatencyRef.current = 0
    cacheHitsRef.current = 0
  }, [])

  const handleLLMUsage = useCallback((data: Record<string, unknown>) => {
    const callData = data.call as Record<string, unknown> | undefined
    const totalsData = data.totals as Record<string, unknown> | undefined

    if (callData) {
      const newCall: LLMCall = {
        model: callData.model as string || 'unknown',
        tokens_in: callData.tokens_in as number || 0,
        tokens_out: callData.tokens_out as number || 0,
        cost_usd: callData.cost_usd as number || 0,
        latency_ms: callData.latency_ms as number || 0,
        cached: callData.cached as boolean || false,
        agent_id: callData.agent_id as string | null,
        timestamp: Date.now(),
      }

      setRecentCalls((prev) => [newCall, ...prev].slice(0, MAX_RECENT_CALLS))

      // Update running totals
      totalLatencyRef.current += newCall.latency_ms
      if (newCall.cached) {
        cacheHitsRef.current += 1
      }

      setTotals((prev) => {
        const newTotalCalls = prev.total_calls + 1
        return {
          total_calls: newTotalCalls,
          total_tokens_in: prev.total_tokens_in + newCall.tokens_in,
          total_tokens_out: prev.total_tokens_out + newCall.tokens_out,
          total_cost_usd: prev.total_cost_usd + newCall.cost_usd,
          average_latency_ms: totalLatencyRef.current / newTotalCalls,
          cache_hit_rate: cacheHitsRef.current / newTotalCalls,
        }
      })
    }

    // If server sends totals, use those instead (more accurate)
    if (totalsData) {
      setTotals({
        total_calls: totalsData.total_calls as number || 0,
        total_tokens_in: totalsData.total_tokens_in as number || 0,
        total_tokens_out: totalsData.total_tokens_out as number || 0,
        total_cost_usd: totalsData.total_cost_usd as number || 0,
        average_latency_ms: totalsData.average_latency_ms as number || 0,
        cache_hit_rate: totalsData.cache_hit_rate as number || 0,
      })
    }
  }, [])

  useEffect(() => {
    // Filter for llm_usage events only
    const url = `${API_URL}/api/stream?types=llm_usage`

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

          // Process LLM usage events
          if (data.type === 'llm_usage' && data.data) {
            handleLLMUsage(data.data)
          }
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
  }, [handleLLMUsage])

  return {
    recentCalls,
    totals,
    isConnected,
    error,
    clearHistory,
  }
}
