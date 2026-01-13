# Project Specification: Village Simulation

**Codename:** TBD (suggestions: "The Hamlet", "Little Lives", "Agent Village", "The Commons")
**Status:** Concept / Pre-development
**Author:** Synthesized from Keepers Vigil learnings

---

## Executive Summary

A persistent, multi-agent village simulation where AI-driven characters with distinct personalities live, interact, form relationships, pursue goals, and create emergent narratives. The simulation runs continuously and is broadcast live via web interface, creating a "Big Brother with AI agents" entertainment experience.

---

## Concept

### Core Idea

Drop 10-20 AI agents with unique personalities into a small village. Give them needs, goals, and opinions. Let them interact. Watch what happens.

The magic is in **emergence** - we don't script storylines, we create conditions for stories to emerge from agent interactions. The scheming merchant befriends the lonely baker. The paranoid hermit accuses the mayor of cheese theft. Alliances form. Grudges fester. Romance blooms.

### What Makes This Different

| Traditional Simulation | This Project |
|------------------------|--------------|
| Pre-scripted events | Emergent behavior |
| Static personalities | Evolving relationships |
| Player-driven | Autonomous agents |
| Private experience | Live broadcast |
| Single playthrough | Persistent world |

### The Development Loop (Proven in Keepers Vigil)

```
┌─────────────────────────────────────────────────────┐
│  SIMULATE → OBSERVE → ANALYZE → IMPROVE → REPEAT   │
└─────────────────────────────────────────────────────┘
```

This is the key innovation: we don't guess what agents will do. We run simulations, observe emergent behavior, identify issues (boring loops, unrealistic choices, missed opportunities), and iterate on the systems that drive behavior.

---

## Features

### 1. Live Feed

Real-time stream of village events displayed in terminal-aesthetic interface.

```
[14:32] Agnes left the Bakery
[14:32] Agnes arrived at Town Square
[14:33] Agnes noticed Bob sitting on the bench
[14:33] Agnes: "Still moping about the harvest festival, Bob?"
[14:33] Bob: "She didn't even look at my pumpkin, Agnes. Not once."
[14:34] Agnes sat down next to Bob
[14:35] EVENT: New relationship formed - Agnes & Bob (Acquaintance → Friend)
```

**Features:**
- Filterable by location, character, event type
- Expandable entries for full dialogue
- Timestamp + relative time ("2 minutes ago")
- Event categorization (movement, dialogue, discovery, relationship change)
- Auto-scroll with pause-on-hover

### 2. Character Profiles

Detailed pages for each agent showing their current state and history.

**Profile Contents:**
- Portrait/avatar (generated or illustrated)
- Personality summary (2-3 sentences)
- Current location and activity
- Inventory
- Goals (public and private/hidden)
- Relationship web (who they like/dislike)
- Recent memories (last 10-20 significant events)
- Stats/traits

**Example Profile:**
```
AGNES THORNBURY
"The village baker with a sharp tongue and sharper memory"

Location: Town Square (with Bob)
Activity: Consoling Bob about the harvest festival

TRAITS
├── Curiosity    ████████░░ 8/10
├── Empathy      ██████░░░░ 6/10
├── Ambition     ████░░░░░░ 4/10
├── Discretion   ██░░░░░░░░ 2/10  ← (she's a gossip)
└── Energy       ███████░░░ 7/10

RELATIONSHIPS
♥♥♥♥♥ Martha (Best Friend)
♥♥♥♥○ Bob (Friend) ↑ recently improved
♥♥○○○ Mayor Hendricks (Neutral)
♥○○○○ Old Tom (Suspicious of)

CURRENT GOALS
• Find out why Martha has been avoiding the tavern
• Perfect her sourdough recipe
• [Hidden] Discover who's been stealing from the church collection

RECENT MEMORIES
• Comforted Bob about his pumpkin (today)
• Overheard whispers about missing church funds (yesterday)
• Had tense exchange with Old Tom about flour prices (2 days ago)
```

### 3. Viewer Polls

Community-driven influence on the simulation without breaking agent autonomy.

**Poll Types:**

**A. Event Injection**
> "Tomorrow morning, the Mayor will discover something is missing from his office. What should it be?"
> - [ ] The town treasury ledger
> - [ ] A wheel of aged cheese (57%)  ← THE PEOPLE HAVE SPOKEN
> - [ ] A love letter from 20 years ago
> - [ ] His favorite quill pen

