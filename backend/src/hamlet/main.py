"""FastAPI application entry point."""

import asyncio
import logging

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hamlet.api import (
    agents_router,
    auth_router,
    chat_router,
    digest_router,
    events_router,
    goals_router,
    llm_router,
    locations_router,
    polls_router,
    relationships_router,
    stats_router,
    stream_router,
    world_router,
)
from hamlet.config import settings
from hamlet.db import LLMUsage, SessionLocal
from hamlet.db.seed import seed_database
from hamlet.llm.usage import CallRecord, UsageStats, get_usage_tracker
from hamlet.simulation.engine import SimulationEngine
from hamlet.simulation.events import EventType, SimulationEvent, event_bus

logger = logging.getLogger(__name__)

# Global simulation engine instance
simulation_engine: SimulationEngine | None = None


def persist_llm_call(record: CallRecord) -> None:
    """Persist an LLM call to the database."""
    db = SessionLocal()
    try:
        usage = LLMUsage(
            timestamp=record.timestamp,
            model=record.model,
            tokens_in=record.tokens_in,
            tokens_out=record.tokens_out,
            cost_usd=record.cost_usd,
            latency_ms=record.latency_ms,
            cached=record.cached,
            agent_id=record.agent_id,
            call_type=record.call_type,
        )
        db.add(usage)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to persist LLM usage: {e}")
        db.rollback()
    finally:
        db.close()


async def publish_llm_event(record: CallRecord, stats: UsageStats) -> None:
    """Publish LLM usage event to SSE stream."""
    import time
    event = SimulationEvent(
        type=EventType.LLM_USAGE,
        summary=f"LLM call: {record.tokens_in}+{record.tokens_out} tokens (${record.cost_usd:.4f})",
        timestamp=int(time.time()),
        data={
            "call": {
                "model": record.model,
                "tokens_in": record.tokens_in,
                "tokens_out": record.tokens_out,
                "cost_usd": round(record.cost_usd, 6),
                "latency_ms": round(record.latency_ms, 1),
                "cached": record.cached,
                "agent_id": record.agent_id,
            },
            "totals": stats.to_dict(),
        },
    )
    await event_bus.publish(event)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    global simulation_engine

    # Startup
    logger.info("Starting Clockwork Hamlet...")

    # 1. Seed database if empty
    logger.info("Checking database...")
    seed_database()

    # 2. Set up LLM usage tracking
    logger.info("Setting up LLM usage tracking...")
    tracker = get_usage_tracker()
    tracker.set_db_callback(persist_llm_call)
    tracker.set_event_callback(publish_llm_event)

    # 3. Start simulation engine
    logger.info("Starting simulation engine...")
    simulation_engine = SimulationEngine(tick_interval=settings.tick_interval_seconds)
    await simulation_engine.start()

    logger.info("Clockwork Hamlet is running!")

    yield

    # Shutdown
    logger.info("Shutting down Clockwork Hamlet...")
    if simulation_engine:
        await simulation_engine.stop()
    logger.info("Goodbye!")


app = FastAPI(
    title=settings.app_name,
    description="AI-driven village simulation with emergent narratives",
    version="0.1.0",
    lifespan=lifespan,
)

# Build CORS origins list
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
    # Production
    "https://clockwork.oceanheart.ai",
    # Vercel deployments
    "https://clockwork-hamlet.vercel.app",
    "https://clockwork-hamlet-rick-halletts-projects.vercel.app",
]

# Add any additional origins from environment variable
if settings.cors_origins:
    cors_origins.extend([o.strip() for o in settings.cors_origins.split(",") if o.strip()])

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://clockwork-hamlet.*\.vercel\.app",  # Allow all Vercel preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(world_router)
app.include_router(agents_router)
app.include_router(chat_router)
app.include_router(locations_router)
app.include_router(events_router)
app.include_router(relationships_router)
app.include_router(goals_router)
app.include_router(polls_router)
app.include_router(digest_router)
app.include_router(stream_router)
app.include_router(llm_router)
app.include_router(stats_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Clockwork Hamlet", "version": "0.1.0"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


def main():
    """Run the application."""
    uvicorn.run(
        "hamlet.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
