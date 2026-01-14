import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LocationDetail } from './LocationDetail'
import type { Location } from '../../hooks/useLocations'
import type { AgentSummary } from '../../hooks/useAgents'

const mockLocation: Location = {
  id: 'town_square',
  name: 'Town Square',
  description: 'The center of the village',
  connections: ['bakery', 'tavern', 'church'],
  objects: ['fountain', 'bench'],
  capacity: 20,
  agents_present: ['agnes', 'bob'],
}

const mockAgents: AgentSummary[] = [
  { id: 'agnes', name: 'Agnes', state: 'idle', location_id: 'town_square', location_name: 'Town Square' },
  { id: 'bob', name: 'Bob', state: 'busy', location_id: 'town_square', location_name: 'Town Square' },
  { id: 'martha', name: 'Martha', state: 'sleeping', location_id: 'bakery', location_name: 'Bakery' },
]

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('LocationDetail', () => {
  it('renders location name and description', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    expect(screen.getByText('Town Square')).toBeInTheDocument()
    expect(screen.getByText('The center of the village')).toBeInTheDocument()
  })

  it('displays occupancy stats', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    // Should show "2 / 20" for occupants
    expect(screen.getByText('2 / 20')).toBeInTheDocument()
    // Should show "3 paths" for connections
    expect(screen.getByText('3 paths')).toBeInTheDocument()
  })

  it('lists agents present at the location', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    expect(screen.getByText('Agnes')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    // Martha is at the bakery, not town square
    expect(screen.queryByText('Martha')).not.toBeInTheDocument()
  })

  it('shows agent states with badges', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    expect(screen.getByText('idle')).toBeInTheDocument()
    expect(screen.getByText('busy')).toBeInTheDocument()
  })

  it('displays objects in the location', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    expect(screen.getByText('fountain')).toBeInTheDocument()
    expect(screen.getByText('bench')).toBeInTheDocument()
  })

  it('displays connected locations', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    expect(screen.getByText('bakery')).toBeInTheDocument()
    expect(screen.getByText('tavern')).toBeInTheDocument()
    expect(screen.getByText('church')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)
    expect(onClose).toHaveBeenCalled()
  })

  it('renders agent links to their profiles', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    const agnesLink = screen.getByText('Agnes').closest('a')
    expect(agnesLink).toHaveAttribute('href', '/agents/agnes')

    const bobLink = screen.getByText('Bob').closest('a')
    expect(bobLink).toHaveAttribute('href', '/agents/bob')
  })

  it('shows empty state when no agents present', () => {
    const emptyLocation: Location = {
      ...mockLocation,
      agents_present: [],
    }
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={emptyLocation} agents={mockAgents} onClose={onClose} />
    )

    expect(screen.getByText('No one is here right now')).toBeInTheDocument()
  })

  it('renders location icon', () => {
    const onClose = vi.fn()
    renderWithRouter(
      <LocationDetail location={mockLocation} agents={mockAgents} onClose={onClose} />
    )

    // Town square icon is the fountain emoji
    expect(screen.getByText('\u26f2')).toBeInTheDocument()
  })
})
