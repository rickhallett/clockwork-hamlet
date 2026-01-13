import { Link, useParams } from 'react-router-dom'
import { Card, CardGrid, Badge, Terminal } from '../components/common'

// Placeholder agent data - will be replaced with API calls
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
  const agent = agents.find((a) => a.id === agentId)

  if (!agent) {
    return (
      <div className="text-center py-12">
        <p className="text-fg-dim">Agent not found</p>
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
                {agent.name.charAt(0)}
              </span>
            </div>
            <h1 className="text-xl font-bold text-fg-primary">{agent.name}</h1>
            <p className="text-fg-dim text-sm">{agent.location}</p>
            <Badge variant="green" className="mt-2">{agent.state}</Badge>
          </div>
        </Card>

        {/* Stats and info */}
        <div className="lg:col-span-2 space-y-4">
          <Card title="Personality Traits">
            <div className="space-y-3">
              {['Curiosity', 'Empathy', 'Ambition', 'Courage'].map((trait) => (
                <div key={trait} className="flex items-center gap-3">
                  <span className="text-fg-secondary w-24 text-sm">{trait}</span>
                  <div className="flex-1 bg-bg-highlight rounded-full h-2">
                    <div
                      className="bg-accent-blue rounded-full h-2"
                      style={{ width: `${Math.random() * 60 + 40}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Terminal title="recent_memories.log">
            <div className="space-y-1 text-sm">
              <p className="text-fg-dim">No recent memories</p>
            </div>
          </Terminal>
        </div>
      </div>
    </div>
  )
}
