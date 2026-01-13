import { useState, useEffect, useCallback } from 'react'

export interface GraphNode {
  id: string
  name: string
  location?: string
}

export interface GraphLink {
  source: string
  target: string
  type: string
  score: number
}

export interface RelationshipGraph {
  nodes: GraphNode[]
  links: GraphLink[]
}

interface UseRelationshipsReturn {
  graph: RelationshipGraph | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Placeholder data when API is unavailable
const PLACEHOLDER_GRAPH: RelationshipGraph = {
  nodes: [
    { id: 'agnes', name: 'Agnes Thornbury', location: 'Bakery' },
    { id: 'bob', name: 'Bob Fletcher', location: 'Town Square' },
    { id: 'martha', name: 'Martha Greenwood', location: 'Tavern' },
  ],
  links: [
    { source: 'agnes', target: 'bob', type: 'friend', score: 5 },
    { source: 'agnes', target: 'martha', type: 'acquaintance', score: 2 },
    { source: 'bob', target: 'martha', type: 'friend', score: 4 },
  ],
}

export function useRelationships(): UseRelationshipsReturn {
  const [graph, setGraph] = useState<RelationshipGraph | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRelationships = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/relationships/graph`)
      if (!response.ok) {
        throw new Error(`Failed to fetch relationships: ${response.statusText}`)
      }
      const data = await response.json()
      setGraph(data)
    } catch (err) {
      // Use placeholder data if API fails
      setGraph(PLACEHOLDER_GRAPH)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRelationships()
  }, [fetchRelationships])

  return {
    graph,
    isLoading,
    error,
    refetch: fetchRelationships,
  }
}
