import { useRef, useEffect, useCallback } from 'react'
import { Terminal } from '../common'
import { EventCard } from './EventCard'
import type { VillageEvent } from '../../hooks'

interface EventStreamProps {
  events: VillageEvent[]
  isPaused: boolean
  onPause: () => void
  onResume: () => void
  className?: string
}

export function EventStream({
  events,
  isPaused,
  onPause,
  onResume,
  className = '',
}: EventStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const isUserScrolling = useRef(false)

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
          <div className="sticky top-0 bg-accent-yellow/10 border border-accent-yellow/30 rounded-lg px-3 py-2 mb-3 text-sm text-accent-yellow">
            Stream paused - hover to browse
          </div>
        )}

        {events.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-fg-dim animate-pulse">Waiting for events...</p>
          </div>
        ) : (
          <div className="space-y-1">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
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
