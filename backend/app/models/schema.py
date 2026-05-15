from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class AnalyzerBaseModel(BaseModel):
    model_config = {
        "populate_by_name": True,
        "extra": "forbid",
    }


class AudioMetadata(AnalyzerBaseModel):
    original_filename: str
    stored_filename: str
    stored_path: str
    asset_url: str
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str


class Beat(AnalyzerBaseModel):
    index: int
    time_seconds: float
    confidence: float = 0.5
    is_downbeat: bool = False
    strength: float = 0.0


class Bar(AnalyzerBaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    beat_start_index: int
    beat_count: int = 4
    confidence: float = 0.5


class TempoMap(AnalyzerBaseModel):
    bpm: float
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4
    beats: list[Beat] = Field(default_factory=list)
    bars: list[Bar] = Field(default_factory=list)
    downbeat_offset_beats: int = 0
    confidence: float = 0.5


class Section(AnalyzerBaseModel):
    id: str = Field(default_factory=lambda: new_id("section"))
    label: str
    start_seconds: float
    end_seconds: float
    confidence: float = 0.4


class LyricSyllable(AnalyzerBaseModel):
    id: str = Field(default_factory=lambda: new_id("syll"))
    text: str
    parent_word: str
    syllable_index: int
    stress: float = 0.0


class LyricToken(AnalyzerBaseModel):
    id: str = Field(default_factory=lambda: new_id("token"))
    text: str
    normalized: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    confidence: float = 0.0
    syllables: list[LyricSyllable] = Field(default_factory=list)


class QuantizationCandidate(AnalyzerBaseModel):
    label: str
    subdivision_per_beat: int
    triplet: bool = False
    start_beats: float
    duration_beats: float
    error_seconds: float
    score: float


class AcousticFeatures(AnalyzerBaseModel):
    onset_strength: float = 0.0
    rms: float = 0.0
    spectral_centroid: float = 0.0


class RhythmEvent(AnalyzerBaseModel):
    id: str = Field(default_factory=lambda: new_id("evt"))
    token_id: str | None = None
    syllable_id: str | None = None
    label: str
    word: str | None = None
    syllable: str | None = None
    start_seconds: float
    duration_seconds: float
    end_seconds: float
    free_start_beats: float
    free_duration_beats: float
    quantized_start_beats: float
    quantized_duration_beats: float
    bar_index: int
    beat_index_within_bar: float
    subdivision_label: str
    rest_before_beats: float = 0.0
    accent: float = 0.0
    stress: float = 0.0
    confidence: float = 0.5
    low_confidence: bool = False
    source: Literal["lyrics", "asr", "fallback"] = "fallback"
    acoustic_features: AcousticFeatures = Field(default_factory=AcousticFeatures)
    quantization_candidates: list[QuantizationCandidate] = Field(default_factory=list)


class QuantizationProfile(AnalyzerBaseModel):
    id: str = Field(default_factory=lambda: new_id("quant"))
    label: str
    subdivision_per_beat: int
    supports_triplets: bool = False
    average_error_seconds: float
    confidence: float


class AnalyticsSummary(AnalyzerBaseModel):
    syllables_per_beat: float = 0.0
    syllables_per_bar: float = 0.0
    dominant_subdivision: str = "unknown"
    triplet_density: float = 0.0
    syncopation_estimate: float = 0.0
    accent_pattern_by_bar: list[list[float]] = Field(default_factory=list)


class CapabilityStatus(AnalyzerBaseModel):
    source_separation: str = "unavailable"
    asr: str = "fallback"
    section_detection: str = "heuristic"
    notes: list[str] = Field(default_factory=list)


class AnalysisPayload(AnalyzerBaseModel):
    tempo_map: TempoMap
    sections: list[Section] = Field(default_factory=list)
    lyric_tokens: list[LyricToken] = Field(default_factory=list)
    rhythm_events: list[RhythmEvent] = Field(default_factory=list)
    quantization_profiles: list[QuantizationProfile] = Field(default_factory=list)
    analytics: AnalyticsSummary = Field(default_factory=AnalyticsSummary)
    warnings: list[str] = Field(default_factory=list)
    capability_status: CapabilityStatus = Field(default_factory=CapabilityStatus)


class BarEdit(AnalyzerBaseModel):
    bar_index: int
    start_seconds: float
    end_seconds: float


class CanonicalState(AnalyzerBaseModel):
    tempo_map: TempoMap
    rhythm_events: list[RhythmEvent]
    bar_edits: list[BarEdit] = Field(default_factory=list)
    selected_quantization_profile_id: str | None = None
    notes: str = ""


class UIState(AnalyzerBaseModel):
    zoom: float = 1.0
    selected_event_id: str | None = None
    show_confidence_overlay: bool = True
    notation_measures_per_row: int = 4
    scroll_seconds: float = 0.0


class ProjectMetadata(AnalyzerBaseModel):
    id: str = Field(default_factory=lambda: new_id("project"))
    name: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    app_version: str = "0.1.0"


class RapRhythmProject(AnalyzerBaseModel):
    metadata: ProjectMetadata
    audio: AudioMetadata
    lyrics_text: str = ""
    raw_analysis: AnalysisPayload
    canonical_state: CanonicalState
    ui_state: UIState = Field(default_factory=UIState)


class AnalyzeOptions(AnalyzerBaseModel):
    project_name: str = "Untitled Analysis"
    lyrics_text: str = ""
    use_source_separation: bool = False


class SaveProjectRequest(AnalyzerBaseModel):
    project: RapRhythmProject
    save_as: str | None = None


class ExportRequest(AnalyzerBaseModel):
    project: RapRhythmProject


class ProjectFileReference(AnalyzerBaseModel):
    filename: str
    path: str
    created_at: datetime


class DemoRequest(AnalyzerBaseModel):
    project_name: str = "Demo Flow"


class ErrorResponse(AnalyzerBaseModel):
    detail: str
    context: dict[str, Any] = Field(default_factory=dict)
