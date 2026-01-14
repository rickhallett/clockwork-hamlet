import { Link } from 'react-router-dom'
import { Card, Badge } from '../common'
import type { Location } from '../../hooks/useLocations'
import type { AgentSummary } from '../../hooks/useAgents'

interface LocationDetailProps {
  location: Location
  agents: AgentSummary[]
  onClose: () => void
}

// Icons for location types
const LOCATION_ICONS: Record<string, string> = {
  town_square: '\u26f2',
  bakery: '\ud83c\udf5e',
  tavern: '\ud83c\udf7a',
  blacksmith: '\u2692\ufe0f',
  church: '\u26ea',
  inn: '\ud83c\udfe8',
  garden: '\ud83c\udf3b',
  mayor_house: '\ud83c\udfe0',
  market: '\ud83c\udfea',
}

function getStateColor(state: string): 'green' | 'blue' | 'yellow' | 'magenta' {
  switch (state) {
    case 'idle':
      return 'green'
    case 'busy':
      return 'blue'
    case 'sleeping':
      return 'magenta'
    default:
      return 'yellow'
  }
}

export function LocationDetail({ location, agents, onClose }: LocationDetailProps) {
  const icon = LOCATION_ICONS[location.id] || '\ud83d\udccd'
  const agentsHere = agents.filter((a) => location.agents_present.includes(a.id))

  return (
    <Card className="relative">
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-fg-dim hover:text-fg-primary transition-colors"
        aria-label="Close"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>

      {/* Header */}
      <div className="flex items-start gap-3 mb-4 pr-8">
        <span className="text-2xl">{icon}</span>
        <div>
          <h3 className="text-lg font-semibold text-fg-primary">{location.name}</h3>
          {location.description && (
            <p className="text-fg-secondary text-sm mt-1">{location.description}</p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-bg-primary rounded p-3">
          <p className="text-fg-dim text-xs uppercase mb-1">Occupants</p>
          <p className="text-fg-primary text-lg font-semibold">
            {agentsHere.length} / {location.capacity}
          </p>
        </div>
        <div className="bg-bg-primary rounded p-3">
          <p className="text-fg-dim text-xs uppercase mb-1">Connections</p>
          <p className="text-fg-primary text-lg font-semibold">
            {location.connections.length} paths
          </p>
        </div>
      </div>

      {/* Agents present */}
      <div className="mb-4">
        <h4 className="text-fg-primary font-medium mb-2">
          Agents Present ({agentsHere.length})
        </h4>
        {agentsHere.length > 0 ? (
          <div className="space-y-2">
            {agentsHere.map((agent) => (
              <Link
                key={agent.id}
                to={`/agents/${agent.id}`}
                className="flex items-center justify-between p-2 rounded bg-bg-primary hover:bg-bg-highlight transition-colors"
              >
                <span className="text-accent-cyan">{agent.name}</span>
                <Badge variant={getStateColor(agent.state)}>
                  {agent.state}
                </Badge>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-fg-dim text-sm">No one is here right now</p>
        )}
      </div>

      {/* Objects in location */}
      {location.objects.length > 0 && (
        <div className="mb-4">
          <h4 className="text-fg-primary font-medium mb-2">Objects</h4>
          <div className="flex flex-wrap gap-2">
            {location.objects.map((obj, idx) => (
              <Badge key={idx} variant="yellow">
                {obj}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Connected locations */}
      <div>
        <h4 className="text-fg-primary font-medium mb-2">Connected To</h4>
        <div className="flex flex-wrap gap-2">
          {location.connections.map((connId) => (
            <Badge key={connId} variant="blue">
              {connId.replace(/_/g, ' ')}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  )
}
