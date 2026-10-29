import re
from math import ceil


def _chunks(text: str, max_words: int = 11) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i:i + max_words]))
    return chunks or [text.strip()]


def build_cues(text: str, duration: float) -> list[dict]:
    chunks = _chunks(text)
    weights = [max(1, len(c.split())) for c in chunks]
    total = sum(weights)
    cues = []
    cursor = 0.0
    for index, (chunk, weight) in enumerate(zip(chunks, weights), start=1):
        span = duration * weight / total
        end = duration if index == len(chunks) else min(duration, cursor + span)
        cues.append({"start": round(cursor, 3), "end": round(end, 3), "text": chunk})
        cursor = end
    return cues


def srt_timestamp(seconds: float) -> str:
    ms = int(round(max(0, seconds) * 1000))
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def cues_to_srt(cues: list[dict]) -> str:
    return "\n\n".join(
        f"{i}\n{srt_timestamp(c['start'])} --> {srt_timestamp(c['end'])}\n{c['text']}"
        for i, c in enumerate(cues, start=1)
    ) + "\n"
