"""
Voice Service

Integration with Whisper for speech-to-text and voice-based family interactions.
"""

import httpx
import asyncio
import json
import base64
import io
import wave
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceConfig(BaseModel):
    whisper_url: str = "http://localhost:30900"
    whisper_model: str = "small"
    language: str = "es"  # Default to Spanish for family use
    timeout: int = 30
    max_audio_size: int = 25 * 1024 * 1024  # 25MB limit
    supported_formats: List[str] = ["wav", "mp3", "ogg", "m4a", "flac"]

class AudioMetadata(BaseModel):
    format: str
    duration: float
    sample_rate: int
    channels: int
    size: int

class TranscriptionResult(BaseModel):
    text: str
    confidence: float
    language_detected: str
    processing_time: float
    audio_metadata: AudioMetadata

class VoiceInteractionRequest(BaseModel):
    audio_data: bytes
    audio_format: str
    family_id: str
    member_id: str
    context: Optional[Dict[str, Any]] = {}

class VoiceInteractionResponse(BaseModel):
    transcription: str
    confidence: float
    language: str
    response: Optional[str] = None
    audio_response_url: Optional[str] = None
    processing_time: float

class VoiceService:
    """Service for voice-based family interactions using Whisper."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.whisper_url,
            timeout=self.config.timeout
        )

    async def health_check(self) -> bool:
        """Check if Whisper service is available."""
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Whisper health check failed: {e}")
            return False

    def validate_audio_format(self, audio_data: bytes, format: str) -> bool:
        """Validate audio format and size."""
        if format not in self.config.supported_formats:
            logger.error(f"Unsupported audio format: {format}")
            return False

        if len(audio_data) > self.config.max_audio_size:
            logger.error(f"Audio file too large: {len(audio_data)} bytes")
            return False

        # Basic format validation
        if format == "wav" and len(audio_data) < 44:
            logger.error("Invalid WAV file - too small for header")
            return False

        return True

    def get_audio_metadata(self, audio_data: bytes, format: str) -> AudioMetadata:
        """Extract audio metadata."""
        try:
            if format == "wav":
                # Parse WAV header for metadata
                with io.BytesIO(audio_data) as wav_io:
                    with wave.open(wav_io, 'rb') as wav_file:
                        return AudioMetadata(
                            format=format,
                            duration=wav_file.getnframes() / wav_file.getframerate(),
                            sample_rate=wav_file.getframerate(),
                            channels=wav_file.getnchannels(),
                            size=len(audio_data)
                        )
            else:
                # For other formats, provide basic metadata
                return AudioMetadata(
                    format=format,
                    duration=0.0,  # Unknown
                    sample_rate=44100,  # Assumed
                    channels=1,  # Assumed mono
                    size=len(audio_data)
                )
        except Exception as e:
            logger.warning(f"Failed to extract audio metadata: {e}")
            return AudioMetadata(
                format=format,
                duration=0.0,
                sample_rate=44100,
                channels=1,
                size=len(audio_data)
            )

    async def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio using Whisper service."""
        import time
        start_time = time.time()

        try:
            # Validate audio
            if not self.validate_audio_format(audio_data, audio_format):
                raise ValueError(f"Invalid audio format or size: {audio_format}")

            # Get metadata
            metadata = self.get_audio_metadata(audio_data, audio_format)

            # Prepare request to Whisper
            files = {
                "audio_file": (f"audio.{audio_format}", audio_data, f"audio/{audio_format}")
            }

            data = {
                "model": self.config.whisper_model,
                "language": language or self.config.language,
                "response_format": "json"
            }

            # Send to Whisper service
            response = await self.client.post(
                "/asr",
                files=files,
                data=data
            )

            processing_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Extract transcription data
                text = result.get("text", "").strip()
                confidence = result.get("confidence", 0.0)
                language_detected = result.get("language", language or self.config.language)

                return TranscriptionResult(
                    text=text,
                    confidence=confidence,
                    language_detected=language_detected,
                    processing_time=processing_time,
                    audio_metadata=metadata
                )
            else:
                logger.error(f"Whisper transcription failed: {response.status_code} - {response.text}")
                raise Exception(f"Transcription failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Voice transcription error: {e}")
            raise

    async def process_voice_interaction(
        self,
        request: VoiceInteractionRequest,
        family_engine=None
    ) -> VoiceInteractionResponse:
        """Process a complete voice interaction."""
        import time
        start_time = time.time()

        try:
            # Check Whisper service availability
            if not await self.health_check():
                raise Exception("Whisper service is not available")

            # Transcribe audio
            transcription_result = await self.transcribe_audio(
                audio_data=request.audio_data,
                audio_format=request.audio_format
            )

            logger.info(f"Transcription: {transcription_result.text} (confidence: {transcription_result.confidence})")

            # Process with family engine if available
            ai_response = None
            if family_engine and transcription_result.text:
                from services.family_engine import InteractionRequest

                interaction_request = InteractionRequest(
                    message=transcription_result.text,
                    interaction_type="voice",
                    language=transcription_result.language_detected,
                    context=request.context,
                    member_id=request.member_id
                )

                interaction_response = await family_engine.process_interaction(interaction_request)
                ai_response = interaction_response.response

            total_processing_time = time.time() - start_time

            return VoiceInteractionResponse(
                transcription=transcription_result.text,
                confidence=transcription_result.confidence,
                language=transcription_result.language_detected,
                response=ai_response,
                processing_time=total_processing_time
            )

        except Exception as e:
            logger.error(f"Voice interaction processing failed: {e}")
            raise

    async def get_supported_languages(self) -> List[str]:
        """Get list of languages supported by Whisper."""
        try:
            response = await self.client.get("/languages")
            if response.status_code == 200:
                languages = response.json()
                return languages.get("languages", ["es", "en"])
            return ["es", "en"]  # Default fallback
        except:
            return ["es", "en"]

    async def get_service_info(self) -> Dict[str, Any]:
        """Get information about the Whisper service."""
        try:
            response = await self.client.get("/info")
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    async def preprocess_audio(self, audio_data: bytes, format: str) -> bytes:
        """Preprocess audio for better transcription quality."""
        try:
            # For now, just return the original audio
            # In production, could implement:
            # - Noise reduction
            # - Volume normalization
            # - Sample rate conversion
            # - Format conversion to optimal format for Whisper
            return audio_data
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            return audio_data

    def detect_voice_activity(self, audio_data: bytes, format: str) -> bool:
        """Simple voice activity detection."""
        try:
            if format == "wav":
                with io.BytesIO(audio_data) as wav_io:
                    with wave.open(wav_io, 'rb') as wav_file:
                        # Get audio samples
                        frames = wav_file.readframes(-1)
                        if len(frames) == 0:
                            return False

                        # Simple energy-based VAD
                        import struct
                        samples = struct.unpack(f'{len(frames)//2}h', frames)
                        avg_energy = sum(abs(s) for s in samples) / len(samples)

                        # Threshold for voice detection (adjustable)
                        threshold = 500
                        return avg_energy > threshold
            else:
                # For non-WAV formats, assume there's voice activity if file is reasonable size
                return len(audio_data) > 1000  # 1KB minimum
        except:
            return True  # Assume voice activity if we can't analyze

    async def cleanup_old_recordings(self, family_id: str, days_old: int = 7) -> int:
        """Clean up old voice recordings (placeholder)."""
        # In production, this would:
        # 1. Scan recording storage directory
        # 2. Delete files older than specified days
        # 3. Update database records
        logger.info(f"Cleanup task for family {family_id} - recordings older than {days_old} days")
        return 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()