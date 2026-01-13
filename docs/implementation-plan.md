# Clockwork Hamlet: Implementation Plan

**Optimized for:** Agentic development with Ralph Wiggum loops
**Strategy:** Atomic phases with clear completion promises and verification steps

---

## Overview

This plan breaks the project into discrete phases, each designed for a single ralph-loop execution. Each phase has:

- **Scope:** What to build
- **Verification:** How to know it works
- **Promise:** The completion signal
- **Files:** Expected outputs

---

## Phase 0: Project Scaffolding

**Goal:** Set up monorepo structure with backend and frontend skeletons.

### Tasks
1. Create Python backend structure with FastAPI
2. Create frontend structure with Vite + React + TypeScript
3. Set up shared configuration (pyproject.toml, package.json, tsconfig)
4. Add basic dev scripts and Makefile
5. Configure linting (ruff for Python, eslint for TS)

### Directory Structure
```
clockwork-hamlet/
├── backend/
│   ├── src/
│   │   └── hamlet/
│   │       ├── __init__.py
│   │       ├── main.py          # FastAPI app
│   │       ├── config.py        # Settings
│   │       └── api/
│   │           └── __init__.py
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   └── styles/
│   │       └── tokyo.css
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── Makefile
└── README.md
```

### Verification
```bash
# Backend starts
cd backend && python -m hamlet.main  # Should show "Uvicorn running"

# Frontend starts
cd frontend && bun run dev  # Should show Vite dev server

# Both lint clean
make lint  # No errors
```

### Ralph Loop
```
/ralph-loop "Implement Phase 0: Project Scaffolding per docs/implementation-plan.md. Verify backend starts with uvicorn, frontend starts with vite, and linting passes. Output <promise>PHASE 0 COMPLETE</promise> when all verification checks pass." --completion-promise "PHASE 0 COMPLETE" --max-iterations 15
```

---

## Phase 1: Database Schema & Models

**Goal:** Implement SQLite database with Turso, define all core models.

### Tasks
1. Set up Turso/libsql connection
2. Create SQLAlchemy models for all entities
3. Write migration/seed script for initial data
4. Create Pydantic schemas for API serialization
5. Seed with 3 locations, 3 agents for testing

### Models
- `Agent` — id, name, personality_prompt, traits (JSON), location_id, inventory, mood, state
- `Location` — id, name, description, connections (JSON), objects (JSON)
- `Relationship` — agent_id, target_id, type, score, history (JSON)
- `Memory` — id, agent_id, timestamp, type, content, significance, compressed
- `Goal` — id, agent_id, type, description, priority, target_id, status
- `Event` — id, timestamp, type, actors (JSON), location_id, summary, detail, significance
- `Poll` — id, question, options (JSON), votes (JSON), status, created_at, closes_at

### Verification
```bash
# Run seed script
python -m hamlet.db.seed

# Query test
python -c "from hamlet.db import get_db; db = get_db(); print(db.execute('SELECT * FROM agents').fetchall())"
# Should show 3 agents

# Models import clean
python -c "from hamlet.models import Agent, Location, Relationship, Memory, Goal, Event, Poll"
```

### Ralph Loop
```
/ralph-loop "Implement Phase 1: Database Schema & Models per docs/implementation-plan.md. Create SQLite/Turso connection, all SQLAlchemy models, Pydantic schemas, and seed script. Verify by running seed and querying agents. Output <promise>PHASE 1 COMPLETE</promise> when verification passes." --completion-promise "PHASE 1 COMPLETE" --max-iterations 20
```

---

## Phase 2: Core Simulation Engine

**Goal:** Implement the tick system and world state management.

### Tasks
1. Create `World` class to hold global state
2. Implement tick loop with asyncio
3. Add agent state updates (needs: hunger, energy, social)
4. Implement day/night cycle
5. Create event bus for broadcasting changes
6. Add basic logging of all ticks

