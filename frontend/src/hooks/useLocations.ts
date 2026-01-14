import { useState, useEffect, useCallback } from 'react'

export interface Location {
  id: string
  name: string
  description: string | null
  connections: string[]
  objects: string[]
  capacity: number
  agents_present: string[]
}

interface UseLocationsReturn {
  locations: Location[]
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useLocations(): UseLocationsReturn {
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
      setLocations(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setLocations([])
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLocations()
  }, [fetchLocations])

  return {
    locations,
    isLoading,
    error,
    refetch: fetchLocations,
  }
}
