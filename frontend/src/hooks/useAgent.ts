import { useState, useEffect, useCallback } from 'react'

export interface AgentTraits {
  curiosity: number
  empathy: number
  ambition: number
  courage: number
  sociability: number
}

export interface AgentRelationship {
  target_id: string
  target_name: string
  type: string
  score: number
}

export interface AgentMemory {
  id: string
  content: string
  significance: number
  timestamp: string
  type: string
}

export interface AgentGoal {
  id: string
  description: string
  category: string
  priority: number
  progress: number
  status: string
}

export interface Agent {
  id: string
  name: string
  personality: string
  state: string
  location_id: string
  location_name: string
  traits: AgentTraits
  relationships: AgentRelationship[]
  memories: AgentMemory[]
  goals: AgentGoal[]
}

interface UseAgentReturn {
  agent: Agent | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useAgent(agentId: string | undefined): UseAgentReturn {
  const [agent, setAgent] = useState<Agent | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAgent = useCallback(async () => {
    if (!agentId) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/agents/${agentId}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch agent: ${response.statusText}`)
      }
      const data = await response.json()
      setAgent(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setAgent(null)
    } finally {
      setIsLoading(false)
    }
  }, [agentId])

  useEffect(() => {
    fetchAgent()
  }, [fetchAgent])

  return {
    agent,
    isLoading,
    error,
    refetch: fetchAgent,
  }
}
