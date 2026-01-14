# CLAUDE.md - Clockwork Hamlet

## Project Overview

Clockwork Hamlet is a persistent, multi-agent village simulation where AI-driven characters live, interact, form relationships, and create emergent narratives. The simulation runs on a tick system with LLM-powered decision making.

## Architecture

```
clockwork-hamlet/
├── backend/                 # FastAPI + SQLite + Claude LLM
│   ├── src/hamlet/
│   │   ├── api/            # REST endpoints + SSE streaming
│   │   ├── db/             # SQLAlchemy models + seeding
│   │   ├── llm/            # LLM client + agent decision logic
│   │   ├── actions/        # Action types + execution + validation
│   │   └── simulation/     # Engine, world state, events
│   └── tests/              # pytest test suite
├── frontend/               # React + Vite + Tailwind (Tokyo Night)
│   └── src/
│       ├── components/     # UI components
│       ├── hooks/          # Data fetching + SSE hooks
│       └── pages/          # Route pages
├── docs/                   # Documentation + guides
└── docker-compose.yml      # Production deployment
```

## Development Philosophy: Agentic Coding

This project follows an **agentic development** approach:

### Core Principles

1. **Stop Coding Manually** - Use agents for implementation; focus on orchestration
2. **One Agent, One Purpose** - Fresh context windows for each task
3. **Feedback Loops Always** - Include validation commands in every workflow
4. **Target Zero Touch** - Build toward autonomous execution

### Workflow Commands

```bash
# Autonomous development loop
/ralph-wiggum:ralph-loop "TASK" --max-iterations N --completion-promise "SUCCESS_CRITERIA"

# Cancel active loop
/ralph-wiggum:cancel-ralph

# Get help
/ralph-wiggum:help
```

### Feedback Loops

Always run after changes:

```bash
# Backend
cd backend && uv run pytest              # Tests
cd backend && uv run ruff check .        # Linting

# Frontend
cd frontend && npm run build             # TypeScript compilation
cd frontend && npm run lint              # ESLint

# Docker
docker-compose up -d --build             # Full stack
curl http://localhost:8000/api/health    # Health check
```

## Python Package Management

**Always use `uv` for Python package management** - never use pip directly.

```bash
# Install dependencies
uv sync                           # Install from pyproject.toml
uv pip install <package>          # Install a package (in venv)

# Run commands
uv run pytest                     # Run with project deps
uv run python script.py           # Run scripts

# Create virtual environment
uv venv .venv                     # Create venv
source .venv/bin/activate         # Activate

# Install editable package
uv pip install -e .               # Install current project
```

## Git Practices

- Make atomic commits representing single logical changes
- Commit frequently as work progresses
- Write clear messages focusing on "why" not "what"
- Do not include co-author attributions
- **Reference ticket keys in commit messages** (e.g., `[AUTH-4] Add Google OAuth provider`)

## Development Workflow (MANDATORY)

**All development tasks MUST be tracked in the ticket system.**

### Before Starting Work
1. Ensure an Epic exists for the feature area
2. Create a Story under the Epic for the user-facing goal
3. Create Task(s) under the Story for implementation steps
4. Mark the task as in_progress: `ticket start <KEY>`

### During Development
- Keep ticket status in sync with actual progress
- Use `ticket modify` to update details as scope clarifies
- Add comments for blockers or decisions: `ticket comment <KEY> "note"`

### When Committing
- Reference the ticket key in commit messages:
  ```
  [PROJ-123] Implement feature X

  - Added foo module
  - Updated bar config
  ```

### After Completing Work
- Mark task as done: `ticket done <KEY>`
- Verify parent Story/Epic status reflects overall progress

### Example Workflow
```bash
# 1. Create tickets
ticket add epic "User Authentication" --project AUTH
ticket add story "OAuth2 login support" --epic AUTH-1
ticket add task "Add Google provider" --story AUTH-2 --assignee me

# 2. Start work
ticket start AUTH-3

# 3. Commit with reference
git commit -m "[AUTH-3] Add Google OAuth provider"

# 4. Complete
ticket done AUTH-3
```

## Key Files

- `backend/src/hamlet/main.py` - FastAPI app entry, lifespan, routers
- `backend/src/hamlet/simulation/engine.py` - Tick loop, agent processing
- `backend/src/hamlet/llm/agent.py` - LLM decision making
- `backend/src/hamlet/actions/` - Action types and execution
- `backend/src/hamlet/db/seed.py` - Database seeding (10 agents, 11 locations)

## Running the Project

### Docker (Recommended)
```bash
# Ensure .env has ANTHROPIC_API_KEY
docker-compose up -d --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3003
```

### Local Development
```bash
# Backend
cd backend && uv sync && uv run uvicorn hamlet.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Testing

```bash
# Run all tests
cd backend && uv run pytest

# Run specific test file
cd backend && uv run pytest tests/test_api.py

# Run with coverage
cd backend && uv run pytest --cov=hamlet
```

## Common Tasks

### Add New Agent Action
1. Define action class in `backend/src/hamlet/actions/types.py`
2. Add executor in `backend/src/hamlet/actions/execution.py`
3. Add tests in `backend/tests/test_actions.py`
4. Run: `uv run pytest tests/test_actions.py`

### Add API Endpoint
1. Create/modify router in `backend/src/hamlet/api/`
2. Add tests in `backend/tests/test_api.py`
3. Run: `uv run pytest tests/test_api.py`

### Fix Frontend Bug
1. Identify component in `frontend/src/`
2. Make fix
3. Run: `npm run build && npm run lint`

## Troubleshooting

- **SSE disconnection**: Check CORS origins in `main.py` include frontend port
- **Database errors**: Check DATABASE_URL format (sqlite:///path/to/db)
- **LLM not working**: Verify ANTHROPIC_API_KEY in .env
- **Docker build fails**: Run `docker system prune -f` then rebuild

## Ticket Manager CLI

Local JIRA-like ticket management for development roadmap.

### Slash Commands

Use these commands for ticket operations:

| Command | Usage | Description |
|---------|-------|-------------|
| `/ticket-create` | `/ticket-create task "Fix bug" for AUTH-2` | Create epic/story/task |
| `/ticket-list` | `/ticket-list status:todo` | List and filter tickets |
| `/ticket-start` | `/ticket-start AUTH-3` | Begin work on ticket |
| `/ticket-done` | `/ticket-done AUTH-3` | Mark ticket complete |
| `/ticket-show` | `/ticket-show AUTH-3` | Show ticket details |

### Direct CLI Usage

```bash
# Setup (from project root)
uv venv .venv && source .venv/bin/activate && uv pip install -e .
ticket init

# Create hierarchy
ticket add epic "Feature" --project PROJ
ticket add story "User story" --epic PROJ-1
ticket add task "Task" --story PROJ-2

# Filter
ticket list status:todo +urgent type:task

# Workflow
ticket start PROJ-1 → ticket done PROJ-1
```

## Documentation

- `docs/agentic-development-guide.md` - Full agentic workflow guide
- `docs/specs/clockwork-hamlet.spec.md` - Original specification
