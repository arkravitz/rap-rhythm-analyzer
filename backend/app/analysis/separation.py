from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def demucs_available() -> bool:
    return importlib.util.find_spec("demucs") is not None


def separate_vocals(audio_path: Path, output_dir: Path) -> dict[str, Path]:
    if not demucs_available():
        raise RuntimeError("Demucs is not installed.")

    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "demucs.separate",
        "--two-stems=vocals",
        "-n",
        "htdemucs",
        "-o",
        str(output_dir),
        str(audio_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        if "torchcodec" in stderr.lower():
            raise RuntimeError(
                "Demucs needs torchcodec in this environment. Install it with "
                "`pip install torchcodec` or `pip install -r backend/requirements-optional.txt`."
            ) from exc
        raise RuntimeError(
            f"Demucs separation failed: {stderr or exc.stdout or str(exc)}"
        ) from exc
    stem_root = output_dir / "htdemucs" / audio_path.stem
    vocals = stem_root / "vocals.wav"
    accompaniment = stem_root / "no_vocals.wav"
    if not vocals.exists() or not accompaniment.exists():
        raise RuntimeError("Demucs finished without producing expected stems.")
    return {"vocals": vocals, "accompaniment": accompaniment}
