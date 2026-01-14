import { useState, useEffect, useCallback } from 'react'

export interface AgentSummary {
  id: string
  name: string
  state: string
  location_id: string
  location_name: string
}

interface UseAgentsReturn {
  agents: AgentSummary[]
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Location ID to name mapping (could be fetched from API)
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

export function useAgents(): UseAgentsReturn {
  const [agents, setAgents] = useState<AgentSummary[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAgents = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/agents`)
      if (!response.ok) {
        throw new Error(`Failed to fetch agents: ${response.statusText}`)
      }
      const data = await response.json()

      // Transform to frontend format
      const transformed: AgentSummary[] = data.map((agent: Record<string, unknown>) => ({
        id: agent.id,
        name: agent.name,
        state: agent.state,
        location_id: agent.location_id,
        location_name: LOCATION_NAMES[agent.location_id as string] || agent.location_id,
      }))

      setAgents(transformed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setAgents([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  return {
    agents,
    isLoading,
    error,
    refetch: fetchAgents,
  }
}
