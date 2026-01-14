# Clockwork Hamlet: Agentic Development Roadmap

## Overview

This document defines the tactical roadmap for parallel agentic development across five epics. It establishes workflows, success criteria, and reusable patterns to maximize AFK (away-from-keyboard) development streaks.

**Design Principles:**
- All work on feature branches with atomic commits
- All features require tests before merge
- Tickets maintained in real-time by agents
- Human involvement limited to planning and review gates

---

## Epic Dependency Graph

```
                    ┌─────────────────────────────────────────┐
                    │           FOUNDATION LAYER              │
                    │  (SSE streaming, DB, API patterns)      │
                    │              ✓ COMPLETE                 │
                    └─────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
    │    FEED     │            │    POLL     │            │    LIFE     │
    │  (Display)  │            │  (Voting)   │            │ (Behavior)  │
    │             │            │             │            │             │
    │ Independent │            │ Independent │            │ Independent │
    └─────────────┘            └─────────────┘            └─────────────┘
           │                           │                           │
           │                           │                           │
           ▼                           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
    │    DASH     │◄───────────│ POLL+SIM    │◄───────────│ LIFE+POLL   │
    │   (Stats)   │            │(Integration)│            │(Integration)│
    └─────────────┘            └─────────────┘            └─────────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
              ┌─────────────────┐
              │      USER       │
              │  (Interaction)  │
              │                 │
              │ Depends on:     │
              │ - Auth layer    │
              │ - Agent system  │
              │ - Chat/LLM      │
              └─────────────────┘
```

---

## Phase Structure

### Phase 1: Parallel Quick Wins (Complexity: Low)
**Can run simultaneously - no dependencies between tracks**

| Track | Epic | Work | Branch Pattern |
|-------|------|------|----------------|
| A | FEED | Enhanced feed display, filtering, search | `feat/feed/...` |
| B | POLL | Core voting infrastructure | `feat/poll/...` |
| C | LIFE | Humor injection, dramatic events | `feat/life/...` |

### Phase 2: Core Features (Complexity: Medium)
**Some parallelization possible with coordination**

| Track | Epic | Work | Dependencies |
|-------|------|------|--------------|
| D | DASH | Map visualization, stats endpoints | FEED patterns |
| E | USER | Agent creation API + forms | None |
| F | POLL | Simulation integration | POLL Phase 1 |

### Phase 3: Advanced Integration (Complexity: High)
**Sequential within tracks, parallel between tracks**

| Track | Epic | Work | Dependencies |
|-------|------|------|--------------|
| G | USER | Agent chat with LLM | USER Phase 2, Auth |
| H | DASH | Real-time dashboard | DASH Phase 2 |
| I | LIFE | Complex emergent behaviors | All core features |

---

## Detailed Epic Breakdown

### FEED Epic

**Current State:** Basic SSE streaming exists, frontend has EventStream component

**FEED-1: Enhanced Event Display** (Phase 1)
```yaml
stories:
  - FEED-2: Add event significance indicators (icons, colors)
  - FEED-3: Implement event grouping by time windows
  - FEED-4: Add text search/filter on event content
  - FEED-5: Infinite scroll with virtualization

success_criteria:
  - Feed handles 1000+ events without performance degradation
  - Search returns results in <100ms
  - All new components have unit tests

branch: feat/feed/enhanced-display
```

**FEED-6: Event History & Export** (Phase 2)
```yaml
stories:
  - FEED-7: Backend pagination with cursor-based queries
  - FEED-8: Export to JSON/CSV functionality
  - FEED-9: Event archival vs live mode toggle

success_criteria:
  - Export 10k events in <5 seconds
  - History queries use indexed columns
  - Integration tests for export formats

branch: feat/feed/history-export
```

---

### POLL Epic

**Current State:** Basic Poll model exists, simple voting API, localStorage tracking

**POLL-1: Enhanced Polling System** (Phase 1)
```yaml
stories:
  - POLL-2: Admin poll creation endpoint
  - POLL-3: Poll scheduling (auto-open/close)
  - POLL-4: Multiple choice vs single choice support
  - POLL-5: Poll categories and tagging

success_criteria:
  - Create/schedule polls via API
  - Polls auto-close at scheduled time
  - 100% API test coverage

branch: feat/poll/enhanced-system
```

**POLL-6: Simulation Integration** (Phase 2)
```yaml
stories:
  - POLL-7: Agents can vote based on personality
  - POLL-8: Poll results trigger reactive goals
  - POLL-9: Relationship changes from voting alignment
  - POLL-10: Memory creation for votes

success_criteria:
  - Agents vote probabilistically based on traits
  - Poll closure triggers simulation events
  - Integration tests with mock LLM

branch: feat/poll/simulation-integration
```

