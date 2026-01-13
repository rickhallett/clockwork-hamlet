import { Link } from 'react-router-dom'
import { Terminal, Card, CardGrid, Badge } from '../components/common'

export function Home() {
  return (
    <div className="space-y-8">
      {/* Hero section */}
      <div className="text-center py-8">
        <h1 className="text-4xl font-bold text-accent-blue mb-4">
          Clockwork Hamlet
        </h1>
        <p className="text-fg-secondary text-lg max-w-2xl mx-auto">
          A persistent, multi-agent village simulation where AI-driven characters
          live, interact, form relationships, and create emergent narratives.
        </p>
      </div>

      {/* Status terminal */}
      <Terminal title="simulation.log" className="max-w-2xl mx-auto">
        <div className="space-y-1">
          <p className="text-fg-dim">
            <span className="text-accent-cyan">[System]</span> Initializing world state...
          </p>
          <p className="text-fg-dim">
            <span className="text-accent-cyan">[System]</span> Loading agents...
          </p>
          <p className="text-accent-green">
            <span className="text-accent-cyan">[System]</span> Simulation ready.
          </p>
          <p className="text-fg-secondary mt-2">
            <span className="text-accent-yellow">[Agnes]</span> walks to the Town Square
          </p>
          <p className="text-fg-secondary">
            <span className="text-accent-magenta">[Bob]</span> greets Agnes warmly
          </p>
        </div>
      </Terminal>

      {/* Feature cards */}
      <div className="pt-8">
        <h2 className="text-xl font-semibold text-fg-primary mb-4">Explore</h2>
        <CardGrid columns={3}>
          <Card
            title="Live Feed"
            subtitle="Watch events unfold in real-time"
            hoverable
          >
            <Link to="/feed" className="text-accent-blue hover:text-accent-cyan">
              View live events →
            </Link>
          </Card>

          <Card
            title="Agents"
            subtitle="Meet the villagers"
            hoverable
          >
            <div className="flex gap-2 mb-3">
              <Badge variant="green">Agnes</Badge>
              <Badge variant="blue">Bob</Badge>
              <Badge variant="magenta">Martha</Badge>
            </div>
            <Link to="/agents" className="text-accent-blue hover:text-accent-cyan">
              View all agents →
            </Link>
          </Card>

          <Card
            title="Relationships"
            subtitle="Explore the social network"
            hoverable
          >
            <Link to="/relationships" className="text-accent-blue hover:text-accent-cyan">
              View relationships →
            </Link>
          </Card>
        </CardGrid>
      </div>
    </div>
  )
}
