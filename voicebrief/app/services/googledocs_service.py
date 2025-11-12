"""
Google Docs service for extracting text content from Google Docs.
Supports both service account and OAuth2 user authentication.
"""
import logging
import re
from typing import Optional
from datetime import datetime, timezone
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GoogleDocsService:
    """Service for Google Docs API interactions."""

    def __init__(self):
        """Initialize Google Docs client."""
        self.credentials = None
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Docs API service with credentials."""
        try:
            if settings.google_credentials_file:
                # Use service account credentials from file
                self.credentials = service_account.Credentials.from_service_account_file(
                    settings.google_credentials_file,
                    scopes=['https://www.googleapis.com/auth/documents.readonly']
                )
                self.service = build('docs', 'v1', credentials=self.credentials)
                logger.info("Google Docs service initialized with service account")
            elif settings.google_credentials_json:
                # Use service account credentials from JSON string
                import json
                credentials_info = json.loads(settings.google_credentials_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/documents.readonly']
                )
                self.service = build('docs', 'v1', credentials=self.credentials)
                logger.info("Google Docs service initialized with JSON credentials")
            else:
                logger.warning("No Google Docs credentials configured - Google Docs extraction will not work")
        except Exception as e:
            logger.error(f"Error initializing Google Docs service: {e}")
            self.service = None

    def extract_document_id(self, url: str) -> Optional[str]:
        """
        Extract document ID from Google Docs URL.

        Args:
            url: Google Docs URL (e.g., https://docs.google.com/document/d/DOC_ID/edit)

        Returns:
            Document ID or None if invalid URL
        """
        # Pattern to match Google Docs URLs
        # Supports: /document/d/DOC_ID/edit, /document/d/DOC_ID, etc.
        patterns = [
            r'docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
            r'drive\.google\.com/file/d/([a-zA-Z0-9-_]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_document_content(self, document_id: str) -> str:
        """
        Retrieve text content from a Google Doc.

        Args:
            document_id: The Google Docs document ID

        Returns:
            Plain text content from the document

        Raises:
            Exception: If document cannot be retrieved
        """
        if not self.service:
            raise Exception("Google Docs service not initialized - check credentials configuration")

        try:
            # Retrieve the document
            document = self.service.documents().get(documentId=document_id).execute()

            # Extract text content from the document structure
            content = self._extract_text_from_document(document)

            logger.info(f"Successfully extracted {len(content)} characters from Google Doc {document_id}")
            return content

        except HttpError as e:
            if e.resp.status == 404:
                raise Exception(f"Google Doc not found: {document_id}. Make sure the document exists and is shared with the service account.")
            elif e.resp.status == 403:
                raise Exception(f"Access denied to Google Doc {document_id}. Make sure the document is shared with the service account email.")
            else:
                logger.error(f"HTTP error retrieving Google Doc {document_id}: {e}")
                raise Exception(f"Error retrieving Google Doc: {e}")
        except Exception as e:
            logger.error(f"Error retrieving Google Doc {document_id}: {e}")
            raise

    def _extract_text_from_document(self, document: dict) -> str:
        """
        Extract plain text from Google Docs document structure.

        Args:
            document: Google Docs API document response

        Returns:
            Plain text content
        """
        text_parts = []

        # Get document body content
        content = document.get('body', {}).get('content', [])

        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                paragraph_text = self._extract_text_from_paragraph(paragraph)
                if paragraph_text:
                    text_parts.append(paragraph_text)
            elif 'table' in element:
                table = element['table']
                table_text = self._extract_text_from_table(table)
                if table_text:
                    text_parts.append(table_text)

        return '\n\n'.join(text_parts)

    def _extract_text_from_paragraph(self, paragraph: dict) -> str:
        """Extract text from a paragraph element."""
        text_parts = []

        for element in paragraph.get('elements', []):
            if 'textRun' in element:
                text_run = element['textRun']
                text_content = text_run.get('content', '')
                text_parts.append(text_content)

        return ''.join(text_parts).strip()

    def _extract_text_from_table(self, table: dict) -> str:
        """Extract text from a table element."""
        table_text = []

        for row in table.get('tableRows', []):
            row_text = []
            for cell in row.get('tableCells', []):
                cell_content = []
                for content_element in cell.get('content', []):
                    if 'paragraph' in content_element:
                        paragraph_text = self._extract_text_from_paragraph(content_element['paragraph'])
                        if paragraph_text:
                            cell_content.append(paragraph_text)
                row_text.append(' '.join(cell_content))
            table_text.append(' | '.join(row_text))

        return '\n'.join(table_text)

    def extract_from_url(self, url: str, user_id: Optional[str] = None) -> str:
        """
        Extract text content from a Google Docs URL.
        Uses OAuth2 user credentials if user_id is provided, otherwise uses service account.

        Args:
            url: Full Google Docs URL
            user_id: Optional Slack user ID for OAuth2 authentication

        Returns:
            Plain text content from the document

        Raises:
            Exception: If URL is invalid or document cannot be retrieved
        """
        document_id = self.extract_document_id(url)

        if not document_id:
            raise Exception(f"Invalid Google Docs URL: {url}")

        # Use OAuth2 if user_id provided
        if user_id:
            return self.get_document_content_with_user_auth(document_id, user_id)
        else:
            return self.get_document_content(document_id)

    async def get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Get and refresh user OAuth2 credentials from database.

        Args:
            user_id: Slack user ID

        Returns:
            Google OAuth2 Credentials or None if user hasn't connected
        """
        try:
            from app.config import get_settings
            from supabase import create_client

            settings = get_settings()
            supabase = create_client(settings.supabase_url, settings.supabase_key)

            # Get user tokens from database
            result = supabase.table('google_oauth_tokens').select('*').eq('user_id', user_id).execute()

            if not result.data or len(result.data) == 0:
                logger.info(f"No Google OAuth tokens found for user {user_id}")
                return None

            token_data = result.data[0]

            # Create credentials object
            creds = Credentials(
                token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/documents.readonly'])
            )

            # Refresh if expired
            if token_data.get('token_expiry'):
                expiry = datetime.fromisoformat(token_data['token_expiry'].replace('Z', '+00:00'))
                if expiry <= datetime.now(timezone.utc):
                    logger.info(f"Refreshing expired token for user {user_id}")
                    creds.refresh(Request())

                    # Update database with new tokens
                    supabase.table('google_oauth_tokens').update({
                        'access_token': creds.token,
                        'refresh_token': creds.refresh_token,
                        'token_expiry': creds.expiry.isoformat() if creds.expiry else None,
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }).eq('user_id', user_id).execute()

                    logger.info(f"Updated OAuth tokens for user {user_id}")

            return creds

        except Exception as e:
            logger.error(f"Error getting user credentials for {user_id}: {e}")
            return None

    def get_document_content_with_user_auth(self, document_id: str, user_id: str) -> str:
        """
        Retrieve text content from a Google Doc using user OAuth2 credentials.

        Args:
            document_id: The Google Docs document ID
            user_id: Slack user ID

        Returns:
            Plain text content from the document

        Raises:
            Exception: If document cannot be retrieved or user not authenticated
        """
        import asyncio

        # Get user credentials
        try:
            # Run async function in sync context
            creds = asyncio.run(self.get_user_credentials(user_id))
        except RuntimeError:
            # Already in async context, use existing event loop
            import nest_asyncio
            nest_asyncio.apply()
            creds = asyncio.run(self.get_user_credentials(user_id))

        if not creds:
            raise Exception(f"User {user_id} has not connected their Google account. Please connect via Slack first.")

        try:
            # Build service with user credentials
            user_service = build('docs', 'v1', credentials=creds)

            # Retrieve the document
            document = user_service.documents().get(documentId=document_id).execute()

            # Extract text content from the document structure
            content = self._extract_text_from_document(document)

            logger.info(f"Successfully extracted {len(content)} characters from Google Doc {document_id} for user {user_id}")
            return content

        except HttpError as e:
            if e.resp.status == 404:
                raise Exception(f"Google Doc not found: {document_id}. Make sure the document exists.")
            elif e.resp.status == 403:
                raise Exception(f"Access denied to Google Doc {document_id}. Make sure you have permission to view this document.")
            else:
                logger.error(f"HTTP error retrieving Google Doc {document_id}: {e}")
                raise Exception(f"Error retrieving Google Doc: {e}")
        except Exception as e:
            logger.error(f"Error retrieving Google Doc {document_id} for user {user_id}: {e}")
            raise


# Global instance
googledocs_service = GoogleDocsService()
