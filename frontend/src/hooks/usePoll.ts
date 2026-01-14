import { useState, useEffect, useCallback } from 'react'

export interface PollOption {
  id: number
  text: string
  votes: number
}

export interface Poll {
  id: number
  question: string
  options: PollOption[]
  total_votes: number
  is_active: boolean
  ends_at: string | null
  created_at: string
}

interface UsePollReturn {
  poll: Poll | null
  isLoading: boolean
  error: string | null
  hasVoted: boolean
  vote: (optionId: number) => Promise<void>
  refetch: () => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Placeholder poll when API is unavailable
const PLACEHOLDER_POLL: Poll = {
  id: 1,
  question: 'What should happen in the village next?',
  options: [
    { id: 0, text: 'A mysterious stranger arrives', votes: 12 },
    { id: 1, text: 'A storm approaches', votes: 8 },
    { id: 2, text: 'A lost item is found', votes: 5 },
  ],
  total_votes: 25,
  is_active: true,
  ends_at: null,
  created_at: new Date().toISOString(),
}

export function usePoll(): UsePollReturn {
  const [poll, setPoll] = useState<Poll | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasVoted, setHasVoted] = useState(false)

  // Check if user has already voted (stored in localStorage)
  useEffect(() => {
    if (poll) {
      const votedPolls = JSON.parse(localStorage.getItem('votedPolls') || '[]')
      setHasVoted(votedPolls.includes(poll.id))
    }
  }, [poll])

  const fetchPoll = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/polls/active`)
      if (!response.ok) {
        if (response.status === 404) {
          // No active poll
          setPoll(null)
          return
        }
        throw new Error(`Failed to fetch poll: ${response.statusText}`)
      }
      const data = await response.json()
      if (!data) {
        setPoll(null)
        return
      }
      // Transform backend format to frontend format
      const options: PollOption[] = (data.options || []).map((text: string, idx: number) => ({
        id: idx,
        text,
        votes: data.votes?.[String(idx)] || 0,
      }))
      const totalVotes = options.reduce((sum, opt) => sum + opt.votes, 0)
      setPoll({
        id: data.id,
        question: data.question,
        options,
        total_votes: totalVotes,
        is_active: data.status === 'active',
        ends_at: data.closes_at ? new Date(data.closes_at * 1000).toISOString() : null,
        created_at: new Date(data.created_at * 1000).toISOString(),
      })
    } catch (err) {
      // Use placeholder if API fails
      setPoll(PLACEHOLDER_POLL)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const vote = useCallback(async (optionId: number) => {
    if (!poll || hasVoted) return

    try {
      const response = await fetch(`${API_URL}/api/polls/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ poll_id: poll.id, option: optionId }),
      })

      if (!response.ok) {
        throw new Error(`Failed to vote: ${response.statusText}`)
      }

      // Mark as voted in localStorage
      const votedPolls = JSON.parse(localStorage.getItem('votedPolls') || '[]')
      votedPolls.push(poll.id)
      localStorage.setItem('votedPolls', JSON.stringify(votedPolls))
      setHasVoted(true)

      // Optimistic update
      setPoll((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          total_votes: prev.total_votes + 1,
          options: prev.options.map((opt) =>
            opt.id === optionId ? { ...opt, votes: opt.votes + 1 } : opt
          ),
        }
      })
    } catch (err) {
      // Still update locally even if API fails (for demo purposes)
      const votedPolls = JSON.parse(localStorage.getItem('votedPolls') || '[]')
      votedPolls.push(poll.id)
      localStorage.setItem('votedPolls', JSON.stringify(votedPolls))
      setHasVoted(true)

      setPoll((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          total_votes: prev.total_votes + 1,
          options: prev.options.map((opt) =>
            opt.id === optionId ? { ...opt, votes: opt.votes + 1 } : opt
          ),
        }
      })
    }
  }, [poll, hasVoted])

  useEffect(() => {
    fetchPoll()
  }, [fetchPoll])

  return {
    poll,
    isLoading,
    error,
    hasVoted,
    vote,
    refetch: fetchPoll,
  }
}
