from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GeneratedAudio:
    audio_bytes: bytes
    mime_type: str
    extension: str
    sample_rate: int
    model: str
    voice: str


class TTSProvider(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, voice: str = "Kore") -> GeneratedAudio:
        raise NotImplementedError
