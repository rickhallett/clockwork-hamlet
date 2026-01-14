# Feature Start Command

Start work on a feature ticket with full multi-agent coordination.

## Arguments
- `$ARGUMENTS` - The ticket ID (e.g., FEED-4, POLL-5)

## Pre-Flight Checks

**CRITICAL: Before starting, verify no conflicts exist.**

1. **Check active work registry:**
   ```bash
   cat .claude/ACTIVE_WORK.md
   ```
   - Ensure no other agent is on your track
   - If conflict exists, STOP and choose different track

2. **Check the ticket exists and is available:**
   ```bash
   source .venv/bin/activate && ticket show $ARGUMENTS
   ```
   - Should be in `backlog` or `todo` status
   - If `in_progress` by someone else, STOP

## Workflow

1. **Identify which track this ticket belongs to:**
   - FEED-4,5,6,7 → Track A (FEED display)
   - POLL-5,6,7,8 → Track B (POLL system)
   - LIFE-22,23,24,25 → Track C (LIFE humor)
   - etc. (see `.claude/ACTIVE_WORK.md` for full mapping)

2. **Register in ACTIVE_WORK.md:**
   Edit `.claude/ACTIVE_WORK.md` and add your row to the "Currently Active Agents" table:
   ```
   | <Track> | $ARGUMENTS | feat/<epic>/<name> | <session-id> | <timestamp> | starting |
   ```

3. **Create feature branch from master:**
   ```bash
   git checkout master
   git pull origin master
   git checkout -b feat/<epic-lowercase>/<descriptive-name>
   ```
   Example: `feat/feed/significance-indicators` for FEED-4

4. **Update ticket status:**
   ```bash
   source .venv/bin/activate
   ticket todo $ARGUMENTS && ticket start $ARGUMENTS
   ```

5. **Read the ticket specification thoroughly:**
   ```bash
   ticket show $ARGUMENTS
   ```
   Understand:
   - What needs to be built
   - Acceptance criteria
   - Parent story context

6. **Explore relevant codebase areas:**
   - For FEED: `frontend/src/components/feed/`, `frontend/src/pages/LiveFeed.tsx`
   - For POLL: `backend/src/hamlet/api/polls.py`, `backend/src/hamlet/db/models.py`
   - For DASH: `backend/src/hamlet/api/`, `frontend/src/components/`
   - For USER: `backend/src/hamlet/` (new auth module)
   - For LIFE: `backend/src/hamlet/llm/`, `backend/src/hamlet/simulation/`

7. **Create implementation plan:**
   Use TodoWrite to track:
   - [ ] Understand existing code patterns
   - [ ] Implement core feature
   - [ ] Write tests
   - [ ] Update any documentation
   - [ ] Commit with ticket reference

8. **Begin implementation** following existing patterns

## Commit Guidelines

Every commit should reference the ticket:
```bash
git commit -m "FEAT: Add significance indicators to event cards

- Add significance prop to EventCard component
- Create icon mapping for levels 1-3
- Update EventStream to pass significance

Implements FEED-4"
```

## Success Criteria
- Registered in ACTIVE_WORK.md
- Branch created and checked out
- Ticket status is `in_progress`
- Implementation plan created
- Ready to begin coding

## Important Reminders

- **You are part of a team** - Other agents may be working in parallel
- **Stay in your lane** - Only modify files relevant to your track
- **Push frequently** - `git push` after meaningful progress
- **Update ACTIVE_WORK.md** - Keep status column current
- **Run tests before commits** - `cd backend && uv run pytest`
