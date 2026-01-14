import { Badge } from '../common'
import type { AgentGoal } from '../../hooks/useAgent'

interface GoalListProps {
  goals: AgentGoal[]
}

type BadgeVariant = 'green' | 'blue' | 'yellow' | 'magenta' | 'cyan'

function getCategoryColor(category: string): BadgeVariant {
  switch (category.toLowerCase()) {
    case 'need':
      return 'magenta'
    case 'desire':
      return 'cyan'
    case 'reactive':
      return 'yellow'
    default:
      return 'blue'
  }
}

function getStatusIcon(status: string): string {
  switch (status.toLowerCase()) {
    case 'completed':
      return '\u2713' // ✓
    case 'in_progress':
      return '\u25B6' // ▶
    case 'blocked':
      return '\u25A0' // ■
    default:
      return '\u25CB' // ○
  }
}

export function GoalList({ goals }: GoalListProps) {
  if (!goals || goals.length === 0) {
    return (
      <p className="text-fg-dim text-sm text-center py-4">
        No active goals
      </p>
    )
  }

  // Sort by priority (higher first)
  const sortedGoals = [...goals].sort((a, b) => b.priority - a.priority)

  return (
    <div className="space-y-3">
      {sortedGoals.map((goal) => (
        <div
          key={goal.id}
          className="p-3 bg-bg-highlight/30 rounded-lg border border-bg-highlight"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              <span className="text-fg-dim">{getStatusIcon(goal.status)}</span>
              <Badge variant={getCategoryColor(goal.category)} className="text-xs">
                {goal.category}
              </Badge>
            </div>
            <span className="text-fg-dim text-xs">
              Priority: {goal.priority}
            </span>
          </div>

          <p className="text-fg-secondary text-sm mb-2">
            {goal.description}
          </p>

          {goal.progress > 0 && (
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-bg-primary rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-accent-green rounded-full h-1.5 transition-all duration-300"
                  style={{ width: `${Math.round(goal.progress * 100)}%` }}
                />
              </div>
              <span className="text-fg-dim text-xs">
                {Math.round(goal.progress * 100)}%
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
