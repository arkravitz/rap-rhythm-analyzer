from __future__ import annotations

import math

import librosa
import numpy as np
from app.config import DEFAULT_BEATS_PER_BAR
from app.models.schema import (
    AcousticFeatures,
    LyricToken,
    QuantizationCandidate,
    QuantizationProfile,
    RhythmEvent,
    TempoMap,
)

GRID_PRESETS = [
    ("quarter", 1, False),
    ("eighth", 2, False),
    ("eighth-triplet", 3, True),
    ("sixteenth", 4, False),
    ("sixteenth-triplet", 6, True),
]


def _nearest_quantization(
    value_beats: float, bpm: float
) -> list[QuantizationCandidate]:
    candidates: list[QuantizationCandidate] = []
    beat_seconds = 60.0 / max(bpm, 1.0)
    for label, subdivision, triplet in GRID_PRESETS:
        step = 1.0 / subdivision
        start_q = round(value_beats / step) * step
        duration_q = max(step, round(step / step) * step)
        error = abs(value_beats - start_q) * beat_seconds
        candidates.append(
            QuantizationCandidate(
                label=label,
                subdivision_per_beat=subdivision,
                triplet=triplet,
                start_beats=round(start_q, 6),
                duration_beats=round(duration_q, 6),
                error_seconds=round(error, 6),
                score=round(1.0 / (1.0 + error * 12), 4),
            )
        )
    candidates.sort(key=lambda item: item.error_seconds)
    return candidates


def _build_profiles(events: list[RhythmEvent]) -> list[QuantizationProfile]:
    profiles: list[QuantizationProfile] = []
    by_label: dict[str, list[float]] = {}
    for event in events:
        for candidate in event.quantization_candidates[:3]:
            by_label.setdefault(candidate.label, []).append(candidate.error_seconds)
    for label, subdivision, triplet in GRID_PRESETS:
        errors = by_label.get(label, [0.25])
        average_error = float(sum(errors) / len(errors))
        profiles.append(
            QuantizationProfile(
                label=label,
                subdivision_per_beat=subdivision,
                supports_triplets=triplet,
                average_error_seconds=round(average_error, 6),
                confidence=round(1.0 / (1.0 + average_error * 10), 4),
            )
        )
    profiles.sort(key=lambda profile: profile.average_error_seconds)
    return profiles


def _estimate_duration(
    next_start: float | None, current_start: float, beat_seconds: float
) -> float:
    if next_start is None:
        return beat_seconds / 2
    return max(0.06, min(next_start - current_start, beat_seconds * 1.5))


def _find_bar_index(start_seconds: float, tempo_map: TempoMap) -> tuple[int, float]:
    for bar in tempo_map.bars:
        if bar.start_seconds <= start_seconds < bar.end_seconds:
            beat_offset = (start_seconds - bar.start_seconds) / (
                60.0 / max(tempo_map.bpm, 1.0)
            )
            return bar.index, beat_offset
    if tempo_map.bars:
        last_bar = tempo_map.bars[-1]
        beat_offset = (start_seconds - last_bar.start_seconds) / (
            60.0 / max(tempo_map.bpm, 1.0)
        )
        return last_bar.index, max(0.0, beat_offset)
    return 0, 0.0


def _compute_acoustic_features(
    y_mono: np.ndarray, sr: int, start_seconds: float
) -> AcousticFeatures:
    frame = int(start_seconds * sr)
    window = y_mono[max(0, frame - 1024) : min(len(y_mono), frame + 2048)]
    if len(window) == 0:
        return AcousticFeatures()
    rms = float(np.sqrt(np.mean(np.square(window))))
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=window, sr=sr)))
    onset_strength = float(np.max(np.abs(np.diff(window)))) if len(window) > 1 else 0.0
    return AcousticFeatures(
        onset_strength=onset_strength, rms=rms, spectral_centroid=centroid
    )


