import { ChangeEvent } from "react";

interface SaveExportPanelProps {
  busy: boolean;
  saveMessage: string | null;
  onSaveProject: () => void;
  onLoadProjectFile: (file: File | null) => void;
  onExport: (format: "json" | "midi" | "musicxml" | "pdf") => void;
}

export function SaveExportPanel({
  busy,
  saveMessage,
  onSaveProject,
  onLoadProjectFile,
  onExport
}: SaveExportPanelProps) {
  const handleProjectFile = (event: ChangeEvent<HTMLInputElement>) => {
    onLoadProjectFile(event.target.files?.[0] ?? null);
  };

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Persistence</p>
          <h2>Save, load, export</h2>
        </div>
      </div>
      <div className="button-row">
        <button className="button button-primary" onClick={onSaveProject} disabled={busy}>
          Save project JSON
        </button>
        <label className="button button-file">
          Load project JSON
          <input type="file" accept=".json" onChange={handleProjectFile} />
        </label>
      </div>
      <div className="button-row">
        <button className="button" onClick={() => onExport("json")} disabled={busy}>
          Export JSON
        </button>
        <button className="button" onClick={() => onExport("midi")} disabled={busy}>
          Export MIDI
        </button>
        <button className="button" onClick={() => onExport("musicxml")} disabled={busy}>
          Export MusicXML
        </button>
        <button className="button" onClick={() => onExport("pdf")} disabled={busy}>
          Export PDF
        </button>
      </div>
      {saveMessage && <p className="muted">{saveMessage}</p>}
    </section>
  );
}