### Core Logic
```python
# Every tick:
# 1. Advance world time
# 2. Update agent needs
# 3. Wake sleeping agents if morning
# 4. For each active agent: gather perception
# 5. Queue actions (random for now, LLM in Phase 4)
# 6. Execute actions
# 7. Broadcast events
# 8. Persist state
```

### Verification
```bash
# Run simulation for 10 ticks
python -m hamlet.simulation --ticks 10

# Should output:
# [Tick 1] World time: 06:00, Day 1
# [Tick 1] Agent agnes: hunger 1, energy 9
# [Tick 2] World time: 06:30, Day 1
# ... etc

# Events logged to DB
python -c "from hamlet.db import get_db; print(len(get_db().execute('SELECT * FROM events').fetchall()))"
# Should show > 0 events
```

### Ralph Loop
```
/ralph-loop "Implement Phase 2: Core Simulation Engine per docs/implementation-plan.md. Create World class, tick loop, agent needs system, day/night cycle, and event bus. Verify by running 10 ticks and checking events in DB. Output <promise>PHASE 2 COMPLETE</promise> when verification passes." --completion-promise "PHASE 2 COMPLETE" --max-iterations 20
```

---

## Phase 3: Actions & Interactions

**Goal:** Implement the action system for agents.

### Tasks
1. Define action types (Move, Examine, Take, Wait, Sleep, Work)
2. Define social actions (Greet, Talk, Give, Help, Confront, Avoid)
3. Implement action validation
4. Implement action execution
5. Add witness system (nearby agents observe)
6. Update relationships based on interactions

### Action Flow
```python
def execute_action(agent, action):
    if not validate(action): return Failure
    result = perform(action)
    update_relationships(agent, action.target, result)
    create_memories(agent, action.target, witnesses)
    broadcast_event(action, result)
    return result
```

### Verification
```bash
# Run action tests
pytest backend/tests/test_actions.py -v

# Test specific actions work
python -c "
from hamlet.actions import Move, execute_action
from hamlet.db import get_agent
agent = get_agent('agnes')
result = execute_action(agent, Move('town_square'))
print(f'Agnes moved: {result.success}')
"
# Should print: Agnes moved: True
```

### Ralph Loop
```
/ralph-loop "Implement Phase 3: Actions & Interactions per docs/implementation-plan.md. Create all action types, validation, execution, witness system, and relationship updates. Verify with pytest and manual action test. Output <promise>PHASE 3 COMPLETE</promise> when all tests pass." --completion-promise "PHASE 3 COMPLETE" --max-iterations 25
```

---

## Phase 4: LLM Integration

**Goal:** Connect agents to LLM for decision-making and dialogue.

### Tasks
1. Create LLM client wrapper (Claude/OpenAI compatible)
2. Implement context builder (personality + state + memories + goals)
3. Create decision prompt template
4. Create dialogue prompt template
5. Parse LLM responses into valid actions
6. Add response caching to reduce costs
7. Implement fallback for API failures

### Context Template
```
You are {name}. {personality_summary}

TRAITS: {traits}
LOCATION: {location} with {nearby_agents}
MOOD: {mood}
RECENT: {last_5_memories}
GOALS: {active_goals}

What do you do next? Choose from: {available_actions}
```

### Verification
```bash
# Test LLM integration (requires API key in env)
python -m hamlet.llm.test_integration

# Should output:
# Context built: 850 tokens
# Decision received: Move(town_square)
# Dialogue generated: "Good morning, Bob!"

# Run 3 ticks with LLM
python -m hamlet.simulation --ticks 3 --use-llm
# Should show agent decisions from LLM
```

### Ralph Loop
```
/ralph-loop "Implement Phase 4: LLM Integration per docs/implementation-plan.md. Create LLM client, context builder, decision/dialogue prompts, response parsing, and caching. Verify with test_integration and 3 LLM-powered ticks. Output <promise>PHASE 4 COMPLETE</promise> when verification passes." --completion-promise "PHASE 4 COMPLETE" --max-iterations 25
```

