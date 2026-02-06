from __future__ import annotations

from dataclasses import dataclass

import librosa
import numpy as np
from app.config import DEFAULT_BEATS_PER_BAR, DEFAULT_TIME_SIGNATURE
from app.models.schema import Bar, Beat, TempoMap


@dataclass
class BeatGridResult:
    tempo_map: TempoMap
    onset_envelope: np.ndarray
    sr: int
    hop_length: int


def _as_scalar_float(value: float | np.ndarray, default: float = 0.0) -> float:
    array = np.asarray(value)
    if array.size == 0:
        return default
    return float(array.reshape(-1)[0])


def _estimate_downbeat_offset(beat_frames: np.ndarray, low_band_env: np.ndarray) -> int:
    if len(beat_frames) < DEFAULT_BEATS_PER_BAR:
        return 0
    scores: list[float] = []
    for candidate in range(DEFAULT_BEATS_PER_BAR):
        candidate_frames = beat_frames[candidate::DEFAULT_BEATS_PER_BAR]
        if len(candidate_frames) == 0:
            scores.append(0.0)
            continue
        scores.append(
            float(
                np.mean(
                    low_band_env[np.clip(candidate_frames, 0, len(low_band_env) - 1)]
                )
            )
        )
    return int(np.argmax(scores))


def detect_beat_grid(
    y: np.ndarray,
    sr: int,
    total_duration: float,
) -> BeatGridResult:
    hop_length = 512
    y_mono = librosa.to_mono(y if y.ndim > 1 else np.expand_dims(y, axis=0))

    onset_env = librosa.onset.onset_strength(y=y_mono, sr=sr, hop_length=hop_length)
    tempo, beat_frames = librosa.beat.beat_track(
        y=y_mono, sr=sr, onset_envelope=onset_env, hop_length=hop_length
    )
    beat_frames = np.asarray(beat_frames, dtype=int).reshape(-1)
    tempo_value = _as_scalar_float(tempo)
    if len(beat_frames) < 4:
        estimated_bpm = tempo_value if tempo_value > 0 else 90.0
        beat_times = np.arange(0.0, total_duration, 60.0 / estimated_bpm)
        beat_frames = librosa.time_to_frames(beat_times, sr=sr, hop_length=hop_length)
        beat_frames = np.asarray(beat_frames, dtype=int).reshape(-1)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    lowpassed = librosa.effects.preemphasis(
        librosa.resample(y_mono, orig_sr=sr, target_sr=sr)
    )
    low_band_env = librosa.onset.onset_strength(
        y=lowpassed, sr=sr, hop_length=hop_length
    )
    downbeat_offset = _estimate_downbeat_offset(beat_frames, low_band_env)

    beats: list[Beat] = []
    for index, time_value in enumerate(beat_times):
        frame = int(np.clip(beat_frames[index], 0, len(onset_env) - 1))
        strength = _as_scalar_float(onset_env[frame])
        beats.append(
            Beat(
                index=index,
                time_seconds=_as_scalar_float(time_value),
                confidence=min(
                    1.0,
                    0.3
                    + strength
                    / (_as_scalar_float(np.max(onset_env), default=1.0) + 1e-6),
                ),
                is_downbeat=((index - downbeat_offset) % DEFAULT_BEATS_PER_BAR == 0),
                strength=strength,
            )
        )

    bars: list[Bar] = []
    bar_index = 0
    current_start_idx = downbeat_offset
    if current_start_idx > 0 and beats:
        bars.append(
            Bar(
                index=bar_index,
                start_seconds=0.0,
                end_seconds=beats[min(current_start_idx, len(beats) - 1)].time_seconds,
                beat_start_index=0,
                beat_count=current_start_idx,
                confidence=0.35,
            )
        )
        bar_index += 1
    while current_start_idx < len(beats):
        start_time = beats[current_start_idx].time_seconds
        end_beat_idx = min(current_start_idx + DEFAULT_BEATS_PER_BAR, len(beats) - 1)
        if end_beat_idx == len(beats) - 1:
            end_time = total_duration
        else:
            end_time = beats[end_beat_idx].time_seconds
        bars.append(
            Bar(
                index=bar_index,
                start_seconds=_as_scalar_float(start_time),
                end_seconds=_as_scalar_float(max(end_time, start_time + 0.01)),
                beat_start_index=current_start_idx,
                beat_count=min(DEFAULT_BEATS_PER_BAR, len(beats) - current_start_idx),
                confidence=0.6,
            )
        )
        bar_index += 1
        current_start_idx += DEFAULT_BEATS_PER_BAR

    bpm = tempo_value
    if bpm <= 0:
        intervals = np.diff(beat_times[: min(len(beat_times), 16)])
        bpm = (
            _as_scalar_float(60.0 / np.mean(intervals), default=90.0)
            if len(intervals)
            else 90.0
        )
    tempo_map = TempoMap(
        bpm=bpm,
        time_signature_numerator=DEFAULT_TIME_SIGNATURE[0],
        time_signature_denominator=DEFAULT_TIME_SIGNATURE[1],
        beats=beats,
        bars=bars,
        downbeat_offset_beats=downbeat_offset,
        confidence=0.6 if len(beats) > 8 else 0.35,
    )
    return BeatGridResult(
        tempo_map=tempo_map, onset_envelope=onset_env, sr=sr, hop_length=hop_length
    )
