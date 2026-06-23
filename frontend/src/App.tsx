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

