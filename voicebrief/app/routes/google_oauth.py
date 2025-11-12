"""
Google OAuth2 flow endpoints for user authentication.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from datetime import datetime, timezone
import logging
import secrets

from app.config import get_settings
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth/google", tags=["google-oauth"])

# In-memory state storage (in production, use Redis or database)
oauth_states = {}


@router.get("/connect")
async def connect_google(user_id: str):
    """
    Initiate Google OAuth2 flow for a user.

    Args:
        user_id: Slack user ID

    Returns:
        Redirect to Google OAuth consent screen
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    try:
        # Create OAuth2 flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_oauth_redirect_uri or f"{settings.app_base_url}/auth/google/callback"]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/userinfo.email',
                'openid'
            ]
        )

        flow.redirect_uri = settings.google_oauth_redirect_uri or f"{settings.app_base_url}/auth/google/callback"

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        oauth_states[state] = {
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc)
        }

        # Get authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent screen to get refresh token
        )

        logger.info(f"Redirecting user {user_id} to Google OAuth")
        return RedirectResponse(authorization_url)

    except Exception as e:
        logger.error(f"Error initiating Google OAuth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def google_oauth_callback(request: Request):
    """
    Handle Google OAuth2 callback.

    Exchanges authorization code for access token and stores in database.
    """
    try:
        # Get query parameters
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')

        if error:
            logger.error(f"OAuth error: {error}")
            return HTMLResponse(f"""
                <html>
                    <head><title>Connection Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Connection Failed</h1>
                        <p>Error: {error}</p>
                        <p>Please try again or contact support.</p>
                    </body>
                </html>
            """)

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state parameter")

        # Verify state
        if state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        user_id = oauth_states[state]['user_id']
        del oauth_states[state]  # Clean up state

        # Create flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.google_oauth_redirect_uri or f"{settings.app_base_url}/auth/google/callback"]
                }
            },
            scopes=[
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/userinfo.email',
                'openid'
            ],
            state=state
        )

        flow.redirect_uri = settings.google_oauth_redirect_uri or f"{settings.app_base_url}/auth/google/callback"

        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user info
        from googleapiclient.discovery import build
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        user_email = user_info.get('email')

        # Store tokens in database
        token_data = {
            'user_id': user_id,
            'user_email': user_email,
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'scopes': credentials.scopes,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        # Check if user already has tokens
        existing = supabase_service.client.table('google_oauth_tokens').select('*').eq('user_id', user_id).execute()

        if existing.data and len(existing.data) > 0:
            # Update existing record
            supabase_service.client.table('google_oauth_tokens').update(token_data).eq('user_id', user_id).execute()
            logger.info(f"Updated Google OAuth tokens for user {user_id}")
        else:
            # Insert new record
            token_data['created_at'] = datetime.now(timezone.utc).isoformat()
            supabase_service.client.table('google_oauth_tokens').insert(token_data).execute()
            logger.info(f"Stored new Google OAuth tokens for user {user_id}")

        # Return success page
        return HTMLResponse("""
            <html>
                <head>
                    <title>Connected Successfully!</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                </head>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial; text-align: center; padding: 50px; background: #f5f5f5;">
                    <div style="background: white; border-radius: 12px; padding: 40px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="font-size: 64px; margin-bottom: 20px;">✅</div>
                        <h1 style="color: #1a73e8; margin-bottom: 10px;">Connected Successfully!</h1>
                        <p style="color: #5f6368; font-size: 16px; margin-bottom: 30px;">
                            Your Google account is now connected to VoiceBrief.
                        </p>
                        <p style="color: #5f6368; font-size: 14px;">
                            You can now create voice briefings from your Google Docs!<br>
                            You can close this window and return to Slack.
                        </p>
                    </div>
                    <script>
                        // Auto-close window after 3 seconds
                        setTimeout(() => {
                            window.close();
                        }, 3000);
                    </script>
                </body>
            </html>
        """)

    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        return HTMLResponse(f"""
            <html>
                <head><title>Connection Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Connection Failed</h1>
                    <p>Error: {str(e)}</p>
                    <p>Please try again or contact support.</p>
                </body>
            </html>
        """)


@router.get("/disconnect")
async def disconnect_google(user_id: str):
    """
    Disconnect user's Google account.

    Args:
        user_id: Slack user ID
    """
    try:
        # Delete tokens from database
        supabase_service.client.table('google_oauth_tokens').delete().eq('user_id', user_id).execute()
        logger.info(f"Disconnected Google account for user {user_id}")

        return {"message": "Google account disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting Google account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def google_connection_status(user_id: str):
    """
    Check if user has connected their Google account.

    Args:
        user_id: Slack user ID

    Returns:
        Connection status and user email if connected
    """
    try:
        result = supabase_service.client.table('google_oauth_tokens').select('user_email, created_at').eq('user_id', user_id).execute()

        if result.data and len(result.data) > 0:
            return {
                "connected": True,
                "email": result.data[0].get('user_email'),
                "connected_at": result.data[0].get('created_at')
            }
        else:
            return {"connected": False}

    except Exception as e:
        logger.error(f"Error checking Google connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
