"""FastAPI application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hamlet.api import (
    agents_router,
    digest_router,
    events_router,
    locations_router,
    polls_router,
    relationships_router,
    world_router,
)
from hamlet.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI-driven village simulation with emergent narratives",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
