import { ChangeEvent } from "react";

interface UploadPanelProps {
  projectName: string;
  lyricsText: string;
  useSourceSeparation: boolean;
  audioFile: File | null;
  busy: boolean;
  onProjectNameChange: (value: string) => void;
  onLyricsChange: (value: string) => void;
  onSourceSeparationChange: (value: boolean) => void;
  onAudioFileChange: (file: File | null) => void;
  onAnalyze: () => void;
  onDemo: () => void;
}

export function UploadPanel(props: UploadPanelProps) {
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    props.onAudioFileChange(event.target.files?.[0] ?? null);
  };

  return (
    <section className="panel panel-accent">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Import</p>
          <h2>Analyze one song at a time</h2>
        </div>
      </div>
      <label className="field">
        <span>Project name</span>
        <input value={props.projectName} onChange={(event) => props.onProjectNameChange(event.target.value)} />
      </label>
      <label className="field">
        <span>Audio file</span>
        <input type="file" accept=".wav,.mp3,.m4a,.flac,.ogg" onChange={handleFileChange} />
      </label>
      <label className="field">
        <span>Optional lyrics</span>
        <textarea
          rows={8}
          value={props.lyricsText}
          onChange={(event) => props.onLyricsChange(event.target.value)}
          placeholder="Paste raw lyrics here to improve syllable labels and timing."
        />
      </label>
      <label className="toggle">
        <input
          type="checkbox"
          checked={props.useSourceSeparation}
          onChange={(event) => props.onSourceSeparationChange(event.target.checked)}
        />
        <span>Use optional stem separation when available</span>
      </label>
      <div className="button-row">
        <button className="button button-primary" onClick={props.onAnalyze} disabled={!props.audioFile || props.busy}>
          {props.busy ? "Analyzing..." : "Run analysis"}
        </button>
        <button className="button" onClick={props.onDemo} disabled={props.busy}>
          Load demo
        </button>
      </div>
      <p className="muted">
        Recommended for v1: one mixed commercial track, one lead performer, up to six minutes.
      </p>
    </section>
  );
}
