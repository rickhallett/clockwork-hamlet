# Active Work Registry

> **IMPORTANT**: This file tracks parallel agentic development. Read this FIRST when starting work.

## How This Works

Multiple Claude Code agents work on this codebase simultaneously. This file prevents conflicts and enables coordination.

**Before starting ANY work:**
1. Read this file to see what others are doing
2. Check out your work (add entry below)
3. Work on your assigned track
4. Check in when done (remove entry)

---

## Currently Active Agents

<!--
Format:
| Track | Ticket | Branch | Agent Session | Started | Status |
-->

| Track | Ticket | Branch | Agent Session | Started | Status |
|-------|--------|--------|---------------|---------|--------|
| F | POLL-9 | feat/poll/agent-voting | claude-opus | 2026-01-14 | complete |
| L | LIFE-26,27,28,29 | feat/life/dramatic-events | claude-opus-4.5 | 2026-01-14 | complete |

---

## How to Check In/Out

### Starting Work (Check In)
```bash
# 1. Add your entry to the table above:
#    | A | FEED-4 | feat/feed/significance | session-abc123 | 2024-01-15 14:00 | implementing |

# 2. Then start your work
git checkout -b feat/<epic>/<feature>
ticket start <TICKET-ID>
```

### Completing Work (Check Out)
```bash
# 1. Commit and push your work
git add -A && git commit -m "..." && git push -u origin HEAD

# 2. Update ticket
ticket review <TICKET-ID>  # or ticket done <TICKET-ID>

# 3. Remove your entry from the table above
```

---

## Development Tracks

These are the parallel tracks. **Pick ONE track** - don't work across tracks.

### Phase 1 Tracks (Can Start Now)

| Track | Epic | Story | Tasks | Focus |
|-------|------|-------|-------|-------|
| **A** | FEED | FEED-2 | FEED-4,5,6,7 | Frontend event display enhancements |
| **B** | POLL | POLL-2 | POLL-5,6,7,8 | Backend poll system |
| **C** | LIFE | LIFE-19 | LIFE-22,23,24,25 | Backend humor/wit in dialogue |

### Phase 2 Tracks (After Phase 1 Stories Complete)

| Track | Epic | Story | Tasks | Focus |
|-------|------|-------|-------|-------|
| **D** | DASH | DASH-2 | DASH-5,6,7,8 | Frontend village map |
| **E** | DASH | DASH-3 | DASH-9,10,11,12 | Backend stats API |
| **F** | POLL | POLL-3 | POLL-9,10,11,12 | Backend poll+simulation |
| **G** | USER | USER-2 | USER-5,6,7,8 | Backend auth foundation |
| **H** | FEED | FEED-3 | FEED-8,9,10 | Backend+Frontend history/export |

### Phase 3 Tracks (After Phase 2)

| Track | Epic | Story | Tasks | Focus |
|-------|------|-------|-------|-------|
| **I** | DASH | DASH-4 | DASH-13,14,15,16 | Real-time dashboard |
| **J** | USER | USER-3 | USER-9,10,11,12 | Agent creation |
| **K** | USER | USER-4 | USER-13,14,15,16,17 | Agent chat |
| **L** | LIFE | LIFE-20 | LIFE-26,27,28,29 | Dramatic events |
| **M** | LIFE | LIFE-21 | LIFE-30,31,32,33 | Emergent narratives |

---

## Conflict Avoidance Rules

1. **One agent per track** - Never work on the same track as another agent
2. **Stay in your lane** - Only modify files relevant to your track
3. **Communicate via commits** - Push frequently so others see your progress
4. **Update this file** - Check in/out religiously

### File Ownership by Track

| Track | Primary Files | Shared (Coordinate) |
|-------|--------------|---------------------|
| A (FEED display) | `frontend/src/components/feed/*`, `frontend/src/pages/LiveFeed.tsx` | - |
| B (POLL system) | `backend/src/hamlet/api/polls.py`, `backend/src/hamlet/db/models.py` (Poll) | models.py |
| C (LIFE humor) | `backend/src/hamlet/llm/context.py`, `backend/src/hamlet/simulation/` | context.py |
| D (DASH map) | `frontend/src/components/map/*`, `frontend/src/pages/Dashboard.tsx` | - |
| E (DASH API) | `backend/src/hamlet/api/stats.py` (new) | - |
| F (POLL sim) | `backend/src/hamlet/simulation/polls.py` (new) | simulation/ |
| G (USER auth) | `backend/src/hamlet/auth/*` (new), `backend/src/hamlet/db/models.py` (User) | models.py |

---

## Quick Reference

```bash
# See what's being worked on
cat .claude/ACTIVE_WORK.md

# See all tickets
source .venv/bin/activate && ticket list

# See specific epic
ticket show FEED-1   # Shows children

# Start a task
/feature-start FEED-4

# Complete a task
/feature-complete FEED-4
```

---

## Current Roadmap Status

Check `AGENTIC_ROADMAP.md` for full details.

**Completed:** LIFE-1 (core life features)
**In Progress:** See active agents table above
**Up Next:** Phase 1 tracks A, B, C
