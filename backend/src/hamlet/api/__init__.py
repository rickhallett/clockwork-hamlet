"""API routes package."""

from hamlet.api.agents import router as agents_router
from hamlet.api.digest import router as digest_router
from hamlet.api.events import router as events_router
from hamlet.api.goals import router as goals_router
from hamlet.api.locations import router as locations_router
from hamlet.api.polls import router as polls_router
from hamlet.api.relationships import router as relationships_router
from hamlet.api.stream import router as stream_router
from hamlet.api.world import router as world_router

__all__ = [
    "agents_router",
    "digest_router",
    "events_router",
    "goals_router",
    "locations_router",
    "polls_router",
    "relationships_router",
    "stream_router",
    "world_router",
]
