"""FastAPI application entry point."""

import asyncio
import logging

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hamlet.api import (
    agents_router,
    digest_router,
    events_router,
    locations_router,
    polls_router,
    relationships_router,
    stream_router,
    world_router,
)
from hamlet.config import settings
from hamlet.db.seed import seed_database
from hamlet.simulation.engine import SimulationEngine

logger = logging.getLogger(__name__)

# Global simulation engine instance
simulation_engine: SimulationEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    global simulation_engine

    # Startup
    logger.info("Starting Clockwork Hamlet...")

    # 1. Seed database if empty
    logger.info("Checking database...")
    seed_database()

    # 2. Start simulation engine
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

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        # Add production domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(world_router)
app.include_router(agents_router)
app.include_router(locations_router)
app.include_router(events_router)
app.include_router(relationships_router)
app.include_router(polls_router)
app.include_router(digest_router)
app.include_router(stream_router)


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