---

## Phase 5: Goal System

**Goal:** Give agents motivations that drive behavior.

### Tasks
1. Implement goal hierarchy (Needs → Desires → Reactive)
2. Create goal generation based on personality traits
3. Add goal prioritization
4. Implement goal completion/failure detection
5. Generate new goals from events
6. Handle goal conflicts

### Goal Types
```python
NEEDS = ["eat", "sleep", "socialize"]
DESIRES = ["investigate", "gain_wealth", "make_friend", "find_romance"]
REACTIVE = ["confront", "share_gossip", "help_friend"]
```

### Verification
```bash
# Test goal generation
pytest backend/tests/test_goals.py -v

# Test goal-driven behavior
python -c "
from hamlet.goals import generate_goals
from hamlet.db import get_agent
agent = get_agent('agnes')
agent.hunger = 8  # Very hungry
goals = generate_goals(agent)
print(f'Top goal: {goals[0].type}')
"
# Should print: Top goal: eat
```

### Ralph Loop
```
/ralph-loop "Implement Phase 5: Goal System per docs/implementation-plan.md. Create goal hierarchy, generation, prioritization, completion detection, and conflict handling. Verify with pytest and goal generation test. Output <promise>PHASE 5 COMPLETE</promise> when all tests pass." --completion-promise "PHASE 5 COMPLETE" --max-iterations 20
```

---

## Phase 6: Memory System

**Goal:** Implement working, recent, and long-term memory with compression.

### Tasks
1. Implement working memory (last 5-10 interactions)
2. Implement recent memory (daily summaries)
3. Implement long-term memory (compressed facts)
4. Create end-of-day compression routine
5. Build context from memory layers
6. Add memory significance scoring

### Compression Flow
```python
def end_of_day_compression(agent):
    significant = [m for m in working_memory if m.significance > 5]
    summary = llm.summarize(significant)
    facts = llm.extract_facts(significant)
    recent_memory.append(DaySummary(summary))
    long_term_memory.extend(facts)
    working_memory.clear()
```

### Verification
```bash
# Test memory compression
pytest backend/tests/test_memory.py -v

# Test compression with real data
python -m hamlet.memory.test_compression
# Should output:
# Working memories: 15
# Compressed to summary: 2 sentences
# Extracted facts: 3
# Long-term memory updated
```

### Ralph Loop
```
/ralph-loop "Implement Phase 6: Memory System per docs/implementation-plan.md. Create working/recent/long-term memory, compression routine, and significance scoring. Verify with pytest and compression test. Output <promise>PHASE 6 COMPLETE</promise> when all tests pass." --completion-promise "PHASE 6 COMPLETE" --max-iterations 20
```

---

## Phase 7: REST API

**Goal:** Expose simulation state via FastAPI endpoints.

### Endpoints
```
GET  /api/world              - Current world state
GET  /api/agents             - List all agents
GET  /api/agents/{id}        - Agent profile
GET  /api/agents/{id}/memory - Agent memories
GET  /api/locations          - All locations
GET  /api/events             - Paginated events
GET  /api/events/highlights  - Significant events
GET  /api/relationships      - Relationship graph
GET  /api/polls/active       - Current poll
POST /api/polls/vote         - Submit vote
GET  /api/digest/daily       - Today's summary
```

### Verification
```bash
# Start server
python -m hamlet.main &

# Test endpoints
curl http://localhost:8000/api/world | jq .
curl http://localhost:8000/api/agents | jq .
curl http://localhost:8000/api/agents/agnes | jq .

# All should return valid JSON

# Run API tests
pytest backend/tests/test_api.py -v
```

### Ralph Loop
```
/ralph-loop "Implement Phase 7: REST API per docs/implementation-plan.md. Create all FastAPI endpoints for world, agents, locations, events, relationships, polls, and digest. Verify with curl tests and pytest. Output <promise>PHASE 7 COMPLETE</promise> when all endpoints work and tests pass." --completion-promise "PHASE 7 COMPLETE" --max-iterations 20
```

