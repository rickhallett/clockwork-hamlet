import { Card, Badge } from '../components/common'

// Placeholder relationship data - will be replaced with API calls
const relationships = [
  { source: 'Agnes', target: 'Bob', type: 'friend', score: 5 },
  { source: 'Agnes', target: 'Martha', type: 'acquaintance', score: 2 },
  { source: 'Bob', target: 'Martha', type: 'friend', score: 4 },
  { source: 'Martha', target: 'Agnes', type: 'acquaintance', score: 1 },
]

function getScoreColor(score: number): 'green' | 'blue' | 'yellow' | 'red' {
  if (score >= 5) return 'green'
  if (score >= 2) return 'blue'
  if (score >= -2) return 'yellow'
  return 'red'
}

function getScoreLabel(score: number): string {
  if (score >= 7) return 'Close Friends'
  if (score >= 4) return 'Friends'
  if (score >= 0) return 'Acquaintances'
  if (score >= -4) return 'Wary'
  return 'Hostile'
}

export function Relationships() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-fg-primary mb-2">Relationships</h1>
        <p className="text-fg-secondary">
          The social network of Clockwork Hamlet. See how villagers feel about each other.
        </p>
      </div>

      {/* Placeholder for graph visualization */}
      <Card className="min-h-[400px] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-accent-cyan/20 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-accent-cyan"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          </div>
          <p className="text-fg-dim">
            Interactive relationship graph coming in Phase 12
          </p>
        </div>
      </Card>

      {/* Relationship list */}
      <div>
        <h2 className="text-lg font-semibold text-fg-primary mb-4">All Relationships</h2>
        <div className="space-y-3">
          {relationships.map((rel, idx) => (
            <Card key={idx} className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-accent-magenta font-medium">{rel.source}</span>
                  <span className="text-fg-dim">→</span>
                  <span className="text-accent-cyan font-medium">{rel.target}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant={getScoreColor(rel.score)}>
                  {getScoreLabel(rel.score)}
                </Badge>
                <span className="text-fg-dim text-sm w-8 text-right">
                  {rel.score > 0 ? '+' : ''}{rel.score}
                </span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
