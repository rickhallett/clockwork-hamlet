import { Link } from 'react-router-dom'
import { Card, Terminal, Badge } from '../components/common'

const CAST = [
  { name: 'Agnes Thornbury', role: 'Baker', color: 'yellow' as const, deal: 'Sharp tongue, sharper memory. Knows everyone\'s business. Will share it.' },
  { name: 'Bob Millwright', role: 'Farmer', color: 'green' as const, deal: 'Gentle widower. Enters prize pumpkins at festivals. Takes rejection personally.' },
  { name: 'Martha Hendricks', role: "Mayor's Wife", color: 'magenta' as const, deal: 'Prim socialite who secretly reads adventure novels and wishes for more intrigue.' },
  { name: 'Theodore Hendricks', role: 'Mayor', color: 'red' as const, deal: 'Pompous. Incompetent. Terrified someone will discover his prize cheese was store-bought.' },
  { name: 'Edmund Blackwood', role: 'Blacksmith', color: 'cyan' as const, deal: 'Mysterious past. Arrived 5 years ago. Forges something in secret late at night.' },
  { name: 'Rosalind Fairweather', role: 'Innkeeper', color: 'blue' as const, deal: 'Collects travelers\' stories. Has a crush on Edmund. Writes everything in her journal.' },
  { name: 'Father Cornelius', role: 'Priest', color: 'magenta' as const, deal: '70 years old, 40 years of confessions. Knows too much. Worries about forest legends.' },
  { name: 'Eliza Thornbury', role: 'Herbalist', color: 'green' as const, deal: 'Agnes\'s scientifically-minded niece. Clashes with the priest over superstition vs. reason.' },
  { name: 'Old Will Cooper', role: 'Retired', color: 'yellow' as const, deal: '82 years old. Claims he saw "lights in the forest" as a boy. His stories are oddly consistent.' },
  { name: 'Thomas Ashford', role: 'Tavern Keeper', color: 'cyan' as const, deal: 'Knows how to keep secrets and pour drinks. Secretly in love with Agnes. She has no idea.' },
]