---

## Phase 8: SSE Live Stream

**Goal:** Real-time event streaming to clients.

### Tasks
1. Create event bus with asyncio queues
2. Implement SSE endpoint `/api/stream`
3. Add event type filtering
4. Handle client disconnect gracefully
5. Add heartbeat for connection keep-alive

### Verification
```bash
# Start server with simulation running
python -m hamlet.main --simulate &

# Connect to stream
curl -N http://localhost:8000/api/stream

# Should see events streaming:
# data: {"type": "movement", "summary": "Agnes moved to Town Square"}
# data: {"type": "dialogue", "summary": "Agnes: 'Good morning!'"}
```

### Ralph Loop
```
/ralph-loop "Implement Phase 8: SSE Live Stream per docs/implementation-plan.md. Create event bus, SSE endpoint with filtering, disconnect handling, and heartbeat. Verify by connecting to stream and seeing live events. Output <promise>PHASE 8 COMPLETE</promise> when streaming works." --completion-promise "PHASE 8 COMPLETE" --max-iterations 15
```

---

## Phase 9: Frontend Foundation

**Goal:** Set up React app with Tokyo Night theme and routing.

### Tasks
1. Configure Tailwind with Tokyo Night colors
2. Create base layout component
3. Set up React Router (Home, Agent, Relationships pages)
4. Create common components (Terminal, Badge, Card)
5. Add JetBrains Mono font
6. Create navigation header

### Verification
```bash
# Start frontend
cd frontend && bun run dev

# Visit http://localhost:5173
# Should see:
# - Dark background (#1a1b26)
# - Monospace font
# - Navigation links
# - Terminal-style container
```

### Ralph Loop
```
/ralph-loop "Implement Phase 9: Frontend Foundation per docs/implementation-plan.md. Configure Tailwind Tokyo theme, create layout, routing, and common components. Verify frontend runs with correct styling. Output <promise>PHASE 9 COMPLETE</promise> when visual verification passes." --completion-promise "PHASE 9 COMPLETE" --max-iterations 15
```

---

## Phase 10: Live Feed Component

**Goal:** Real-time event feed with SSE integration.

### Tasks
1. Create `useVillageStream` hook for SSE
2. Create `EventCard` component for each event type
3. Create `EventStream` component with auto-scroll
4. Add `FilterBar` for filtering by type/agent/location
5. Implement pause-on-hover
6. Show relative timestamps

### Verification
```bash
# Start backend with simulation
cd backend && python -m hamlet.main --simulate &

# Start frontend
cd frontend && bun run dev

# Visit http://localhost:5173
# Should see:
# - Events appearing in real-time
# - Different styling per event type
# - Filter controls working
# - Auto-scroll with pause on hover
```

### Ralph Loop
```
/ralph-loop "Implement Phase 10: Live Feed Component per docs/implementation-plan.md. Create SSE hook, EventCard, EventStream with auto-scroll, FilterBar, and timestamps. Verify by running full stack and seeing live events. Output <promise>PHASE 10 COMPLETE</promise> when live feed works end-to-end." --completion-promise "PHASE 10 COMPLETE" --max-iterations 20
```

---

## Phase 11: Agent Profile Page

**Goal:** Detailed agent view with all state.

### Tasks
1. Create `useAgent` hook for fetching agent data
2. Create `TraitBars` component (visual stat bars)
3. Create `RelationshipList` component
4. Create `MemoryLog` component
5. Create `GoalList` component
6. Create `AgentProfile` page combining all

### Verification
```bash
# Visit http://localhost:5173/agent/agnes
# Should see:
# - Agent name and personality summary
# - Trait bars (Curiosity, Empathy, etc.)
# - Relationship list with sentiment colors
# - Recent memories
# - Active goals
# - Current location and activity
```

