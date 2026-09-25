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

export function applyQuantization(
  project: RapRhythmProject,
  label: string,
  scope: "all" | "selected-bar"
): RapRhythmProject {
  const next = cloneProject(project);
  const selected = next.canonical_state.rhythm_events.find((event) => event.id === next.ui_state.selected_event_id);
  const selectedBar = selected?.bar_index ?? 0;
  next.canonical_state.rhythm_events = next.canonical_state.rhythm_events.map((event) => {
    if (scope === "selected-bar" && event.bar_index !== selectedBar) {
      return event;
    }
    const candidate = event.quantization_candidates.find((item) => item.label === label);
    if (!candidate) {
      return event;
    }
    return recalculateEvent(
      {
        ...event,
        subdivision_label: candidate.label,
        quantized_start_beats: candidate.start_beats,
        quantized_duration_beats: Math.max(candidate.duration_beats, event.quantized_duration_beats)
      },
      next.canonical_state.tempo_map
    );
  });
  next.canonical_state.selected_quantization_profile_id =
    next.raw_analysis.quantization_profiles.find((profile) => profile.label === label)?.id ?? null;
  return next;
}

export function updateTempo(project: RapRhythmProject, bpm: number): RapRhythmProject {
  const next = cloneProject(project);
  next.canonical_state.tempo_map.bpm = bpm;
  next.canonical_state.tempo_map = recomputeBars(next.canonical_state.tempo_map);
  next.canonical_state.rhythm_events = next.canonical_state.rhythm_events.map((event) =>
    recalculateEvent(event, next.canonical_state.tempo_map)
  );
  return next;
}

export function shiftDownbeat(project: RapRhythmProject, deltaBeats: number): RapRhythmProject {
  const next = cloneProject(project);
  next.canonical_state.tempo_map.downbeat_offset_beats =
    (next.canonical_state.tempo_map.downbeat_offset_beats + deltaBeats + BEATS_PER_BAR) % BEATS_PER_BAR;
  next.canonical_state.rhythm_events = next.canonical_state.rhythm_events.map((event) =>
    recalculateEvent(
      {
        ...event,
        quantized_start_beats: Math.max(0, event.quantized_start_beats + deltaBeats)
      },
      next.canonical_state.tempo_map
    )
  );
  return next;
}

export function addBarAtTime(project: RapRhythmProject, seconds: number): RapRhythmProject {
  const next = cloneProject(project);
  const bars = [...next.canonical_state.tempo_map.bars, {
    index: next.canonical_state.tempo_map.bars.length,
    start_seconds: seconds,
    end_seconds: seconds + beatSeconds(next.canonical_state.tempo_map) * BEATS_PER_BAR,
    beat_start_index: next.canonical_state.tempo_map.bars.length * BEATS_PER_BAR,
    beat_count: BEATS_PER_BAR,
    confidence: 0.5
  }].sort((a, b) => a.start_seconds - b.start_seconds);
  next.canonical_state.tempo_map.bars = bars.map((bar, index) => ({ ...bar, index }));
  next.canonical_state.bar_edits.push({
    bar_index: next.canonical_state.tempo_map.bars.length - 1,
    start_seconds: seconds,
    end_seconds: seconds + beatSeconds(next.canonical_state.tempo_map) * BEATS_PER_BAR
  });
  return next;
}

export function removeLastBar(project: RapRhythmProject): RapRhythmProject {
  const next = cloneProject(project);
  next.canonical_state.tempo_map.bars = next.canonical_state.tempo_map.bars.slice(0, -1);
  return next;
}

export function updateBar(project: RapRhythmProject, barIndex: number, start: number, end: number): RapRhythmProject {
  const next = cloneProject(project);
  next.canonical_state.tempo_map.bars = next.canonical_state.tempo_map.bars.map((bar) =>
    bar.index === barIndex ? { ...bar, start_seconds: start, end_seconds: Math.max(end, start + 0.1) } : bar
  );
  const existing = next.canonical_state.bar_edits.find((edit) => edit.bar_index === barIndex);
  if (existing) {
    existing.start_seconds = start;
    existing.end_seconds = end;
  } else {
    next.canonical_state.bar_edits.push({ bar_index: barIndex, start_seconds: start, end_seconds: end });
  }
  return next;
}

export function updateZoom(project: RapRhythmProject, zoom: number): RapRhythmProject {
  const next = cloneProject(project);
  next.ui_state.zoom = zoom;
  return next;
}
