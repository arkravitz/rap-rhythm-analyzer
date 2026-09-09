import { RapRhythmProject, RhythmEvent } from "../lib/types";

interface EventInspectorProps {
  project: RapRhythmProject;
  currentTime: number;
  onUpdateEvent: (eventId: string, patch: Partial<RhythmEvent>) => void;
  onDeleteEvent: (eventId: string) => void;
  onAddEvent: (atBeats: number) => void;
}

export function EventInspector({
  project,
  currentTime,
  onUpdateEvent,
  onDeleteEvent,
  onAddEvent
}: EventInspectorProps) {
  const selected = project.canonical_state.rhythm_events.find(
    (event) => event.id === project.ui_state.selected_event_id
  );

  if (!selected) {
    return (
      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Inspector</p>
            <h2>Event detail</h2>
          </div>
        </div>
        <p className="muted">Select a rhythm block to edit it, or add a new event at the current playhead.</p>
        <button className="button" onClick={() => onAddEvent((currentTime * project.canonical_state.tempo_map.bpm) / 60)}>
          Add event at playhead
        </button>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Inspector</p>
          <h2>Event detail</h2>
        </div>
        <span className={`confidence-pill ${selected.low_confidence ? "low" : "high"}`}>
          confidence {Math.round(selected.confidence * 100)}%
        </span>
      </div>
      <div className="inspector-grid">
        <label className="field">
          <span>Label</span>
          <input value={selected.label} onChange={(event) => onUpdateEvent(selected.id, { label: event.target.value })} />
        </label>
        <label className="field">
          <span>Start beats</span>
          <input
            type="number"
            step="0.125"
            value={selected.quantized_start_beats}
            onChange={(event) => onUpdateEvent(selected.id, { quantized_start_beats: Number(event.target.value) })}
          />
        </label>
        <label className="field">
          <span>Duration beats</span>
          <input
            type="number"
            step="0.125"
            value={selected.quantized_duration_beats}
            onChange={(event) => onUpdateEvent(selected.id, { quantized_duration_beats: Number(event.target.value) })}
          />
        </label>
        <label className="field">
          <span>Accent</span>
          <input
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={selected.accent}
            onChange={(event) => onUpdateEvent(selected.id, { accent: Number(event.target.value) })}
          />
        </label>
        <label className="field">
          <span>Confidence</span>
          <input
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={selected.confidence}
            onChange={(event) => onUpdateEvent(selected.id, { confidence: Number(event.target.value) })}
          />
        </label>
      </div>
      <p className="muted">
        Source: {selected.source} | subdivision: {selected.subdivision_label} | bar {selected.bar_index + 1}
      </p>
      <div className="button-row">
        <button className="button" onClick={() => onAddEvent(selected.quantized_start_beats + selected.quantized_duration_beats)}>
          Add after
        </button>
        <button className="button button-danger" onClick={() => onDeleteEvent(selected.id)}>
          Delete event
        </button>
      </div>
    </section>
  );
}
