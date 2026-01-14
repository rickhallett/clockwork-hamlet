# Agent Briefing Command

**Run this FIRST when starting a new session.** This orients you to the multi-agent development environment.

## Workflow

1. **Read the active work registry:**
   ```bash
   cat .claude/ACTIVE_WORK.md
   ```
   - See what other agents are currently working on
   - Identify which tracks are available

2. **Read the full roadmap:**
   ```bash
   cat AGENTIC_ROADMAP.md
   ```
   - Understand the overall development plan
   - See epic dependencies and phase structure

3. **Check current ticket status:**
   ```bash
   source .venv/bin/activate && ticket list
   ```
   - See what's in progress, what's done, what's available

4. **Check git branch status:**
   ```bash
   git branch -a | grep feat/
   git log --oneline -10
   ```
   - See what feature branches exist
   - Understand recent work

5. **Report your findings:**
   Provide a summary:
   ```markdown
   ## Session Briefing

   ### Active Agents
   - [List from ACTIVE_WORK.md]

   ### Available Tracks
   - Track X: [description] - Ready to start
   - Track Y: [description] - Ready to start

   ### Recent Activity
   - [Recent commits/branches]

   ### Recommended Next Action
   - [Suggested track/ticket to work on]
   ```

## Context You Need to Know

### This is a Multi-Agent Project
- Multiple Claude Code instances work in parallel
- Each agent owns ONE track (set of related tasks)
- Coordination happens through `.claude/ACTIVE_WORK.md`
- Never work on another agent's track

### Development Tracks
Tracks are sets of related tasks that can be worked on independently:
- **Phase 1 (now):** FEED display, POLL backend, LIFE humor
- **Phase 2 (next):** DASH map, DASH API, POLL simulation, USER auth
- **Phase 3 (later):** Real-time dashboard, Agent creation, Agent chat

### Your Responsibilities
1. Check in to ACTIVE_WORK.md when starting
2. Work only on your assigned track
3. Push frequently (so others see progress)
4. Check out when done
5. Keep tickets synchronized with actual work

### Key Commands
- `/feature-start TICKET` - Start work on a ticket
- `/feature-complete TICKET` - Complete work
- `/verify-branch` - Pre-merge checks
- `/run-tests` - Execute test suite

## After Briefing

Once oriented, either:
1. **Join an existing track** - If you were assigned specific work
2. **Claim an available track** - Pick from available Phase 1 tracks
3. **Wait for assignment** - If unsure, report findings and wait

To claim a track:
```bash
# 1. Edit .claude/ACTIVE_WORK.md to add your entry
# 2. Run: /feature-start <first-ticket-in-track>
```
