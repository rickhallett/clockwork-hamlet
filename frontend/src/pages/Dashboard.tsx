/**
 * Real-time Dashboard (DASH-11 through DASH-15)
 *
 * Features:
 * - DASH-12: Agent positions update via SSE
 * - DASH-13: Live LLM cost tracking widget
 * - DASH-14: Simulation health indicators
 * - DASH-15: Event rate sparklines
 */

import { Card, CardGrid, Badge } from '../components/common'
import { useDashboard, HealthMetrics, LLMStats, EventRates, AgentPosition } from '../hooks'

// Location name mapping
const LOCATION_NAMES: Record<string, string> = {
  bakery: 'Bakery',
  town_square: 'Town Square',
  tavern: 'Tavern',
  blacksmith: 'Blacksmith',
  church: 'Church',
  inn: 'Inn',
  garden: 'Garden',
  mayor_house: "Mayor's House",
  market: 'Market',
}

// Sparkline component for event rates (DASH-15)
function Sparkline({ data, height = 40, color = '#60a5fa' }: { data: number[]; height?: number; color?: string }) {
  if (!data || data.length === 0) return null

  const max = Math.max(...data, 1) // Avoid division by zero
  const width = 200
  const stepX = width / (data.length - 1 || 1)

  const points = data.map((value, index) => {
    const x = index * stepX
    const y = height - (value / max) * height
    return `${x},${y}`
  }).join(' ')

  // Create fill area
  const fillPoints = `0,${height} ${points} ${width},${height}`

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Fill area */}
      <polygon
        points={fillPoints}
        fill={color}
        fillOpacity={0.1}
      />
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Current value dot */}
      {data.length > 0 && (
        <circle
          cx={width}
          cy={height - (data[data.length - 1] / max) * height}
          r={3}
          fill={color}
        />
      )}
    </svg>
  )
}

// Health indicator widget (DASH-14)
function HealthWidget({ health, status }: { health: HealthMetrics | null; status: string }) {
  if (!health) {
    return (
      <Card title="Simulation Health">
        <div className="text-fg-dim text-sm">Loading...</div>
      </Card>
    )
  }

  const statusBadge = status === 'healthy' ? (
    <Badge variant="green">Healthy</Badge>
  ) : status === 'degraded' ? (
    <Badge variant="yellow">Degraded</Badge>
  ) : (
    <Badge variant="default">Unknown</Badge>
  )

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    if (hours > 0) return `${hours}h ${mins}m`
    if (mins > 0) return `${mins}m ${secs}s`
    return `${secs}s`
  }

  return (
    <Card title="Simulation Health" subtitle="Real-time indicators">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-fg-secondary">Status</span>
          {statusBadge}
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-fg-dim">Uptime</div>
            <div className="text-fg-primary font-mono">{formatUptime(health.uptime_seconds)}</div>
          </div>
          <div>
            <div className="text-fg-dim">Total Ticks</div>
            <div className="text-fg-primary font-mono">{health.total_ticks}</div>
          </div>
          <div>
            <div className="text-fg-dim">Tick Rate</div>
            <div className="text-fg-primary font-mono">{health.ticks_per_minute.toFixed(1)}/min</div>
          </div>
          <div>
            <div className="text-fg-dim">Errors</div>
            <div className={`font-mono ${health.error_count > 0 ? 'text-accent-red' : 'text-accent-green'}`}>
              {health.error_count}
            </div>
          </div>
          <div>
            <div className="text-fg-dim">Avg Latency</div>
            <div className="text-fg-primary font-mono">{health.avg_tick_duration_ms.toFixed(0)}ms</div>
          </div>
          <div>
            <div className="text-fg-dim">Queue</div>
            <div className="text-fg-primary font-mono">{health.queue_depth}</div>
          </div>
        </div>
      </div>
    </Card>
  )
}

