import { Terminal } from '../common'
import type { AgentMemory } from '../../hooks/useAgent'

interface MemoryLogProps {
  memories: AgentMemory[]
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function getSignificanceIndicator(significance: number): string {
  if (significance >= 0.8) return '\u2605\u2605\u2605' // ★★★
  if (significance >= 0.5) return '\u2605\u2605' // ★★
  if (significance >= 0.3) return '\u2605' // ★
  return ''
}

export function MemoryLog({ memories }: MemoryLogProps) {
  return (
    <Terminal title="memories.log" className="max-h-[300px] overflow-y-auto">
      {!memories || memories.length === 0 ? (
        <p className="text-fg-dim text-sm">No memories recorded</p>
      ) : (
        <div className="space-y-3">
          {memories.map((memory) => (
            <div key={memory.id} className="border-l-2 border-bg-highlight pl-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-fg-secondary text-sm leading-relaxed">
                  {memory.content}
                </p>
                <span className="text-accent-yellow text-xs shrink-0">
                  {getSignificanceIndicator(memory.significance)}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-fg-dim text-xs">
                  {formatTimestamp(memory.timestamp)}
                </span>
                <span className="text-fg-dim text-xs">
                  [{memory.type}]
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Terminal>
  )
}
