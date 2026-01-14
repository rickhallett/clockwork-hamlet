# Create Story Command

Create a new story with child tasks in the ticket system.

## Arguments
- `$ARGUMENTS` - Format: `<EPIC-PREFIX> "<Story Title>" "<Task1>" "<Task2>" ...`

Example: `FEED "Enhanced Display" "Add significance icons" "Implement grouping" "Add search"`

## Workflow

1. **Parse arguments:**
   - Extract epic prefix (FEED, POLL, DASH, USER, LIFE)
   - Extract story title
   - Extract task titles (remaining arguments)

2. **Find parent epic:**
   ```bash
   ticket list --all | grep "<EPIC>-1"
   ```

3. **Create story ticket:**
   ```bash
   ticket create -t story -p <EPIC>-1 "<Story Title>"
   ```
   - Note the created story ID

4. **Create task tickets for each task:**
   ```bash
   ticket create -t task -p <STORY-ID> "<Task Title>"
   ```

5. **Report created tickets:**
   ```markdown
   ## Created Tickets

   ### Story
   - <STORY-ID>: <Story Title>
     - Parent: <EPIC>-1

   ### Tasks
   - <TASK-1>: <Task 1 Title>
   - <TASK-2>: <Task 2 Title>
   - <TASK-3>: <Task 3 Title>

   ### Next Steps
   1. Add descriptions to tickets
   2. Set priorities if needed
   3. Begin work with `/feature-start <TASK-ID>`
   ```

## Success Criteria
- Story created under correct epic
- All tasks created under story
- Ticket IDs reported for reference

## Notes
- Keep task titles concise but descriptive
- Stories should be completable in ~1-2 days
- Tasks should be completable in ~2-4 hours
