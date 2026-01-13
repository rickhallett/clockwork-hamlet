# Clockwork Hamlet

A persistent, multi-agent village simulation where AI-driven characters with distinct personalities live, interact, form relationships, pursue goals, and create emergent narratives.

## Concept

Drop 10-20 AI agents with unique personalities into a small village. Give them needs, goals, and opinions. Let them interact. Watch what happens.

The magic is in **emergence** — we don't script storylines, we create conditions for stories to emerge from agent interactions. The scheming merchant befriends the lonely baker. The paranoid hermit accuses the mayor of cheese theft. Alliances form. Grudges fester. Romance blooms.

## Features

- **Live Feed** — Real-time stream of village events in a terminal-aesthetic interface
- **Character Profiles** — Detailed pages showing agent state, traits, relationships, and memories
- **Viewer Polls** — Community-driven influence on the simulation without breaking agent autonomy
- **Highlight Reels** — LLM-generated summaries of interesting events
- **Relationship Graphs** — Visual network showing connections between all agents

## Tech Stack

### Backend
- **FastAPI** — Async API server with SSE support
- **SQLite via Turso** — Simple, edge-ready persistence
- **Claude Haiku / Gemini Flash** — Fast, cheap LLM for agent decisions

### Frontend
- **Bun + Vite** — Fast builds and HMR
- **React 18** — SSE hooks, component ecosystem
- **Tailwind** — Tokyo Night terminal aesthetic

## Architecture

```
SIMULATE → OBSERVE → ANALYZE → IMPROVE → REPEAT
```

The simulation runs on a tick system where agents perceive their environment, make decisions via LLM calls, and execute actions deterministically. Relationships evolve, memories compress, and narratives emerge.

## Status

**Pre-development** — See [docs/specs/clockwork-hamlet.spec.md](docs/specs/clockwork-hamlet.spec.md) for the full specification.

## License

TBD
