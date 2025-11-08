"""
Slack service for posting messages and handling interactions.
"""
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.config import get_settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class SlackService:
    """Service for Slack API interactions."""

    def __init__(self):
        """Initialize Slack client."""
        self.client = WebClient(token=settings.slack_bot_token)
        self.default_channel = settings.slack_default_channel

    def post_briefing(
        self,
        briefing_id: str,
        title: str,
        listen_url: str,
        channel: str = None
    ) -> Dict[str, Any]:
        """
        Post a briefing message to Slack with interactive buttons.

        Args:
            briefing_id: UUID of the briefing
            title: Briefing title
            listen_url: URL to listen to the audio
            channel: Slack channel (defaults to configured channel)

        Returns:
            Slack API response
        """
        if not channel:
            channel = self.default_channel

        try:
            # Create interactive message blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📢 New Company Briefing"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*\n\nA new audio briefing is ready for you to listen to."
                    }
                },
                {
                    "type": "actions",
                    "block_id": f"briefing_{briefing_id}",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "▶️ Listen"
                            },
                            "url": listen_url,
                            "style": "primary",
                            "action_id": "listen_briefing"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Mark as Done"
                            },
                            "value": briefing_id,
                            "action_id": "mark_done",
                            "style": "primary"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📊 Click 'Mark as Done' once you've listened to track completion"
                        }
                    ]
                }
            ]

            response = self.client.chat_postMessage(
                channel=channel,
                text=f"New Briefing: {title}",  # Fallback text
                blocks=blocks
            )

            logger.info(f"Posted briefing to {channel}: {response['ts']}")
            return {
                "channel": response["channel"],
                "message_ts": response["ts"],
                "ok": response["ok"]
            }

        except SlackApiError as e:
            logger.error(f"Error posting to Slack: {e.response['error']}")
            raise

    def send_completion_confirmation(
        self,
        user_id: str,
        briefing_title: str
    ) -> None:
        """
        Send a DM to user confirming they completed a briefing.

        Args:
            user_id: Slack user ID
            briefing_title: Title of the briefing
        """
        try:
            self.client.chat_postMessage(
                channel=user_id,
                text=f"✅ Thanks for completing the briefing: *{briefing_title}*"
            )
            logger.info(f"Sent completion confirmation to {user_id}")
        except SlackApiError as e:
            logger.error(f"Error sending DM: {e.response['error']}")

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Slack.

        Args:
            user_id: Slack user ID

        Returns:
            User information
        """
        try:
            response = self.client.users_info(user=user_id)
            return response["user"]
        except SlackApiError as e:
            logger.error(f"Error getting user info: {e.response['error']}")
            return {}

    def update_message(
        self,
        channel: str,
        message_ts: str,
        text: str = None,
        blocks: list = None
    ) -> None:
        """
        Update an existing Slack message.

        Args:
            channel: Channel ID
            message_ts: Message timestamp
            text: New text
            blocks: New blocks
        """
        try:
            self.client.chat_update(
                channel=channel,
                ts=message_ts,
                text=text,
                blocks=blocks
            )
            logger.info(f"Updated message {message_ts} in {channel}")
        except SlackApiError as e:
            logger.error(f"Error updating message: {e.response['error']}")


# Global instance
slack_service = SlackService()
