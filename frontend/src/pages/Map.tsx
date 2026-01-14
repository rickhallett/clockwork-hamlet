import { useState, useRef, useEffect } from 'react'
import { Card } from '../components/common'
import { VillageMap, LocationDetail } from '../components/map'
import { useLocations, useAgents } from '../hooks'

export function Map() {
  const { locations, isLoading: locationsLoading, error: locationsError } = useLocations()
  const { agents, isLoading: agentsLoading } = useAgents()
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 600, height: 500 })

  // Update dimensions based on container size
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({
          width: rect.width,
          height: Math.max(400, Math.min(600, rect.width * 0.75)),
        })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const selectedLocationData = selectedLocation
    ? locations.find((loc) => loc.id === selectedLocation)
    : null

  const isLoading = locationsLoading || agentsLoading

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-fg-primary mb-2">Village Map</h1>
        <p className="text-fg-secondary">
          Explore Clockwork Hamlet. Click on a location to see who&apos;s there.
        </p>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 text-sm flex-wrap">
        <span className="text-fg-dim">Key:</span>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-accent-blue flex items-center justify-center">
            <span className="text-[8px] font-bold text-bg-primary">3</span>
          </div>
          <span className="text-fg-secondary">Agent count</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-0.5 bg-bg-highlight" style={{ borderStyle: 'dashed' }} />
          <span className="text-fg-secondary">Paths</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full border-2 border-accent-magenta" />
          <span className="text-fg-secondary">Selected</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <Card className="lg:col-span-2 overflow-hidden p-0">
          <div ref={containerRef} className="w-full">
            {isLoading ? (
              <div
                className="flex items-center justify-center bg-bg-primary rounded-lg"
                style={{ height: dimensions.height }}
              >
                <div className="animate-pulse text-fg-dim">Loading village map...</div>
              </div>
            ) : locationsError ? (
              <div
                className="flex items-center justify-center bg-bg-primary rounded-lg"
                style={{ height: dimensions.height }}
              >
                <p className="text-accent-red">{locationsError}</p>
              </div>
            ) : (
              <VillageMap
                locations={locations}
                selectedLocation={selectedLocation}
                onLocationClick={setSelectedLocation}
                width={dimensions.width}
                height={dimensions.height}
              />
            )}
          </div>
        </Card>

        {/* Location detail panel */}
        <div className="lg:col-span-1">
          {selectedLocationData ? (
            <LocationDetail
              location={selectedLocationData}
              agents={agents}
              onClose={() => setSelectedLocation(null)}
            />
          ) : (
            <Card className="text-center py-12">
              <p className="text-fg-dim mb-2">Click a location on the map</p>
              <p className="text-fg-secondary text-sm">
                View details about each location and see which villagers are there
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* Location quick stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {locations.map((loc) => (
          <Card
            key={loc.id}
            className={`cursor-pointer transition-all ${
              selectedLocation === loc.id
                ? 'border-accent-magenta ring-1 ring-accent-magenta/50'
                : 'hover:border-accent-blue/50'
            }`}
            onClick={() => setSelectedLocation(loc.id)}
          >
            <div className="text-center">
              <span className="text-xl block mb-1">
                {loc.id === 'town_square' ? '\u26f2' :
                 loc.id === 'bakery' ? '\ud83c\udf5e' :
                 loc.id === 'tavern' ? '\ud83c\udf7a' :
                 loc.id === 'blacksmith' ? '\u2692\ufe0f' :
                 loc.id === 'church' ? '\u26ea' :
                 loc.id === 'inn' ? '\ud83c\udfe8' :
                 loc.id === 'garden' ? '\ud83c\udf3b' :
                 loc.id === 'mayor_house' ? '\ud83c\udfe0' :
                 loc.id === 'market' ? '\ud83c\udfea' : '\ud83d\udccd'}
              </span>
              <p className="text-xs text-fg-secondary truncate">{loc.name.split(' ')[0]}</p>
              <p className="text-accent-blue font-semibold mt-1">
                {loc.agents_present.length}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
