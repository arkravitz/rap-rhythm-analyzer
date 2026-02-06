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


