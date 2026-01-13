"""Location API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Agent, Location
from hamlet.schemas.location import LocationResponse

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
async def list_locations(db: Session = Depends(get_db)):
    """List all locations."""
    locations = db.query(Location).all()
    return [_location_to_response(loc, db) for loc in locations]


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: str, db: Session = Depends(get_db)):
    """Get a specific location by ID."""
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return _location_to_response(location, db)


def _location_to_response(location: Location, db: Session) -> LocationResponse:
    """Convert Location model to response schema."""
    # Get agents currently at this location
    agents_here = db.query(Agent).filter(Agent.location_id == location.id).all()
    agent_ids = [a.id for a in agents_here]

    return LocationResponse(
        id=location.id,
        name=location.name,
        description=location.description,
        connections=location.connections_list,
        objects=location.objects_list,
        capacity=location.capacity,
        agents_present=agent_ids,
    )
