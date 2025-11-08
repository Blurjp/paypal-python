"""
ElevenLabs service for text-to-speech conversion.
"""
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class ElevenLabsService:
    """Service for ElevenLabs TTS API."""

    def __init__(self):
        """Initialize ElevenLabs API."""
        set_api_key(settings.elevenlabs_api_key)
        self.voice_id = settings.elevenlabs_voice_id

    def generate_audio(self, text: str, voice_id: str = None) -> bytes:
        """
        Convert text to speech using ElevenLabs API.

        Args:
            text: The text to convert to speech
            voice_id: Optional voice ID (defaults to configured voice)

        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            if not voice_id:
                voice_id = self.voice_id

            logger.info(f"Generating audio for {len(text)} characters with voice {voice_id}")

            # Generate audio with optimized settings for briefings
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(
                        stability=0.5,  # Moderate stability for natural speech
                        similarity_boost=0.75,  # High similarity to voice
                        style=0.0,  # Neutral style
                        use_speaker_boost=True  # Enhanced clarity
                    )
                ),
                model="eleven_monolingual_v1"  # High-quality English model
            )

            # Convert generator to bytes
            audio_bytes = b"".join(audio)
            logger.info(f"Generated {len(audio_bytes)} bytes of audio")

            return audio_bytes

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise


# Global instance
elevenlabs_service = ElevenLabsService()
