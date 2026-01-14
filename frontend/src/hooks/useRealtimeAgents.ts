import { useState, useEffect, useCallback, useRef } from 'react'

export interface RealtimeAgent {
  id: string
  name: string
  state: string
  location_id: string
  location_name: string
}

interface AgentPosition {
  agent_id: string
  location_id: string
  timestamp: number
}

interface UseRealtimeAgentsReturn {
  agents: RealtimeAgent[]
  isLoading: boolean
  isConnected: boolean
  error: string | null
  lastUpdate: number | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Location ID to name mapping
const LOCATION_NAMES: Record<string, string> = {
  bakery: 'The Warm Hearth Bakery',
  town_square: 'Town Square',
  tavern: 'The Rusty Tankard',
  blacksmith: 'The Anvil & Ember',
  church: "St. Aldhelm's Church",
  inn: 'The Weary Traveler Inn',
  garden: 'Village Garden',
  mayor_house: "The Mayor's Residence",
  market: 'Market Square',
}

/**
 * Hook for real-time agent position tracking.
 * Fetches initial agent data and subscribes to movement events via SSE.
 *
 * Implements DASH-13: Agent position SSE updates
 */
export function useRealtimeAgents(): UseRealtimeAgentsReturn {
  const [agents, setAgents] = useState<RealtimeAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<number | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const agentMapRef = useRef<Map<string, RealtimeAgent>>(new Map())

  const fetchAgents = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/agents`)
      if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.statusText}`)
      }
      const data = await response.json()

      // Transform and store in map for efficient updates
      const newAgentMap = new Map<string, RealtimeAgent>()
      data.forEach((agent: Record<string, unknown>) => {
        const locationId = agent.location_id as string
        newAgentMap.set(agent.id as string, {
          id: agent.id as string,
          name: agent.name as string,
          state: agent.state as string,
          location_id: locationId,
          location_name: LOCATION_NAMES[locationId] || locationId,
        })
      })

      agentMapRef.current = newAgentMap
      setAgents(Array.from(newAgentMap.values()))
      setLastUpdate(Date.now())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setAgents([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Handle agent position update from SSE
  const handlePositionUpdate = useCallback((position: AgentPosition) => {
    const agent = agentMapRef.current.get(position.agent_id)
    if (agent) {
      const updatedAgent: RealtimeAgent = {
        ...agent,
        location_id: position.location_id,
        location_name: LOCATION_NAMES[position.location_id] || position.location_id,
      }
      agentMapRef.current.set(position.agent_id, updatedAgent)
      setAgents(Array.from(agentMapRef.current.values()))
      setLastUpdate(position.timestamp)
    }
  }, [])

  // Connect to SSE stream for movement events
  useEffect(() => {
    // Filter for movement events only
    const url = `${API_URL}/api/stream?types=movement`

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

          // Only process movement events
          if (data.type === 'movement') {
            // Extract agent ID from actors array
            const agentId = data.actors?.[0]
            const locationId = data.location_id

            if (agentId && locationId) {
              handlePositionUpdate({
                agent_id: agentId,
                location_id: locationId,
                timestamp: data.timestamp * 1000 || Date.now(),
              })
            }
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
  }, [handlePositionUpdate])

  // Initial fetch
  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  return {
    agents,
    isLoading,
    isConnected,
    error,
    lastUpdate,
    refetch: fetchAgents,
  }
}
