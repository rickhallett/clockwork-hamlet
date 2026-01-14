import { Badge } from '../common'

interface FilterBarProps {
  activeTypes: string[]
  onToggleType: (type: string) => void
  onClear: () => void
  groupByTime: boolean
  onToggleGrouping: () => void
}

const EVENT_TYPES = [
  { type: 'movement', label: 'movement', variant: 'cyan' as const },
  { type: 'dialogue', label: 'dialogue', variant: 'green' as const },
  { type: 'action', label: 'action', variant: 'yellow' as const },
  { type: 'relationship', label: 'relationship', variant: 'magenta' as const },
  { type: 'goal', label: 'goal', variant: 'blue' as const },
]

export function FilterBar({
  activeTypes,
  onToggleType,
  onClear,
  groupByTime,
  onToggleGrouping,
}: FilterBarProps) {
  const hasFilters = activeTypes.length > 0

  return (
    <div className="flex items-center justify-between flex-wrap gap-3">
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

      <button
        onClick={onToggleGrouping}
        className={`text-sm px-3 py-1 rounded border transition-colors ${
          groupByTime
            ? 'border-accent-cyan text-accent-cyan bg-accent-cyan/10'
            : 'border-bg-highlight text-fg-dim hover:text-fg-secondary hover:border-fg-dim'
        }`}
      >
        {groupByTime ? 'Grouped' : 'Group by time'}
      </button>
    </div>
  )
}