// LLM Cost widget (DASH-13)
function LLMCostWidget({ stats, sessionCost }: { stats: LLMStats | null; sessionCost: string }) {
  if (!stats) {
    return (
      <Card title="LLM Costs">
        <div className="text-fg-dim text-sm">Loading...</div>
      </Card>
    )
  }

  return (
    <Card title="LLM Costs" subtitle="Token usage and spending">
      <div className="space-y-4">
        {/* Main cost display */}
        <div className="text-center py-2">
          <div className="text-3xl font-bold text-accent-blue">{sessionCost}</div>
          <div className="text-fg-dim text-sm">Session Cost</div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-fg-dim">Total Calls</div>
            <div className="text-fg-primary font-mono">{stats.total_calls}</div>
          </div>
          <div>
            <div className="text-fg-dim">Cached</div>
            <div className="text-accent-green font-mono">{stats.cached_calls}</div>
          </div>
          <div>
            <div className="text-fg-dim">Input Tokens</div>
            <div className="text-fg-primary font-mono">{stats.tokens_in.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-fg-dim">Output Tokens</div>
            <div className="text-fg-primary font-mono">{stats.tokens_out.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-fg-dim">Avg Latency</div>
            <div className="text-fg-primary font-mono">{stats.avg_latency_ms.toFixed(0)}ms</div>
          </div>
          <div>
            <div className="text-fg-dim">API Calls</div>
            <div className="text-fg-primary font-mono">{stats.api_calls}</div>
          </div>
        </div>

        {/* Token usage bar */}
        <div>
          <div className="flex justify-between text-xs text-fg-dim mb-1">
            <span>Token Distribution</span>
            <span>{stats.total_tokens.toLocaleString()} total</span>
          </div>
          <div className="h-2 bg-bg-highlight rounded-full overflow-hidden flex">
            <div
              className="bg-accent-cyan"
              style={{ width: `${(stats.tokens_in / stats.total_tokens) * 100}%` }}
            />
            <div
              className="bg-accent-magenta"
              style={{ width: `${(stats.tokens_out / stats.total_tokens) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs mt-1">
            <span className="text-accent-cyan">Input</span>
            <span className="text-accent-magenta">Output</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

// Event Rates widget with sparklines (DASH-15)
function EventRatesWidget({ rates }: { rates: EventRates | null }) {
  if (!rates) {
    return (
      <Card title="Event Rates">
        <div className="text-fg-dim text-sm">Loading...</div>
      </Card>
    )
  }

  return (
    <Card title="Event Rates" subtitle="Events per minute (last hour)">
      <div className="space-y-4">
        {/* Main sparkline */}
        <div>
          <div className="flex justify-between items-end mb-2">
            <div>
              <div className="text-2xl font-bold text-fg-primary">{rates.current_rate}</div>
              <div className="text-fg-dim text-sm">events/min</div>
            </div>
            <div className="text-right text-sm">
              <div className="text-fg-secondary">Peak: {rates.peak_rate}/min</div>
              <div className="text-fg-dim">Avg: {rates.avg_rate}/min</div>
            </div>
          </div>
          <Sparkline data={rates.events_per_bucket} height={60} color="#60a5fa" />
        </div>

        {/* Event types breakdown */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          {Object.entries(rates.by_type).slice(0, 6).map(([type, buckets]) => {
            const total = buckets.reduce((a, b) => a + b, 0)
            return (
              <div key={type} className="text-center p-2 bg-bg-primary rounded">
                <div className="text-fg-dim capitalize">{type}</div>
                <div className="text-fg-primary font-mono">{total}</div>
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}

// Agent Positions widget (DASH-12)
function PositionsWidget({
  positions,
  positionsByLocation,
}: {
  positions: AgentPosition[]
  positionsByLocation: Record<string, AgentPosition[]>
}) {
  const locationIds = Object.keys(positionsByLocation).sort()

  return (
    <Card title="Agent Positions" subtitle={`${positions.length} agents across ${locationIds.length} locations`}>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {locationIds.map((locId) => {
          const agents = positionsByLocation[locId]
          const locationName = LOCATION_NAMES[locId] || locId

          return (
            <div key={locId} className="border-b border-bg-highlight pb-2 last:border-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-fg-secondary font-medium">{locationName}</span>
                <Badge variant="blue">{agents.length}</Badge>
              </div>
              <div className="flex flex-wrap gap-1">
                {agents.map((agent) => (
                  <span
                    key={agent.id}
                    className={`text-xs px-2 py-0.5 rounded ${
                      agent.state === 'sleeping'
                        ? 'bg-bg-highlight text-fg-dim'
                        : agent.state === 'busy'
                        ? 'bg-accent-yellow/10 text-accent-yellow'
                        : 'bg-accent-green/10 text-accent-green'
                    }`}
                  >
                    {agent.name}
                  </span>
                ))}
              </div>
            </div>
          )
        })}

        {locationIds.length === 0 && (
          <div className="text-fg-dim text-sm text-center py-4">No agent data available</div>
        )}
      </div>
    </Card>
  )
}

// Connection status indicator
function ConnectionStatus({ isConnected, error }: { isConnected: boolean; error: string | null }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <div
        className={`w-2 h-2 rounded-full ${
          isConnected ? 'bg-accent-green animate-pulse' : 'bg-accent-red'
        }`}
      />
      <span className={isConnected ? 'text-accent-green' : 'text-accent-red'}>
        {isConnected ? 'Live' : 'Disconnected'}
      </span>
      {error && <span className="text-fg-dim">({error})</span>}
    </div>
  )
}

// Main Dashboard page
export function Dashboard() {
  const {
    positions,
    positionsByLocation,
    llmStats,
    sessionCost,
    health,
    healthStatus,
    eventRates,
    isConnected,
    error,
  } = useDashboard()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fg-primary mb-1">Real-Time Dashboard</h1>
          <p className="text-fg-secondary">
            Live simulation monitoring - updates within 1 tick
          </p>
        </div>
        <ConnectionStatus isConnected={isConnected} error={error} />
      </div>

      {/* Top row - Key metrics */}
      <CardGrid columns={3}>
        <HealthWidget health={health} status={healthStatus} />
        <LLMCostWidget stats={llmStats} sessionCost={sessionCost} />
        <EventRatesWidget rates={eventRates} />
      </CardGrid>

      {/* Bottom row - Positions */}
      <PositionsWidget positions={positions} positionsByLocation={positionsByLocation} />
    </div>
  )
}
