import { useState, useCallback, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Types matching backend schemas
export interface Traits {
  curiosity: number
  empathy: number
  ambition: number
  discretion: number
  energy: number
  courage: number
  charm: number
  perception: number
}

export interface TraitPreset {
  id: string
  name: string
  description: string
  traits?: Traits
}

export interface AgentQuota {
  max_agents: number
  agents_created: number
  remaining: number
  can_create: boolean
  next_creation_available_at: number | null
}

export interface AgentPreview {
  name: string
  personality_prompt: string
  traits: Traits
  location_name: string | null
  trait_summary: string
  personality_archetype: string
  compatibility_notes: string[]
}

export interface CreatedAgent {
  id: string
  name: string
  personality_prompt: string | null
  traits: Traits
  location_id: string | null
  mood: { happiness: number; energy: number }
  state: string
  creator_id: number | null
  created_at: number | null
  is_user_created: boolean
}

export interface Location {
  id: string
  name: string
}

export interface CreateAgentRequest {
  name: string
  personality_prompt: string
  traits: Traits
  location_id?: string
  preset?: string
}

export const DEFAULT_TRAITS: Traits = {
  curiosity: 5,
  empathy: 5,
  ambition: 5,
  discretion: 5,
  energy: 5,
  courage: 5,
  charm: 5,
  perception: 5,
}

// Hook for fetching trait presets
export function useTraitPresets() {
  const [presets, setPresets] = useState<TraitPreset[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPresets = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/agents/presets`)
      if (!response.ok) {
        throw new Error(`Failed to fetch presets: ${response.statusText}`)
      }
      const data = await response.json()
      setPresets(data.presets)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchPresetDetails = useCallback(async (presetId: string): Promise<TraitPreset | null> => {
    try {
      const response = await fetch(`${API_URL}/api/agents/presets/${presetId}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch preset: ${response.statusText}`)
      }
      return await response.json()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    }
  }, [])

  useEffect(() => {
    fetchPresets()
  }, [fetchPresets])

  return { presets, isLoading, error, fetchPresetDetails }
}

// Hook for fetching locations
export function useLocations() {
  const [locations, setLocations] = useState<Location[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchLocations = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/locations`)
      if (!response.ok) {
        throw new Error(`Failed to fetch locations: ${response.statusText}`)
      }
      const data = await response.json()
      setLocations(data.map((loc: { id: string; name: string }) => ({
        id: loc.id,
        name: loc.name,
      })))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLocations()
  }, [fetchLocations])

  return { locations, isLoading, error }
}

// Hook for agent creation with auth
export function useAgentCreation(token: string | null) {
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [quota, setQuota] = useState<AgentQuota | null>(null)
  const [quotaLoading, setQuotaLoading] = useState(false)

  const fetchQuota = useCallback(async () => {
    if (!token) {
      setQuota(null)
      return
    }
    setQuotaLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/agents/quota`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Please log in to create agents')
        }
        throw new Error(`Failed to fetch quota: ${response.statusText}`)
      }
      const data = await response.json()
      setQuota(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setQuota(null)
    } finally {
      setQuotaLoading(false)
    }
  }, [token])

  const previewAgent = useCallback(async (
    request: Omit<CreateAgentRequest, 'preset'>
  ): Promise<AgentPreview | null> => {
    try {
      const response = await fetch(`${API_URL}/api/agents/preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(request),
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to preview agent: ${response.statusText}`)
      }
      return await response.json()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    }
  }, [token])

  const createAgent = useCallback(async (
    request: CreateAgentRequest
  ): Promise<CreatedAgent | null> => {
    if (!token) {
      setError('Please log in to create agents')
      return null
    }
    setIsCreating(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/agents/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(request),
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        if (response.status === 429) {
          throw new Error('Rate limited. Please wait before creating another agent.')
        }
        if (response.status === 403) {
          throw new Error(errorData.detail || 'Agent quota exceeded')
        }
        throw new Error(errorData.detail || `Failed to create agent: ${response.statusText}`)
      }
      const agent = await response.json()
      // Refresh quota after creation
      fetchQuota()
      return agent
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      return null
    } finally {
      setIsCreating(false)
    }
  }, [token, fetchQuota])

  useEffect(() => {
    fetchQuota()
  }, [fetchQuota])

  return {
    quota,
    quotaLoading,
    isCreating,
    error,
    setError,
    previewAgent,
    createAgent,
    refetchQuota: fetchQuota,
  }
}