### Ralph Loop
```
/ralph-loop "Implement Phase 11: Agent Profile Page per docs/implementation-plan.md. Create agent data hook and all profile components (TraitBars, RelationshipList, MemoryLog, GoalList). Verify by viewing agent profile with all sections populated. Output <promise>PHASE 11 COMPLETE</promise> when profile displays correctly." --completion-promise "PHASE 11 COMPLETE" --max-iterations 20
```

---

## Phase 12: Relationship Graph

**Goal:** Visual network of agent relationships.

### Tasks
1. Integrate force-directed graph library (d3-force or react-force-graph)
2. Create `ForceGraph` component
3. Color edges by relationship sentiment
4. Size edges by relationship strength
5. Add click-to-focus on agent
6. Create `GraphControls` for filtering

### Verification
```bash
# Visit http://localhost:5173/relationships
# Should see:
# - Force-directed graph with agent nodes
# - Green/red edges based on sentiment
# - Click node to highlight connections
# - Filter by relationship type
```

### Ralph Loop
```
/ralph-loop "Implement Phase 12: Relationship Graph per docs/implementation-plan.md. Create force-directed graph with colored edges, node interaction, and filtering. Verify by viewing graph with correct relationship visualization. Output <promise>PHASE 12 COMPLETE</promise> when graph renders correctly." --completion-promise "PHASE 12 COMPLETE" --max-iterations 20
```

---

## Phase 13: Poll System

**Goal:** Viewer voting that influences simulation.

### Tasks
1. Create poll creation endpoint (admin)
2. Create vote submission endpoint
3. Implement poll closing and winner selection
4. Create `ActivePoll` component
5. Create `PollResults` component
6. Inject winning option as world event

### Verification
```bash
# Create test poll via API
curl -X POST http://localhost:8000/api/polls -d '{"question": "What happens next?", "options": ["Storm", "Visitor"]}'

# Vote
curl -X POST http://localhost:8000/api/polls/vote -d '{"poll_id": 1, "option": 0}'

# View in UI - should show poll with vote counts
# Close poll - should inject event into simulation
```

### Ralph Loop
```
/ralph-loop "Implement Phase 13: Poll System per docs/implementation-plan.md. Create poll CRUD endpoints, voting, winner injection, and UI components. Verify by creating poll, voting, and seeing result injected. Output <promise>PHASE 13 COMPLETE</promise> when full poll flow works." --completion-promise "PHASE 13 COMPLETE" --max-iterations 20
```

---

## Phase 14: Highlight Reels

**Goal:** LLM-generated summaries of interesting events.

### Tasks
1. Create daily summary generation job
2. Create weekly digest generation
3. Store summaries in database
4. Create `/api/digest/daily` and `/api/digest/weekly` endpoints
5. Create `DailyDigest` component
6. Style as "newspaper" aesthetic

### Verification
```bash
# Generate daily summary
python -m hamlet.digest.generate --type daily

# Fetch via API
curl http://localhost:8000/api/digest/daily | jq .

# Should return formatted summary like:
# "THE DAILY HAMLET - Day 3
#  HEADLINE: Mayor's Cheese Still Missing..."

# View in UI with newspaper styling
```

### Ralph Loop
```
/ralph-loop "Implement Phase 14: Highlight Reels per docs/implementation-plan.md. Create daily/weekly summary generation, storage, API endpoints, and newspaper-styled UI. Verify by generating and viewing digest. Output <promise>PHASE 14 COMPLETE</promise> when digests generate and display correctly." --completion-promise "PHASE 14 COMPLETE" --max-iterations 20
```

---

## Phase 15: Content & Polish

**Goal:** Expand world, tune personalities, add secrets.

### Tasks
1. Add 7 more agents (total 10) with distinct personalities
2. Add 7 more locations (tavern, church, farm, etc.)
3. Add interactable objects to locations
4. Create 3 initial "mysteries" (stolen cheese, secret affair, hidden treasure)
5. Tune agent traits for maximum drama
6. Add more dialogue variety