**POLL-11: Live Poll Experience** (Phase 2)
```yaml
stories:
  - POLL-12: SSE events for poll state changes
  - POLL-13: Real-time vote count updates
  - POLL-14: Poll result visualization components

success_criteria:
  - Vote updates appear within 1 second
  - No polling loops - pure SSE push
  - Frontend component tests

branch: feat/poll/live-experience
```

---

### DASH Epic

**Current State:** No dashboard exists, WorldState has basic stats

**DASH-1: Village Map** (Phase 1)
```yaml
stories:
  - DASH-2: Static SVG map of village locations
  - DASH-3: Location markers with agent counts
  - DASH-4: Click-to-view location details
  - DASH-5: Basic map styling and theming

success_criteria:
  - All seeded locations displayed
  - Agent counts accurate to current tick
  - Responsive on mobile/desktop

branch: feat/dash/village-map
```

**DASH-6: Stats Endpoints** (Phase 2)
```yaml
stories:
  - DASH-7: /api/stats/agents (count, states, moods)
  - DASH-8: /api/stats/events (counts by type, significance)
  - DASH-9: /api/stats/relationships (network metrics)
  - DASH-10: /api/stats/simulation (tick rate, performance)

success_criteria:
  - Stats compute in <50ms
  - Cached where appropriate
  - OpenAPI documented

branch: feat/dash/stats-endpoints
```

**DASH-11: Real-Time Dashboard** (Phase 3)
```yaml
stories:
  - DASH-12: Agent positions update via SSE
  - DASH-13: Live LLM cost tracking widget
  - DASH-14: Simulation health indicators
  - DASH-15: Event rate sparklines

success_criteria:
  - Updates within 1 tick of state change
  - Dashboard doesn't impact simulation performance
  - E2E tests with simulated events

branch: feat/dash/realtime
```

---

### USER Epic

**Current State:** No user system, no authentication

**USER-1: User Foundation** (Phase 2)
```yaml
stories:
  - USER-2: User model and authentication (JWT)
  - USER-3: User preferences storage
  - USER-4: Session management
  - USER-5: Protected route middleware

success_criteria:
  - JWT auth with refresh tokens
  - Preferences persist across sessions
  - Security audit passing

branch: feat/user/foundation
```

**USER-6: Agent Creation** (Phase 2)
```yaml
stories:
  - USER-7: Agent creation API with validation
  - USER-8: Trait/personality configuration UI
  - USER-9: Agent preview before creation
  - USER-10: User-created agent limitations/quotas

success_criteria:
  - Created agents integrate with simulation
  - Validation prevents invalid trait combos
  - Rate limiting prevents abuse

branch: feat/user/agent-creation
```

**USER-11: Agent Chat** (Phase 3)
```yaml
stories:
  - USER-12: Chat API endpoint
  - USER-13: LLM integration for agent responses
  - USER-14: Chat history persistence
  - USER-15: Agent memory of user conversations
  - USER-16: Chat UI component

success_criteria:
  - Agents respond in character
  - Conversations persist and are recallable
  - Cost tracking for chat LLM usage

branch: feat/user/agent-chat
```

---

### LIFE Epic (Continuation)

**Current State:** Idle behaviors, greetings, reactions, dialogue enhancements complete

**LIFE-18: Humor & Personality** (Phase 1)
```yaml
stories:
  - LIFE-19: Witty response generation based on traits
  - LIFE-20: Situational comedy detection
  - LIFE-21: Running jokes between agents
  - LIFE-22: Absurdist event reactions

success_criteria:
  - Humor matches personality traits
  - No offensive content generation
  - Subjective review by human

branch: feat/life/humor
```

**LIFE-23: Dramatic Events** (Phase 2)
```yaml
stories:
  - LIFE-24: Conflict escalation system
  - LIFE-25: Secret revelation mechanics
  - LIFE-26: Romantic subplot progression
  - LIFE-27: Village-wide event triggers

success_criteria:
  - Dramatic arcs span multiple days
  - Events create lasting memories
  - Relationship impacts are significant

branch: feat/life/dramatic-events
```

**LIFE-28: Emergent Narratives** (Phase 3)
```yaml
stories:
  - LIFE-29: Long-term goal planning
  - LIFE-30: Alliance and faction formation
  - LIFE-31: Agent life events (marriage, etc.)
  - LIFE-32: Narrative arc detection and highlighting

success_criteria:
  - Multi-agent coordinated behaviors
  - Narratives detectable in event stream
  - Story digest generation

branch: feat/life/emergent-narratives
```

