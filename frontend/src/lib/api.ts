import { AnalyzePayload, RapRhythmProject } from "./types";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function analyzeSong(payload: AnalyzePayload): Promise<RapRhythmProject> {
  const formData = new FormData();
  formData.append("audio_file", payload.audioFile);
  formData.append("project_name", payload.projectName);
  formData.append("lyrics_text", payload.lyricsText);
  formData.append("use_source_separation", String(payload.useSourceSeparation));
  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData
  });
  return handleResponse<RapRhythmProject>(response);
}

export async function createDemo(projectName: string): Promise<RapRhythmProject> {
  const response = await fetch("/api/demo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_name: projectName })
  });
  return handleResponse<RapRhythmProject>(response);
}

export async function saveProject(project: RapRhythmProject): Promise<{ path: string; filename: string }> {
  const response = await fetch("/api/projects/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project })
  });
  return handleResponse(response);
}

export async function loadProjectFile(file: File): Promise<RapRhythmProject> {
  const formData = new FormData();
  formData.append("project_file", file);
  const response = await fetch("/api/projects/load", {
    method: "POST",
    body: formData
  });
  return handleResponse<RapRhythmProject>(response);
}

export async function exportProject(project: RapRhythmProject, format: "json" | "midi" | "musicxml" | "pdf"): Promise<Blob> {
  const response = await fetch(`/api/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(project)
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return await response.blob();
}
