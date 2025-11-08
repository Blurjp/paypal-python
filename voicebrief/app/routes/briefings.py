"""
Briefings endpoint for listing and retrieving briefings.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
from uuid import UUID
import logging

from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/briefings", response_model=List[dict])
async def list_briefings(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all briefings, ordered by creation date (newest first).

    Args:
        limit: Maximum number of briefings to return (1-100)
        offset: Number of briefings to skip
    """
    try:
        briefings = supabase_service.list_briefings(limit=limit, offset=offset)
        return briefings
    except Exception as e:
        logger.error(f"Error listing briefings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve briefings")


@router.get("/briefings/{briefing_id}", response_model=dict)
async def get_briefing(briefing_id: UUID):
    """
    Get a specific briefing by ID.

    Args:
        briefing_id: UUID of the briefing
    """
    try:
        briefing = supabase_service.get_briefing(briefing_id)
        if not briefing:
            raise HTTPException(status_code=404, detail="Briefing not found")
        return briefing
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting briefing {briefing_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve briefing")
