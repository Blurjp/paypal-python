"""
Slack events endpoint for handling interactive button clicks.
"""
from fastapi import APIRouter, Request, HTTPException
import json
import logging
from urllib.parse import parse_qs

from app.services.supabase_service import supabase_service
from app.services.slack_service import slack_service
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/slack/events")
async def slack_events(request: Request):
    """
    Handle Slack interactive events (button clicks, etc.).

    Slack sends the payload as form-encoded data with a 'payload' field containing JSON.
    """
    try:
        # Parse form data
        form_data = await request.body()
        parsed = parse_qs(form_data.decode('utf-8'))

        # Extract payload
        if 'payload' not in parsed:
            raise HTTPException(status_code=400, detail="No payload found")

        payload = json.loads(parsed['payload'][0])
        logger.info(f"Received Slack event: {payload.get('type')}")

        # Handle different interaction types
        event_type = payload.get('type')

        if event_type == 'block_actions':
            return await handle_block_actions(payload)
        elif event_type == 'url_verification':
            # Slack URL verification challenge
            return {"challenge": payload.get('challenge')}
        else:
            logger.warning(f"Unhandled event type: {event_type}")
            return {"status": "ok"}

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload format")
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_block_actions(payload: dict):
    """
    Handle block action events (button clicks).
    """
    user = payload.get('user', {})
    user_id = user.get('id')
    user_name = user.get('name', user.get('username', 'Unknown'))

    actions = payload.get('actions', [])

    for action in actions:
        action_id = action.get('action_id')
        value = action.get('value')

        if action_id == 'mark_done':
            # User clicked "Mark as Done"
            briefing_id = value

            try:
                # Update listener status
                supabase_service.update_listener_status(
                    briefing_id=briefing_id,
                    user_id=user_id,
                    status="completed"
                )

                # Get briefing title for confirmation
                briefing = supabase_service.get_briefing(briefing_id)
                briefing_title = briefing.get('title', 'the briefing') if briefing else 'the briefing'

                # Send confirmation DM
                slack_service.send_completion_confirmation(
                    user_id=user_id,
                    briefing_title=briefing_title
                )

                logger.info(f"User {user_id} completed briefing {briefing_id}")

                # Return success response
                return {
                    "response_type": "ephemeral",
                    "text": f"✅ Marked as done! Thanks for listening, {user_name}."
                }

            except Exception as e:
                logger.error(f"Error marking briefing as done: {e}")
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Sorry, there was an error. Please try again."
                }

        elif action_id == 'listen_briefing':
            # User clicked "Listen" - track that they started listening
            # The briefing_id is in the block_id
            block_id = payload.get('actions', [{}])[0].get('block_id', '')
            if block_id.startswith('briefing_'):
                briefing_id = block_id.replace('briefing_', '')

                try:
                    # Track listener as "listened"
                    supabase_service.update_listener_status(
                        briefing_id=briefing_id,
                        user_id=user_id,
                        status="listened"
                    )
                    logger.info(f"User {user_id} started listening to briefing {briefing_id}")
                except Exception as e:
                    logger.error(f"Error tracking listen event: {e}")

        elif action_id == 'connect_google':
            # User clicked "Connect Google Account"
            try:
                # Generate OAuth connection URL
                oauth_url = f"{settings.app_base_url}/auth/google/connect?user_id={user_id}"

                # Send ephemeral message with connection link
                return {
                    "response_type": "ephemeral",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "🔐 *Connect Your Google Account*\n\nClick the button below to securely connect your Google account to VoiceBrief. This allows you to create voice briefings from any of your Google Docs."
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Connect Google Account"
                                    },
                                    "url": oauth_url,
                                    "style": "primary"
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "_You'll be redirected to Google to authorize access. We only request read-only access to your Google Docs._"
                                }
                            ]
                        }
                    ]
                }

            except Exception as e:
                logger.error(f"Error generating Google OAuth URL: {e}")
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Sorry, there was an error. Please try again."
                }

    return {"status": "ok"}


@router.post("/slack/commands/google")
async def slack_google_command(request: Request):
    """
    Handle /voicebrief-google slash command.

    Allows users to connect/disconnect their Google account via Slack.
    """
    try:
        # Parse form data
        form_data = await request.form()
        user_id = form_data.get('user_id')
        text = form_data.get('text', '').strip().lower()

        if not user_id:
            return {
                "response_type": "ephemeral",
                "text": "❌ Error: Could not identify user"
            }

        # Check user's connection status
        result = supabase_service.client.table('google_oauth_tokens').select('user_email').eq('user_id', user_id).execute()
        is_connected = result.data and len(result.data) > 0
        user_email = result.data[0].get('user_email') if is_connected else None

        # Handle subcommands
        if text == 'disconnect':
            if not is_connected:
                return {
                    "response_type": "ephemeral",
                    "text": "ℹ️ Your Google account is not connected."
                }

            # Disconnect user's Google account
            supabase_service.client.table('google_oauth_tokens').delete().eq('user_id', user_id).execute()
            logger.info(f"Disconnected Google account for user {user_id}")

            return {
                "response_type": "ephemeral",
                "text": f"✅ Disconnected Google account ({user_email})"
            }

        elif text == 'status':
            if is_connected:
                return {
                    "response_type": "ephemeral",
                    "text": f"✅ Connected to Google account: {user_email}"
                }
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Not connected to Google. Use `/voicebrief-google connect` to connect."
                }

        elif text == 'connect' or text == '':
            # Show connection instructions
            if is_connected:
                return {
                    "response_type": "ephemeral",
                    "text": f"✅ Already connected to Google account: {user_email}\n\nUse `/voicebrief-google disconnect` to disconnect."
                }

            oauth_url = f"{settings.app_base_url}/auth/google/connect?user_id={user_id}"

            return {
                "response_type": "ephemeral",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔐 *Connect Your Google Account*\n\nConnect your Google account to create voice briefings from your Google Docs!"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Connect Google Account"
                                },
                                "url": oauth_url,
                                "style": "primary"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "_We only request read-only access to your Google Docs. You can disconnect anytime using `/voicebrief-google disconnect`_"
                            }
                        ]
                    }
                ]
            }

        else:
            return {
                "response_type": "ephemeral",
                "text": "ℹ️ *VoiceBrief Google Integration*\n\nAvailable commands:\n• `/voicebrief-google` or `/voicebrief-google connect` - Connect your Google account\n• `/voicebrief-google status` - Check connection status\n• `/voicebrief-google disconnect` - Disconnect your Google account"
            }

    except Exception as e:
        logger.error(f"Error handling Google command: {e}")
        return {
            "response_type": "ephemeral",
            "text": "❌ Sorry, there was an error. Please try again."
        }
