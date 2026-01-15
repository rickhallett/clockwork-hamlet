import { useState, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'agent'
  content: string
  timestamp: number
  tokens_in: number
  tokens_out: number
  cost_usd: number
  latency_ms: number
}

export interface ChatConversation {
  id: number
  user_id: number
  agent_id: string
  agent_name: string
  created_at: number
  updated_at: number
  title: string | null
  is_active: boolean
  message_count: number
}

export interface ChatConversationDetail extends ChatConversation {
  messages: ChatMessage[]
}

interface UseChatReturn {
  messages: ChatMessage[]
  conversationId: number | null
  isLoading: boolean
  isSending: boolean
  error: string | null
  sendMessage: (message: string) => Promise<void>
  loadConversation: (conversationId: number) => Promise<void>
  startNewConversation: () => void
  clearError: () => void
}

export function useChat(agentId: string, authToken: string | null): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getHeaders = useCallback(() => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`
    }
    return headers
  }, [authToken])

  const sendMessage = useCallback(async (message: string) => {
    if (!authToken) {
      setError('Please log in to chat with agents')
      return
    }

    setIsSending(true)
    setError(null)

    try {
      const url = new URL(`${API_URL}/api/agents/${agentId}/chat`)
      if (conversationId) {
        url.searchParams.set('conversation_id', conversationId.toString())
      }

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ message }),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Please log in to chat with agents')
        }
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to send message: ${response.statusText}`)
      }

      const data = await response.json()

      // Add both messages to the state
      setMessages(prev => [...prev, data.message, data.agent_response])
      setConversationId(data.conversation_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    } finally {
      setIsSending(false)
    }
  }, [agentId, authToken, conversationId, getHeaders])

  const loadConversation = useCallback(async (convId: number) => {
    if (!authToken) {
      setError('Please log in to view chat history')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_URL}/api/agents/${agentId}/chat/${convId}`,
        { headers: getHeaders() }
      )

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Please log in to view chat history')
        }
        throw new Error(`Failed to load conversation: ${response.statusText}`)
      }

      const data: ChatConversationDetail = await response.json()
      setMessages(data.messages)
      setConversationId(data.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation')
    } finally {
      setIsLoading(false)
    }
  }, [agentId, authToken, getHeaders])

  const startNewConversation = useCallback(() => {
    setMessages([])
    setConversationId(null)
    setError(null)
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    messages,
    conversationId,
    isLoading,
    isSending,
    error,
    sendMessage,
    loadConversation,
    startNewConversation,
    clearError,
  }
}

// Hook to get chat history list
interface UseChatHistoryReturn {
  conversations: ChatConversation[]
  isLoading: boolean
  error: string | null
  refetch: () => void
}

export function useChatHistory(agentId: string, authToken: string | null): UseChatHistoryReturn {
  const [conversations, setConversations] = useState<ChatConversation[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHistory = useCallback(async () => {
    if (!authToken) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_URL}/api/agents/${agentId}/chat/history`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      )

      if (!response.ok) {
        if (response.status === 401) {
          return // Just don't show history if not authenticated
        }
        throw new Error(`Failed to load chat history: ${response.statusText}`)
      }

      const data = await response.json()
      setConversations(data.conversations)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load chat history')
    } finally {
      setIsLoading(false)
    }
  }, [agentId, authToken])

  // Auto-fetch on mount and when dependencies change
  useState(() => {
    fetchHistory()
  })

  return {
    conversations,
    isLoading,
    error,
    refetch: fetchHistory,
  }
}
