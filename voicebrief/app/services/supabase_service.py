"""
Supabase service for database operations and file storage.
"""
from supabase import create_client, Client
from app.config import get_settings
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseService:
    """Service for interacting with Supabase."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        self.bucket = settings.supabase_bucket

    def create_briefing(
        self,
        title: str,
        summary_text: str,
        audio_url: Optional[str] = None,
        original_content: Optional[str] = None,
        created_by: Optional[str] = None,
        source_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new briefing record."""
        try:
            data = {
                "title": title,
                "summary_text": summary_text,
                "audio_url": audio_url,
                "original_content": original_content,
                "created_by": created_by,
                "source_type": source_type,
                "metadata": metadata or {}
            }
            result = self.client.table("briefings").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating briefing: {e}")
            raise

    def get_briefing(self, briefing_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a briefing by ID."""
        try:
            result = self.client.table("briefings").select("*").eq("id", str(briefing_id)).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting briefing: {e}")
            raise

    def list_briefings(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all briefings, ordered by creation date."""
        try:
            result = (
                self.client.table("briefings")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error listing briefings: {e}")
            raise

    def track_listener(
        self,
        briefing_id: UUID,
        user_id: str,
        user_name: Optional[str] = None,
        status: str = "pending"
    ) -> Dict[str, Any]:
        """Track a listener for a briefing."""
        try:
            data = {
                "briefing_id": str(briefing_id),
                "user_id": user_id,
                "user_name": user_name,
                "status": status
            }
            result = (
                self.client.table("listeners")
                .upsert(data, on_conflict="briefing_id,user_id")
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error tracking listener: {e}")
            raise

    def update_listener_status(
        self,
        briefing_id: UUID,
        user_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update listener status."""
        try:
            update_data = {"status": status}

            if status == "listened":
                update_data["listened_at"] = "now()"
            elif status == "completed":
                update_data["completed_at"] = "now()"

            result = (
                self.client.table("listeners")
                .update(update_data)
                .eq("briefing_id", str(briefing_id))
                .eq("user_id", user_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating listener status: {e}")
            raise

    def save_briefing_post(
        self,
        briefing_id: UUID,
        channel_id: str,
        message_ts: str
    ) -> Dict[str, Any]:
        """Save Slack message reference for a briefing."""
        try:
            data = {
                "briefing_id": str(briefing_id),
                "channel_id": channel_id,
                "message_ts": message_ts
            }
            result = self.client.table("briefing_posts").insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error saving briefing post: {e}")
            raise

    def get_briefing_stats(self) -> List[Dict[str, Any]]:
        """Get analytics stats for all briefings."""
        try:
            result = (
                self.client.table("briefing_stats")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error getting briefing stats: {e}")
            raise

    def upload_audio(self, file_path: str, file_data: bytes) -> str:
        """Upload audio file to Supabase storage."""
        try:
            result = self.client.storage.from_(self.bucket).upload(
                file_path,
                file_data,
                {"content-type": "audio/mpeg"}
            )
            # Get public URL
            public_url = self.client.storage.from_(self.bucket).get_public_url(file_path)
            return public_url
        except Exception as e:
            logger.error(f"Error uploading audio: {e}")
            raise


# Global instance
supabase_service = SupabaseService()