**B. NPC Introduction**
> "A stranger arrives at the village. Who are they?"
> - [ ] A traveling merchant
> - [ ] A lost noble
> - [ ] Someone's long-lost relative
> - [ ] A suspicious "tax collector"

**C. Weather/Events**
> "What happens at the harvest festival?"
> - [ ] A thunderstorm forces everyone inside
> - [ ] A prize pig escapes
> - [ ] An unexpected guest arrives

**Rules:**
- Polls don't control agents directly (preserves autonomy)
- Polls inject world events that agents react to
- Results visible, adds community investment
- One active poll at a time, runs for 6-24 hours

### 4. Highlight Reels

LLM-generated summaries of interesting events.

**Daily Summary:**
```
THE DAILY HAMLET - Day 47

HEADLINE: Mayor's Cheese Vanishes; Accusations Fly

In a scandal that has rocked our quiet village, Mayor Hendricks
arrived at his office this morning to find his prized wheel of
aged Gruyère missing from his desk drawer.

"I've had that cheese for three years," the Mayor reportedly
told Agnes Thornbury, who wasted no time sharing the news with
anyone who would listen.

Suspicion has fallen on Old Tom, who was seen near the town hall
late last night. When confronted, Tom responded only with: "A man
walks where he pleases."

The investigation continues.

OTHER STORIES:
• Bob's pumpkin woes continue; Martha offers sympathy
• Stranger spotted at village edge; no one brave enough to approach
• Tavern runs low on ale; emergency brewing underway
```

**Weekly Digest:**
- Major relationship changes
- Goals completed/failed
- New secrets discovered
- Running storylines summary

### 5. Relationship Graphs

Visual network showing connections between all agents.

**Display Options:**
- Force-directed graph (nodes = agents, edges = relationships)
- Edge color: green (positive) → red (negative)
- Edge thickness: relationship strength
- Click node to see that agent's perspective
- Filter by relationship type (friend, rival, romantic, suspicious)
- Timeline slider to see how relationships evolved

**Relationship Types:**
- Stranger → Acquaintance → Friend → Close Friend → Best Friend
- Neutral → Suspicious → Rival → Enemy
- Acquaintance → Attracted → Courting → Romantic Partner
- Any → Grudge (triggered by specific events)

### 6. Character Ability Stats

Agents have traits that influence their behavior and success at tasks.

**Core Traits (1-10 scale):**

| Trait | Affects |
|-------|---------|
| **Curiosity** | Likelihood to investigate, ask questions, explore |
| **Empathy** | Ability to read others, likelihood to help |
| **Ambition** | Goal-setting, willingness to compete/scheme |
| **Discretion** | Keeping secrets vs. gossiping |
| **Energy** | Activity level, number of actions per day |
| **Courage** | Willingness to confront, take risks |
| **Charm** | Success in social interactions |
| **Perception** | Noticing details, detecting lies |

**Derived Stats:**
- **Reputation**: How the village sees them (earned through actions)
- **Wealth**: Economic resources
- **Influence**: Ability to sway others
- **Secrets Known**: Information they've discovered

**Trait Influence Example:**
```python
# High Discretion agent hears gossip
if agent.discretion >= 7:
    # Keeps it to themselves
    agent.add_memory(secret, share=False)
else:
    # Probability of sharing based on discretion
    share_chance = (10 - agent.discretion) / 10
    if random() < share_chance:
        agent.queue_action(ShareGossip(secret, nearest_acquaintance))
```

---

## Technical Specifications

### Core Engine

**Purpose:** Manage world state, time progression, and deterministic game logic.

**World State Schema:**
```
WORLD
├── time (current tick, day, season)
├── weather (affects mood, available actions)
├── locations[]
│   ├── id, name, description
│   ├── connections[] (adjacent locations)
│   ├── objects[] (interactable items)
│   └── agents[] (who is here now)
├── agents[]
│   ├── id, name, personality_prompt
│   ├── location_id
│   ├── traits{} (curiosity, empathy, etc.)
│   ├── inventory[]
│   ├── goals[]
│   ├── relationships{}
│   ├── memories[]
│   └── state (idle, busy, sleeping)
└── global_events[] (active polls, injected events)
```