def events_from_tokens(
    tokens: list[LyricToken],
    onset_times: list[float],
    tempo_map: TempoMap,
    y_mono: np.ndarray,
    sr: int,
    source: str,
) -> tuple[list[RhythmEvent], list[QuantizationProfile]]:
    beat_seconds = 60.0 / max(tempo_map.bpm, 1.0)
    syllables = []
    for token in tokens:
        syllables.extend(
            [
                (token, syllable, idx, len(token.syllables))
                for idx, syllable in enumerate(token.syllables)
            ]
        )

    if not syllables:
        syllables = [
            (
                LyricToken(
                    text=f"syllable-{idx + 1}",
                    normalized=f"syllable-{idx + 1}",
                    syllables=[],
                ),
                None,
                0,
                1,
            )
            for idx in range(len(onset_times))
        ]

    if not onset_times:
        onset_times = [index * beat_seconds / 2 for index in range(len(syllables))]

    events: list[RhythmEvent] = []
    total_slots = max(len(onset_times), len(syllables))
    for index in range(total_slots):
        token, syllable, syllable_index, syllable_count = syllables[
            min(index, len(syllables) - 1)
        ]
        start_seconds = onset_times[min(index, len(onset_times) - 1)]
        next_start = onset_times[index + 1] if index + 1 < len(onset_times) else None
        if (
            token.start_seconds is not None
            and token.end_seconds is not None
            and syllable_count > 0
        ):
            word_duration = max(0.06, token.end_seconds - token.start_seconds)
            slot = word_duration / syllable_count
            start_seconds = token.start_seconds + slot * syllable_index
            next_start = (
                token.start_seconds + slot * (syllable_index + 1)
                if syllable_index + 1 < syllable_count
                else token.end_seconds
            )

        duration_seconds = _estimate_duration(next_start, start_seconds, beat_seconds)
        free_start_beats = start_seconds / beat_seconds
        free_duration_beats = duration_seconds / beat_seconds
        quantization_candidates = _nearest_quantization(free_start_beats, tempo_map.bpm)
        best_candidate = quantization_candidates[0]
        bar_index, beat_index_within_bar = _find_bar_index(start_seconds, tempo_map)
        acoustic = _compute_acoustic_features(y_mono, sr, start_seconds)
        position_accent = (
            0.9 if math.isclose(beat_index_within_bar % 1, 0.0, abs_tol=0.12) else 0.45
        )
        accent = min(
            1.0, position_accent + acoustic.rms * 4.0 + acoustic.onset_strength * 0.02
        )
        confidence = min(
            1.0,
            0.25
            + best_candidate.score * 0.35
            + getattr(token, "confidence", 0.4) * 0.25
            + accent * 0.15,
        )
        previous_end = events[-1].end_seconds if events else 0.0
        rest_before_beats = max(0.0, (start_seconds - previous_end) / beat_seconds)
        subdivision_label = best_candidate.label
        label = syllable.text if syllable is not None else token.text
        events.append(
            RhythmEvent(
                token_id=token.id if hasattr(token, "id") else None,
                syllable_id=syllable.id if syllable is not None else None,
                label=label,
                word=token.text,
                syllable=label,
                start_seconds=round(start_seconds, 6),
                duration_seconds=round(duration_seconds, 6),
                end_seconds=round(start_seconds + duration_seconds, 6),
                free_start_beats=round(free_start_beats, 6),
                free_duration_beats=round(free_duration_beats, 6),
                quantized_start_beats=best_candidate.start_beats,
                quantized_duration_beats=max(
                    best_candidate.duration_beats, round(free_duration_beats, 6)
                ),
                bar_index=bar_index,
                beat_index_within_bar=round(beat_index_within_bar, 6),
                subdivision_label=subdivision_label,
                rest_before_beats=round(rest_before_beats, 6),
                accent=round(accent, 4),
                stress=getattr(syllable, "stress", 0.0)
                if syllable is not None
                else 0.0,
                confidence=round(confidence, 4),
                low_confidence=confidence < 0.55,
                source=source,
                acoustic_features=acoustic,
                quantization_candidates=quantization_candidates,
            )
        )

    profiles = _build_profiles(events)
    return events, profiles


def detect_onsets(y_mono: np.ndarray, sr: int) -> list[float]:
    onset_frames = librosa.onset.onset_detect(
        y=y_mono,
        sr=sr,
        units="frames",
        backtrack=True,
        delta=0.08,
        wait=1,
        pre_avg=3,
        post_avg=3,
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()
    if len(onset_times) < 8:
        intervals = librosa.effects.split(y_mono, top_db=22)
        onset_times = [float(start / sr) for start, _ in intervals]
    return onset_times
