import { Card } from '../common'
import type { Poll } from '../../hooks/usePoll'

interface ActivePollProps {
  poll: Poll
  hasVoted: boolean
  onVote: (optionId: number) => void
}

export function ActivePoll({ poll, hasVoted, onVote }: ActivePollProps) {
  return (
    <Card title="Community Poll" className="border-accent-magenta/30">
      <div className="space-y-4">
        <p className="text-fg-primary font-medium">{poll.question}</p>

        <div className="space-y-2">
          {poll.options.map((option) => {
            const percentage = poll.total_votes > 0
              ? Math.round((option.votes / poll.total_votes) * 100)
              : 0

            return (
              <button
                key={option.id}
                onClick={() => !hasVoted && onVote(option.id)}
                disabled={hasVoted}
                className={`w-full text-left p-3 rounded-lg border transition-all ${
                  hasVoted
                    ? 'border-bg-highlight cursor-default'
                    : 'border-bg-highlight hover:border-accent-magenta hover:bg-bg-highlight/50 cursor-pointer'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-fg-secondary text-sm">{option.text}</span>
                  {hasVoted && (
                    <span className="text-fg-dim text-xs">{percentage}%</span>
                  )}
                </div>

                {hasVoted && (
                  <div className="w-full bg-bg-primary rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-accent-magenta rounded-full h-1.5 transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                )}
              </button>
            )
          })}
        </div>

        <div className="flex items-center justify-between text-xs text-fg-dim">
          <span>{poll.total_votes} vote{poll.total_votes !== 1 ? 's' : ''}</span>
          {hasVoted ? (
            <span className="text-accent-green">You voted!</span>
          ) : (
            <span>Click to vote</span>
          )}
        </div>
      </div>
    </Card>
  )
}
