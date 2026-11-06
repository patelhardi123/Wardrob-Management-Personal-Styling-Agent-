"""
Voice Service Module for AI Smart Wardrobe Voice Stylist Agent
Provides speech-to-text and text-to-speech functionality with configurable providers.
Uses browser Web Speech API on frontend (free, no API keys).
Backend provides TTS via browser-native synthesis or optional provider APIs.
"""

import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI


class VoiceService:
    """
    Voice service adapter for speech-to-text (STT) and text-to-speech (TTS).
    STT is handled client-side via Web Speech API (browser native).
    TTS can use browser synthesis or optional OpenAI TTS API.
    """

    def __init__(self):
        self.openai_client = None
        self.use_openai_tts = False

        # Initialize OpenAI client if API key is available
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and os.getenv("USE_OPENAI_TTS", "false").lower() == "true":
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                self.use_openai_tts = True
                print("[Voice Service] Using OpenAI TTS API")
            except Exception as e:
                print(f"[Voice Service] Failed to initialize OpenAI TTS: {e}")

    def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """
        Convert text to speech audio.
        Uses OpenAI TTS API if configured, otherwise returns None (frontend will use browser TTS).

        Args:
            text: The text to convert to speech
            voice: Voice model (alloy, echo, fable, onyx, nova, shimmer)

        Returns:
            Audio bytes if using OpenAI TTS, None otherwise
        """
        if not self.use_openai_tts or not self.openai_client:
            return None

        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"[Voice Service] OpenAI TTS failed: {e}")
            return None

    def text_to_speech_base64(self, text: str, voice: str = "alloy") -> Optional[str]:
        """
        Convert text to speech and return as base64 encoded string.

        Args:
            text: The text to convert to speech
            voice: Voice model (alloy, echo, fable, onyx, nova, shimmer)

        Returns:
            Base64 encoded audio data URI if using OpenAI TTS, None otherwise
        """
        audio_bytes = self.text_to_speech(text, voice)
        if audio_bytes:
            import base64
            return f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode('utf-8')}"
        return None


# Singleton instance
voice_service = VoiceService()
