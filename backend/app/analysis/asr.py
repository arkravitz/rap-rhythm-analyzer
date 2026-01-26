from __future__ import annotations

import importlib.util
from typing import Any


def faster_whisper_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def transcribe_words(audio_path: str) -> list[dict[str, Any]]:
    if not faster_whisper_available():
        return []

    from faster_whisper import WhisperModel

    model = WhisperModel("small", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True, vad_filter=True)
    words: list[dict[str, Any]] = []
    for segment in segments:
        for word in segment.words or []:
            words.append(
                {
                    "word": word.word.strip(),
                    "start": float(word.start),
                    "end": float(word.end),
                    "confidence": float(word.probability),
                }
            )
    return words
