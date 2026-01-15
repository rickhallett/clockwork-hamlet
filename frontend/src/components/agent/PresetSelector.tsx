import { useCallback } from 'react'
import type { TraitPreset, Traits } from '../../hooks/useAgentCreation'
import { Badge } from '../common/Badge'

interface PresetSelectorProps {
  presets: TraitPreset[]
  selectedPreset: string | null
  onSelect: (presetId: string | null, traits?: Traits) => void
  onFetchDetails: (presetId: string) => Promise<TraitPreset | null>
  disabled?: boolean
}

// Icon/emoji for each preset
const PRESET_ICONS: Record<string, string> = {
  scholar: '📚',
  merchant: '💰',
  guardian: '🛡️',
  trickster: '🎭',
  hermit: '🏔️',
  healer: '💚',
  leader: '👑',
  artisan: '🎨',
}

// Color variant for each preset
const PRESET_VARIANTS: Record<string, 'cyan' | 'yellow' | 'red' | 'magenta' | 'blue' | 'green' | 'orange' | 'default'> = {
  scholar: 'cyan',
  merchant: 'yellow',
  guardian: 'red',
  trickster: 'magenta',
  hermit: 'blue',
  healer: 'green',
  leader: 'orange',
  artisan: 'default',
}

export function PresetSelector({
  presets,
  selectedPreset,
  onSelect,
  onFetchDetails,
  disabled = false,
}: PresetSelectorProps) {
  const handleSelect = useCallback(
    async (presetId: string) => {
      if (disabled) return

      if (selectedPreset === presetId) {
        // Deselect
        onSelect(null)
        return
      }

      // Fetch preset details to get traits
      const details = await onFetchDetails(presetId)
      if (details && details.traits) {
        onSelect(presetId, details.traits)
      }
    },
    [selectedPreset, onSelect, onFetchDetails, disabled]
  )

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-fg-primary font-medium">Personality Presets</h3>
        {selectedPreset && (
          <button
            onClick={() => onSelect(null)}
            className="text-fg-dim text-xs hover:text-fg-secondary transition-colors"
            disabled={disabled}
          >
            Clear selection
          </button>
        )}
      </div>
      <p className="text-fg-dim text-sm">
        Choose a preset to quickly configure traits, or customize manually below.
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {presets.map((preset) => {
          const isSelected = selectedPreset === preset.id
          const icon = PRESET_ICONS[preset.id] || '🎭'
          const variant = PRESET_VARIANTS[preset.id] || 'default'

          return (
            <button
              key={preset.id}
              onClick={() => handleSelect(preset.id)}
              disabled={disabled}
              className={`
                p-3 rounded-lg border text-left transition-all
                ${isSelected
                  ? 'border-accent-cyan bg-accent-cyan/10'
                  : 'border-bg-highlight bg-bg-secondary hover:border-fg-dim'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{icon}</span>
                <Badge variant={isSelected ? 'cyan' : variant}>
                  {preset.name}
                </Badge>
              </div>
              <p className="text-fg-dim text-xs line-clamp-2">
                {preset.description}
              </p>
            </button>
          )
        })}
      </div>
    </div>
  )
}
