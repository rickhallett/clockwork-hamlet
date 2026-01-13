import { Card, Badge } from '../common'
import type { Poll } from '../../hooks/usePoll'

interface PollResultsProps {
  poll: Poll
}

export function PollResults({ poll }: PollResultsProps) {
  // Find winning option
  const winner = poll.options.reduce((max, opt) =>
    opt.votes > max.votes ? opt : max
  , poll.options[0])

  return (
    <Card title="Poll Results" className="border-accent-green/30">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-2">
          <p className="text-fg-secondary text-sm">{poll.question}</p>
          <Badge variant="green">Closed</Badge>
        </div>

        <div className="space-y-2">
          {poll.options.map((option) => {
            const percentage = poll.total_votes > 0
              ? Math.round((option.votes / poll.total_votes) * 100)
              : 0
            const isWinner = option.id === winner.id

            return (
              <div
                key={option.id}
                className={`p-3 rounded-lg border ${
                  isWinner
                    ? 'border-accent-green/50 bg-accent-green/5'
                    : 'border-bg-highlight'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {isWinner && (
                      <span className="text-accent-green">\u2713</span>
                    )}
                    <span className={`text-sm ${isWinner ? 'text-fg-primary font-medium' : 'text-fg-secondary'}`}>
                      {option.text}
                    </span>
                  </div>
                  <span className="text-fg-dim text-xs">
                    {option.votes} ({percentage}%)
                  </span>
                </div>

                <div className="w-full bg-bg-primary rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`rounded-full h-1.5 transition-all duration-500 ${
                      isWinner ? 'bg-accent-green' : 'bg-bg-highlight'
                    }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>

        <p className="text-fg-dim text-xs text-center">
          {poll.total_votes} total votes
        </p>
      </div>
    </Card>
  )
}