---

## Agentic Workflow Framework

### Git Worktree Architecture

**IMPORTANT:** Agents MUST use git worktrees for parallel development, NOT branch switching.

```
~/worktrees/
├── clockwork-hamlet/              # Main repository
├── .coordination/
│   ├── agents.db                  # SQLite coordination database
│   ├── logs/                      # Agent logs
│   └── setup-worktree.sh          # Setup script (copied)
├── track-a-feed/                  # Worktree for Track A
│   ├── .coordination.env          # Track config (auto-generated)
│   ├── backend/
│   └── frontend/
├── track-b-poll/                  # Worktree for Track B
├── track-c-life/                  # Worktree for Track C
└── ...
```

**Why Worktrees:**
- Each agent works in isolated directory - no branch switching conflicts
- Untracked files (.env, node_modules) don't interfere between agents
- All agents can run tests simultaneously
- No "detached HEAD" disasters from concurrent operations

### Worktree Setup Script

Use `scripts/setup-worktree.sh` to create agent worktrees:

```bash
# From the main repository:
./scripts/setup-worktree.sh <worktree-name> <branch-name> [base-branch]

# Examples:
./scripts/setup-worktree.sh track-a-feed feat/feed/export-csv master
./scripts/setup-worktree.sh track-b-poll feat/poll/live-updates master
./scripts/setup-worktree.sh track-c-life feat/life/dramatic-events master
```

The script automatically:
1. Creates the git worktree with new branch
2. Copies `.env*` files from main repo
3. Copies `.claude/`, `.vscode/`, `.idea/` folders
4. Copies `backend/.env` and `frontend/.env*`
5. Installs backend dependencies (`uv sync`)
6. Installs frontend dependencies (`npm install`)
7. Initializes the coordination database entry
8. Creates `.coordination.env` in the worktree

### Coordination Database

Agents coordinate via SQLite database at `~/worktrees/.coordination/agents.db`

**Why SQLite:**
- No server required
- WAL mode handles concurrent reads excellently
- Writes are serialized but fast (microseconds)
- Prevents file I/O conflicts from ACTIVE_WORK.md

**Database Schema:**
```sql
-- Track/agent registration
agents (track, worktree_path, branch, ticket_id, status, current_task, agent_pid, ...)

-- Inter-agent messaging
messages (from_track, to_track, message_type, content, acknowledged, ...)

-- File locking for shared files
file_locks (file_path, locked_by, reason, ...)
```

**Python API (`scripts/agent_coordination.py`):**
```python
from agent_coordination import AgentCoordinator

coord = AgentCoordinator()  # Auto-loads from .coordination.env

# Claim track and start work
coord.claim_track(ticket_id="FEED-8", task_description="Export to CSV")
coord.update_status("working")

# Coordinate with other agents
coord.send_message("track-b", "warning", "I'm modifying events.py")
coord.broadcast("info", "Pushing changes to origin")
messages = coord.get_messages()

# Lock shared files before editing
if coord.lock_file("backend/src/hamlet/api/events.py", "Adding export endpoint"):
    # ... make changes ...
    coord.unlock_file("backend/src/hamlet/api/events.py")

# Complete work
coord.complete_track()
```

**CLI Interface:**
```bash
# Check all agents status
python scripts/agent_coordination.py status

# Claim track for work
python scripts/agent_coordination.py claim FEED-8 --task "Export to CSV"

# Send message to another agent
python scripts/agent_coordination.py msg --to track-b --type warning "Modifying shared file"

# Broadcast to all agents
python scripts/agent_coordination.py msg --type info "Pushing to origin"

# Check inbox
python scripts/agent_coordination.py inbox

# Show file locks
python scripts/agent_coordination.py locks
```

---

### Standard Agent Types

#### 1. Feature Development Agent
**Trigger:** Ticket assigned with clear specification
**Workflow:**
```
1. Human creates worktree: ./scripts/setup-worktree.sh track-X feat/epic/feature
2. Agent starts in worktree directory
3. Agent claims track: coord.claim_track(ticket_id="EPIC-N")
4. Read ticket specification thoroughly
5. Explore relevant codebase areas
6. Lock shared files before modifying: coord.lock_file("path")
7. Implement feature with atomic commits
8. Write/update tests
9. Unlock files: coord.unlock_file("path")
10. Update status throughout: coord.update_status("working", "Adding tests")
11. Create PR when complete
12. Release track: coord.complete_track()
```

