import { useState, useEffect, useCallback } from 'react'

export interface DigestHighlight {
  title: string
  description: string
  agents_involved: string[]
  significance: number
}

export interface Digest {
  id: number
  type: 'daily' | 'weekly'
  title: string
  headline: string
  summary: string
  highlights: DigestHighlight[]
  day: number
  generated_at: string
}

interface UseDigestReturn {
  digest: Digest | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Placeholder digest when API is unavailable
const PLACEHOLDER_DAILY_DIGEST: Digest = {
  id: 1,
  type: 'daily',
  title: 'THE DAILY HAMLET',
  headline: "Mystery Deepens as Mayor's Prize Cheese Remains Missing",
  summary: `The village of Clockwork Hamlet was abuzz with activity today as residents
went about their daily routines, though an air of mystery hangs over the town square.
Agnes Thornbury was seen having an animated conversation with Bob Fletcher near the bakery,
while Martha Greenwood spent the afternoon tending to her garden with an unusual sense of urgency.`,
  highlights: [
    {
      title: 'Heated Exchange at Town Square',
      description: 'Agnes and Bob were overheard discussing something in hushed tones. Witnesses report both seemed agitated.',
      agents_involved: ['Agnes Thornbury', 'Bob Fletcher'],
      significance: 0.8,
    },
    {
      title: 'Mysterious Visitor at the Tavern',
      description: 'A cloaked figure was spotted entering the tavern just after sunset. No one has seen them leave.',
      agents_involved: [],
      significance: 0.9,
    },
    {
      title: 'Garden Secrets',
      description: 'Martha was seen digging near her rose bushes at an odd hour. What could she be hiding?',
      agents_involved: ['Martha Greenwood'],
      significance: 0.6,
    },
  ],
  day: 3,
  generated_at: new Date().toISOString(),
}

const PLACEHOLDER_WEEKLY_DIGEST: Digest = {
  id: 2,
  type: 'weekly',
  title: 'THE WEEKLY HAMLET CHRONICLE',
  headline: 'A Week of Intrigue in Our Beloved Village',
  summary: `This past week has seen no shortage of drama in Clockwork Hamlet. From the continuing
investigation into the missing cheese to unexpected romantic developments, our village continues
to surprise us all.`,
  highlights: [
    {
      title: 'The Great Cheese Investigation Continues',
      description: 'Despite days of searching, the prize-winning cheese remains at large. Suspicion falls on several villagers.',
      agents_involved: ['Agnes Thornbury', 'Bob Fletcher', 'Martha Greenwood'],
      significance: 0.9,
    },
    {
      title: 'New Friendships Form',
      description: 'Several villagers have been spotted spending more time together, hinting at deepening bonds.',
      agents_involved: ['Agnes Thornbury', 'Martha Greenwood'],
      significance: 0.7,
    },
  ],
  day: 7,
  generated_at: new Date().toISOString(),
}

export function useDigest(type: 'daily' | 'weekly' = 'daily'): UseDigestReturn {
  const [digest, setDigest] = useState<Digest | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDigest = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/digest/${type}`)
      if (!response.ok) {
        if (response.status === 404) {
          setDigest(null)
          return
        }
        throw new Error(`Failed to fetch digest: ${response.statusText}`)
      }
      const data = await response.json()
      setDigest(data)
    } catch (err) {
      // Use placeholder if API fails
      setDigest(type === 'daily' ? PLACEHOLDER_DAILY_DIGEST : PLACEHOLDER_WEEKLY_DIGEST)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [type])

  useEffect(() => {
    fetchDigest()
  }, [fetchDigest])

  return {
    digest,
    isLoading,
    error,
    refetch: fetchDigest,
  }
}
