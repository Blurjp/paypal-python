"""
File processing utilities for extracting text from various sources.
"""
import PyPDF2
import docx
import requests
from io import BytesIO
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FileProcessor:
    """Process various file types and URLs to extract text content."""

    @staticmethod
    def extract_from_pdf(file_data: bytes) -> str:
        """
        Extract text from PDF file.

        Args:
            file_data: PDF file as bytes

        Returns:
            Extracted text content
        """
        try:
            pdf_file = BytesIO(file_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text_content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)

            full_text = "\n\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from PDF")
            return full_text

        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    @staticmethod
    def extract_from_docx(file_data: bytes) -> str:
        """
        Extract text from DOCX file.

        Args:
            file_data: DOCX file as bytes

        Returns:
            Extracted text content
        """
        try:
            docx_file = BytesIO(file_data)
            doc = docx.Document(docx_file)

            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            full_text = "\n\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from DOCX")
            return full_text

        except Exception as e:
            logger.error(f"Error extracting DOCX text: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

    @staticmethod
    def extract_from_url(url: str) -> str:
        """
        Fetch and extract text from URL.
        For Notion pages, this is a simplified version - production should use Notion API.

        Args:
            url: URL to fetch

        Returns:
            Extracted text content
        """
        try:
            # Basic URL fetching
            # Note: For Notion, you should use the official Notion API
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Simple text extraction (in production, use proper HTML parsing)
            content = response.text

            # Basic cleanup - remove HTML tags (simplified)
            # In production, use BeautifulSoup or similar
            import re
            text = re.sub(r'<[^>]+>', '', content)
            text = re.sub(r'\s+', ' ', text).strip()

            logger.info(f"Extracted {len(text)} characters from URL")
            return text

        except Exception as e:
            logger.error(f"Error fetching URL: {e}")
            raise ValueError(f"Failed to fetch content from URL: {str(e)}")

    @staticmethod
    def process_content(
        text: Optional[str] = None,
        url: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Process content from various sources.

        Args:
            text: Direct text content
            url: URL to fetch content from
            file_data: File data as bytes
            filename: Original filename (to determine type)

        Returns:
            Extracted text content
        """
        if text:
            return text

        if url:
            return FileProcessor.extract_from_url(url)

        if file_data and filename:
            if filename.lower().endswith('.pdf'):
                return FileProcessor.extract_from_pdf(file_data)
            elif filename.lower().endswith('.docx'):
                return FileProcessor.extract_from_docx(file_data)
            else:
                # Try to decode as text
                try:
                    return file_data.decode('utf-8')
                except UnicodeDecodeError:
                    raise ValueError(f"Unsupported file type: {filename}")

        raise ValueError("No valid content source provided")


# Global instance
file_processor = FileProcessor()
