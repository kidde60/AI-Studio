import asyncio
import io
import wave

from google import genai
from google.genai import types

from app.core.config import get_settings
from .base import GeneratedAudio, TTSProvider


class GeminiTTSProvider(TTSProvider):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_tts_model

    async def generate_speech(self, text: str, voice: str = "Kore") -> GeneratedAudio:
        if not text.strip():
            raise ValueError("Narration text cannot be empty.")

        def generate():
            return self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice,
                            )
                        )
                    ),
                ),
            )

        response = await asyncio.to_thread(generate)
        audio_data = None
        mime_type = "audio/L16;rate=24000"

        for candidate in response.candidates or []:
            content = candidate.content
            for part in content.parts if content else []:
                inline = part.inline_data
                if inline and inline.data:
                    audio_data = inline.data
                    mime_type = inline.mime_type or mime_type
                    break
            if audio_data:
                break

        if not audio_data:
            raise RuntimeError("Gemini returned no audio data.")

        sample_rate = 24000
        rate_marker = "rate="
        if rate_marker in mime_type:
            try:
                sample_rate = int(mime_type.split(rate_marker, 1)[1].split(";", 1)[0])
            except ValueError:
                pass

        # Gemini TTS returns raw PCM audio. Wrap it in a standard WAV container
        # so browsers and FFmpeg can consume it directly.
        wav = io.BytesIO()
        with wave.open(wav, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)  # 16-bit PCM
            output.setframerate(sample_rate)
            output.writeframes(audio_data)

        return GeneratedAudio(
            audio_bytes=wav.getvalue(),
            mime_type="audio/wav",
            extension="wav",
            sample_rate=sample_rate,
            model=self.model,
            voice=voice,
        )
