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

### Standard Agent Types

#### 1. Feature Development Agent
**Trigger:** Ticket assigned with clear specification
**Workflow:**
```
1. Create feature branch from master
2. Read ticket specification thoroughly
3. Explore relevant codebase areas
4. Implement feature with atomic commits
5. Write/update tests
6. Update ticket status throughout
7. Create PR when complete
```

**Success Criteria:**
- All tests pass
- No linting errors
- Ticket status is "review"
- PR description matches work done

#### 2. Test Coverage Agent
**Trigger:** New code merged or coverage gap identified
**Workflow:**
```
1. Analyze target code
2. Identify untested paths
3. Generate test cases
4. Run tests to verify
5. Report coverage metrics
```

**Success Criteria:**
- Coverage increased
- All new tests pass
- No flaky tests introduced

#### 3. Integration Verification Agent
**Trigger:** Before merge to master
**Workflow:**
```
1. Checkout branch
2. Run full test suite
3. Check for regressions
4. Validate build succeeds
5. Report status
```

**Success Criteria:**
- All tests pass
- Build succeeds
- No new warnings

#### 4. Ticket Sync Agent
**Trigger:** End of work session or commit
**Workflow:**
```
1. Parse recent commits
2. Extract ticket references
3. Update ticket statuses
4. Link commits to tickets
5. Report discrepancies
```

**Success Criteria:**
- All referenced tickets updated
- No orphaned work

---

### Reusable Slash Commands

Create these in `.claude/commands/`:

#### `/feature-start <ticket-id>`
```markdown
Start work on a feature ticket:
1. Read ticket: `ticket show <ticket-id>`
2. Create branch: `git checkout -b feat/<epic>/<short-name>`
3. Update ticket: `ticket start <ticket-id>`
4. Begin implementation based on ticket spec
```

#### `/feature-complete <ticket-id>`
```markdown
Complete feature work:
1. Run tests: `uv run pytest tests/ -v`
2. If tests pass:
   - Stage and commit with ticket reference
   - Update ticket: `ticket review <ticket-id>`
   - Report completion status
3. If tests fail:
   - Report failures
   - Keep ticket in_progress
```

#### `/parallel-launch <ticket-ids...>`
```markdown
Launch parallel development agents:
1. For each ticket-id:
   - Spawn Task agent with feature-dev prompt
   - Agent creates own branch
   - Agent works independently
2. Monitor all agents for completion
3. Report when all complete
```

#### `/verify-branch`
```markdown
Verify current branch is merge-ready:
1. Run full test suite
2. Check commit messages follow convention
3. Verify ticket status matches work
4. Report any issues
```

#### `/sync-tickets`
```markdown
Synchronize ticket status with git state:
1. List recent commits
2. Extract ticket references from messages
3. Update ticket statuses based on branch state
4. Report any discrepancies
```

---

### Ralph Wiggum Integration Patterns

#### Pattern 1: Feature Development Loop
```bash
/ralph-wiggum:ralph-loop "Implement FEED-2: significance indicators" \
  --max-iterations 10 \
  --completion-promise "tests pass and ticket marked review"
```

#### Pattern 2: Test Coverage Loop
```bash
/ralph-wiggum:ralph-loop "Achieve 90% coverage on hamlet.simulation" \
  --max-iterations 5 \
  --completion-promise "coverage report shows >= 90%"
```

#### Pattern 3: Bug Fix Loop
```bash
/ralph-wiggum:ralph-loop "Fix failing test test_agent_decision" \
  --max-iterations 3 \
  --completion-promise "pytest tests/test_agent.py passes"
```

---

### Orchestration Scripts

#### `scripts/parallel-features.py`
```python
"""Launch parallel Claude Code instances for independent features."""
# Spawns separate tmux sessions or processes
# Each instance works on assigned ticket
# Monitors for completion
# Reports aggregated status
```

#### `scripts/verify-all-branches.sh`
```bash
#!/bin/bash
# Iterate through all feature branches
# Run test suite on each
# Report pass/fail matrix
```

#### `scripts/nightly-integration.sh`
```bash
#!/bin/bash
# Merge all ready branches to integration
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
