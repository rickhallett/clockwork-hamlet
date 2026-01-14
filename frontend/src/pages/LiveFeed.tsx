import { useState, useCallback, useMemo } from 'react'
import { useVillageStream, VillageEvent } from '../hooks'
import { EventStream, FilterBar } from '../components/feed'

export function LiveFeed() {
  const [activeTypes, setActiveTypes] = useState<string[]>([])
  const [groupByTime, setGroupByTime] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const filters = useMemo(
    () => ({
      types: activeTypes.length > 0 ? activeTypes : undefined,
    }),
    [activeTypes]
  )

  const { events, isConnected, isPaused, error, pause, resume, clearEvents } =
    useVillageStream({ filters, maxEvents: 100 })

  // Filter events by search query (client-side)
  const filteredEvents = useMemo(() => {
    if (!searchQuery.trim()) return events

    const query = searchQuery.toLowerCase()
    return events.filter((event: VillageEvent) => {
      const searchableText = [
        event.summary,
        event.agent_name,
        event.location_name,
        event.type,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      return searchableText.includes(query)
    })
  }, [events, searchQuery])

  const handleToggleType = useCallback((type: string) => {
    setActiveTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }, [])

  const handleClearFilters = useCallback(() => {
    setActiveTypes([])
    setSearchQuery('')
  }, [])

  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query)
  }, [])

  const handleToggleGrouping = useCallback(() => {
    setGroupByTime((prev) => !prev)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fg-primary mb-2">Live Feed</h1>
          <p className="text-fg-secondary">
            Watch the village come alive in real-time.
          </p>
        </div>
        <div className="flex items-center gap-4">
          {error && (
            <span className="text-accent-yellow text-sm">{error}</span>
          )}
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-accent-green animate-pulse' : 'bg-accent-red'
              }`}
            />
            <span className="text-fg-dim text-sm">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <button
            onClick={clearEvents}
            className="text-fg-dim text-sm hover:text-accent-red transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      <FilterBar
        activeTypes={activeTypes}
        onToggleType={handleToggleType}
        onClear={handleClearFilters}
        groupByTime={groupByTime}
        onToggleGrouping={handleToggleGrouping}
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
      />

      <EventStream
        events={filteredEvents}
        isPaused={isPaused}
        onPause={pause}
        onResume={resume}
        groupByTime={groupByTime}
        className="min-h-[500px]"
      />
    </div>
  )
}
