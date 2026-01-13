import { Link, useParams } from 'react-router-dom'
import { Card, CardGrid, Badge } from '../components/common'
import { TraitBars, RelationshipList, MemoryLog, GoalList } from '../components/agent'
import { useAgent } from '../hooks'

// Placeholder agent data for list - will be replaced with API hook
const agents = [
  { id: 'agnes', name: 'Agnes Thornbury', state: 'idle', location: 'Bakery' },
  { id: 'bob', name: 'Bob Fletcher', state: 'idle', location: 'Town Square' },
  { id: 'martha', name: 'Martha Greenwood', state: 'idle', location: 'Tavern' },
]

export function AgentList() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-fg-primary mb-2">Village Agents</h1>
        <p className="text-fg-secondary">
          The inhabitants of Clockwork Hamlet, each with their own personality and goals.
        </p>
      </div>

      <CardGrid columns={3}>
        {agents.map((agent) => (
          <Card key={agent.id} hoverable>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-fg-primary">{agent.name}</h3>
                <p className="text-fg-dim text-sm">{agent.location}</p>
              </div>
              <Badge variant={agent.state === 'idle' ? 'green' : 'yellow'}>
                {agent.state}
              </Badge>
            </div>
            <Link
              to={`/agents/${agent.id}`}
              className="text-accent-blue hover:text-accent-cyan text-sm"
            >
              View profile →
            </Link>
          </Card>
        ))}
      </CardGrid>
    </div>
  )
}

export function AgentProfile() {
  const { agentId } = useParams<{ agentId: string }>()
  const { agent, isLoading, error } = useAgent(agentId)

  // Fallback to placeholder if API unavailable
  const placeholderAgent = agents.find((a) => a.id === agentId)

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-pulse">
          <div className="w-20 h-20 bg-bg-highlight rounded-full mx-auto mb-4" />
          <div className="h-6 bg-bg-highlight rounded w-48 mx-auto mb-2" />
          <div className="h-4 bg-bg-highlight rounded w-32 mx-auto" />
        </div>
      </div>
    )
  }

  // Use API data if available, otherwise use placeholder
  const displayAgent = agent || (placeholderAgent ? {
    id: placeholderAgent.id,
    name: placeholderAgent.name,
    personality: 'A villager of Clockwork Hamlet',
    state: placeholderAgent.state,
    location_id: placeholderAgent.id,
    location_name: placeholderAgent.location,
    traits: {
      curiosity: 0.6,
      empathy: 0.7,
      ambition: 0.5,
      courage: 0.4,
      sociability: 0.8,
    },
    relationships: [],
    memories: [],
    goals: [],
  } : null)

  if (!displayAgent) {
    return (
      <div className="text-center py-12">
        <p className="text-fg-dim mb-4">
          {error || 'Agent not found'}
        </p>
        <Link to="/agents" className="text-accent-blue hover:text-accent-cyan">
          ← Back to agents
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/agents" className="text-fg-dim hover:text-fg-secondary">
          ← Back
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile card */}
        <Card className="lg:col-span-1">
          <div className="text-center">
            <div className="w-20 h-20 bg-accent-magenta/20 rounded-full mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl text-accent-magenta font-bold">
                {displayAgent.name.charAt(0)}
              </span>
            </div>
            <h1 className="text-xl font-bold text-fg-primary">{displayAgent.name}</h1>
            <p className="text-fg-dim text-sm">{displayAgent.location_name}</p>
            <Badge variant={displayAgent.state === 'idle' ? 'green' : 'yellow'} className="mt-2">
              {displayAgent.state}
            </Badge>

            {displayAgent.personality && (
              <p className="text-fg-secondary text-sm mt-4 italic">
                "{displayAgent.personality}"
              </p>
            )}
          </div>
        </Card>

        {/* Stats and info */}
        <div className="lg:col-span-2 space-y-4">
          <Card title="Personality Traits">
            <TraitBars traits={displayAgent.traits} />
          </Card>

          <Card title="Relationships">
            <RelationshipList relationships={displayAgent.relationships} />
          </Card>

          <Card title="Active Goals">
            <GoalList goals={displayAgent.goals} />
          </Card>

          <MemoryLog memories={displayAgent.memories} />
        </div>
      </div>
    </div>
  )
}
