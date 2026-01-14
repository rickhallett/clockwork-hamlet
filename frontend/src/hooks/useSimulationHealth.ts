import { useState, useEffect, useCallback } from 'react'

export interface SimulationHealth {
  // Basic state
  current_tick: number
  current_day: number
  current_hour: number
  season: string
  weather: string

  // Health indicators (DASH-15)
  is_running: boolean
  queue_depth: number
  tick_rate: number
  events_per_tick: number
  uptime_ticks: number

  // Performance
  tick_interval_seconds: number
}

interface UseSimulationHealthReturn {
  health: SimulationHealth | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Polling interval in milliseconds
const POLL_INTERVAL = 5000

/**
 * Hook for fetching simulation health metrics.
 * Polls the /api/stats/simulation endpoint periodically.
 *
 * Implements DASH-15: Simulation health indicators
 */
export function useSimulationHealth(): UseSimulationHealthReturn {
  const [health, setHealth] = useState<SimulationHealth | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/stats/simulation`)
      if (!response.ok) {
        throw new Error(`Failed to fetch simulation health: ${response.statusText}`)
      }
      const data = await response.json()
      setHealth(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch and polling
  useEffect(() => {
    fetchHealth()

    const interval = setInterval(fetchHealth, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchHealth])

  return {
    health,
    isLoading,
    error,
    refetch: fetchHealth,
  }
}
