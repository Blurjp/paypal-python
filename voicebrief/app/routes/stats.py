"""
Stats endpoint for analytics and completion tracking.
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging

from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats", response_model=List[dict])
async def get_stats():
    """
    Get analytics stats for all briefings.

    Returns completion rates, listener counts, and engagement metrics.
    """
    try:
        stats = supabase_service.get_briefing_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")


@router.get("/stats/summary", response_model=dict)
async def get_stats_summary():
    """
    Get overall summary statistics.
    """
    try:
        stats = supabase_service.get_briefing_stats()

        total_briefings = len(stats)
        total_recipients = sum(s.get('total_recipients', 0) for s in stats)
        total_listeners = sum(s.get('listeners_count', 0) for s in stats)
        total_completed = sum(s.get('completed_count', 0) for s in stats)

        overall_completion_rate = (
            round(100.0 * total_completed / total_recipients, 2)
            if total_recipients > 0
            else 0.0
        )

        return {
            "total_briefings": total_briefings,
            "total_recipients": total_recipients,
            "total_listeners": total_listeners,
            "total_completed": total_completed,
            "overall_completion_rate": overall_completion_rate
        }
    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summary stats")
