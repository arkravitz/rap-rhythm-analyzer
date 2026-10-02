export type SourceType = "lyrics" | "asr" | "fallback";

export interface AudioMetadata {
  original_filename: string;
  stored_filename: string;
  stored_path: string;
  asset_url: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  format: string;
}

export interface Beat {
  index: number;
  time_seconds: number;
  confidence: number;
  is_downbeat: boolean;
  strength: number;
}

export interface Bar {
  index: number;
  start_seconds: number;
  end_seconds: number;
  beat_start_index: number;
  beat_count: number;
  confidence: number;
}

export interface TempoMap {
  bpm: number;
  time_signature_numerator: number;
  time_signature_denominator: number;
  beats: Beat[];
  bars: Bar[];
  downbeat_offset_beats: number;
  confidence: number;
}

export interface Section {
  id: string;
  label: string;
  start_seconds: number;
  end_seconds: number;
  confidence: number;
}

export interface LyricSyllable {
  id: string;
  text: string;
  parent_word: string;
  syllable_index: number;
  stress: number;
}

export interface LyricToken {
  id: string;
  text: string;
  normalized: string;
  start_seconds?: number | null;
  end_seconds?: number | null;
  confidence: number;
  syllables: LyricSyllable[];
}

export interface QuantizationCandidate {
  label: string;
  subdivision_per_beat: number;
  triplet: boolean;
  start_beats: number;
  duration_beats: number;
  error_seconds: number;
  score: number;
}

export interface AcousticFeatures {
  onset_strength: number;
  rms: number;
  spectral_centroid: number;
}

export interface RhythmEvent {
  id: string;
  token_id?: string | null;
  syllable_id?: string | null;
  label: string;
  word?: string | null;
  syllable?: string | null;
  start_seconds: number;
  duration_seconds: number;
  end_seconds: number;
  free_start_beats: number;
  free_duration_beats: number;
  quantized_start_beats: number;
  quantized_duration_beats: number;
  bar_index: number;
  beat_index_within_bar: number;
  subdivision_label: string;
  rest_before_beats: number;
  accent: number;
  stress: number;
  confidence: number;
  low_confidence: boolean;
  source: SourceType;
  acoustic_features: AcousticFeatures;
  quantization_candidates: QuantizationCandidate[];
}

export interface QuantizationProfile {
  id: string;
  label: string;
  subdivision_per_beat: number;
  supports_triplets: boolean;
  average_error_seconds: number;
  confidence: number;
}

export interface AnalyticsSummary {
  syllables_per_beat: number;
  syllables_per_bar: number;
  dominant_subdivision: string;
  triplet_density: number;
  syncopation_estimate: number;
  accent_pattern_by_bar: number[][];
}

export interface CapabilityStatus {
  source_separation: string;
  asr: string;
  section_detection: string;
  notes: string[];
}

export interface AnalysisPayload {
  tempo_map: TempoMap;
  sections: Section[];
  lyric_tokens: LyricToken[];
  rhythm_events: RhythmEvent[];
  quantization_profiles: QuantizationProfile[];
  analytics: AnalyticsSummary;
  warnings: string[];
  capability_status: CapabilityStatus;
}

export interface BarEdit {
  bar_index: number;
  start_seconds: number;
  end_seconds: number;
}

export interface CanonicalState {
  tempo_map: TempoMap;
  rhythm_events: RhythmEvent[];
  bar_edits: BarEdit[];
  selected_quantization_profile_id?: string | null;
  notes: string;
}

export interface UIState {
  zoom: number;
  selected_event_id?: string | null;
  show_confidence_overlay: boolean;
  notation_measures_per_row: number;
  scroll_seconds: number;
}

export interface ProjectMetadata {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  app_version: string;
}

export interface RapRhythmProject {
  metadata: ProjectMetadata;
  audio: AudioMetadata;
  lyrics_text: string;
  raw_analysis: AnalysisPayload;
  canonical_state: CanonicalState;
  ui_state: UIState;
}

export interface AnalyzePayload {
  audioFile: File;
  projectName: string;
  lyricsText: string;
  useSourceSeparation: boolean;
}