**Tick System:**
```
Every TICK_INTERVAL (e.g., 30 seconds):
  1. Advance world time
  2. Update agent needs (hunger, tiredness, boredom)
  3. Wake sleeping agents if it's morning
  4. For each active agent (parallel):
     a. Gather perception (who/what is nearby)
     b. Check for triggered reactions (someone spoke to them)
     c. If no reaction: request decision from LLM
     d. Validate action (is it possible?)
     e. Queue action for execution
  5. Execute all queued actions (deterministic)
  6. Resolve conflicts (two agents grab same object)
  7. Update relationships based on interactions
  8. Generate narrative for significant events
  9. Broadcast changes to subscribers
  10. Persist state
```

**Deterministic vs. LLM Split:**
```
DETERMINISTIC (no LLM cost):
├── Movement between locations
├── Picking up / dropping objects
├── Time passage effects
├── Need updates (hunger, energy)
├── Relationship score calculations
├── Conflict resolution
├── Action validation
└── State persistence

LLM CALLS (cost per call):
├── Agent decision ("What do I want to do?")
├── Dialogue generation ("What do I say to Bob?")
├── Reaction to events ("How do I feel about this?")
├── Memory compression ("Summarize my day")
└── Narrative generation ("Describe this scene")
```

### Interaction Engine

**Purpose:** Handle agent-to-agent and agent-to-world interactions.

**Interaction Types:**
```
SOLO ACTIONS
├── Move(destination)
├── Examine(object)
├── Take(object)
├── Use(object)
├── Wait()
├── Sleep()
└── Work(job_type)

SOCIAL ACTIONS
├── Greet(agent)
├── Talk(agent, topic)
├── Ask(agent, question)
├── Tell(agent, information)
├── Give(agent, object)
├── Help(agent, task)
├── Confront(agent, accusation)
└── Avoid(agent)

SPECIAL ACTIONS
├── Investigate(mystery)
├── Gossip(agent, subject)
├── Scheme(goal)
├── Confess(secret)
└── Observe(agent) [hidden]
```

**Interaction Resolution:**
```python
def resolve_interaction(initiator, action, target):
    # Check if action is valid
    if not validate_action(initiator, action, target):
        return ActionResult(success=False, reason="invalid")

    # Check if target is receptive (for social actions)
    if action.is_social:
        receptiveness = calculate_receptiveness(target, initiator)
        if receptiveness < THRESHOLD:
            return ActionResult(success=False, reason="rebuffed")

    # Execute action
    result = execute_action(initiator, action, target)

    # Update relationships
    update_relationship(initiator, target, action, result)

    # Generate memories for both parties
    initiator.add_memory(create_memory(action, result, perspective="initiator"))
    if target:
        target.add_memory(create_memory(action, result, perspective="target"))

    # Broadcast event
    broadcast(Event(action, result, witnesses=get_nearby_agents()))

    return result
```

**Witness System:**
Agents in the same location can witness interactions and form opinions.
```python
def process_witnesses(event, witnesses):
    for witness in witnesses:
        # Add to their memory
        witness.add_memory(create_memory(event, perspective="witness"))

        # May affect their opinion of participants
        if event.type == "help":
            witness.adjust_opinion(event.initiator, +1, "helpful")
        elif event.type == "confront":
            # Opinion depends on witness's existing relationships
            if witness.opinion_of(event.target) < 0:
                witness.adjust_opinion(event.initiator, +1, "stood up to someone I dislike")
            else:
                witness.adjust_opinion(event.initiator, -1, "aggressive")
```

### Goal Generation

**Purpose:** Give agents motivations that drive interesting behavior.

**Goal Hierarchy:**
```
NEEDS (automatic, always present)
├── Physical: hunger, rest, shelter
├── Social: companionship, recognition
└── Safety: avoid threats, maintain reputation

DESIRES (personality-driven)
├── Curiosity-driven: learn secrets, explore, investigate
├── Ambition-driven: gain wealth, influence, status
├── Social-driven: make friends, find romance, help others
└── Personal: hobby completion, skill mastery

REACTIVE (event-driven)
├── Triggered by events: "Find out who stole the cheese"
├── Triggered by relationships: "Confront Bob about the rumor"
└── Triggered by discovery: "Tell Martha what I learned"
```

