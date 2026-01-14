# Verify Branch Command

Verify that the current branch is ready for merge to master.

## Arguments
- `$ARGUMENTS` - Optional: specific checks to run (tests, lint, tickets, all)

## Workflow

1. **Identify current branch:**
   ```bash
   git branch --show-current
   ```

2. **Run full test suite:**
   ```bash
   cd backend && uv run pytest tests/ -v --tb=short
   ```
   - Report pass/fail count
   - Note any failures

3. **Check commit history:**
   ```bash
   git log master..HEAD --oneline
   ```
   - Verify commits follow conventional format (FEAT:, FIX:, TEST:, etc.)
   - Check for ticket references

4. **Extract ticket IDs from commits** and verify their status:
   ```bash
   ticket show <ticket-id>
   ```
   - Tickets should be in `review` or `done` status

5. **Check for merge conflicts:**
   ```bash
   git fetch origin master
   git merge-base --is-ancestor origin/master HEAD || echo "Needs rebase"
   ```

6. **Generate verification report:**
   ```markdown
   ## Branch Verification: <branch-name>

   ### Tests
   - Status: PASS/FAIL
   - Passed: X
   - Failed: Y

   ### Commits
   - Count: N
   - Convention: OK/ISSUES

   ### Tickets
   - Referenced: TICKET-1, TICKET-2
   - Status: All in review/done

   ### Merge Status
   - Conflicts: None/Needs rebase

   ### Verdict
   - READY FOR MERGE / NEEDS ATTENTION
   ```

## Success Criteria
- All tests pass
- Commits follow convention
- Tickets in correct status
- No merge conflicts

## Notes
- Run this before requesting merge
- Fix any issues before proceeding
- Rebase on master if behind
