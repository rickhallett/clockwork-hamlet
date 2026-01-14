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
    { id: 'bob', name: 'Bob Millwright', location: 'Garden' },
    { id: 'martha', name: 'Martha Hendricks', location: 'Town Square' },
    { id: 'edmund', name: 'Edmund Blackwood', location: 'Blacksmith' },
    { id: 'rosalind', name: 'Rosalind Fairweather', location: 'Inn' },
    { id: 'father_cornelius', name: 'Father Cornelius', location: 'Church' },
    { id: 'theodore', name: 'Theodore Hendricks', location: "Mayor's House" },
    { id: 'eliza', name: 'Eliza Thornbury', location: 'Bakery' },
    { id: 'william', name: 'Old Will Cooper', location: 'Tavern' },
    { id: 'thomas', name: 'Thomas Ashford', location: 'Tavern' },
  ],
  links: [
    { source: 'agnes', target: 'martha', type: 'friend', score: 7 },
    { source: 'agnes', target: 'eliza', type: 'family', score: 8 },
    { source: 'agnes', target: 'bob', type: 'acquaintance', score: 4 },
    { source: 'agnes', target: 'thomas', type: 'friend', score: 5 },
    { source: 'martha', target: 'theodore', type: 'spouse', score: 6 },
    { source: 'bob', target: 'william', type: 'friend', score: 5 },
    { source: 'thomas', target: 'agnes', type: 'friend', score: 7 },
    { source: 'rosalind', target: 'edmund', type: 'acquaintance', score: 6 },
    { source: 'father_cornelius', target: 'eliza', type: 'acquaintance', score: 1 },
    { source: 'edmund', target: 'theodore', type: 'acquaintance', score: -1 },
    { source: 'william', target: 'father_cornelius', type: 'friend', score: 6 },
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
      const response = await fetch(`${API_URL}/api/relationships`)
      if (!response.ok) {
        throw new Error(`Failed to fetch relationships: ${response.statusText}`)
      }
      const data = await response.json()
      // Transform backend format (edges) to frontend format (links)
      setGraph({
        nodes: data.nodes,
        links: data.edges || [],
      })
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
