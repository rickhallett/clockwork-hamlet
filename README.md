# Clockwork Hamlet

A persistent, multi-agent village simulation where AI-driven characters with distinct personalities live, interact, form relationships, pursue goals, and create emergent narratives.

## The Vision

Drop 10 AI agents with unique personalities into a small village. Give them needs, goals, and opinions. Let them interact. Watch what happens.

The magic is in **emergence** — we don't script storylines, we create conditions for stories to emerge from agent interactions. The scheming merchant befriends the lonely baker. The paranoid hermit accuses the mayor of cheese theft. Alliances form. Grudges fester. Romance blooms.

## Status: Live & Running

The simulation is fully operational with:
- 10 unique agents with personalities, traits, and backstories
- 11 interconnected village locations
- Real-time SSE event streaming
- LLM-powered decision making (Claude)
- React frontend with Tokyo Night aesthetic

## Quick Start

```bash
# Clone and configure
git clone <repo>
cd clockwork-hamlet
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run with Docker
docker-compose up -d --build

# Access
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:3003
```

## Features

- **Live Feed** — Real-time stream of village events
- **Character Profiles** — Agent state, traits, relationships, memories
- **Relationship Graph** — Visual network of agent connections
- **Village Digest** — Daily/weekly summaries of notable events
- **Viewer Polls** — Community influence on the simulation

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy, SQLite |
| LLM | Claude (Anthropic API) |
| Frontend | React 18, Vite, Tailwind CSS |
| Streaming | Server-Sent Events (SSE) |
| Deployment | Docker, nginx |

## Architecture

```
PERCEIVE → DECIDE → ACT → OBSERVE → REPEAT

Each tick:
1. Agent perceives environment (location, nearby agents, objects)
2. LLM decides action based on personality + goals + context
3. Action executes with validation and side effects
4. Events published to SSE stream
5. Relationships and memories update
```

## Development Philosophy

This project is developed using **agentic coding** principles:

1. **Orchestrate, Don't Type** — Use AI agents for implementation
2. **Fresh Context Windows** — One agent, one purpose, one task
3. **Feedback Loops** — Every workflow includes validation (tests, builds, lints)
4. **Target Zero Touch** — Build toward autonomous execution

See `docs/agentic-development-guide.md` for the full workflow guide.

### Development Commands

```bash
# Autonomous development loop (ralph-wiggum plugin)
/ralph-wiggum:ralph-loop "TASK" --max-iterations N --completion-promise "CRITERIA"

# Run tests
cd backend && uv run pytest

# Lint
cd backend && uv run ruff check .
cd frontend && npm run lint

# Build
cd frontend && npm run build
docker-compose up -d --build
```

## Project Structure

```
clockwork-hamlet/
├── backend/
│   ├── src/hamlet/
│   │   ├── api/           # REST + SSE endpoints
│   │   ├── db/            # Models + seeding
│   │   ├── llm/           # LLM client + decisions
│   │   ├── actions/       # Action system
│   │   └── simulation/    # Engine + world state
│   └── tests/             # pytest suite (70+ tests)
├── frontend/
│   └── src/
│       ├── components/    # React components
│       ├── hooks/         # Data + SSE hooks
│       └── pages/         # Route pages
├── docs/
│   ├── agentic-development-guide.md
│   └── specs/
└── docker-compose.yml
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/world` | Current simulation state |
| `GET /api/agents` | List all agents |
| `GET /api/agents/{id}` | Agent details |
| `GET /api/locations` | List all locations |
| `GET /api/events` | Recent events |
| `GET /api/relationships` | Relationship graph |
| `GET /api/stream` | SSE event stream |
| `GET /api/digest/daily` | Daily summary |

## The Agents

| Name | Role | Personality |
|------|------|-------------|
| Agnes Thornbury | Baker | Sharp-tongued gossip with a warm heart |
| Bob Millwright | Farmer | Gentle, melancholic widower |
| Martha Hendricks | Mayor's Wife | Prim socialite with secret adventurous streak |
| Theodore Hendricks | Mayor | Pompous but insecure leader |
| Father Cornelius | Priest | Scholarly with doubts about his faith |
| Edmund Blackwood | Blacksmith | Gruff exterior, romantic soul |
| Rosalind Fairweather | Innkeeper | Observant keeper of secrets |
| Eliza Thornbury | Baker's Daughter | Ambitious, dreams of escape |
| William "Old Will" Cooper | Retired Sailor | Storyteller with a mysterious past |
| Thomas Ashford | Merchant | Charming but unscrupulous |

## Contributing

This project uses agentic development workflows. Before contributing:

1. Read `docs/agentic-development-guide.md`
2. Ensure changes include tests
3. Run full validation before PR:
   ```bash
   cd backend && uv run pytest && uv run ruff check .
   cd frontend && npm run build && npm run lint
   ```

## License

TBD