**Goal Generation Process:**
```python
def generate_goals(agent, world_state):
    goals = []

    # Need-based goals (always check)
    if agent.hunger > 7:
        goals.append(Goal("eat", priority=HIGH, target="food"))
    if agent.energy < 3:
        goals.append(Goal("sleep", priority=HIGH))
    if agent.social < 4:
        goals.append(Goal("socialize", priority=MEDIUM))

    # Personality-driven goals (periodic refresh)
    if agent.curiosity > 6 and world_state.has_mysteries():
        mystery = select_mystery(agent, world_state)
        goals.append(Goal("investigate", priority=MEDIUM, target=mystery))

    if agent.ambition > 7:
        goals.append(Goal("increase_wealth", priority=MEDIUM))

    # Relationship-driven goals
    for rel in agent.relationships:
        if rel.type == "grudge" and agent.courage > 5:
            goals.append(Goal("confront", priority=LOW, target=rel.agent))
        if rel.type == "romantic_interest":
            goals.append(Goal("court", priority=MEDIUM, target=rel.agent))

    # Event-driven goals (injected by polls, discoveries)
    for event in agent.pending_reactions:
        goals.append(event.to_goal())

    return prioritize(goals)
```

**Goal Completion:**
- Goals have success/failure conditions
- Completed goals generate satisfaction (affects mood)
- Failed goals generate frustration (may create new goals)
- Some goals are ongoing (maintain friendship)
- Goals can conflict (creates internal drama)

### Memory Compression

**Purpose:** Keep agent context window manageable while preserving important history.

**Memory Types:**
```
WORKING MEMORY (kept in full)
├── Last 5-10 interactions
├── Current goals
├── Current location context
└── Active conversations

RECENT MEMORY (summarized daily)
├── Today's significant events
├── People encountered
├── Information learned
└── Emotional high/low points

LONG-TERM MEMORY (highly compressed)
├── Core relationships (who I trust/distrust)
├── Major life events
├── Secrets I know
├── Skills I've developed
└── Places I've been
```

**Compression Process:**
```python
def compress_memories(agent):
    # Run at end of each day

    # 1. Extract significant events from working memory
    significant = [m for m in agent.working_memory
                   if m.significance > THRESHOLD]

    # 2. Use LLM to summarize the day
    summary = llm.summarize(
        prompt=f"""
        Summarize {agent.name}'s day in 2-3 sentences.
        Focus on: relationship changes, discoveries, emotional moments.
        Events: {significant}
        """,
        max_tokens=150
    )

    # 3. Update long-term memory with key facts
    facts = llm.extract_facts(
        prompt=f"""
        Extract lasting facts from today's events.
        Format: [RELATIONSHIP: X is now Y to me], [SECRET: I learned Z], etc.
        Events: {significant}
        """
    )

    for fact in facts:
        agent.long_term_memory.add(fact)

    # 4. Add summary to recent memory
    agent.recent_memory.append(DaySummary(day=today, summary=summary))

    # 5. Trim recent memory to last 7 days
    agent.recent_memory = agent.recent_memory[-7:]

    # 6. Clear working memory
    agent.working_memory = []
```

**Context Building for LLM Calls:**
```python
def build_agent_context(agent):
    return f"""
    You are {agent.name}. {agent.personality_summary}

    TRAITS: {format_traits(agent.traits)}

    CURRENT STATE:
    - Location: {agent.location.name}
    - Nearby: {agent.perception.agents}, {agent.perception.objects}
    - Mood: {agent.mood}
    - Needs: {format_needs(agent)}

    RELATIONSHIPS:
    {format_relationships(agent.relationships[:10])}

    RECENT MEMORIES:
    {format_recent(agent.recent_memory[-3:])}

    CURRENT GOALS:
    {format_goals(agent.goals[:5])}

    WHAT JUST HAPPENED:
    {format_working_memory(agent.working_memory[-5:])}
    """
```

### Conflict Resolution

**Purpose:** Deterministically resolve situations where multiple agents want incompatible outcomes.

**Conflict Types:**

