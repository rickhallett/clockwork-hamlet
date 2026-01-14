import { useEventRateTracker } from '../../hooks'

/**
 * Mini sparkline chart showing event rate over time.
 *
 * Implements DASH-16: Event rate sparklines
 */
export function EventRateSparkline() {
  const { rateHistory, currentRate, rateByType, isConnected, error } = useEventRateTracker()

  // Find max count for scaling
  const maxCount = Math.max(1, ...rateHistory.map((p) => p.count))

  // SVG dimensions
  const width = 200
  const height = 40
  const padding = 2

  // Calculate points for the sparkline
  const points = rateHistory.map((point, i) => {
    const x = padding + (i / Math.max(1, rateHistory.length - 1)) * (width - 2 * padding)
    const y = height - padding - (point.count / maxCount) * (height - 2 * padding)
    return `${x},${y}`
  }).join(' ')

  return (
    <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-fg-primary font-semibold">Event Rate</h3>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-accent-green' : 'bg-accent-red'
            }`}
          />
          <span className="text-lg font-mono text-accent-blue">
            {currentRate}/min
          </span>
        </div>
      </div>

      {error && (
        <div className="text-accent-red text-xs mb-2">{error}</div>
      )}

      {/* Sparkline */}
      <div className="bg-bg-primary rounded p-2 mb-3">
        {rateHistory.length < 2 ? (
          <div className="h-10 flex items-center justify-center text-fg-dim text-sm">
            Collecting data...
          </div>
        ) : (
          <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
            {/* Background grid lines */}
            <line
              x1={padding}
              y1={height / 2}
              x2={width - padding}
              y2={height / 2}
              stroke="currentColor"
              strokeOpacity={0.1}
              strokeDasharray="2,2"
            />

            {/* Area fill */}
            <polygon
              points={`${padding},${height - padding} ${points} ${width - padding},${height - padding}`}
              fill="currentColor"
              fillOpacity={0.1}
              className="text-accent-blue"
            />

            {/* Line */}
            <polyline
              points={points}
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-accent-blue"
            />
          </svg>
        )}
      </div>

      {/* Rate by type */}
      <div className="text-xs text-fg-dim mb-2">Events by Type (per min)</div>
      <div className="flex flex-wrap gap-2">
        {Object.entries(rateByType)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 4)
          .map(([type, rate]) => (
            <div
              key={type}
              className="bg-bg-primary rounded px-2 py-1 text-xs"
            >
              <span className="text-fg-secondary">{type}</span>
              <span className="text-fg-primary ml-1 font-mono">{rate}</span>
            </div>
          ))}
        {Object.keys(rateByType).length === 0 && (
          <div className="text-fg-dim">No events yet</div>
        )}
      </div>
    </div>
  )
}
