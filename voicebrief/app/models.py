"""
Pydantic models for VoiceBrief API.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class BriefingCreate(BaseModel):
    """Request model for creating a briefing."""
    title: str = Field(..., min_length=1, max_length=255)
    text: Optional[str] = None
    url: Optional[str] = None
    source_type: Literal["text", "pdf", "notion", "url"] = "text"
    created_by: Optional[str] = None


class BriefingResponse(BaseModel):
    """Response model for a briefing."""
    id: UUID
    title: str
    summary_text: str
    audio_url: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    source_type: str

    class Config:
        from_attributes = True


class ListenerUpdate(BaseModel):
    """Update listener status."""
    status: Literal["pending", "listened", "completed"]
    user_id: str
    user_name: Optional[str] = None


class StatsResponse(BaseModel):
    """Analytics stats response."""
    briefing_id: UUID
    title: str
    total_recipients: int
    listeners_count: int
    completed_count: int
    pending_count: int
    completion_rate: float


class SlackInteraction(BaseModel):
    """Slack button interaction payload."""
    type: str
    user: dict
    actions: list
    message: Optional[dict] = None
    response_url: Optional[str] = None
