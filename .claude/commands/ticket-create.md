# Create Ticket

Create a new ticket in the system. Argument: $ARGUMENTS

Instructions:
1. Parse the argument to determine ticket type and details
2. If no parent specified for story/task, ask or infer from context
3. Run the appropriate command:

```bash
# For epic
ticket add epic "TITLE" --project PROJECT

# For story (requires epic)
ticket add story "TITLE" --epic EPIC-KEY

# For task (requires story)
ticket add task "TITLE" --story STORY-KEY
```

4. Report the created ticket key
5. If this is for immediate work, offer to run `ticket start KEY`
