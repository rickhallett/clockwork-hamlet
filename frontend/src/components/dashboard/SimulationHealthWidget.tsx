import { useSimulationHealth } from '../../hooks'

/**
 * Simulation health indicators widget.
 * Shows queue depth, tick rate, and other health metrics.
 *
 * Implements DASH-15: Simulation health indicators
 */
export function SimulationHealthWidget() {
  const { health, isLoading, error } = useSimulationHealth()

  if (isLoading) {
    return (
      <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-4">
        <div className="animate-pulse text-fg-dim text-center">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-4">
        <div className="text-accent-red text-sm">{error}</div>
      </div>
    )
  }

  if (!health) {
    return null
  }

  // Determine health status colors
  const getStatusColor = () => {
    if (!health.is_running) return 'bg-accent-red'
    if (health.queue_depth > 10) return 'bg-accent-yellow'
    return 'bg-accent-green'
  }

  const formatHour = (hour: number) => {
    const h = Math.floor(hour)
    const m = Math.floor((hour % 1) * 60)
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`
  }

  return (
    <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-fg-primary font-semibold">Simulation</h3>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
          <span className="text-xs text-fg-dim">
            {health.is_running ? 'Running' : 'Stopped'}
          </span>
        </div>
      </div>

      {/* Time display */}
      <div className="bg-bg-primary rounded p-3 mb-3 text-center">
        <div className="text-2xl font-mono text-fg-primary">
          Day {health.current_day}, {formatHour(health.current_hour)}
        </div>
        <div className="text-sm text-fg-secondary capitalize">
          {health.season} • {health.weather}
        </div>
      </div>

      {/* Health metrics grid */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Tick</div>
          <div className="font-mono text-fg-primary">
            #{health.current_tick}
          </div>
        </div>
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Tick Rate</div>
          <div className="font-mono text-fg-primary">
            {health.tick_rate}/min
          </div>
        </div>
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Queue Depth</div>
          <div className={`font-mono ${
            health.queue_depth > 10 ? 'text-accent-yellow' : 'text-fg-primary'
          }`}>
            {health.queue_depth}
          </div>
        </div>
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Events/Tick</div>
          <div className="font-mono text-fg-primary">
            {health.events_per_tick.toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  )
}
