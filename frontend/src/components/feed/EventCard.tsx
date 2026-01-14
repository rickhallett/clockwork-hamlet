import { Badge } from '../common'
import type { VillageEvent } from '../../hooks'

interface EventCardProps {
  event: VillageEvent
}

type BadgeVariant = 'blue' | 'green' | 'yellow' | 'magenta' | 'cyan' | 'red'

function getEventColor(type: string): BadgeVariant {
  switch (type) {
    case 'movement':
      return 'cyan'
    case 'dialogue':
      return 'green'
    case 'action':
      return 'yellow'
    case 'relationship':
      return 'magenta'
    case 'goal':
      return 'blue'
    case 'system':
      return 'red'
    default:
      return 'blue'
  }
}

function getEventIcon(type: string): string {
  switch (type) {
    case 'movement':
      return '\u2192' // →
    case 'dialogue':
      return '\u201C' // "
    case 'action':
      return '\u2605' // ★
    case 'relationship':
      return '\u2665' // ♥
    case 'goal':
      return '\u2713' // ✓
    case 'system':
      return '\u2699' // ⚙
    default:
      return '\u25CF' // ●
  }
}

interface SignificanceIndicatorProps {
  level: 1 | 2 | 3
}

function SignificanceIndicator({ level }: SignificanceIndicatorProps) {
  // Level 1: Minor event (default, subtle)
  // Level 2: Notable event (medium emphasis)
  // Level 3: Major event (high emphasis)
  const config = {
    1: { icon: '\u2022', color: 'text-fg-dim', title: 'Minor' }, // •
    2: { icon: '\u25C6', color: 'text-accent-yellow', title: 'Notable' }, // ◆
    3: { icon: '\u2605', color: 'text-accent-red', title: 'Major' }, // ★
  }

  const { icon, color, title } = config[level]

  return (
    <span className={`${color} text-xs`} title={`${title} event`}>
      {icon}
    </span>
  )
}

function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const eventTime = new Date(timestamp)
  const diffMs = now.getTime() - eventTime.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)

  if (diffSeconds < 10) return 'just now'
  if (diffSeconds < 60) return `${diffSeconds}s ago`

  const diffMinutes = Math.floor(diffSeconds / 60)
  if (diffMinutes < 60) return `${diffMinutes}m ago`

  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}

export function EventCard({ event }: EventCardProps) {
  const icon = getEventIcon(event.type)
  const color = getEventColor(event.type)
  const relativeTime = formatRelativeTime(event.timestamp)

  return (
    <div className="flex items-start gap-3 p-3 hover:bg-bg-highlight/50 rounded-lg transition-colors">
      <div className="flex items-center gap-2 shrink-0">
        <span className={`text-accent-${color} font-mono`}>{icon}</span>
        <Badge variant={color} className="text-xs">
          {event.type}
        </Badge>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-fg-secondary leading-relaxed">
          {event.agent_name && (
            <span className="text-accent-magenta font-medium">{event.agent_name} </span>
          )}
          {event.summary}
          {event.location_name && (
            <span className="text-fg-dim"> at {event.location_name}</span>
          )}
        </p>

        <div className="flex items-center gap-3 mt-1">
          <SignificanceIndicator level={event.significance} />
          <span className="text-fg-dim text-xs">{relativeTime}</span>
          {event.agent_id && (
            <span className="text-fg-dim text-xs">#{event.agent_id}</span>
          )}
        </div>
      </div>
    </div>
  )
}
