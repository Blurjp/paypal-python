"""
Upload endpoint for creating new briefings.
"""
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import Optional
from uuid import uuid4
import logging

from app.models import BriefingResponse
from app.services.file_processor import file_processor
from app.services.openai_service import openai_service
from app.services.elevenlabs_service import elevenlabs_service
from app.services.supabase_service import supabase_service
from app.services.slack_service import slack_service
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


async def process_briefing_background(
    briefing_id: str,
    title: str,
    content: str,
    channel: Optional[str] = None
):
    """
    Background task to process briefing: summarize, generate audio, and post to Slack.
    """
    try:
        logger.info(f"Starting background processing for briefing {briefing_id}")

        # Step 1: Summarize content
        logger.info("Generating summary...")
        summary = openai_service.summarize_for_briefing(content, title)

        # Step 2: Generate audio
        logger.info("Generating audio...")
        audio_bytes = elevenlabs_service.generate_audio(summary)

        # Step 3: Upload audio to Supabase
        logger.info("Uploading audio to storage...")
        audio_filename = f"briefings/{briefing_id}.mp3"
        audio_url = supabase_service.upload_audio(audio_filename, audio_bytes)

        # Step 4: Update briefing with summary and audio URL
        logger.info("Updating briefing record...")
        supabase_service.client.table("briefings").update({
            "summary_text": summary,
            "audio_url": audio_url
        }).eq("id", briefing_id).execute()

        # Step 5: Post to Slack
        logger.info("Posting to Slack...")
        listen_url = f"{settings.app_base_url}/listen/{briefing_id}"
        slack_response = slack_service.post_briefing(
            briefing_id=briefing_id,
            title=title,
            listen_url=listen_url,
            channel=channel
        )

        # Step 6: Save Slack post reference
        supabase_service.save_briefing_post(
            briefing_id=briefing_id,
            channel_id=slack_response["channel"],
            message_ts=slack_response["message_ts"]
        )

        logger.info(f"Successfully processed briefing {briefing_id}")

    except Exception as e:
        logger.error(f"Error processing briefing {briefing_id}: {e}")
        # In production, you might want to update the briefing status to "failed"


@router.post("/upload", response_model=dict)
async def upload_briefing(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    channel: Optional[str] = Form(None),
    created_by: Optional[str] = Form(None)
):
    """
    Upload a new briefing from text, URL, or file.

    This endpoint creates a briefing record immediately and processes it in the background.
    """
    try:
        # Extract content from provided source
        content = None
        source_type = "text"

        if file:
            file_data = await file.read()
            content = file_processor.process_content(
                file_data=file_data,
                filename=file.filename
            )
            source_type = "pdf" if file.filename.endswith('.pdf') else "file"
        elif url:
            content = file_processor.process_content(url=url)
            source_type = "url"
        elif text:
            content = text
            source_type = "text"
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either text, url, or file"
            )

        if not content or len(content) < 50:
            raise HTTPException(
                status_code=400,
                detail="Content is too short or empty"
            )

        # Create initial briefing record (without summary/audio yet)
        logger.info(f"Creating briefing: {title}")
        briefing = supabase_service.create_briefing(
            title=title,
            summary_text="Processing...",  # Placeholder
            original_content=content,
            created_by=created_by,
            source_type=source_type
        )

        briefing_id = briefing["id"]

        # Process in background (summarize, generate audio, post to Slack)
        background_tasks.add_task(
            process_briefing_background,
            briefing_id=briefing_id,
            title=title,
            content=content,
            channel=channel
        )

        return {
            "status": "ok",
            "message": "Briefing is being processed",
            "briefing_id": briefing_id,
            "briefing": briefing
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading briefing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
