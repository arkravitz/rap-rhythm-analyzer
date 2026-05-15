from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import ASSETS_DIR, PROJECTS_DIR
from app.models.schema import RapRhythmProject
from fastapi import UploadFile


def copy_audio_upload(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "audio.wav").suffix or ".wav"
    filename = f"{uuid4().hex}{suffix.lower()}"
    destination = ASSETS_DIR / filename
    with destination.open("wb") as target:
        shutil.copyfileobj(upload.file, target)
    return destination


def save_project_file(project: RapRhythmProject, save_as: str | None = None) -> Path:
    slug = (save_as or project.metadata.name).strip().replace(" ", "_").lower()
    filename = f"{slug or 'project'}_{project.metadata.id}.json"
    path = PROJECTS_DIR / filename
    payload = project.model_copy(
        update={
            "metadata": project.metadata.model_copy(
                update={"updated_at": datetime.now(timezone.utc)}
            )
        }
    )
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_project_file(path: Path) -> RapRhythmProject:
    return RapRhythmProject.model_validate_json(path.read_text(encoding="utf-8"))


def save_uploaded_project(upload: UploadFile) -> RapRhythmProject:
    raw = upload.file.read()
    return RapRhythmProject.model_validate_json(raw)


def list_saved_projects() -> list[Path]:
    return sorted(PROJECTS_DIR.glob("*.json"))