**1. Resource Conflicts (two agents want same object)**
```python
def resolve_resource_conflict(agents, resource):
    # Priority order:
    # 1. Already holding it
    # 2. Closer to it
    # 3. Higher relevant stat (e.g., speed)
    # 4. Random tiebreaker

    scores = []
    for agent in agents:
        score = 0
        if agent.holding(resource): score += 1000
        score += (10 - distance(agent, resource)) * 10
        score += agent.traits.energy
        score += random.random()  # Tiebreaker
        scores.append((agent, score))

    winner = max(scores, key=lambda x: x[1])[0]
    loser = [a for a in agents if a != winner][0]

    # Loser gets frustrated
    loser.mood.adjust(-1)
    loser.adjust_opinion(winner, -1, "took what I wanted")

    return winner
```

**2. Social Conflicts (confrontation, argument)**
```python
def resolve_social_conflict(initiator, target, conflict_type):
    # Calculate success based on stats and relationship

    initiator_score = (
        initiator.traits.charm * 2 +
        initiator.traits.courage +
        initiator.reputation +
        (10 if initiator.has_evidence else 0)
    )

    target_score = (
        target.traits.charm * 2 +
        target.traits.discretion +  # Ability to deflect
        target.reputation
    )

    # Witnesses affect outcome
    witnesses = get_witnesses(initiator.location)
    for w in witnesses:
        if w.opinion_of(initiator) > w.opinion_of(target):
            initiator_score += 2
        else:
            target_score += 2

    if initiator_score > target_score:
        return ConflictResult(winner=initiator, loser=target,
                              outcome="initiator_wins")
    else:
        return ConflictResult(winner=target, loser=initiator,
                              outcome="target_deflects")
```

**3. Location Conflicts (two agents want to be alone)**
```python
def resolve_location_conflict(agents, location):
    # Some locations have capacity limits
    if len(agents) <= location.capacity:
        return None  # No conflict

    # Determine who stays based on:
    # 1. Who arrived first
    # 2. Who has business here
    # 3. Social standing

    # Others are politely displaced to adjacent location
```

**4. Scheduling Conflicts (agent wants to do two things)**
```python
def resolve_internal_conflict(agent, goals):
    # Already prioritized, but check for true conflicts

    for i, goal_a in enumerate(goals):
        for goal_b in goals[i+1:]:
            if goals_conflict(goal_a, goal_b):
                # LLM decides based on personality
                choice = llm.decide(
                    prompt=f"""
                    {agent.name} wants to both:
                    A: {goal_a.description}
                    B: {goal_b.description}

                    Given their personality ({agent.personality_summary}),
                    which do they choose? Answer A or B with brief reasoning.
                    """
                )
                # Remove the unchosen goal
                goals.remove(goal_a if choice == "B" else goal_b)

    return goals
```

### Live Broadcast Infrastructure

**Purpose:** Stream simulation state to web clients in real-time.

**Architecture:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Backend   │────▶│  Event Bus  │────▶│  Clients    │
│  (FastAPI)  │     │  (in-proc)  │     │  (Browser)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   ▼                   │
       │           ┌─────────────┐             │
       │           │   SSE/WS    │             │
       │           │  Endpoint   │─────────────┘
       │           └─────────────┘
       │
       ▼
┌─────────────┐
│   SQLite    │
│   (Turso)   │
└─────────────┘
```

**Event Types:**
```typescript
interface VillageEvent {
  id: string;
  timestamp: number;
  type: 'movement' | 'dialogue' | 'action' | 'relationship' | 'discovery' | 'system';
  actors: string[];  // Agent IDs involved
  location: string;
  summary: string;   // One-line description
  detail?: string;   // Full dialogue/description
  significance: 1 | 2 | 3;  // For filtering
}
```

**SSE Endpoint:**
```python
@app.get("/api/stream")
async def event_stream(request: Request):
    async def generate():
        queue = event_bus.subscribe()
        try:
            while True:
                event = await queue.get()
                yield f"data: {event.json()}\n\n"
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**REST Endpoints:**
```
GET  /api/world              - Current world state summary
GET  /api/agents             - List all agents with basic info
GET  /api/agents/{id}        - Full agent profile
GET  /api/agents/{id}/memory - Agent's recent memories
GET  /api/locations          - All locations with occupants
GET  /api/events             - Paginated event history
GET  /api/events/highlights  - Recent significant events
GET  /api/relationships      - Full relationship graph data
GET  /api/polls/active       - Current poll (if any)
POST /api/polls/vote         - Submit vote
GET  /api/digest/daily       - Today's summary
GET  /api/digest/weekly      - This week's summary
```

