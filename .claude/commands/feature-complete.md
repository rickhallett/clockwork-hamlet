# Feature Complete Command

Complete work on a feature and prepare for review.

## Arguments
- `$ARGUMENTS` - The ticket ID (e.g., FEED-2, POLL-3)

## Workflow

1. **Ensure all changes are saved**

2. **Run the test suite:**
   ```bash
   cd backend && uv run pytest tests/ -v --tb=short
   ```

3. **If tests PASS:**
   - Stage all changes: `git add -A`
   - Create commit with ticket reference:
     ```bash
     git commit -m "FEAT: <description>

     - Bullet points of changes

     Implements $ARGUMENTS"
     ```
   - Push branch: `git push -u origin HEAD`
   - Update ticket: `ticket review $ARGUMENTS`
   - Report completion with summary of work done

4. **If tests FAIL:**
   - Report which tests failed and why
   - Keep ticket in `in_progress` status
   - Provide guidance on fixing the failures
   - Do NOT mark ticket as review

5. **Generate handoff summary:**
   ```markdown
   ## Work Completed
   - [List changes made]

   ## Branch
   - Name: <branch-name>
   - Commits: <count>

   ## Tests
   - Status: PASS/FAIL
   - Coverage: X%

   ## Ticket
   - $ARGUMENTS: <new-status>
   ```

## Success Criteria
- All tests pass
- Changes committed with proper message
- Branch pushed to remote
- Ticket status updated to `review`
- Handoff summary provided

## Notes
- Never mark a ticket as review if tests fail
- Include ticket ID in commit message for traceability
- Push to remote so other agents/humans can access the work
