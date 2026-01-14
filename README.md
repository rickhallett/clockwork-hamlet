# Clockwork Hamlet

> *"Big Brother, but with AI agents who have opinions about cheese theft."*

A persistent village simulation where 10 AI characters with distinct personalities live, gossip, scheme, and create emergent drama. We don't write storylines — we create conditions for stories to emerge. Then we watch the chaos unfold.

```
[14:32] Agnes arrived at Town Square
[14:33] Agnes: "Still moping about the harvest festival, Bob?"
[14:33] Bob: "She didn't even look at my pumpkin, Agnes. Not once."
[14:34] Agnes sat down next to Bob
[14:35] RELATIONSHIP CHANGE: Agnes & Bob (Acquaintance → Friend)
[14:36] Martha whispered gossip about Edmund to Agnes
[14:37] Father Cornelius investigated strange noises but found nothing unusual
```

## What Is This?

Ten AI agents wake up each morning in a quaint village. They have personalities, needs, grudges, and secrets. They wander between the bakery and tavern, gossip about each other, form alliances, nurse grievances, and occasionally accuse the mayor of cheese-related crimes.

The magic is **emergence**. We don't script "Agnes befriends Bob on Day 3." We give Agnes a gossipy personality and low discretion stat, put her near a lonely widower, and see what happens. Sometimes they become friends. Sometimes she spreads rumors about his pumpkins. That's the fun.

## The Cast

| Villager | Role | The Deal |
|----------|------|----------|
| **Agnes Thornbury** | Baker | Sharp tongue, sharper memory. Knows everyone's business. Will share it. |
| **Bob Millwright** | Farmer | Gentle widower. Enters prize pumpkins at festivals. Takes rejection personally. |
| **Martha Hendricks** | Mayor's Wife | Prim socialite who secretly reads adventure novels and wishes her life had more... intrigue. |
| **Theodore Hendricks** | Mayor | Pompous. Incompetent. Terrified someone will discover his prize cheese was store-bought. |
| **Edmund Blackwood** | Blacksmith | Mysterious past. Arrived 5 years ago. Forges something in secret late at night. |
| **Rosalind Fairweather** | Innkeeper | Collects travelers' stories. Has a crush on Edmund. Writes everything in her journal. |
| **Father Cornelius** | Priest | 70 years old, 40 years of confessions. Knows too much. Worries about forest legends. |
| **Eliza Thornbury** | Herbalist | Agnes's scientifically-minded niece. Clashes with the priest over superstition vs. reason. |
| **Old Will Cooper** | Retired | 82 years old. Claims he saw "lights in the forest" as a boy. Everyone thinks he's drunk. His stories are oddly consistent. |
| **Thomas Ashford** | Tavern Keeper | Knows how to keep secrets and pour drinks. Secretly in love with Agnes. She has no idea. |

## The Village

```
                    ┌─────────────┐
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
    └───────────┘   └─────────────┘   └───────────┘
```

Agents move between connected locations, interact with whoever's there, examine mysterious objects, and occasionally help each other carry supplies. Or spread rumors. Depends on their mood.

## What They Actually Do

Every 30 seconds, each awake agent:

1. **Perceives** their surroundings (who's nearby, what objects exist)
2. **Decides** what to do based on personality, needs, and goals
3. **Acts** — and actions have consequences

**Action Types:**
- `movement` — Agnes arrived at Town Square
- `dialogue` — Bob chatted with Martha about village news
- `action` — Thomas is busy serving
- `relationship` — Edmund's opinion of Theodore decreased
- `goal` — Eliza investigated strange noises and noticed something odd

Agents form memories. They track relationships (-10 hostile to +10 best friends). They gossip. They help. They scheme. They sleep at night and wake up with fresh grievances.

## Quick Start

```bash
# 1. Get the code
git clone <repo>
cd clockwork-hamlet

# 2. Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Run everything
docker-compose up -d --build

# 4. Watch the drama unfold
open http://localhost:3003
```

**Endpoints:**
- Frontend UI: `http://localhost:3003`
- Backend API: `http://localhost:8000`
- Live event stream: `http://localhost:8000/api/stream`

## Features

### Live Feed
Real-time stream of everything happening in the village. Filter by event type, pause to read, watch relationships evolve.

### Character Profiles
Click any agent to see their personality traits, current relationships, recent memories, and active goals. Watch Agnes's discretion stat and understand why she can't keep a secret.

### Relationship Graph
Force-directed visualization of who likes whom. Green edges for friends, red for rivals. Click a node to see that agent's perspective on everyone else.

### Daily Digest
LLM-generated newspaper summarizing the day's drama:

```
THE DAILY HAMLET - Day 47

HEADLINE: Mayor's Cheese Vanishes; Accusations Fly

In a scandal that has rocked our quiet village, Mayor Hendricks
arrived at his office this morning to find his prized wheel of
aged Gruyère missing from his desk drawer.

Suspicion has fallen on Old Tom, who was seen near the town hall
late last night. When confronted, Tom responded only with:
"A man walks where he pleases."

The investigation continues.
```

### Viewer Polls
Vote on what happens next. A stranger arrives — who are they? The harvest festival is tomorrow — what goes wrong? Polls inject events; agents react autonomously.

## Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| Backend | FastAPI + SQLAlchemy + SQLite | Async, simple, good enough |
| AI | Claude API | Cheap, fast, surprisingly good at being petty villagers |
| Frontend | React 18 + Vite + Tailwind | Tokyo Night aesthetic, terminal vibes |
| Streaming | Server-Sent Events | Real-time, browser-native, no WebSocket complexity |
| Deploy | Docker + nginx | One command, it works |

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  PERCEIVE → DECIDE → ACT → REMEMBER → REPEAT        │
└─────────────────────────────────────────────────────┘
```

**The Tick Loop** (every 30 seconds):
1. Advance world time
2. Update agent needs (hunger, energy, social)
3. Wake/sleep agents based on time of day
4. For each awake agent:
   - Build perception (location, nearby agents, objects)
   - LLM decides action based on personality + goals + context
   - Execute action with validation
   - Update relationships and memories
   - Broadcast event to SSE stream
5. Commit all changes

**What's Deterministic (no LLM cost):**
- Movement validation
- Relationship score math
- Time/need updates
- Event recording

**What Uses LLM:**
- "What do I want to do?" decisions
- Dialogue generation
- Emotional reactions
- Memory compression (daily)

**Monthly LLM cost:** ~$10-15 for 10 agents at 1 tick/30sec.

## API Reference

| Endpoint | What You Get |
|----------|--------------|
| `GET /api/stream` | SSE stream of live events |
| `GET /api/agents` | All 10 villagers |
| `GET /api/agents/{id}` | Full profile with traits |
| `GET /api/agents/{id}/memory` | What they remember |
| `GET /api/relationships` | Full relationship graph |
| `GET /api/relationships/agent/{id}` | One agent's relationships |
| `GET /api/goals/agent/{id}` | Active goals |
| `GET /api/events` | Recent event history |
| `GET /api/locations` | Village map data |
| `GET /api/digest/daily` | Today's newspaper |
| `GET /api/polls/active` | Current community poll |

## Development

```bash
# Run backend locally
cd backend
uv run uvicorn hamlet.main:app --reload

# Run frontend locally
cd frontend
npm run dev

# Run tests
cd backend && uv run pytest

# Lint everything
cd backend && uv run ruff check .
cd frontend && npm run lint
```

**Project Structure:**
```
clockwork-hamlet/
├── backend/
│   └── src/hamlet/
│       ├── api/           # FastAPI routes
│       ├── actions/       # Action types + execution
│       ├── simulation/    # Engine + world state
│       ├── memory/        # Memory compression
│       ├── goals/         # Goal generation
│       └── llm/           # Claude integration
├── frontend/
│   └── src/
│       ├── components/    # React components
│       ├── hooks/         # Data fetching + SSE
│       └── pages/         # Route pages
└── docker-compose.yml
```

## The Philosophy

This project follows **agentic development** principles:

1. **Emergence over scripting** — Create systems, not storylines
2. **Observe and iterate** — Run simulations, watch what's boring, fix it
3. **Personality drives behavior** — Stats and traits, not IF statements
4. **Let them surprise you** — The best stories are the ones we didn't plan

The development loop:
```
SIMULATE → OBSERVE → ANALYZE → IMPROVE → REPEAT
```

We don't guess what agents will do. We watch them do it, notice when Agnes greets Bob for the 47th time in a row, and add more action variety. Then we watch again.

## Roadmap

- [x] Core simulation engine
- [x] 10 agents with personalities
- [x] Real-time SSE streaming
- [x] Relationship tracking
- [x] Memory system
- [x] Goal-driven behavior
- [x] Frontend with Tokyo Night aesthetic
- [ ] LLM-powered decisions (currently random with weighted variety)
- [ ] Memory compression (daily summaries)
- [ ] Viewer polls that inject events
- [ ] Seasonal events (harvest festival, winter market)
- [ ] Agent secrets and discovery mechanics
- [ ] Romance subplots

## License

TBD

---

*"A man walks where he pleases." — Old Tom, when accused of cheese theft*
