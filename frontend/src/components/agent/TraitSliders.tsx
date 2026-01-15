import { useCallback } from 'react'
import type { Traits } from '../../hooks/useAgentCreation'

interface TraitSlidersProps {
  traits: Traits
  onChange: (traits: Traits) => void
  disabled?: boolean
}

interface TraitConfig {
  key: keyof Traits
  label: string
  color: string
  description: string
}

const TRAIT_CONFIG: TraitConfig[] = [
  {
    key: 'curiosity',
    label: 'Curiosity',
    color: 'accent-cyan',
    description: 'Desire to explore and learn new things',
  },
  {
    key: 'empathy',
    label: 'Empathy',
    color: 'accent-magenta',
    description: 'Ability to understand and share feelings',
  },
  {
    key: 'ambition',
    label: 'Ambition',
    color: 'accent-yellow',
    description: 'Drive to achieve goals and status',
  },
  {
    key: 'discretion',
    label: 'Discretion',
    color: 'accent-blue',
    description: 'Tendency to keep secrets and be private',
  },
  {
    key: 'energy',
    label: 'Energy',
    color: 'accent-green',
    description: 'Physical vitality and enthusiasm',
  },
  {
    key: 'courage',
    label: 'Courage',
    color: 'accent-red',
    description: 'Willingness to face danger or difficulty',
  },
  {
    key: 'charm',
    label: 'Charm',
    color: 'accent-orange',
    description: 'Natural attractiveness and charisma',
  },
  {
    key: 'perception',
    label: 'Perception',
    color: 'fg-primary',
    description: 'Awareness of surroundings and details',
  },
]

export function TraitSliders({ traits, onChange, disabled = false }: TraitSlidersProps) {
  const handleTraitChange = useCallback(
    (key: keyof Traits, value: number) => {
      onChange({ ...traits, [key]: value })
    },
    [traits, onChange]
  )

  return (
    <div className="space-y-4">
      {TRAIT_CONFIG.map(({ key, label, color, description }) => {
        const value = traits[key]

        return (
          <div key={key} className="group">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className={`text-${color} font-medium text-sm`}>{label}</span>
                <span className="text-fg-dim text-xs hidden group-hover:inline">
                  {description}
                </span>
              </div>
              <span className={`text-${color} text-sm font-mono w-6 text-right`}>
                {value}
              </span>
            </div>
            <div className="relative flex items-center gap-2">
              <span className="text-fg-dim text-xs w-4">1</span>
              <input
                type="range"
                min={1}
                max={10}
                value={value}
                onChange={(e) => handleTraitChange(key, parseInt(e.target.value, 10))}
                disabled={disabled}
                className={`flex-1 h-2 rounded-full appearance-none cursor-pointer
                  bg-bg-highlight
                  [&::-webkit-slider-thumb]:appearance-none
                  [&::-webkit-slider-thumb]:w-4
                  [&::-webkit-slider-thumb]:h-4
                  [&::-webkit-slider-thumb]:rounded-full
                  [&::-webkit-slider-thumb]:bg-${color}
                  [&::-webkit-slider-thumb]:cursor-pointer
                  [&::-webkit-slider-thumb]:transition-transform
                  [&::-webkit-slider-thumb]:hover:scale-125
                  [&::-moz-range-thumb]:w-4
                  [&::-moz-range-thumb]:h-4
                  [&::-moz-range-thumb]:rounded-full
                  [&::-moz-range-thumb]:bg-${color}
                  [&::-moz-range-thumb]:cursor-pointer
                  [&::-moz-range-thumb]:border-0
                  disabled:opacity-50
                  disabled:cursor-not-allowed
                `}
                style={{
                  background: `linear-gradient(to right, var(--color-${color}) ${((value - 1) / 9) * 100}%, var(--color-bg-highlight) ${((value - 1) / 9) * 100}%)`,
                }}
              />
              <span className="text-fg-dim text-xs w-6">10</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Compact display version for preview
export function TraitDisplay({ traits }: { traits: Traits }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-2">
      {TRAIT_CONFIG.map(({ key, label, color }) => {
        const value = traits[key]
        const percentage = ((value - 1) / 9) * 100

        return (
          <div key={key} className="flex items-center gap-2">
            <span className="text-fg-secondary text-xs w-20 shrink-0">{label}</span>
            <div className="flex-1 bg-bg-highlight rounded-full h-1.5 overflow-hidden">
              <div
                className={`bg-${color} rounded-full h-1.5 transition-all duration-300`}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <span className="text-fg-dim text-xs w-4 text-right">{value}</span>
          </div>
        )
      })}
    </div>
  )
}
