# List Tickets

List tickets with optional filters. Argument: $ARGUMENTS

Run:
```bash
ticket list $ARGUMENTS
```

Common filters:
- `status:todo` / `status:in_progress` - by status
- `type:epic` / `type:story` / `type:task` - by type
- `+tagname` - by tag
- `assignee:name` - by assignee
- `--all` / `-a` - include done/cancelled
