"""
OpenAI service for text summarization.
"""
from openai import OpenAI
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIService:
    """Service for OpenAI API interactions."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def summarize_for_briefing(self, content: str, title: str = "") -> str:
        """
        Summarize content into a concise, engaging 400-500 word spoken briefing.

        Args:
            content: The full content to summarize
            title: Optional title context for the briefing

        Returns:
            Summarized text optimized for audio narration
        """
        try:
            prompt = f"""You are an expert at creating engaging spoken briefings for busy professionals.

Your task is to summarize the following internal company document into a concise, conversational briefing that can be listened to in about 2-3 minutes.

TITLE: {title if title else "Company Update"}

CONTENT:
{content}

INSTRUCTIONS:
1. Create a 400-500 word summary optimized for listening (not reading)
2. Use a conversational, professional tone
3. Start with a clear introduction of what this briefing covers
4. Highlight the most important points and key takeaways
5. Use transitions like "First," "Additionally," "Most importantly"
6. End with clear next steps or key takeaways
7. Avoid jargon unless necessary, and explain it when used
8. Write for speech - use shorter sentences and natural language
9. DO NOT include any meta-instructions or formatting markers
10. DO NOT say things like "Here's your briefing" or "This document covers"

Write the briefing now:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating concise, engaging spoken briefings from written content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary of {len(summary)} characters")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise


# Global instance
openai_service = OpenAIService()