### Verification
```bash
# Verify world has full content
python -c "
from hamlet.db import get_db
agents = get_db().execute('SELECT COUNT(*) FROM agents').fetchone()[0]
locations = get_db().execute('SELECT COUNT(*) FROM locations').fetchone()[0]
print(f'Agents: {agents}, Locations: {locations}')
"
# Should print: Agents: 10, Locations: 10

# Run 20 ticks and verify interesting events happen
python -m hamlet.simulation --ticks 20 --use-llm
# Should see varied interactions, gossip, investigations
```

### Ralph Loop
```
/ralph-loop "Implement Phase 15: Content & Polish per docs/implementation-plan.md. Add 7 more agents, 7 more locations, objects, mysteries, and tune personalities. Verify by counting entities and running simulation for interesting behavior. Output <promise>PHASE 15 COMPLETE</promise> when world is fully populated and running." --completion-promise "PHASE 15 COMPLETE" --max-iterations 25
```

---

## Phase 16: Deployment

**Goal:** Deploy to production.

### Tasks
1. Create Dockerfile for backend
2. Create Dockerfile for frontend (static build)
3. Set up Fly.io or Railway configuration
4. Configure Turso production database
5. Set up environment variables
6. Create deploy script
7. Add health check endpoint

### Verification
```bash
# Build and test locally
docker-compose up --build

# Deploy
./scripts/deploy.sh

# Verify production
curl https://clockwork-hamlet.fly.dev/api/health
# Should return: {"status": "ok"}

# Visit production URL
# Should see full app running with live simulation
```

### Ralph Loop
```
/ralph-loop "Implement Phase 16: Deployment per docs/implementation-plan.md. Create Dockerfiles, deployment config, and deploy script. Verify by deploying and accessing production URL. Output <promise>PHASE 16 COMPLETE</promise> when app is live in production." --completion-promise "PHASE 16 COMPLETE" --max-iterations 20
```

---

## Execution Strategy

### Recommended Order

Run phases sequentially. Each builds on the previous:

```
Phase 0  → 1  → 2  → 3  → 4  → 5  → 6   (Backend core)
                ↓
Phase 7  → 8                             (API layer)
                ↓
Phase 9  → 10 → 11 → 12 → 13 → 14       (Frontend)
                ↓
Phase 15 → 16                            (Content & Deploy)
```

### Tips for Ralph Loops

1. **Start each phase fresh:** `git status` should be clean
2. **Commit between phases:** Each phase = one commit
3. **If stuck:** Cancel with `/cancel-ralph` and adjust prompt
4. **Iteration limits:** Start with suggested limits, increase if needed
5. **Check verification:** Each phase has clear success criteria

### Handling Failures

If a phase fails repeatedly:
1. Check which verification step fails
2. Read error messages carefully
3. Consider splitting into smaller sub-phases
4. Add more context to the ralph-loop prompt

---

## Quick Reference

| Phase | Focus | Est. Iterations |
|-------|-------|-----------------|
| 0 | Scaffolding | 15 |
| 1 | Database | 20 |
| 2 | Tick System | 20 |
| 3 | Actions | 25 |
| 4 | LLM | 25 |
| 5 | Goals | 20 |
| 6 | Memory | 20 |
| 7 | REST API | 20 |
| 8 | SSE | 15 |
| 9 | Frontend Base | 15 |
| 10 | Live Feed | 20 |
| 11 | Profiles | 20 |
| 12 | Graph | 20 |
| 13 | Polls | 20 |
| 14 | Digests | 20 |
| 15 | Content | 25 |
| 16 | Deploy | 20 |

**Total:** 16 phases, ~320 max iterations

---

*This plan is designed for iterative agentic development. Each phase is self-contained with clear verification and completion signals.*