**Success Criteria:**
- All tests pass
- No linting errors
- Ticket status is "review"
- PR description matches work done
- All file locks released

#### 2. Test Coverage Agent
**Trigger:** New code merged or coverage gap identified
**Workflow:**
```
1. Claim track in coordination DB
2. Analyze target code
3. Identify untested paths
4. Generate test cases
5. Run tests to verify
6. Report coverage metrics
7. Release track
```

#### 3. Integration Verification Agent
**Trigger:** Before merge to master
**Workflow:**
```
1. Work in dedicated worktree
2. Pull latest master
3. Run full test suite
4. Check for regressions
5. Validate build succeeds
6. Report status to coordination DB
```

---

### Reusable Slash Commands

Create these in `.claude/commands/`:

#### `/worktree-start <track-name> <ticket-id>`
```markdown
Start work in a worktree (run from worktree directory):
1. Verify .coordination.env exists
2. Claim track: `python scripts/agent_coordination.py claim <ticket-id>`
3. Check for messages: `python scripts/agent_coordination.py inbox`
4. Read ticket specification
5. Begin implementation
```

#### `/worktree-complete <ticket-id>`
```markdown
Complete work in worktree:
1. Run tests: `cd backend && uv run pytest tests/ -v`
2. If tests pass:
   - Release all file locks
   - Stage and commit with ticket reference
   - Push branch to origin
   - Create PR via `gh pr create`
   - Mark track complete: `python scripts/agent_coordination.py release`
   - Broadcast completion: `python scripts/agent_coordination.py msg --type done "PR created"`
3. If tests fail:
   - Report failures
   - Keep track claimed
```

#### `/coord-status`
```markdown
Check coordination status:
1. Show all agents: `python scripts/agent_coordination.py status`
2. Show my messages: `python scripts/agent_coordination.py inbox`
3. Show file locks: `python scripts/agent_coordination.py locks`
```

#### `/lock-file <path> <reason>`
```markdown
Lock a file before editing:
1. Check if already locked: `python scripts/agent_coordination.py locks`
2. If locked by another, message them or wait
3. Lock file via coordination API
4. Proceed with edit
5. ALWAYS unlock when done
```

---

### Parallel Launch Protocol

To launch N parallel agents:

```bash
# 1. Create worktrees for each track (human does this once)
./scripts/setup-worktree.sh track-a feat/feed/export master
./scripts/setup-worktree.sh track-b feat/poll/live master
./scripts/setup-worktree.sh track-c feat/life/drama master

# 2. Launch Claude Code in separate terminals/tmux panes
# Terminal 1:
cd ~/worktrees/track-a && claude
# Prompt: "Work on FEED-8 (export to CSV). Use /worktree-start track-a FEED-8"

# Terminal 2:
cd ~/worktrees/track-b && claude
# Prompt: "Work on POLL-12 (SSE updates). Use /worktree-start track-b POLL-12"

# Terminal 3:
cd ~/worktrees/track-c && claude
# Prompt: "Work on LIFE-24 (conflict escalation). Use /worktree-start track-c LIFE-24"

# 3. Monitor progress
watch -n5 'python ~/worktrees/clockwork-hamlet/scripts/agent_coordination.py status'
```

---

### Ralph Wiggum Integration Patterns

#### Pattern 1: Feature Development Loop
```bash
/ralph-wiggum:ralph-loop "Implement FEED-8: CSV export. Claim track first, lock files before editing, release when done." \
  --max-iterations 10 \
  --completion-promise "tests pass and PR created"
```

#### Pattern 2: Test Coverage Loop
```bash
/ralph-wiggum:ralph-loop "Achieve 90% coverage on hamlet.simulation" \
  --max-iterations 5 \
  --completion-promise "coverage report shows >= 90%"
```

---

### Orchestration Scripts

#### `scripts/setup-worktree.sh`
Creates a fully configured worktree with:
- Git worktree on new branch
- Copied .env files (root, backend, frontend)
- Copied dot-folders (.claude, .vscode, .idea)
- Installed dependencies
- Coordination DB entry
- Local .coordination.env config

#### `scripts/agent_coordination.py`
Python module and CLI for:
- Track claiming/releasing
- Status updates
- Inter-agent messaging
- File locking
- Coordination queries

#### `scripts/cleanup-worktrees.sh` (TODO)
```bash
#!/bin/bash
# Remove completed worktrees
# Archive coordination logs
# Prune merged branches
```

