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

## Git Practices

- Make atomic commits representing single logical changes
- Commit frequently as work progresses
- Write clear messages focusing on "why" not "what"
- Do not include co-author attributions

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

## Documentation

- `docs/agentic-development-guide.md` - Full agentic workflow guide
- `docs/specs/clockwork-hamlet.spec.md` - Original specification
