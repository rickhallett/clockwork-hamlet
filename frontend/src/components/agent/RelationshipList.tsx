import { Link } from 'react-router-dom'
import { Badge } from '../common'
import type { AgentRelationship } from '../../hooks/useAgent'

interface RelationshipListProps {
  relationships: AgentRelationship[]
}

type BadgeVariant = 'green' | 'blue' | 'yellow' | 'red'

function getScoreColor(score: number): BadgeVariant {
  if (score >= 5) return 'green'
  if (score >= 2) return 'blue'
  if (score >= -2) return 'yellow'
  return 'red'
}

function getScoreLabel(score: number): string {
  if (score >= 7) return 'Close Friend'
  if (score >= 4) return 'Friend'
  if (score >= 0) return 'Acquaintance'
  if (score >= -4) return 'Wary'
  return 'Hostile'
}

export function RelationshipList({ relationships }: RelationshipListProps) {
  if (!relationships || relationships.length === 0) {
    return (
      <p className="text-fg-dim text-sm text-center py-4">
        No relationships yet
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {relationships.map((rel) => (
        <div
          key={rel.target_id}
          className="flex items-center justify-between p-2 hover:bg-bg-highlight/50 rounded-lg transition-colors"
        >
          <Link
            to={`/agents/${rel.target_id}`}
            className="text-accent-cyan hover:text-accent-blue transition-colors font-medium"
          >
            {rel.target_name}
          </Link>

          <div className="flex items-center gap-3">
            <Badge variant={getScoreColor(rel.score)}>
              {getScoreLabel(rel.score)}
            </Badge>
            <span className="text-fg-dim text-sm w-8 text-right">
              {rel.score > 0 ? '+' : ''}
              {rel.score}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
