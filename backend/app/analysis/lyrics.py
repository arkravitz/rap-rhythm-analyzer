from __future__ import annotations

import importlib.util
import re

from app.models.schema import LyricSyllable, LyricToken

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _pyphen_dict():
    if importlib.util.find_spec("pyphen") is None:
        return None
    import pyphen

    return pyphen.Pyphen(lang="en_US")


def tokenize_lyrics(text: str) -> list[LyricToken]:
    tokens: list[LyricToken] = []
    dic = _pyphen_dict()
    for match in WORD_RE.finditer(text):
        raw = match.group(0)
        normalized = raw.lower()
        syllable_parts = [raw]
        if dic is not None:
            inserted = dic.inserted(raw)
            syllable_parts = [part for part in inserted.split("-") if part] or [raw]
        syllables = [
            LyricSyllable(
                text=part,
                parent_word=raw,
                syllable_index=index,
                stress=1.0 if index == 0 and len(syllable_parts) == 1 else 0.35,
            )
            for index, part in enumerate(syllable_parts)
        ]
        tokens.append(
            LyricToken(
                text=raw,
                normalized=normalized,
                confidence=1.0,
                syllables=syllables,
            )
        )
    return tokens


def syllables_from_asr_words(words: list[dict[str, float | str]]) -> list[LyricToken]:
    dic = _pyphen_dict()
    tokens: list[LyricToken] = []
    for word in words:
        text = str(word["word"]).strip()
        if not text:
            continue
        syllable_parts = [text]
        if dic is not None:
            inserted = dic.inserted(text)
            syllable_parts = [part for part in inserted.split("-") if part] or [text]
        start = float(word["start"])
        end = float(word["end"])
        syllables = []
        for index, part in enumerate(syllable_parts):
            syllables.append(
                LyricSyllable(
                    text=part,
                    parent_word=text,
                    syllable_index=index,
                    stress=1.0 if index == 0 and len(syllable_parts) == 1 else 0.3,
                )
            )
        tokens.append(
            LyricToken(
                text=text,
                normalized=text.lower(),
                start_seconds=start,
                end_seconds=end,
                confidence=float(word.get("confidence", 0.6)),
                syllables=syllables,
            )
        )
    return tokens
