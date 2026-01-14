import { useLLMCostTracker } from '../../hooks'

/**
 * Real-time LLM cost tracking widget.
 * Shows running totals and recent API calls.
 *
 * Implements DASH-14: Live LLM cost tracking widget
 */
export function LLMCostWidget() {
  const { totals, recentCalls, isConnected, error } = useLLMCostTracker()

  return (
    <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-fg-primary font-semibold">LLM Costs</h3>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-accent-green' : 'bg-accent-red'
            }`}
          />
          <span className="text-xs text-fg-dim">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {error && (
        <div className="text-accent-red text-sm mb-3">{error}</div>
      )}

      {/* Totals */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Total Cost</div>
          <div className="text-lg font-mono text-accent-yellow">
            ${totals.total_cost_usd.toFixed(4)}
          </div>
        </div>
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Total Calls</div>
          <div className="text-lg font-mono text-fg-primary">
            {totals.total_calls}
          </div>
        </div>
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Tokens In/Out</div>
          <div className="text-sm font-mono text-fg-secondary">
            {totals.total_tokens_in.toLocaleString()} / {totals.total_tokens_out.toLocaleString()}
          </div>
        </div>
        <div className="bg-bg-primary rounded p-2">
          <div className="text-xs text-fg-dim">Avg Latency</div>
          <div className="text-sm font-mono text-fg-secondary">
            {totals.average_latency_ms.toFixed(0)}ms
          </div>
        </div>
      </div>

      {/* Recent calls */}
      <div className="text-xs text-fg-dim mb-2">Recent Calls</div>
      <div className="max-h-32 overflow-y-auto space-y-1">
        {recentCalls.length === 0 ? (
          <div className="text-fg-dim text-sm text-center py-2">
            Waiting for LLM calls...
          </div>
        ) : (
          recentCalls.slice(0, 5).map((call, i) => (
            <div
              key={i}
              className="flex items-center justify-between text-xs bg-bg-primary rounded px-2 py-1"
            >
              <span className="text-fg-secondary truncate max-w-[100px]">
                {call.agent_id || 'system'}
              </span>
              <span className="text-fg-dim">
                {call.tokens_in}+{call.tokens_out}
              </span>
              <span className="text-accent-yellow font-mono">
                ${call.cost_usd.toFixed(4)}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
