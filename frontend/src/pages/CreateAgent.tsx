import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card } from '../components/common/Card'
import { TraitSliders } from '../components/agent/TraitSliders'
import { PresetSelector } from '../components/agent/PresetSelector'
import { AgentPreview, QuotaDisplay } from '../components/agent/AgentPreview'
import {
  useTraitPresets,
  useLocations,
  useAgentCreation,
  DEFAULT_TRAITS,
  type Traits,
} from '../hooks/useAgentCreation'

// Simple auth hook - you may want to replace this with your actual auth implementation
function useAuth() {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('access_token')
  })

  const login = useCallback((newToken: string) => {
    localStorage.setItem('access_token', newToken)
    setToken(newToken)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setToken(null)
  }, [])

  return { token, login, logout, isAuthenticated: !!token }
}

export function CreateAgent() {
  const navigate = useNavigate()
  const { token, isAuthenticated } = useAuth()

  // Form state
  const [name, setName] = useState('')
  const [personalityPrompt, setPersonalityPrompt] = useState('')
  const [traits, setTraits] = useState<Traits>(DEFAULT_TRAITS)
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)
  const [selectedLocation, setSelectedLocation] = useState<string>('town_square')

  // API hooks
  const { presets, isLoading: presetsLoading, fetchPresetDetails } = useTraitPresets()
  const { locations, isLoading: locationsLoading } = useLocations()
  const {
    quota,
    quotaLoading,
    isCreating,
    error,
    setError,
    previewAgent,
    createAgent,
  } = useAgentCreation(token)

  // Validation state
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Handle preset selection
  const handlePresetSelect = useCallback((presetId: string | null, presetTraits?: Traits) => {
    setSelectedPreset(presetId)
    if (presetTraits) {
      setTraits(presetTraits)
    } else if (presetId === null) {
      // Reset to default when clearing preset
      setTraits(DEFAULT_TRAITS)
    }
  }, [])

  // Validation
  const validate = useCallback((): boolean => {
    const errors: Record<string, string> = {}

    if (!name || name.length < 2) {
      errors.name = 'Name must be at least 2 characters'
    } else if (name.length > 50) {
      errors.name = 'Name must be less than 50 characters'
    } else if (!/^[a-zA-Z][a-zA-Z\s'\-]*$/.test(name)) {
      errors.name = 'Name must start with a letter and contain only letters, spaces, apostrophes, and hyphens'
    }

    if (!personalityPrompt || personalityPrompt.length < 20) {
      errors.personalityPrompt = 'Personality description must be at least 20 characters'
    } else if (personalityPrompt.length > 1000) {
      errors.personalityPrompt = 'Personality description must be less than 1000 characters'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }, [name, personalityPrompt])

  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!validate()) {
      return
    }

    if (!isAuthenticated) {
      setError('Please log in to create an agent')
      return
    }

    if (!quota?.can_create) {
      setError('You cannot create an agent at this time. Check your quota.')
      return
    }

    const agent = await createAgent({
      name,
      personality_prompt: personalityPrompt,
      traits,
      location_id: selectedLocation,
      preset: selectedPreset || undefined,
    })

    if (agent) {
      // Navigate to the new agent's page
      navigate(`/agents/${agent.id}`)
    }
  }, [
    name,
    personalityPrompt,
    traits,
    selectedLocation,
    selectedPreset,
    validate,
    createAgent,
    navigate,
    isAuthenticated,
    quota,
    setError,
  ])

  // Clear error when inputs change
  useEffect(() => {
    setError(null)
  }, [name, personalityPrompt, traits, selectedLocation, setError])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-fg-primary mb-2">Create New Agent</h1>
        <p className="text-fg-secondary">
          Design a new villager to join the simulation. Configure their personality traits
          and watch them come to life.
        </p>
      </div>

      {/* Quota Display */}
      <div className="flex items-center justify-between">
        <QuotaDisplay quota={quota} isLoading={quotaLoading} />
        {!isAuthenticated && (
          <p className="text-accent-yellow text-sm">
            Log in to create agents
          </p>
        )}
      </div>

      {/* Main Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Form */}
        <div className="space-y-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <Card title="Basic Information">
              <div className="space-y-4">
                {/* Name Input */}
                <div>
                  <label htmlFor="name" className="block text-fg-primary text-sm font-medium mb-1">
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter agent name..."
                    className={`w-full bg-bg-primary border rounded px-3 py-2 text-fg-primary placeholder:text-fg-dim focus:outline-none focus:border-accent-cyan transition-colors ${
                      validationErrors.name ? 'border-accent-red' : 'border-bg-highlight'
                    }`}
                  />
                  {validationErrors.name && (
                    <p className="text-accent-red text-xs mt-1">{validationErrors.name}</p>
                  )}
                </div>

                {/* Personality Prompt */}
                <div>
                  <label htmlFor="personality" className="block text-fg-primary text-sm font-medium mb-1">
                    Personality Description
                  </label>
                  <textarea
                    id="personality"
                    value={personalityPrompt}
                    onChange={(e) => setPersonalityPrompt(e.target.value)}
                    placeholder="Describe your agent's personality, background, and quirks..."
                    rows={4}
                    className={`w-full bg-bg-primary border rounded px-3 py-2 text-fg-primary placeholder:text-fg-dim focus:outline-none focus:border-accent-cyan transition-colors resize-none ${
                      validationErrors.personalityPrompt ? 'border-accent-red' : 'border-bg-highlight'
                    }`}
                  />
                  <div className="flex justify-between mt-1">
                    {validationErrors.personalityPrompt ? (
                      <p className="text-accent-red text-xs">{validationErrors.personalityPrompt}</p>
                    ) : (
                      <span />
                    )}
                    <span className={`text-xs ${personalityPrompt.length > 1000 ? 'text-accent-red' : 'text-fg-dim'}`}>
                      {personalityPrompt.length}/1000
                    </span>
                  </div>
                </div>

                {/* Location Selector */}
                <div>
                  <label htmlFor="location" className="block text-fg-primary text-sm font-medium mb-1">
                    Starting Location
                  </label>
                  <select
                    id="location"
                    value={selectedLocation}
                    onChange={(e) => setSelectedLocation(e.target.value)}
                    disabled={locationsLoading}
                    className="w-full bg-bg-primary border border-bg-highlight rounded px-3 py-2 text-fg-primary focus:outline-none focus:border-accent-cyan transition-colors"
                  >
                    {locationsLoading ? (
                      <option>Loading locations...</option>
                    ) : (
                      locations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                          {loc.name}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              </div>
            </Card>

            {/* Presets */}
            <Card>
              <PresetSelector
                presets={presets}
                selectedPreset={selectedPreset}
                onSelect={handlePresetSelect}
                onFetchDetails={fetchPresetDetails}
                disabled={presetsLoading}
              />
            </Card>

            {/* Trait Sliders */}
            <Card title="Personality Traits">
              <p className="text-fg-dim text-sm mb-4">
                Adjust individual traits to fine-tune your agent's personality.
              </p>
              <TraitSliders
                traits={traits}
                onChange={setTraits}
              />
            </Card>

            {/* Submit Button */}
            <div className="space-y-3">
              {error && (
                <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-3">
                  <p className="text-accent-red text-sm">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={isCreating || !isAuthenticated || !quota?.can_create}
                className={`w-full py-3 rounded-lg font-medium transition-all ${
                  isCreating || !isAuthenticated || !quota?.can_create
                    ? 'bg-bg-highlight text-fg-dim cursor-not-allowed'
                    : 'bg-accent-cyan text-bg-primary hover:bg-accent-cyan/90'
                }`}
              >
                {isCreating ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⚙️</span>
                    Creating Agent...
                  </span>
                ) : !isAuthenticated ? (
                  'Log in to Create Agent'
                ) : !quota?.can_create ? (
                  'Cannot Create Agent'
                ) : (
                  'Create Agent'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Right Column - Preview */}
        <div className="lg:sticky lg:top-6 space-y-4">
          <h2 className="text-lg font-medium text-fg-primary">Preview</h2>
          <AgentPreview
            name={name}
            personalityPrompt={personalityPrompt}
            traits={traits}
            locationId={selectedLocation}
            onPreview={previewAgent}
          />
        </div>
      </div>
    </div>
  )
}
