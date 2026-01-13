import { Badge } from '../common'

interface FilterBarProps {
  activeTypes: string[]
  onToggleType: (type: string) => void
  onClear: () => void
}

const EVENT_TYPES = [
  { type: 'movement', label: 'movement', variant: 'cyan' as const },
  { type: 'dialogue', label: 'dialogue', variant: 'green' as const },
  { type: 'action', label: 'action', variant: 'yellow' as const },
  { type: 'relationship', label: 'relationship', variant: 'magenta' as const },
  { type: 'goal', label: 'goal', variant: 'blue' as const },
]

export function FilterBar({ activeTypes, onToggleType, onClear }: FilterBarProps) {
  const hasFilters = activeTypes.length > 0

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <span className="text-fg-dim text-sm">Filter:</span>

      {EVENT_TYPES.map(({ type, label, variant }) => {
        const isActive = activeTypes.includes(type)
        return (
          <button
            key={type}
            onClick={() => onToggleType(type)}
            className={`transition-all ${
              isActive ? 'opacity-100 scale-105' : 'opacity-50 hover:opacity-75'
            }`}
          >
            <Badge variant={variant}>{label}</Badge>
          </button>
        )
      })}

      {hasFilters && (
        <button
          onClick={onClear}
          className="text-fg-dim text-sm hover:text-accent-red transition-colors ml-2"
        >
          clear
        </button>
      )}
    </div>
  )
}