**Frontend Connection:**
```typescript
// hooks/useVillageStream.ts
export function useVillageStream() {
  const [events, setEvents] = useState<VillageEvent[]>([]);

  useEffect(() => {
    const eventSource = new EventSource('/api/stream');

    eventSource.onmessage = (e) => {
      const event = JSON.parse(e.data);
      setEvents(prev => [...prev.slice(-100), event]);  // Keep last 100
    };

    return () => eventSource.close();
  }, []);

  return events;
}
```

---

## Tech Stack

### Backend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| API Server | **FastAPI** | Async, fast, great DX, SSE support |
| Database | **SQLite via Turso** | Simple, edge-ready, good enough for this scale |
| LLM | **Claude Haiku / Gemini Flash** | Cheap, fast, good enough for agent decisions |
| Task Queue | **In-process asyncio** | No need for Celery/Redis at this scale |
| Caching | **In-memory dict** | Simple, reset on restart is fine |

**Why SQLite over NoSQL:**
- Structured data (agents, locations, relationships) fits relational model
- JSON columns for flexible data (memories, traits)
- Turso gives us edge deployment and easy CLI
- Simpler ops than MongoDB/Postgres for a hobby project
- Can always migrate later if needed

**Database Schema (SQLite):**
```sql
-- Core entities
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    personality_prompt TEXT,
    traits JSON,  -- {"curiosity": 8, "empathy": 6, ...}
    location_id TEXT REFERENCES locations(id),
    inventory JSON,  -- ["bread", "letter"]
    mood JSON,  -- {"happiness": 5, "energy": 7}
    state TEXT DEFAULT 'idle'
);

CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    connections JSON,  -- ["town_square", "bakery"]
    objects JSON  -- ["bench", "fountain"]
);

CREATE TABLE relationships (
    agent_id TEXT REFERENCES agents(id),
    target_id TEXT REFERENCES agents(id),
    type TEXT,  -- 'friend', 'rival', 'romantic', etc.
    score INTEGER,  -- -10 to +10
    history JSON,  -- Recent interaction summaries
    PRIMARY KEY (agent_id, target_id)
);

CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT REFERENCES agents(id),
    timestamp INTEGER,
    type TEXT,  -- 'working', 'recent', 'longterm'
    content TEXT,
    significance INTEGER,
    compressed BOOLEAN DEFAULT FALSE
);

CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT REFERENCES agents(id),
    type TEXT,
    description TEXT,
    priority INTEGER,
    target_id TEXT,
    status TEXT DEFAULT 'active',
    created_at INTEGER
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER,
    type TEXT,
    actors JSON,  -- Agent IDs
    location_id TEXT,
    summary TEXT,
    detail TEXT,
    significance INTEGER
);

CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    options JSON,
    votes JSON,  -- {"option_1": 45, "option_2": 32}
    status TEXT DEFAULT 'active',
    created_at INTEGER,
    closes_at INTEGER
);
```

### Frontend

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Runtime | **Bun** | Fast, modern, good DX |
| Framework | **React 18** | Familiar, SSE hooks, good ecosystem |
| Build | **Vite** | Fast HMR, simple config |
| Styling | **Tailwind + custom Tokyo theme** | Rapid iteration, terminal aesthetic |
| State | **Zustand or Jotai** | Simple, no boilerplate |
| Data Fetching | **TanStack Query** | Caching, refetching, SSE integration |

**Tokyo Terminal Styling:**
```css
:root {
  --bg-primary: #1a1b26;
  --bg-secondary: #24283b;
  --bg-highlight: #414868;
  --fg-primary: #c0caf5;
  --fg-secondary: #a9b1d6;
  --fg-dim: #565f89;
  --accent-blue: #7aa2f7;
  --accent-cyan: #7dcfff;
  --accent-green: #9ece6a;
  --accent-magenta: #bb9af7;
  --accent-red: #f7768e;
  --accent-yellow: #e0af68;

  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

body {
  background: var(--bg-primary);
  color: var(--fg-primary);
  font-family: var(--font-mono);
}
```

