"""World state API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Agent, Location, WorldState
from hamlet.schemas.world import WorldStateResponse

router = APIRouter(prefix="/api/world", tags=["world"])


@router.get("", response_model=WorldStateResponse)
async def get_world_state(db: Session = Depends(get_db)):
    """Get current world state."""
    state = db.query(WorldState).first()
    agent_count = db.query(Agent).count()
    location_count = db.query(Location).count()

    if not state:
        # Return default state if none exists
        return WorldStateResponse(
            current_tick=0,
            current_day=1,
            current_hour=6.0,
            season="spring",
            weather="clear",
            agent_count=agent_count,
            location_count=location_count,
        )

    return WorldStateResponse(
        current_tick=state.current_tick,
        current_day=state.current_day,
        current_hour=state.current_hour,
        season=state.season,
        weather=state.weather,
        agent_count=agent_count,
        location_count=location_count,
    )
