import { RapRhythmProject } from "../lib/types";

interface GridControlsProps {
  project: RapRhythmProject;
  currentTime: number;
  onTempoChange: (bpm: number) => void;
  onShiftDownbeat: (delta: number) => void;
  onApplyQuantization: (label: string, scope: "all" | "selected-bar") => void;
  onAddBarAtTime: (seconds: number) => void;
  onRemoveLastBar: () => void;
  onUpdateBar: (barIndex: number, start: number, end: number) => void;
  onZoomChange: (zoom: number) => void;
}

export function GridControls({
  project,
  currentTime,
  onTempoChange,
  onShiftDownbeat,
  onApplyQuantization,
  onAddBarAtTime,
  onRemoveLastBar,
  onUpdateBar,
  onZoomChange
}: GridControlsProps) {
  const profiles = project.raw_analysis.quantization_profiles;
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Grid control</p>
          <h2>Manual correction tools</h2>
        </div>
      </div>
      <div className="inspector-grid">
        <label className="field">
          <span>BPM</span>
          <input
            type="number"
            step="0.1"
            value={project.canonical_state.tempo_map.bpm}
            onChange={(event) => onTempoChange(Number(event.target.value))}
          />
        </label>
        <label className="field">
          <span>Zoom</span>
          <input
            type="range"
            min="0.6"
            max="2.4"
            step="0.1"
            value={project.ui_state.zoom}
            onChange={(event) => onZoomChange(Number(event.target.value))}
          />
        </label>
        <label className="field">
          <span>Re-quantize</span>
          <select
            value={project.raw_analysis.quantization_profiles[0]?.label ?? "eighth"}
            onChange={(event) => onApplyQuantization(event.target.value, "all")}
          >
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.label}>
                {profile.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="button-row">
        <button className="button" onClick={() => onShiftDownbeat(-1)}>
          Shift downbeat -1 beat
        </button>
        <button className="button" onClick={() => onShiftDownbeat(1)}>
          Shift downbeat +1 beat
        </button>
        <button className="button" onClick={() => onApplyQuantization(project.raw_analysis.quantization_profiles[0]?.label ?? "eighth", "selected-bar")}>
          Quantize selected bar
        </button>
      </div>
      <div className="button-row">
        <button className="button" onClick={() => onAddBarAtTime(currentTime)}>
          Add bar at playhead
        </button>
        <button className="button button-danger" onClick={onRemoveLastBar}>
          Remove last bar
        </button>
      </div>
      <div className="bar-table">
        {project.canonical_state.tempo_map.bars.slice(0, 8).map((bar) => (
          <div className="bar-row" key={bar.index}>
            <span>Bar {bar.index + 1}</span>
            <input
              type="number"
              step="0.1"
              value={bar.start_seconds}
              onChange={(event) => onUpdateBar(bar.index, Number(event.target.value), bar.end_seconds)}
            />
            <input
              type="number"
              step="0.1"
              value={bar.end_seconds}
              onChange={(event) => onUpdateBar(bar.index, bar.start_seconds, Number(event.target.value))}
            />
          </div>
        ))}
      </div>
    </section>
  );
}
