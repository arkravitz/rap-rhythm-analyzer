from __future__ import annotations

from collections import Counter

from app.models.schema import AnalyticsSummary, RhythmEvent, TempoMap


def build_analytics(events: list[RhythmEvent], tempo_map: TempoMap) -> AnalyticsSummary:
    if not events or not tempo_map.beats or not tempo_map.bars:
        return AnalyticsSummary()

    total_beats = max(len(tempo_map.beats), 1)
    total_bars = max(len(tempo_map.bars), 1)
    syllables_per_beat = len(events) / total_beats
    syllables_per_bar = len(events) / total_bars

    subdivisions = Counter(event.subdivision_label for event in events)
    dominant_subdivision = (
        subdivisions.most_common(1)[0][0] if subdivisions else "unknown"
    )
    triplet_density = sum(
        1 for event in events if "triplet" in event.subdivision_label
    ) / len(events)

    syncopated = 0
    accent_pattern_by_bar: list[list[float]] = [[] for _ in range(total_bars)]
    for event in events:
        beat_position = event.quantized_start_beats % 1
        if 0.10 < beat_position < 0.90:
            syncopated += 1
        if 0 <= event.bar_index < len(accent_pattern_by_bar):
            accent_pattern_by_bar[event.bar_index].append(round(event.accent, 3))

    return AnalyticsSummary(
        syllables_per_beat=round(syllables_per_beat, 3),
        syllables_per_bar=round(syllables_per_bar, 3),
        dominant_subdivision=dominant_subdivision,
        triplet_density=round(triplet_density, 3),
        syncopation_estimate=round(syncopated / len(events), 3),
        accent_pattern_by_bar=accent_pattern_by_bar,
    )
