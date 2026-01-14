import { useState, useMemo } from 'react'
import type { Location } from '../../hooks/useLocations'

// Location coordinates on the SVG canvas (relative positions)
// Arranged in a roughly village-like layout
const LOCATION_POSITIONS: Record<string, { x: number; y: number }> = {
  town_square: { x: 50, y: 50 },
  bakery: { x: 25, y: 35 },
  tavern: { x: 75, y: 35 },
  blacksmith: { x: 20, y: 65 },
  church: { x: 50, y: 20 },
  inn: { x: 80, y: 60 },
  garden: { x: 35, y: 75 },
  mayor_house: { x: 65, y: 75 },
  market: { x: 50, y: 85 },
}

// Icons for each location type
const LOCATION_ICONS: Record<string, string> = {
  town_square: '\u26f2', // Fountain
  bakery: '\ud83c\udf5e', // Bread
  tavern: '\ud83c\udf7a', // Beer
  blacksmith: '\u2692\ufe0f', // Hammer
  church: '\u26ea', // Church
  inn: '\ud83c\udfe8', // Hotel
  garden: '\ud83c\udf3b', // Sunflower
  mayor_house: '\ud83c\udfe0', // House
  market: '\ud83c\udfea', // Shop
}

interface VillageMapProps {
  locations: Location[]
  selectedLocation: string | null
  onLocationClick: (locationId: string) => void
  width?: number
  height?: number
}

interface LocationNodeProps {
  location: Location
  x: number
  y: number
  isSelected: boolean
  onClick: () => void
}

function LocationNode({ location, x, y, isSelected, onClick }: LocationNodeProps) {
  const [isHovered, setIsHovered] = useState(false)
  const agentCount = location.agents_present.length
  const icon = LOCATION_ICONS[location.id] || '\ud83d\udccd'

  // Calculate size based on agent count
  const baseRadius = 24
  const radius = baseRadius + Math.min(agentCount * 2, 12)

  return (
    <g
      transform={`translate(${x}, ${y})`}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ cursor: 'pointer' }}
    >
      {/* Outer glow for selected/hovered */}
      {(isSelected || isHovered) && (
        <circle
          r={radius + 6}
          fill="none"
          stroke={isSelected ? '#bb9af7' : '#7dcfff'}
          strokeWidth={2}
          opacity={0.6}
        />
      )}

      {/* Main circle background */}
      <circle
        r={radius}
        fill={isSelected ? '#bb9af7' : isHovered ? '#414868' : '#24283b'}
        stroke={isSelected ? '#bb9af7' : '#565f89'}
        strokeWidth={2}
      />

      {/* Location icon */}
      <text
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={18}
        fill="#c0caf5"
        style={{ pointerEvents: 'none' }}
      >
        {icon}
      </text>

      {/* Agent count badge */}
      {agentCount > 0 && (
        <g transform={`translate(${radius - 4}, ${-radius + 4})`}>
          <circle r={10} fill="#7aa2f7" />
          <text
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={11}
            fontWeight="bold"
            fill="#1a1b26"
            style={{ pointerEvents: 'none' }}
          >
            {agentCount}
          </text>
        </g>
      )}

      {/* Location name label */}
      <text
        y={radius + 14}
        textAnchor="middle"
        fontSize={11}
        fill={isSelected || isHovered ? '#c0caf5' : '#a9b1d6'}
        fontFamily="JetBrains Mono, monospace"
        style={{ pointerEvents: 'none' }}
      >
        {location.name.split(' ').slice(0, 2).join(' ')}
      </text>
    </g>
  )
}

export function VillageMap({
  locations,
  selectedLocation,
  onLocationClick,
  width = 600,
  height = 500,
}: VillageMapProps) {
  // Map locations to their positions
  const locationData = useMemo(() => {
    return locations.map((loc) => ({
      location: loc,
      position: LOCATION_POSITIONS[loc.id] || { x: 50, y: 50 },
    }))
  }, [locations])

  // Calculate connections between locations
  const connections = useMemo(() => {
    const lines: Array<{ from: { x: number; y: number }; to: { x: number; y: number } }> = []
    const addedConnections = new Set<string>()

    locations.forEach((loc) => {
      const fromPos = LOCATION_POSITIONS[loc.id]
      if (!fromPos) return

      loc.connections.forEach((connId) => {
        const toPos = LOCATION_POSITIONS[connId]
        if (!toPos) return

        // Avoid duplicate connections (A-B and B-A)
        const connectionKey = [loc.id, connId].sort().join('-')
        if (addedConnections.has(connectionKey)) return
        addedConnections.add(connectionKey)

        lines.push({
          from: fromPos,
          to: toPos,
        })
      })
    })

    return lines
  }, [locations])

  // Convert percentage positions to actual coordinates
  const scaleX = (pct: number) => (pct / 100) * width
  const scaleY = (pct: number) => (pct / 100) * height

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="bg-bg-primary rounded-lg"
    >
      {/* Background pattern - grass/terrain */}
      <defs>
        <pattern id="village-bg" patternUnits="userSpaceOnUse" width="20" height="20">
          <circle cx="10" cy="10" r="1" fill="#1e1f2a" opacity="0.5" />
        </pattern>
      </defs>
      <rect width={width} height={height} fill="url(#village-bg)" rx={8} />

      {/* Connection paths between locations */}
      <g className="connections">
        {connections.map((conn, idx) => (
          <line
            key={idx}
            x1={scaleX(conn.from.x)}
            y1={scaleY(conn.from.y)}
            x2={scaleX(conn.to.x)}
            y2={scaleY(conn.to.y)}
            stroke="#414868"
            strokeWidth={2}
            strokeDasharray="6 4"
            opacity={0.5}
          />
        ))}
      </g>

      {/* Location nodes */}
      <g className="locations">
        {locationData.map(({ location, position }) => (
          <LocationNode
            key={location.id}
            location={location}
            x={scaleX(position.x)}
            y={scaleY(position.y)}
            isSelected={selectedLocation === location.id}
            onClick={() => onLocationClick(location.id)}
          />
        ))}
      </g>

      {/* Title */}
      <text
        x={width / 2}
        y={20}
        textAnchor="middle"
        fontSize={14}
        fill="#565f89"
        fontFamily="JetBrains Mono, monospace"
      >
        Clockwork Hamlet
      </text>
    </svg>
  )
}
