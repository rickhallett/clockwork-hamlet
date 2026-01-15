import { useEffect, useState, useCallback } from 'react'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { TraitDisplay } from './TraitSliders'
import type { AgentPreview as AgentPreviewData, Traits, CreateAgentRequest } from '../../hooks/useAgentCreation'

interface AgentPreviewProps {
  name: string
  personalityPrompt: string
  traits: Traits
  locationId: string | null
  onPreview: (request: Omit<CreateAgentRequest, 'preset'>) => Promise<AgentPreviewData | null>
}

export function AgentPreview({
  name,
  personalityPrompt,
  traits,
  locationId,
  onPreview,
}: AgentPreviewProps) {
  const [preview, setPreview] = useState<AgentPreviewData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPreview = useCallback(async () => {
    if (!name || name.length < 2 || !personalityPrompt || personalityPrompt.length < 20) {
      setPreview(null)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const result = await onPreview({
        name,
        personality_prompt: personalityPrompt,
        traits,
        location_id: locationId || undefined,
      })
      setPreview(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preview')
      setPreview(null)
    } finally {
      setIsLoading(false)
    }
  }, [name, personalityPrompt, traits, locationId, onPreview])

  // Debounce preview generation
  useEffect(() => {
    const timer = setTimeout(fetchPreview, 500)
    return () => clearTimeout(timer)
  }, [fetchPreview])

  if (!name || name.length < 2) {
    return (
      <Card title="Agent Preview">
        <p className="text-fg-dim text-sm">
          Enter a name to see a preview of your agent.
        </p>
      </Card>
    )
  }

  if (!personalityPrompt || personalityPrompt.length < 20) {
    return (
      <Card title="Agent Preview">
        <p className="text-fg-dim text-sm">
          Add a personality description (at least 20 characters) to see a preview.
        </p>
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card title="Agent Preview">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-bg-highlight rounded w-1/2" />
          <div className="h-3 bg-bg-highlight rounded w-3/4" />
          <div className="h-3 bg-bg-highlight rounded w-2/3" />
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card title="Agent Preview">
        <p className="text-accent-red text-sm">{error}</p>
      </Card>
    )
  }

  if (!preview) {
    return (
      <Card title="Agent Preview">
        <p className="text-fg-dim text-sm">
          Preview will appear here...
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-fg-primary font-bold text-lg">{preview.name}</h3>
            <p className="text-fg-dim text-sm">{preview.location_name}</p>
          </div>
          <Badge variant="magenta">{preview.personality_archetype}</Badge>
        </div>

        {/* Personality Description */}
        <div>
          <p className="text-fg-secondary text-sm italic line-clamp-3">
            "{preview.personality_prompt}"
          </p>
        </div>

        {/* Trait Summary */}
        <div className="bg-bg-primary rounded-lg p-3">
          <h4 className="text-fg-primary text-sm font-medium mb-2">Personality Analysis</h4>
          <p className="text-fg-secondary text-sm">{preview.trait_summary}</p>
        </div>

        {/* Traits Visualization */}
        <div>
          <h4 className="text-fg-primary text-sm font-medium mb-2">Traits</h4>
          <TraitDisplay traits={preview.traits} />
        </div>

        {/* Compatibility Notes */}
        {preview.compatibility_notes && preview.compatibility_notes.length > 0 && (
          <div>
            <h4 className="text-fg-primary text-sm font-medium mb-2">Village Interactions</h4>
            <ul className="space-y-1">
              {preview.compatibility_notes.map((note, index) => (
                <li key={index} className="text-fg-secondary text-sm flex items-start gap-2">
                  <span className="text-accent-cyan">•</span>
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  )
}

// Quota display component
export function QuotaDisplay({
  quota,
  isLoading,
}: {
  quota: { max_agents: number; agents_created: number; remaining: number; can_create: boolean; next_creation_available_at: number | null } | null
  isLoading: boolean
}) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-fg-dim text-sm">
        <span className="animate-pulse">Loading quota...</span>
      </div>
    )
  }

  if (!quota) {
    return (
      <div className="flex items-center gap-2 text-fg-dim text-sm">
        <span>Log in to see your quota</span>
      </div>
    )
  }

  const formatTimeRemaining = (timestamp: number): string => {
    const now = Date.now() / 1000
    const remaining = timestamp - now
    if (remaining <= 0) return 'now'
    const minutes = Math.ceil(remaining / 60)
    if (minutes < 60) return `${minutes}m`
    const hours = Math.ceil(minutes / 60)
    return `${hours}h`
  }

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-fg-dim">Agents:</span>
        <span className={quota.remaining > 0 ? 'text-accent-green' : 'text-accent-red'}>
          {quota.agents_created}/{quota.max_agents}
        </span>
      </div>
      {!quota.can_create && quota.next_creation_available_at && (
        <div className="flex items-center gap-2">
          <span className="text-fg-dim">Next available:</span>
          <span className="text-accent-yellow">
            {formatTimeRemaining(quota.next_creation_available_at)}
          </span>
        </div>
      )}
      {quota.can_create && (
        <Badge variant="green">Ready to create</Badge>
      )}
    </div>
  )
}
