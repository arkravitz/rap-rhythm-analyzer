from __future__ import annotations

from pathlib import Path

import soundfile as sf
from app.models.schema import AudioMetadata


def read_audio_metadata(
    audio_path: Path, asset_url: str, original_filename: str
) -> AudioMetadata:
    info = sf.info(str(audio_path))
    return AudioMetadata(
        original_filename=original_filename,
        stored_filename=audio_path.name,
        stored_path=str(audio_path),
        asset_url=asset_url,
        duration_seconds=float(info.duration),
        sample_rate=int(info.samplerate),
        channels=int(info.channels),
        format=info.format or audio_path.suffix.lstrip(".").upper(),
    )
