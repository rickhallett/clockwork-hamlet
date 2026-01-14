import { useRef, useEffect, useCallback, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Terminal } from '../common'
import { EventCard } from './EventCard'
import type { VillageEvent } from '../../hooks'

interface EventStreamProps {
  events: VillageEvent[]
  isPaused: boolean
  onPause: () => void
  onResume: () => void
  className?: string
  groupByTime?: boolean
}

interface EventGroup {
  label: string
  events: VillageEvent[]
}

function getTimeGroupLabel(timestamp: string): string {
  const now = new Date()
  const eventTime = new Date(timestamp)
  const diffMs = now.getTime() - eventTime.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 5) return 'Last 5 minutes'
  if (diffMinutes < 15) return 'Last 15 minutes'
  if (diffMinutes < 30) return 'Last 30 minutes'
  if (diffMinutes < 60) return 'Last hour'

  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 2) return '1 hour ago'
  if (diffHours < 6) return `${diffHours} hours ago`
  if (diffHours < 12) return 'Earlier today'
  if (diffHours < 24) return 'Today'

  return 'Older'
}

function groupEventsByTime(events: VillageEvent[]): EventGroup[] {
  const groups: Map<string, VillageEvent[]> = new Map()

  for (const event of events) {
    const label = getTimeGroupLabel(event.timestamp)
    const existing = groups.get(label) || []
    existing.push(event)
    groups.set(label, existing)
  }

  return Array.from(groups.entries()).map(([label, groupEvents]) => ({
    label,
    events: groupEvents,
  }))
}

function TimeGroupHeader({ label, count }: { label: string; count: number }) {
  return (
    <div className="sticky top-0 bg-bg-secondary/95 backdrop-blur-sm border-b border-bg-highlight px-3 py-2 mb-2 -mx-3">
      <div className="flex items-center justify-between">
        <span className="text-fg-secondary text-sm font-medium">{label}</span>
        <span className="text-fg-dim text-xs">{count} event{count !== 1 ? 's' : ''}</span>
      </div>
    </div>
  )
}

// Estimated height of each event card row (including gap)
const ESTIMATED_ROW_HEIGHT = 72

export function EventStream({
  events,
  isPaused,
  onPause,
  onResume,
  className = '',
  groupByTime = false,
}: EventStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const isUserScrolling = useRef(false)

  const groupedEvents = useMemo(() => {
    if (!groupByTime) return null
    return groupEventsByTime(events)
  }, [events, groupByTime])

  const virtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ESTIMATED_ROW_HEIGHT,
    overscan: 5,
  })

  // Auto-scroll to top when new events arrive (if not paused)
  useEffect(() => {
    if (!isPaused && !isUserScrolling.current && scrollRef.current) {
      scrollRef.current.scrollTop = 0
    }
  }, [events, isPaused])

  const handleMouseEnter = useCallback(() => {
    onPause()
  }, [onPause])

  const handleMouseLeave = useCallback(() => {
    onResume()
    isUserScrolling.current = false
  }, [onResume])

  const handleScroll = useCallback(() => {
    if (scrollRef.current) {
      // If user scrolls away from top, mark as user scrolling
      isUserScrolling.current = scrollRef.current.scrollTop > 50
    }
  }, [])

  const renderGroupedEvents = () => (
    <div className="space-y-4">
      {groupedEvents?.map((group) => (
        <div key={group.label} className="relative">
          <TimeGroupHeader label={group.label} count={group.events.length} />
          <div className="space-y-1">
            {group.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )

  const virtualItems = virtualizer.getVirtualItems()

  const renderVirtualizedEvents = () => (
    <div
      style={{
        height: `${virtualizer.getTotalSize()}px`,
        width: '100%',
        position: 'relative',
      }}
    >
      {virtualItems.map((virtualItem) => {
        const event = events[virtualItem.index]
        return (
          <div
            key={event.id}
            data-index={virtualItem.index}
            ref={virtualizer.measureElement}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <EventCard event={event} />
          </div>
        )
      })}
    </div>
  )

  return (
    <Terminal title="event_stream.log" className={className}>
      <div
        ref={scrollRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onScroll={handleScroll}
        className="max-h-[600px] overflow-y-auto scrollbar-thin scrollbar-thumb-bg-highlight scrollbar-track-transparent"
      >
        {isPaused && (
          <div className="sticky top-0 z-10 bg-accent-yellow/10 border border-accent-yellow/30 rounded-lg px-3 py-2 mb-3 text-sm text-accent-yellow">
            Stream paused - hover to browse
          </div>
        )}

        {events.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-fg-dim animate-pulse">Waiting for events...</p>
          </div>
        ) : groupByTime ? (
          renderGroupedEvents()
        ) : (
          renderVirtualizedEvents()
        )}

        {events.length > 0 && (
          <div className="pt-4 border-t border-bg-highlight mt-4">
            <p className="text-fg-dim text-sm text-center">
              {events.length} event{events.length !== 1 ? 's' : ''} in feed
            </p>
          </div>
        )}
      </div>
    </Terminal>
  )
}