#### `scripts/nightly-integration.sh`
```bash
#!/bin/bash
# Check coordination DB for completed tracks
# Merge all ready branches to master
# Run full test suite
# Generate coverage report
# Notify on failures
```

---

## Success Metrics Framework

### Per-Feature Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | >80% | pytest-cov |
| API Response Time | <100ms | pytest benchmarks |
| Build Success | 100% | CI pipeline |
| Ticket Accuracy | 100% | Manual audit |

### Per-Sprint Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Features Completed | Plan count | Ticket status |
| Test Pass Rate | 100% | CI history |
| Regression Count | 0 | Bug tickets created |
| AFK Success Rate | >90% | Human intervention count |

### Quality Gates
- **Pre-merge:** All tests pass, coverage maintained, ticket updated
- **Post-merge:** Integration tests pass, no performance regression
- **Release:** E2E tests pass, manual smoke test

---

## Branch Strategy

```
master (protected)
├── feat/feed/enhanced-display
├── feat/feed/history-export
├── feat/poll/enhanced-system
├── feat/poll/simulation-integration
├── feat/poll/live-experience
├── feat/dash/village-map
├── feat/dash/stats-endpoints
├── feat/dash/realtime
├── feat/user/foundation
├── feat/user/agent-creation
├── feat/user/agent-chat
├── feat/life/humor
├── feat/life/dramatic-events
└── feat/life/emergent-narratives
```

**Merge Rules:**
1. Feature branches merge to master only
2. No direct commits to master
3. All merges require passing tests
4. Squash merge for clean history

---

## Parallel Execution Matrix

### Phase 1 (3 parallel tracks)
```
Week N:
  Track A (FEED): FEED-2,3,4,5
  Track B (POLL): POLL-2,3,4,5
  Track C (LIFE): LIFE-19,20,21,22
```

### Phase 2 (4 parallel tracks)
```
Week N+1:
  Track D (DASH): DASH-2,3,4,5
  Track E (USER): USER-2,3,4,5
  Track F (POLL): POLL-7,8,9,10
  Track G (FEED): FEED-7,8,9
```

### Phase 3 (3 parallel tracks)
```
Week N+2:
  Track H (DASH): DASH-12,13,14,15
  Track I (USER): USER-12,13,14,15,16
  Track J (LIFE): LIFE-24,25,26,27
```

---

## Agent Handoff Protocol

When an agent completes work or needs to hand off:

1. **Commit all work** with descriptive messages
2. **Update ticket** to appropriate status
3. **Document blockers** in ticket comments
4. **Push branch** to remote
5. **Create summary** of work done and next steps

**Handoff Template:**
```markdown
## Work Completed
- [List of completed items]

## Current State
- Branch: `feat/epic/feature`
- Ticket: `EPIC-N` (status: X)
- Tests: passing/failing

## Next Steps
- [What remains to be done]

## Blockers
- [Any issues encountered]
```

---

## Ticket Templates

### Story Template
```yaml
title: "[EPIC-N] Feature Name"
type: story
description: |
  ## Overview
  Brief description of the feature

  ## Acceptance Criteria
  - [ ] Criterion 1
  - [ ] Criterion 2

  ## Technical Notes
  - Implementation hints
  - Integration points

  ## Success Metrics
  - Measurable outcomes
```

### Task Template
```yaml
title: "[EPIC-N] Specific Task"
type: task
parent: EPIC-M
description: |
  ## Task
  Specific work to be done

  ## Done When
  - [ ] Code complete
  - [ ] Tests written
  - [ ] Tests passing
```

---

## Human Review Gates

### Gate 1: Phase Planning
- Review epic breakdown
- Approve parallelization plan
- Allocate resources

### Gate 2: Feature Review
- Review completed feature branches
- Approve for merge
- Verify acceptance criteria

### Gate 3: Integration Review
- Review integrated features
- Approve for release
- Sign off on quality

---

## Appendix: Command Reference

```bash
# Ticket management
ticket create -t task -p EPIC-N "Task title"
ticket todo TICKET-ID
ticket start TICKET-ID
ticket review TICKET-ID
ticket done TICKET-ID
ticket show TICKET-ID
ticket list --all

# Git workflow
git checkout -b feat/epic/feature
git add -A && git commit -m "TYPE: Description"
git push -u origin HEAD

# Testing
cd backend && uv run pytest tests/ -v
cd backend && uv run pytest tests/ --cov=hamlet --cov-report=html

# Development
cd backend && uv run uvicorn hamlet.main:app --reload
cd frontend && npm run dev
```
