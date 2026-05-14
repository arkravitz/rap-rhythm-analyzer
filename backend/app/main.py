from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.analysis.pipeline import analyze_audio
from app.config import (
    ASSETS_DIR,
    DATA_DIR,
    MAX_AUDIO_DURATION_SECONDS,
    ensure_directories,
)
from app.exports.exporters import export_bytes
from app.models.schema import (
    AnalyzeOptions,
    DemoRequest,
    ProjectFileReference,
    RapRhythmProject,
    SaveProjectRequest,
)
from app.services.audio import read_audio_metadata
from app.services.storage import (
    copy_audio_upload,
    list_saved_projects,
    save_project_file,
    save_uploaded_project,
)

ensure_directories()
app = FastAPI(title="Rap Rhythm Analyzer", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


def _project_from_analysis(
    project_name: str, audio_metadata, lyrics_text: str, analysis
) -> RapRhythmProject:
    from app.models.schema import CanonicalState, ProjectMetadata

    chosen_profile = (
        analysis.quantization_profiles[0].id if analysis.quantization_profiles else None
    )
    return RapRhythmProject(
        metadata=ProjectMetadata(name=project_name),
        audio=audio_metadata,
        lyrics_text=lyrics_text,
        raw_analysis=analysis,
        canonical_state=CanonicalState(
            tempo_map=analysis.tempo_map,
            rhythm_events=analysis.rhythm_events,
            selected_quantization_profile_id=chosen_profile,
        ),
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=RapRhythmProject)
async def analyze_endpoint(
    audio_file: UploadFile = File(...),
    project_name: str = Form("Untitled Analysis"),
    lyrics_text: str = Form(""),
    use_source_separation: bool = Form(False),
) -> RapRhythmProject:
    audio_path = copy_audio_upload(audio_file)
    asset_url = f"/assets/{audio_path.name}"
    try:
        audio_metadata = read_audio_metadata(
            audio_path, asset_url, audio_file.filename or audio_path.name
        )
        if audio_metadata.duration_seconds > MAX_AUDIO_DURATION_SECONDS:
            raise HTTPException(
                status_code=400, detail="Audio exceeds the 6 minute limit."
            )
        analysis = analyze_audio(
            audio_path,
            AnalyzeOptions(
                project_name=project_name,
                lyrics_text=lyrics_text,
                use_source_separation=use_source_separation,
            ),
        )
        return _project_from_analysis(
            project_name, audio_metadata, lyrics_text, analysis
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/projects/save")
def save_project(request: SaveProjectRequest) -> dict[str, str]:
    path = save_project_file(request.project, request.save_as)
    return {"path": str(path), "filename": path.name}


@app.post("/api/projects/load", response_model=RapRhythmProject)
async def load_project(project_file: UploadFile = File(...)) -> RapRhythmProject:
    try:
        return save_uploaded_project(project_file)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Unable to parse project JSON: {exc}"
        ) from exc


@app.get("/api/projects")
def list_projects() -> list[ProjectFileReference]:
    references = []
    for project_path in list_saved_projects():
        stat = project_path.stat()
        references.append(
            ProjectFileReference(
                filename=project_path.name,
                path=str(project_path),
                created_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
            )
        )
    return references


@app.post("/api/export/{export_format}")
def export_project(export_format: str, project: RapRhythmProject) -> Response:
    try:
        payload, media_type, filename = export_bytes(project, export_format)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=payload, media_type=media_type, headers=headers)


@app.post("/api/demo", response_model=RapRhythmProject)
def demo_project(request: DemoRequest) -> RapRhythmProject:
    from app.models.schema import (
        AcousticFeatures,
        AnalysisPayload,
        AnalyticsSummary,
        AudioMetadata,
        Beat,
        CanonicalState,
        ProjectMetadata,
        QuantizationProfile,
        RhythmEvent,
        TempoMap,
    )

    bpm = 92.0
    beats = [
        Beat(
            index=index,
            time_seconds=index * 60.0 / bpm,
            is_downbeat=index % 4 == 0,
            confidence=0.9,
            strength=0.7,
        )
        for index in range(32)
    ]
    bars = []
    for index in range(8):
        start = index * 4 * 60.0 / bpm
        end = (index + 1) * 4 * 60.0 / bpm
        from app.models.schema import Bar

        bars.append(
            Bar(
                index=index,
                start_seconds=start,
                end_seconds=end,
                beat_start_index=index * 4,
                confidence=0.8,
            )
        )
    tempo_map = TempoMap(bpm=bpm, beats=beats, bars=bars, confidence=0.9)
    labels = [
        "back",
        "on",
        "the",
        "grid",
        "but",
        "lean",
        "past",
        "snare",
        "trip",
        "let",
        "fall",
        "in",
    ]
    events = []
    for index, label in enumerate(labels):
        start_beats = [0, 0.5, 1, 1.5, 4, 4.5, 5.25, 6, 8, 8 + 1 / 3, 8 + 2 / 3, 9.5][
            index
        ]
        duration_beats = 0.5 if index not in {8, 9, 10} else 1 / 3
        start_seconds = start_beats * 60.0 / bpm
        events.append(
            RhythmEvent(
                label=label,
                word=label,
                syllable=label,
                start_seconds=start_seconds,
                duration_seconds=duration_beats * 60.0 / bpm,
                end_seconds=start_seconds + duration_beats * 60.0 / bpm,
                free_start_beats=start_beats,
                free_duration_beats=duration_beats,
                quantized_start_beats=start_beats,
                quantized_duration_beats=duration_beats,
                bar_index=int(start_beats // 4),
                beat_index_within_bar=start_beats % 4,
                subdivision_label="eighth-triplet" if index in {8, 9, 10} else "eighth",
                accent=0.5 + (0.35 if start_beats % 1 == 0 else 0.0),
                stress=0.5,
                confidence=0.88,
                source="fallback",
                acoustic_features=AcousticFeatures(
                    onset_strength=0.5, rms=0.2, spectral_centroid=1800
                ),
            )
        )
    analysis = AnalysisPayload(
        tempo_map=tempo_map,
        rhythm_events=events,
        quantization_profiles=[
            QuantizationProfile(
                label="eighth",
                subdivision_per_beat=2,
                average_error_seconds=0.04,
                confidence=0.8,
            ),
            QuantizationProfile(
                label="eighth-triplet",
                subdivision_per_beat=3,
                supports_triplets=True,
                average_error_seconds=0.03,
                confidence=0.84,
            ),
        ],
        analytics=AnalyticsSummary(
            syllables_per_beat=1.5,
            syllables_per_bar=6.0,
            dominant_subdivision="eighth",
            triplet_density=0.25,
            syncopation_estimate=0.33,
            accent_pattern_by_bar=[[0.85, 0.45, 0.7], [0.8, 0.55, 0.6]],
        ),
        warnings=["Demo project generated locally without audio."],
    )
    audio = AudioMetadata(
        original_filename="demo.wav",
        stored_filename="demo.wav",
        stored_path="",
        asset_url="",
        duration_seconds=32 * 60.0 / bpm,
        sample_rate=22050,
        channels=2,
        format="WAV",
    )
    return RapRhythmProject(
        metadata=ProjectMetadata(name=request.project_name),
        audio=audio,
        lyrics_text="back on the grid but lean past snare trip let fall in",
        raw_analysis=analysis,
        canonical_state=CanonicalState(
            tempo_map=tempo_map,
            rhythm_events=events,
            selected_quantization_profile_id=analysis.quantization_profiles[0].id,
        ),
    )
