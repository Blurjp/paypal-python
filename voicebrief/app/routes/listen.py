"""
Listen endpoint for playing audio briefings.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from uuid import UUID
import logging

from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/listen/{briefing_id}", response_class=HTMLResponse)
async def listen_page(request: Request, briefing_id: UUID):
    """
    Serve a simple HTML page with an audio player for the briefing.

    Args:
        briefing_id: UUID of the briefing to play
    """
    try:
        # Get briefing from database
        briefing = supabase_service.get_briefing(briefing_id)

        if not briefing:
            raise HTTPException(status_code=404, detail="Briefing not found")

        if not briefing.get('audio_url'):
            raise HTTPException(status_code=404, detail="Audio not yet available")

        # Render HTML player page
        return templates.TemplateResponse(
            "listen.html",
            {
                "request": request,
                "briefing": briefing
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading listen page: {e}")
        raise HTTPException(status_code=500, detail="Failed to load audio player")
