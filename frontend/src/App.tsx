import { useMemo, useState } from "react";

import { EventInspector } from "./components/EventInspector";
import { GridControls } from "./components/GridControls";
import { GridEditor } from "./components/GridEditor";
import { NotationSummary } from "./components/NotationSummary";
import { SaveExportPanel } from "./components/SaveExportPanel";
import { SectionOverview } from "./components/SectionOverview";
import { StatsPanel } from "./components/StatsPanel";
import { UploadPanel } from "./components/UploadPanel";
import { WaveformPanel } from "./components/WaveformPanel";
import { analyzeSong, createDemo, exportProject, loadProjectFile, saveProject } from "./lib/api";
import {
  addBarAtTime,
  addEvent,
  applyQuantization,
  deleteEvent,
  removeLastBar,
  setSelectedEvent,
  shiftDownbeat,
  updateBar,
  updateEvent,
  updateTempo,
  updateZoom
} from "./lib/project";
import { RapRhythmProject } from "./lib/types";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [projectName, setProjectName] = useState("Untitled Analysis");
  const [lyricsText, setLyricsText] = useState("");
  const [useSourceSeparation, setUseSourceSeparation] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [project, setProject] = useState<RapRhythmProject | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);

  const audioUrl = useMemo(() => {
    if (!project?.audio.asset_url) {
      return audioFile ? URL.createObjectURL(audioFile) : undefined;
    }
    return project.audio.asset_url;
  }, [audioFile, project]);

  const handleAnalyze = async () => {
    if (!audioFile) {
      return;
    }
    setBusy(true);
    setError(null);
    setSaveMessage(null);
    try {
      const analyzed = await analyzeSong({
        audioFile,
        projectName,
        lyricsText,
        useSourceSeparation
      });
      analyzed.ui_state.selected_event_id = analyzed.canonical_state.rhythm_events[0]?.id ?? null;
      analyzed.ui_state.zoom = analyzed.ui_state.zoom || 1;
      setProject(analyzed);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  };

  const handleDemo = async () => {
    setBusy(true);
    setError(null);
    setSaveMessage(null);
    try {
      const demo = await createDemo(projectName || "Demo Flow");
      demo.ui_state.selected_event_id = demo.canonical_state.rhythm_events[0]?.id ?? null;
      setProject(demo);
      setAudioFile(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  };

  const applyProjectChange = (next: RapRhythmProject | null) => {
    if (!next) {
      return;
    }
    next.metadata.updated_at = new Date().toISOString();
    setProject(next);
  };

  const handleSaveProject = async () => {
    if (!project) {
      return;
    }
    setBusy(true);
    try {
      const result = await saveProject(project);
      setSaveMessage(`Saved ${result.filename} to ${result.path}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  };

  const handleLoadProjectFile = async (file: File | null) => {
    if (!file) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const loaded = await loadProjectFile(file);
      setProject(loaded);
      setProjectName(loaded.metadata.name);
      setLyricsText(loaded.lyrics_text);
      setAudioFile(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async (format: "json" | "midi" | "musicxml" | "pdf") => {
    if (!project) {
      return;
    }
    setBusy(true);
    try {
      const blob = await exportProject(project, format);
      downloadBlob(blob, `${project.metadata.name}.${format === "midi" ? "mid" : format}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Local-first web app</p>
          <h1>Rap Rhythm Analyzer</h1>
          <p className="hero-copy">
            Study rap and sung-rap flows against beat and bar grids, correct the automatic analysis, and export the result as a reusable study sheet.
          </p>
        </div>
        <div className="hero-meta">
          <span>React + Python</span>
          <span>Fully local</span>
          <span>One-song workflow</span>
        </div>
      </header>

      <section className="layout-top">
        <UploadPanel
          projectName={projectName}
          lyricsText={lyricsText}
          useSourceSeparation={useSourceSeparation}
          audioFile={audioFile}
          busy={busy}
          onProjectNameChange={setProjectName}
          onLyricsChange={setLyricsText}
          onSourceSeparationChange={setUseSourceSeparation}
          onAudioFileChange={setAudioFile}
          onAnalyze={handleAnalyze}
          onDemo={handleDemo}
        />
        <div className="stack">
          <WaveformPanel audioUrl={audioUrl} currentTime={currentTime} onTimeUpdate={setCurrentTime} />
          {project && (
            <SaveExportPanel
              busy={busy}
              saveMessage={saveMessage}
              onSaveProject={handleSaveProject}
              onLoadProjectFile={handleLoadProjectFile}
              onExport={handleExport}
            />
          )}
        </div>
      </section>

      {error && <div className="error-banner">{error}</div>}

      {project ? (
        <>
          <section className="layout-main">
            <div className="stack">
              <GridControls
                project={project}
                currentTime={currentTime}
                onTempoChange={(bpm) => applyProjectChange(updateTempo(project, bpm))}
                onShiftDownbeat={(delta) => applyProjectChange(shiftDownbeat(project, delta))}
                onApplyQuantization={(label, scope) => applyProjectChange(applyQuantization(project, label, scope))}
                onAddBarAtTime={(seconds) => applyProjectChange(addBarAtTime(project, seconds))}
                onRemoveLastBar={() => applyProjectChange(removeLastBar(project))}
                onUpdateBar={(barIndex, start, end) => applyProjectChange(updateBar(project, barIndex, start, end))}
                onZoomChange={(zoom) => applyProjectChange(updateZoom(project, zoom))}
              />
              <GridEditor
                project={project}
                currentTime={currentTime}
                onSelectEvent={(eventId) => applyProjectChange(setSelectedEvent(project, eventId))}
                onUpdateEvent={(eventId, patch) => applyProjectChange(updateEvent(project, eventId, patch))}
              />
              <NotationSummary project={project} />
            </div>
            <div className="stack">
              <EventInspector
                project={project}
                currentTime={currentTime}
                onUpdateEvent={(eventId, patch) => applyProjectChange(updateEvent(project, eventId, patch))}
                onDeleteEvent={(eventId) => applyProjectChange(deleteEvent(project, eventId))}
                onAddEvent={(atBeats) => applyProjectChange(addEvent(project, atBeats))}
              />
              <SectionOverview project={project} />
              <StatsPanel project={project} />
            </div>
          </section>
        </>
      ) : (
        <section className="empty-state">
          <h2>No project loaded yet</h2>
          <p>Import a song to analyze it or start with the built-in demo to inspect the editor and export flow.</p>
        </section>
      )}
    </main>
  );
}
