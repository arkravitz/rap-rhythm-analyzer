from __future__ import annotations

import librosa
import numpy as np
from app.models.schema import Section


def suggest_sections(y: np.ndarray, sr: int, duration: float) -> list[Section]:
    y_mono = librosa.to_mono(y if y.ndim > 1 else np.expand_dims(y, axis=0))
    if duration < 20:
        return [
            Section(
                label="full section",
                start_seconds=0.0,
                end_seconds=duration,
                confidence=0.35,
            )
        ]

    hop_length = 2048
    rms = librosa.feature.rms(y=y_mono, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    threshold = float(np.percentile(rms, 35))
    voiced = rms > threshold
    changes = np.where(np.diff(voiced.astype(int)) != 0)[0]
    cut_times = [0.0]
    for idx in changes[:8]:
        cut_times.append(float(times[idx]))
    cut_times.append(duration)
    cut_times = sorted(
        set(round(time, 1) for time in cut_times if 0 <= time <= duration)
    )
    if len(cut_times) < 3:
        step = max(16.0, duration / 4)
        cut_times = [0.0]
        cursor = step
        while cursor < duration:
            cut_times.append(round(cursor, 2))
            cursor += step
        cut_times.append(duration)

    labels = ["intro", "verse", "hook", "verse", "bridge", "hook", "outro"]
    sections: list[Section] = []
    for index in range(len(cut_times) - 1):
        start = cut_times[index]
        end = cut_times[index + 1]
        if end - start < 4:
            continue
        label = labels[min(index, len(labels) - 1)]
        sections.append(
            Section(
                label=label,
                start_seconds=start,
                end_seconds=end,
                confidence=0.4,
            )
        )
    return sections or [
        Section(
            label="full section",
            start_seconds=0.0,
            end_seconds=duration,
            confidence=0.3,
        )
    ]