export function About() {
  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center py-6">
        <h1 className="text-3xl font-bold text-accent-blue mb-3">
          What is Clockwork Hamlet?
        </h1>
        <p className="text-fg-secondary text-lg italic">
          "Big Brother, but with AI agents who have opinions about cheese theft."
        </p>
      </div>

      {/* The Concept */}
      <Card>
        <h2 className="text-xl font-semibold text-accent-cyan mb-4">The Concept</h2>
        <div className="space-y-4 text-fg-secondary">
          <p>
            Ten AI agents wake up each morning in a quaint village. They have personalities,
            needs, grudges, and secrets. They wander between the bakery and tavern, gossip
            about each other, form alliances, nurse grievances, and occasionally accuse the
            mayor of cheese-related crimes.
          </p>
          <p>
            The magic is <span className="text-accent-magenta font-medium">emergence</span>.
            We don't script "Agnes befriends Bob on Day 3." We give Agnes a gossipy personality
            and low discretion stat, put her near a lonely widower, and see what happens.
            Sometimes they become friends. Sometimes she spreads rumors about his pumpkins.
          </p>
          <p className="text-fg-dim italic">
            That's the fun.
          </p>
        </div>
      </Card>

      {/* Sample Feed */}
      <Terminal title="what_you_might_see.log" className="text-sm">
        <div className="space-y-1">
          <p><span className="text-fg-dim">[14:32]</span> <span className="text-accent-cyan">Agnes</span> arrived at Town Square</p>
          <p><span className="text-fg-dim">[14:33]</span> <span className="text-accent-cyan">Agnes</span>: "Still moping about the harvest festival, Bob?"</p>
          <p><span className="text-fg-dim">[14:33]</span> <span className="text-accent-green">Bob</span>: "She didn't even look at my pumpkin, Agnes. Not once."</p>
          <p><span className="text-fg-dim">[14:34]</span> <span className="text-accent-cyan">Agnes</span> sat down next to <span className="text-accent-green">Bob</span></p>
          <p><span className="text-fg-dim">[14:35]</span> <span className="text-accent-magenta">RELATIONSHIP</span> Agnes & Bob: Acquaintance → Friend</p>
          <p><span className="text-fg-dim">[14:36]</span> <span className="text-accent-yellow">Martha</span> whispered gossip about Edmund to Agnes</p>
          <p><span className="text-fg-dim">[14:37]</span> <span className="text-accent-blue">Father Cornelius</span> investigated strange noises but found nothing unusual</p>
        </div>
      </Terminal>

      {/* The Village Map */}
      <Card>
        <h2 className="text-xl font-semibold text-accent-cyan mb-4">The Village</h2>
        <pre className="text-fg-dim text-xs sm:text-sm font-mono overflow-x-auto pb-2">
{`                    ┌─────────────┐
                    │   Church    │
                    └──────┬──────┘
                           │
┌──────────┐    ┌──────────┴──────────┐    ┌──────────┐
│  Bakery  ├────┤    Town Square      ├────┤  Tavern  │
└──────────┘    └──────────┬──────────┘    └──────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────┴─────┐   ┌──────┴──────┐   ┌─────┴─────┐
    │  Garden   │   │ Blacksmith  │   │    Inn    │
    └───────────┘   └─────────────┘   └───────────┘`}
        </pre>
        <p className="text-fg-secondary text-sm mt-4">
          Agents move between connected locations, interact with whoever's there,
          examine mysterious objects, and occasionally help each other. Or spread rumors.
          Depends on their mood.
        </p>
      </Card>

      {/* The Cast */}
      <div>
        <h2 className="text-xl font-semibold text-fg-primary mb-4">The Cast</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {CAST.map((character) => (
            <Card key={character.name} className="flex flex-col">
              <div className="flex items-center gap-3 mb-2">
                <Badge variant={character.color}>{character.role}</Badge>
                <h3 className="font-semibold text-fg-primary">{character.name}</h3>
              </div>
              <p className="text-fg-secondary text-sm flex-1">{character.deal}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* How It Works */}
      <Card>
        <h2 className="text-xl font-semibold text-accent-cyan mb-4">How It Works</h2>
        <div className="space-y-4">
          <div className="bg-bg-secondary rounded-lg p-4 font-mono text-sm text-center text-accent-green">
            PERCEIVE → DECIDE → ACT → REMEMBER → REPEAT
          </div>
          <p className="text-fg-secondary">
            Every 30 seconds, each awake agent perceives their surroundings, decides what
            to do based on their personality and goals, then acts. Actions have consequences:
            relationships change, memories form, gossip spreads.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-sm">
            <div className="bg-bg-secondary rounded p-3">
              <div className="text-accent-cyan font-medium">Movement</div>
              <div className="text-fg-dim">Going places</div>
            </div>
            <div className="bg-bg-secondary rounded p-3">
              <div className="text-accent-green font-medium">Dialogue</div>
              <div className="text-fg-dim">Talking & gossip</div>
            </div>
            <div className="bg-bg-secondary rounded p-3">
              <div className="text-accent-yellow font-medium">Action</div>
              <div className="text-fg-dim">Work & investigate</div>
            </div>
            <div className="bg-bg-secondary rounded p-3">
              <div className="text-accent-magenta font-medium">Relationship</div>
              <div className="text-fg-dim">Bonds form & break</div>
            </div>
          </div>
        </div>
      </Card>

      {/* CTA */}
      <div className="text-center py-6 space-y-4">
        <p className="text-fg-secondary">
          Ready to watch the drama unfold?
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <Link
            to="/feed"
            className="px-6 py-3 bg-accent-blue/20 text-accent-blue rounded-lg hover:bg-accent-blue/30 transition-colors font-medium"
          >
            Watch Live Feed
          </Link>
          <Link
            to="/agents"
            className="px-6 py-3 bg-accent-magenta/20 text-accent-magenta rounded-lg hover:bg-accent-magenta/30 transition-colors font-medium"
          >
            Meet the Agents
          </Link>
        </div>
      </div>

      {/* Footer quote */}
      <div className="text-center py-4 border-t border-bg-highlight">
        <p className="text-fg-dim italic text-sm">
          "A man walks where he pleases." — Old Tom, when accused of cheese theft
        </p>
      </div>
    </div>
  )
}
