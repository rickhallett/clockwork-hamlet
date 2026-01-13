import { Terminal, Badge } from '../components/common'

// Placeholder event data - will be replaced with SSE stream
const events = [
  { type: 'movement', summary: 'Agnes walked to the Town Square', time: '2 min ago' },
  { type: 'dialogue', summary: 'Bob greeted Agnes warmly', time: '3 min ago' },
  { type: 'action', summary: 'Martha examined the notice board', time: '5 min ago' },
  { type: 'dialogue', summary: 'Agnes: "Good morning, Bob!"', time: '6 min ago' },
  { type: 'movement', summary: 'Martha left the Tavern', time: '8 min ago' },
]

function getEventColor(type: string): 'blue' | 'green' | 'yellow' | 'magenta' | 'cyan' {
  switch (type) {
    case 'movement': return 'cyan'
    case 'dialogue': return 'green'
    case 'action': return 'yellow'
    case 'relationship': return 'magenta'
    default: return 'blue'
  }
}

export function LiveFeed() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fg-primary mb-2">Live Feed</h1>
          <p className="text-fg-secondary">
            Watch the village come alive in real-time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
          <span className="text-fg-dim text-sm">Connected</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 flex-wrap">
        <Badge variant="cyan" className="cursor-pointer hover:opacity-80">movement</Badge>
        <Badge variant="green" className="cursor-pointer hover:opacity-80">dialogue</Badge>
        <Badge variant="yellow" className="cursor-pointer hover:opacity-80">action</Badge>
        <Badge variant="magenta" className="cursor-pointer hover:opacity-80">relationship</Badge>
      </div>

      {/* Event stream */}
      <Terminal title="event_stream.log" className="min-h-[500px]">
        <div className="space-y-3">
          {events.map((event, idx) => (
            <div key={idx} className="flex items-start gap-3">
              <Badge variant={getEventColor(event.type)} className="shrink-0 mt-0.5">
                {event.type}
              </Badge>
              <div className="flex-1">
                <p className="text-fg-secondary">{event.summary}</p>
                <p className="text-fg-dim text-xs mt-1">{event.time}</p>
              </div>
            </div>
          ))}

          <div className="pt-4 border-t border-bg-highlight">
            <p className="text-fg-dim text-sm animate-pulse">
              Waiting for new events...
            </p>
          </div>
        </div>
      </Terminal>
    </div>
  )
}
