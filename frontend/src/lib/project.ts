import { RapRhythmProject, RhythmEvent, TempoMap } from "./types";

const BEATS_PER_BAR = 4;

function beatSeconds(tempoMap: TempoMap): number {
  return 60 / Math.max(tempoMap.bpm, 1);
}

function cloneProject(project: RapRhythmProject): RapRhythmProject {
  return structuredClone(project);
}

function recomputeBars(tempoMap: TempoMap): TempoMap {
  const next = structuredClone(tempoMap);
  const barLengthSeconds = beatSeconds(next) * next.time_signature_numerator;
  next.bars = next.bars.map((bar, index) => ({
    ...bar,
    index,
    start_seconds: index * barLengthSeconds,
    end_seconds: (index + 1) * barLengthSeconds,
    beat_start_index: index * next.time_signature_numerator
  }));
  next.beats = next.beats.map((beat, index) => ({
    ...beat,
    index,
    time_seconds: index * beatSeconds(next),
    is_downbeat: index % next.time_signature_numerator === next.downbeat_offset_beats % next.time_signature_numerator
  }));
  return next;
}

function recalculateEvent(event: RhythmEvent, tempoMap: TempoMap): RhythmEvent {
  const secondsPerBeat = beatSeconds(tempoMap);
  const barIndex = Math.floor(event.quantized_start_beats / BEATS_PER_BAR);
  return {
    ...event,
    bar_index: barIndex,
    beat_index_within_bar: event.quantized_start_beats - barIndex * BEATS_PER_BAR,
    start_seconds: event.quantized_start_beats * secondsPerBeat,
    duration_seconds: Math.max(0.05, event.quantized_duration_beats * secondsPerBeat),
    end_seconds: event.quantized_start_beats * secondsPerBeat + Math.max(0.05, event.quantized_duration_beats * secondsPerBeat),
    free_start_beats: event.quantized_start_beats,
    free_duration_beats: event.quantized_duration_beats,
    low_confidence: event.confidence < 0.55
  };
}

export function setSelectedEvent(project: RapRhythmProject, eventId: string | null): RapRhythmProject {
  const next = cloneProject(project);
  next.ui_state.selected_event_id = eventId;
  return next;
}

export function updateEvent(project: RapRhythmProject, eventId: string, patch: Partial<RhythmEvent>): RapRhythmProject {
  const next = cloneProject(project);
  next.canonical_state.rhythm_events = next.canonical_state.rhythm_events.map((event) =>
    event.id === eventId ? recalculateEvent({ ...event, ...patch }, next.canonical_state.tempo_map) : event
  );
  return next;
}

export function deleteEvent(project: RapRhythmProject, eventId: string): RapRhythmProject {
  const next = cloneProject(project);
  next.canonical_state.rhythm_events = next.canonical_state.rhythm_events.filter((event) => event.id !== eventId);
  if (next.ui_state.selected_event_id === eventId) {
    next.ui_state.selected_event_id = next.canonical_state.rhythm_events[0]?.id ?? null;
  }
  return next;
}

export function addEvent(project: RapRhythmProject, atBeats: number): RapRhythmProject {
  const next = cloneProject(project);
  const secondsPerBeat = beatSeconds(next.canonical_state.tempo_map);
  const newEvent: RhythmEvent = {
    id: `evt_manual_${crypto.randomUUID().slice(0, 8)}`,
    label: "new",
    word: "new",
    syllable: "new",
    start_seconds: atBeats * secondsPerBeat,
    duration_seconds: 0.5 * secondsPerBeat,
    end_seconds: (atBeats + 0.5) * secondsPerBeat,
    free_start_beats: atBeats,
    free_duration_beats: 0.5,
    quantized_start_beats: atBeats,
    quantized_duration_beats: 0.5,
    bar_index: Math.floor(atBeats / BEATS_PER_BAR),
    beat_index_within_bar: atBeats % BEATS_PER_BAR,
    subdivision_label: "eighth",
    rest_before_beats: 0,
    accent: 0.5,
    stress: 0.3,
    confidence: 0.55,
    low_confidence: false,
    source: "fallback",
    acoustic_features: { onset_strength: 0, rms: 0, spectral_centroid: 0 },
    quantization_candidates: []
  };
  next.canonical_state.rhythm_events = [...next.canonical_state.rhythm_events, newEvent].sort(
    (a, b) => a.quantized_start_beats - b.quantized_start_beats
  );
  next.ui_state.selected_event_id = newEvent.id;
  return next;
}