**Component Structure:**
```
src/
├── components/
│   ├── LiveFeed/
│   │   ├── EventCard.tsx
│   │   ├── EventStream.tsx
│   │   └── FilterBar.tsx
│   ├── AgentProfile/
│   │   ├── TraitBars.tsx
│   │   ├── RelationshipList.tsx
│   │   ├── MemoryLog.tsx
│   │   └── GoalList.tsx
│   ├── RelationshipGraph/
│   │   ├── ForceGraph.tsx
│   │   └── GraphControls.tsx
│   ├── Poll/
│   │   ├── ActivePoll.tsx
│   │   └── PollResults.tsx
│   └── common/
│       ├── Terminal.tsx  (scrolling container)
│       └── Badge.tsx
├── hooks/
│   ├── useVillageStream.ts
│   ├── useAgent.ts
│   └── usePoll.ts
├── stores/
│   └── villageStore.ts
└── styles/
    └── tokyo.css
```

---

## Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up monorepo structure
- [ ] Initialize FastAPI backend with Turso
- [ ] Create basic world state (3 locations, 3 agents)
- [ ] Implement tick system (no LLM yet, random actions)
- [ ] Basic event logging to SQLite
- [ ] Minimal frontend with live feed

### Phase 2: Agent Intelligence (Week 3-4)
- [ ] Integrate LLM for agent decisions
- [ ] Implement goal system
- [ ] Add personality traits
- [ ] Basic dialogue generation
- [ ] Memory system (working memory only)

### Phase 3: Social Systems (Week 5-6)
- [ ] Relationship tracking
- [ ] Agent-to-agent interactions
- [ ] Witness system
- [ ] Conflict resolution
- [ ] Gossip mechanics

### Phase 4: Polish & Broadcast (Week 7-8)
- [ ] Memory compression
- [ ] Character profiles UI
- [ ] Relationship graph visualization
- [ ] Highlight reel generation
- [ ] Poll system

### Phase 5: Content & Tuning (Ongoing)
- [ ] Add more locations, objects, agents
- [ ] Tune personalities for drama
- [ ] Add mysteries/secrets
- [ ] Community features
- [ ] Performance optimization

---

## Cost Projections

**Assumptions:**
- 10 agents
- 1 tick per minute during "day" (12 hours)
- Agents sleep 8 hours (no decisions)
- ~720 decision calls/day + ~200 dialogue calls + ~10 summaries

**Daily LLM Costs (Claude Haiku):**
| Call Type | Count | Tokens/call | Total Tokens | Cost |
|-----------|-------|-------------|--------------|------|
| Decisions | 720 | 500 in / 100 out | 432K | ~$0.15 |
| Dialogue | 200 | 800 in / 200 out | 200K | ~$0.10 |
| Summaries | 10 | 1000 in / 300 out | 13K | ~$0.01 |
| **Total** | | | **~650K** | **~$0.25/day** |

**Monthly:** ~$7.50
**With 20 agents:** ~$15/month

This is extremely sustainable.

**Infrastructure Costs:**
- Turso free tier: $0 (up to 500 DBs, 9GB storage)
- Hosting (Fly.io/Railway): ~$5-10/month
- Domain: ~$12/year

**Total Monthly:** ~$15-25

---

## Open Questions

1. **Agent count:** 10 feels manageable; 20 creates more drama but more cost. Start with 10?

2. **Tick rate:** 1/minute is responsive but costly. 1/5min is cheaper but slower. Make configurable?

3. **Viewer influence:** How much control should polls have? Too much breaks emergence; too little feels pointless.

4. **Persistence:** How long do we keep history? Forever? Rolling 30 days?

5. **Moderation:** If this goes public, do we need content filtering on agent outputs?

6. **Agent death/birth:** Do agents live forever? Can new ones be added? What about romance → children?

---

## References

- Stanford Generative Agents paper: https://arxiv.org/abs/2304.03442
- Keepers Vigil codebase (this repo): Simulation framework, persona system
- Tokyo Night theme: https://github.com/enkia/tokyo-night-vscode-theme
- oceanheart.ai: Visual reference for terminal aesthetic

---

*This specification is a living document. Update as design evolves.*
