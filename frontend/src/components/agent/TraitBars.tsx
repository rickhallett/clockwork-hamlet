import type { AgentTraits } from '../../hooks/useAgent'

interface TraitBarsProps {
  traits: AgentTraits
}

interface TraitConfig {
  key: keyof AgentTraits
  label: string
  color: string
}

const TRAIT_CONFIG: TraitConfig[] = [
  { key: 'curiosity', label: 'Curiosity', color: 'bg-accent-cyan' },
  { key: 'empathy', label: 'Empathy', color: 'bg-accent-magenta' },
  { key: 'ambition', label: 'Ambition', color: 'bg-accent-yellow' },
  { key: 'courage', label: 'Courage', color: 'bg-accent-red' },
  { key: 'sociability', label: 'Sociability', color: 'bg-accent-green' },
]

export function TraitBars({ traits }: TraitBarsProps) {
  return (
    <div className="space-y-3">
      {TRAIT_CONFIG.map(({ key, label, color }) => {
        const value = traits[key] ?? 0.5
        const percentage = Math.round(value * 100)

        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-fg-secondary text-sm w-24 shrink-0">{label}</span>
            <div className="flex-1 bg-bg-highlight rounded-full h-2 overflow-hidden">
              <div
                className={`${color} rounded-full h-2 transition-all duration-500`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="text-fg-dim text-xs w-10 text-right">{percentage}%</span>
          </div>
        )
      })}
    </div>
  )
}
