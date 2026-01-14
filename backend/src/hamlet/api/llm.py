"""LLM usage and cost tracking API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from hamlet.db import LLMUsage, get_db
from hamlet.llm.usage import CallRecord, get_usage_tracker

router = APIRouter(prefix="/api/llm", tags=["llm"])


def persist_call(record: CallRecord, db: Session) -> None:
    """Persist a call record to the database."""
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


@router.get("/stats")
async def get_llm_stats(db: Session = Depends(get_db)) -> dict:
    """Get LLM usage statistics.

    Returns both session stats (since server start) and historical stats from database.
    """
    tracker = get_usage_tracker()
    session_stats = tracker.get_stats().to_dict()

    # Get historical stats from database
    historical = db.query(
        func.count(LLMUsage.id).label("total_calls"),
        func.sum(LLMUsage.tokens_in).label("tokens_in"),
        func.sum(LLMUsage.tokens_out).label("tokens_out"),
        func.sum(LLMUsage.cost_usd).label("total_cost"),
    ).filter(LLMUsage.cached == False).first()

    cached_count = db.query(func.count(LLMUsage.id)).filter(LLMUsage.cached == True).scalar() or 0

    # Get stats by model from database
    by_model_rows = db.query(
        LLMUsage.model,
        func.count(LLMUsage.id).label("calls"),
        func.sum(LLMUsage.tokens_in).label("tokens_in"),
        func.sum(LLMUsage.tokens_out).label("tokens_out"),
        func.sum(LLMUsage.cost_usd).label("cost"),
    ).filter(LLMUsage.cached == False).group_by(LLMUsage.model).all()

    by_model = {
        row.model: {
            "calls": row.calls,
            "tokens_in": row.tokens_in or 0,
            "tokens_out": row.tokens_out or 0,
            "cost_usd": round(row.cost or 0, 6),
        }
        for row in by_model_rows
    }

    # Get recent calls
    recent = tracker.get_recent_calls(20)
    recent_calls = [
        {
            "timestamp": r.timestamp,
            "model": r.model,
            "tokens_in": r.tokens_in,
            "tokens_out": r.tokens_out,
            "cost_usd": round(r.cost_usd, 6),
            "latency_ms": round(r.latency_ms, 1),
            "cached": r.cached,
            "agent_id": r.agent_id,
            "call_type": r.call_type,
        }
        for r in recent
    ]

    return {
        "session": session_stats,
        "historical": {
            "total_calls": (historical.total_calls or 0) + cached_count,
            "api_calls": historical.total_calls or 0,
            "cached_calls": cached_count,
            "tokens_in": historical.tokens_in or 0,
            "tokens_out": historical.tokens_out or 0,
            "total_tokens": (historical.tokens_in or 0) + (historical.tokens_out or 0),
            "total_cost_usd": round(historical.total_cost or 0, 6),
            "total_cost_display": f"${historical.total_cost or 0:.4f}",
            "by_model": by_model,
        },
        "recent_calls": recent_calls,
    }


@router.post("/reset")
async def reset_session_stats() -> dict:
    """Reset session statistics (does not affect historical database)."""
    tracker = get_usage_tracker()
    tracker.reset()
    return {"status": "ok", "message": "Session stats reset"}


@router.get("/cost-summary")
async def get_cost_summary(db: Session = Depends(get_db)) -> dict:
    """Get a simple cost summary for display."""
    tracker = get_usage_tracker()
    stats = tracker.get_stats()

    # Historical total
    historical_cost = db.query(func.sum(LLMUsage.cost_usd)).filter(LLMUsage.cached == False).scalar() or 0

    return {
        "session_cost": f"${stats.total_cost_usd:.4f}",
        "historical_cost": f"${historical_cost:.4f}",
        "session_calls": stats.total_calls,
        "session_tokens": stats.tokens_in + stats.tokens_out,
    }
