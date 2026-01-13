"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return health status of the service."""
    return {
        "status": "ok",
        "service": "clockwork-hamlet",
        "version": "0.1.0",
    }
