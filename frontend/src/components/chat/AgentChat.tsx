import { useState, useRef, useEffect, FormEvent } from 'react'
import { useChat, ChatMessage } from '../../hooks/useChat'
import { Terminal } from '../common/Terminal'

interface AgentChatProps {
  agentId: string
  agentName: string
  authToken: string | null
  onClose?: () => void
}

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ChatBubble({ message, agentName }: { message: ChatMessage; agentName: string }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-accent-blue/20 text-fg-primary ml-4'
            : 'bg-bg-highlight text-fg-primary mr-4'
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-medium ${isUser ? 'text-accent-blue' : 'text-accent-magenta'}`}>
            {isUser ? 'You' : agentName}
          </span>
          <span className="text-xs text-fg-dim">{formatTime(message.timestamp)}</span>
        </div>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {!isUser && message.latency_ms > 0 && (
          <div className="flex items-center gap-2 mt-1 text-xs text-fg-dim">
            <span>{message.latency_ms.toFixed(0)}ms</span>
            {message.cost_usd > 0 && <span>${message.cost_usd.toFixed(4)}</span>}
          </div>
        )}
      </div>
    </div>
  )
}

export function AgentChat({ agentId, agentName, authToken, onClose }: AgentChatProps) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const {
    messages,
    conversationId,
    isLoading,
    isSending,
    error,
    sendMessage,
    startNewConversation,
    clearError,
  } = useChat(agentId, authToken)

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || isSending) return

    const message = inputValue.trim()
    setInputValue('')
    await sendMessage(message)
  }

  if (!authToken) {
    return (
      <Terminal title={`Chat with ${agentName}`} className="h-[400px]">
        <div className="flex flex-col items-center justify-center h-full text-center">
          <div className="text-accent-yellow mb-2">Authentication Required</div>
          <p className="text-fg-dim text-sm">
            Please log in to chat with village agents.
          </p>
        </div>
      </Terminal>
    )
  }

  return (
    <Terminal title={`Chat with ${agentName}`} className="flex flex-col h-[500px]">
      {/* Header with actions */}
      <div className="flex items-center justify-between border-b border-bg-highlight pb-2 mb-2">
        <div className="text-xs text-fg-dim">
          {conversationId ? `Conversation #${conversationId}` : 'New conversation'}
        </div>
        <div className="flex gap-2">
          <button
            onClick={startNewConversation}
            className="text-xs text-accent-blue hover:text-accent-cyan"
          >
            New Chat
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-xs text-fg-dim hover:text-fg-secondary"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto min-h-0 pr-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-fg-dim">Loading conversation...</div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-fg-dim mb-2">Start a conversation with {agentName}</div>
            <p className="text-xs text-fg-dim">
              Ask them about their day, their thoughts, or anything else!
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} agentName={agentName} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="flex items-center justify-between bg-accent-red/10 border border-accent-red/30 rounded px-3 py-2 mb-2">
          <span className="text-sm text-accent-red">{error}</span>
          <button
            onClick={clearError}
            className="text-accent-red hover:text-accent-red/80 text-sm"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Input area */}
      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-bg-highlight pt-3">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={`Say something to ${agentName}...`}
          disabled={isSending}
          className="flex-1 bg-bg-highlight border border-bg-highlight rounded px-3 py-2 text-sm text-fg-primary placeholder:text-fg-dim focus:outline-none focus:border-accent-blue disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isSending || !inputValue.trim()}
          className="bg-accent-blue hover:bg-accent-blue/80 disabled:bg-bg-highlight disabled:text-fg-dim px-4 py-2 rounded text-sm font-medium transition-colors"
        >
          {isSending ? (
            <span className="flex items-center gap-2">
              <span className="animate-pulse">...</span>
            </span>
          ) : (
            'Send'
          )}
        </button>
      </form>
    </Terminal>
  )
}
