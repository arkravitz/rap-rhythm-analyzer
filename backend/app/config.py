from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
ASSETS_DIR = DATA_DIR / "assets"
PROJECTS_DIR = DATA_DIR / "projects"
EXPORTS_DIR = DATA_DIR / "exports"

MAX_AUDIO_DURATION_SECONDS = 6 * 60
DEFAULT_TIME_SIGNATURE = (4, 4)
DEFAULT_BEATS_PER_BAR = 4


def ensure_directories() -> None:
    for directory in (DATA_DIR, ASSETS_DIR, PROJECTS_DIR, EXPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
