# Feature Start Command

Start work on a feature ticket. This command initializes the development environment for a new feature.

## Arguments
- `$ARGUMENTS` - The ticket ID (e.g., FEED-2, POLL-3)

## Workflow

1. **Read the ticket specification:**
   ```
   ticket show $ARGUMENTS
   ```

2. **Extract epic prefix from ticket ID** to determine branch naming

3. **Create feature branch from master:**
   ```
   git checkout master
   git pull origin master
   git checkout -b feat/<epic-lowercase>/<descriptive-name>
   ```

4. **Update ticket status to in_progress:**
   ```
   ticket todo $ARGUMENTS && ticket start $ARGUMENTS
   ```

5. **Explore relevant codebase areas** based on ticket description

6. **Create initial todo list** with implementation steps based on ticket requirements

7. **Begin implementation** - write code following existing patterns in the codebase

## Success Criteria
- Branch created and checked out
- Ticket status is `in_progress`
- Todo list created with clear implementation steps
- Ready to begin coding

## Notes
- Always read the ticket thoroughly before starting
- Check for related tickets that might have dependencies
- Ensure you understand the acceptance criteria before coding
