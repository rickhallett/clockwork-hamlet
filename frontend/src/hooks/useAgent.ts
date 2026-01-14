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

// Transform backend traits (1-10) to frontend format (0-1)
function transformTraits(backendTraits: Record<string, number>): AgentTraits {
  return {
    curiosity: (backendTraits.curiosity || 5) / 10,
    empathy: (backendTraits.empathy || 5) / 10,
    ambition: (backendTraits.ambition || 5) / 10,
    courage: (backendTraits.courage || 5) / 10,
    sociability: (backendTraits.charm || 5) / 10, // Map charm to sociability
  }
}

export function useAgent(agentId: string | undefined): UseAgentReturn {
  const [agent, setAgent] = useState<Agent | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAgent = useCallback(async () => {
    if (!agentId) return

    setIsLoading(true)
    setError(null)

    try {
      // Fetch agent, relationships, memories, and goals in parallel
      const [agentRes, relRes, memRes, goalsRes] = await Promise.all([
        fetch(`${API_URL}/api/agents/${agentId}`),
        fetch(`${API_URL}/api/relationships/agent/${agentId}`),
        fetch(`${API_URL}/api/agents/${agentId}/memory`),
        fetch(`${API_URL}/api/goals/agent/${agentId}`),
      ])

      if (!agentRes.ok) {
        throw new Error(`Failed to fetch agent: ${agentRes.statusText}`)
      }

      const agentData = await agentRes.json()
      const relationships = relRes.ok ? await relRes.json() : []
      const memoryData = memRes.ok ? await memRes.json() : { working: [], recent: [], longterm: [] }
      const goalsData = goalsRes.ok ? await goalsRes.json() : []

      // Combine all memory types and transform
      const allMemories = [
        ...(memoryData.working || []),
        ...(memoryData.recent || []),
        ...(memoryData.longterm || []),
      ]

      // Transform to frontend format
      const transformedAgent: Agent = {
        id: agentData.id,
        name: agentData.name,
        personality: agentData.personality_prompt || '',
        state: agentData.state,
        location_id: agentData.location_id,
        location_name: agentData.location_id, // TODO: Fetch location name
        traits: transformTraits(agentData.traits || {}),
        relationships: relationships.map((r: Record<string, unknown>) => ({
          target_id: r.target_id,
          target_name: r.target_name || r.target_id,
          type: r.type,
          score: r.score,
        })),
        memories: allMemories.map((m: Record<string, unknown>) => ({
          id: String(m.id),
          content: String(m.content || ''),
          significance: (m.significance as number) / 10, // Normalize to 0-1
          timestamp: new Date((m.timestamp as number) * 1000).toISOString(),
          type: String(m.type || 'unknown'),
        })),
        goals: goalsData.map((g: Record<string, unknown>) => ({
          id: String(g.id),
          description: g.description,
          category: g.type || 'unknown',
          priority: g.priority,
          progress: 0, // Backend doesn't track progress yet
          status: g.status,
        })),
      }

      setAgent(transformedAgent)
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
