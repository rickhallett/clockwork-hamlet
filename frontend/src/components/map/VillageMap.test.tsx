import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VillageMap } from './VillageMap'
import type { Location } from '../../hooks/useLocations'

const mockLocations: Location[] = [
  {
    id: 'town_square',
    name: 'Town Square',
    description: 'The center of the village',
    connections: ['bakery', 'tavern'],
    objects: ['fountain', 'bench'],
    capacity: 20,
    agents_present: ['agnes', 'bob'],
  },
  {
    id: 'bakery',
    name: 'The Warm Hearth Bakery',
    description: 'A cozy bakery',
    connections: ['town_square'],
    objects: ['oven', 'counter'],
    capacity: 5,
    agents_present: ['martha'],
  },
  {
    id: 'tavern',
    name: 'The Rusty Tankard',
    description: 'Village tavern',
    connections: ['town_square'],
    objects: ['bar', 'tables'],
    capacity: 15,
    agents_present: [],
  },
]

describe('VillageMap', () => {
  it('renders all locations', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
      />
    )

    // Check that SVG is rendered
    const svg = document.querySelector('svg')
    expect(svg).toBeInTheDocument()

    // Check location labels are rendered (first word or two of name)
    expect(screen.getByText('Town Square')).toBeInTheDocument()
    expect(screen.getByText('The Warm')).toBeInTheDocument()
    expect(screen.getByText('The Rusty')).toBeInTheDocument()
  })

  it('displays agent count badges for occupied locations', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
      />
    )

    // Town Square has 2 agents
    expect(screen.getByText('2')).toBeInTheDocument()
    // Bakery has 1 agent
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('calls onLocationClick when a location is clicked', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
      />
    )

    // Find and click the Town Square location group
    const townSquareLabel = screen.getByText('Town Square')
    const locationGroup = townSquareLabel.closest('g')
    expect(locationGroup).toBeInTheDocument()

    if (locationGroup) {
      fireEvent.click(locationGroup)
      expect(onLocationClick).toHaveBeenCalledWith('town_square')
    }
  })

  it('renders connection paths between locations', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
      />
    )

    // Check that connection lines are rendered
    const lines = document.querySelectorAll('line')
    expect(lines.length).toBeGreaterThan(0)
  })

  it('applies selected styling when a location is selected', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation="town_square"
        onLocationClick={onLocationClick}
      />
    )

    // The selected location should have a highlighted circle
    const circles = document.querySelectorAll('circle')
    const selectedCircle = Array.from(circles).find(
      (c) => c.getAttribute('fill') === '#bb9af7'
    )
    expect(selectedCircle).toBeInTheDocument()
  })

  it('renders with custom dimensions', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
        width={800}
        height={600}
      />
    )

    const svg = document.querySelector('svg')
    expect(svg).toHaveAttribute('width', '800')
    expect(svg).toHaveAttribute('height', '600')
  })

  it('renders map title', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
      />
    )

    expect(screen.getByText('Clockwork Hamlet')).toBeInTheDocument()
  })

  it('renders location icons', () => {
    const onLocationClick = vi.fn()
    render(
      <VillageMap
        locations={mockLocations}
        selectedLocation={null}
        onLocationClick={onLocationClick}
      />
    )

    // Check for location-specific icons (fountain for town square, bread for bakery, beer for tavern)
    expect(screen.getByText('\u26f2')).toBeInTheDocument() // Fountain
    expect(screen.getByText('\ud83c\udf5e')).toBeInTheDocument() // Bread
    expect(screen.getByText('\ud83c\udf7a')).toBeInTheDocument() // Beer
  })
})
