from app.analysis.analytics import build_analytics
from app.models.schema import Bar, Beat, RhythmEvent, TempoMap


def test_analytics_summary_handles_triplets() -> None:
    tempo_map = TempoMap(
        bpm=90.0,
        beats=[
            Beat(index=i, time_seconds=i * 2 / 3, is_downbeat=i % 4 == 0)
            for i in range(8)
        ],
        bars=[
            Bar(index=0, start_seconds=0.0, end_seconds=2.666, beat_start_index=0),
            Bar(index=1, start_seconds=2.666, end_seconds=5.333, beat_start_index=4),
        ],
    )
    events = [
        RhythmEvent(
            label="trip",
            start_seconds=0.0,
            duration_seconds=0.22,
            end_seconds=0.22,
            free_start_beats=0.0,
            free_duration_beats=1 / 3,
            quantized_start_beats=0.0,
            quantized_duration_beats=1 / 3,
            bar_index=0,
            beat_index_within_bar=0.0,
            subdivision_label="eighth-triplet",
        ),
        RhythmEvent(
            label="let",
            start_seconds=0.22,
            duration_seconds=0.22,
            end_seconds=0.44,
            free_start_beats=1 / 3,
            free_duration_beats=1 / 3,
            quantized_start_beats=1 / 3,
            quantized_duration_beats=1 / 3,
            bar_index=0,
            beat_index_within_bar=1 / 3,
            subdivision_label="eighth-triplet",
        ),
    ]

    summary = build_analytics(events, tempo_map)

    assert summary.triplet_density == 1.0
    assert summary.dominant_subdivision == "eighth-triplet"
