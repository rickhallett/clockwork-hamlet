# Sync Tickets Command

Synchronize ticket statuses with git state. Ensures tickets reflect actual work state.

## Arguments
- `$ARGUMENTS` - Optional: epic prefix to filter (FEED, POLL, DASH, USER, LIFE)

## Workflow

1. **List all feature branches:**
   ```bash
   git branch -a | grep 'feat/'
   ```

2. **For each branch, extract ticket references from commits:**
   ```bash
   git log master..<branch> --oneline | grep -oE '[A-Z]+-[0-9]+'
   ```

3. **Determine expected ticket status based on branch state:**
   - Branch exists, not merged → ticket should be `in_progress` or `review`
   - Branch merged to master → ticket should be `done`
   - No branch exists → ticket should be `backlog` or `todo`

4. **Check current ticket status:**
   ```bash
   ticket show <ticket-id>
   ```

5. **Report discrepancies:**
   ```markdown
   ## Ticket Sync Report

   ### In Sync
   - TICKET-1: in_progress (branch: feat/epic/feature)
   - TICKET-2: done (merged)

   ### Needs Update
   - TICKET-3: Expected `review`, found `in_progress`
     - Action: `ticket review TICKET-3`
   - TICKET-4: Expected `done`, found `review`
     - Action: `ticket done TICKET-4`

   ### Orphaned Work
   - Branch `feat/epic/old` has no associated ticket
   ```

6. **Optionally fix discrepancies** (if `--fix` in arguments):
   - Update ticket statuses to match expected state

## Success Criteria
- All tickets match their git state
- No orphaned branches
- Clear report of any discrepancies

## Notes
- Run periodically to keep tickets accurate
- Use before planning to ensure accurate backlog
- Helps identify abandoned work
