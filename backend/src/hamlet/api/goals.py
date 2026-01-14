"""Goal API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Goal
from hamlet.schemas.goal import GoalResponse

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("/agent/{agent_id}", response_model=list[GoalResponse])
async def get_agent_goals(
    agent_id: str,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Get goals for a specific agent."""
    query = db.query(Goal).filter(Goal.agent_id == agent_id)

    if status:
        query = query.filter(Goal.status == status)

    goals = query.order_by(Goal.priority.desc()).all()
    return [_goal_to_response(g) for g in goals]


@router.get("", response_model=list[GoalResponse])
async def list_goals(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all goals, optionally filtered by status."""
    query = db.query(Goal)

    if status:
        query = query.filter(Goal.status == status)

    goals = query.order_by(Goal.priority.desc()).all()
    return [_goal_to_response(g) for g in goals]


def _goal_to_response(goal: Goal) -> GoalResponse:
    """Convert Goal model to response schema."""
    return GoalResponse(
        id=goal.id,
        agent_id=goal.agent_id,
        type=goal.type,
        description=goal.description,
        priority=goal.priority,
        target_id=goal.target_id,
        status=goal.status,
        created_at=goal.created_at,
    )
