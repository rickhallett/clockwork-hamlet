import { Badge } from '../common'

interface GraphControlsProps {
  activeTypes: string[]
  onToggleType: (type: string) => void
  selectedNode: string | null
  onClearSelection: () => void
}

const RELATIONSHIP_TYPES = [
  { type: 'friend', label: 'Friend', variant: 'green' as const },
  { type: 'acquaintance', label: 'Acquaintance', variant: 'blue' as const },
  { type: 'rival', label: 'Rival', variant: 'yellow' as const },
  { type: 'enemy', label: 'Enemy', variant: 'red' as const },
]

export function GraphControls({
  activeTypes,
  onToggleType,
  selectedNode,
  onClearSelection,
}: GraphControlsProps) {
  const hasFilters = activeTypes.length > 0

  return (
    <div className="flex items-center justify-between flex-wrap gap-4">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-fg-dim text-sm">Filter by type:</span>

        {RELATIONSHIP_TYPES.map(({ type, label, variant }) => {
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
            onClick={() => activeTypes.forEach(onToggleType)}
            className="text-fg-dim text-sm hover:text-accent-red transition-colors"
          >
            clear
          </button>
        )}
      </div>

      {selectedNode && (
        <button
          onClick={onClearSelection}
          className="text-accent-magenta text-sm hover:text-accent-cyan transition-colors"
        >
          Clear selection ({selectedNode})
        </button>
      )}
    </div>
  )
}
