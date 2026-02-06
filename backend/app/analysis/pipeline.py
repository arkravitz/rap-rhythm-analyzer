from __future__ import annotations

from pathlib import Path

import librosa
import numpy as np
from app.analysis.analytics import build_analytics
from app.analysis.asr import faster_whisper_available, transcribe_words
from app.analysis.beat_grid import detect_beat_grid
from app.analysis.lyrics import syllables_from_asr_words, tokenize_lyrics
from app.analysis.rhythm import detect_onsets, events_from_tokens
from app.analysis.sections import suggest_sections
from app.analysis.separation import demucs_available, separate_vocals
from app.config import MAX_AUDIO_DURATION_SECONDS, PROJECTS_DIR
from app.models.schema import AnalysisPayload, AnalyzeOptions, CapabilityStatus


def analyze_audio(audio_path: Path, options: AnalyzeOptions) -> AnalysisPayload:
    warnings: list[str] = []
    capability_notes: list[str] = []

    y, sr = librosa.load(audio_path, sr=22050, mono=False)
    if y.ndim == 1:
        y = np.expand_dims(y, axis=0)
    duration = float(librosa.get_duration(y=librosa.to_mono(y), sr=sr))
    if duration > MAX_AUDIO_DURATION_SECONDS:
        raise ValueError(f"Audio duration {duration:.1f}s exceeds the 6 minute limit.")

    rhythm_source_path = audio_path
    beat_source = y
    source_separation_status = "fallback"
    if options.use_source_separation:
        if demucs_available():
            try:
                stem_output = PROJECTS_DIR / "stems" / audio_path.stem
                stems = separate_vocals(audio_path, stem_output)
                rhythm_source_path = stems["vocals"]
                beat_source, _ = librosa.load(stems["accompaniment"], sr=sr, mono=False)
                source_separation_status = "enabled"
                capability_notes.append(
                    "Demucs stem separation was used for beat anchoring and vocal analysis."
                )
            except (
                Exception
            ) as exc:  # pragma: no cover - depends on local binary/runtime
                warnings.append(
                    f"Stem separation failed, falling back to full mix: {exc}"
                )
                capability_notes.append(
                    "Stem separation requested but full mix fallback was used."
                )
        else:
            warnings.append("Stem separation requested, but Demucs is not installed.")
            capability_notes.append("Install demucs to enable local stem separation.")

    rhythm_y, _ = librosa.load(rhythm_source_path, sr=sr, mono=False)
    if rhythm_y.ndim == 1:
        rhythm_y = np.expand_dims(rhythm_y, axis=0)
    y_mono = librosa.to_mono(rhythm_y)

    beat_grid = detect_beat_grid(beat_source, sr, duration)
    sections = suggest_sections(beat_source, sr, duration)
    onset_times = detect_onsets(y_mono, sr)

    source = "fallback"
    lyric_tokens = []
    if options.lyrics_text.strip():
        lyric_tokens = tokenize_lyrics(options.lyrics_text)
        source = "lyrics"
        capability_notes.append(
            "User-provided lyrics were used to build syllable labels."
        )
    else:
        asr_words = transcribe_words(str(rhythm_source_path))
        if asr_words:
            lyric_tokens = syllables_from_asr_words(asr_words)
            source = "asr"
            capability_notes.append("Local Whisper transcription provided timed words.")
        else:
            warnings.append(
                "ASR unavailable, so labels were derived from onset placeholders."
            )
            capability_notes.append(
                "Install faster-whisper and download a local model for stronger label quality."
            )

    events, quant_profiles = events_from_tokens(
        lyric_tokens,
        onset_times,
        beat_grid.tempo_map,
        y_mono,
        sr,
        source=source,
    )
    analytics = build_analytics(events, beat_grid.tempo_map)

    return AnalysisPayload(
        tempo_map=beat_grid.tempo_map,
        sections=sections,
        lyric_tokens=lyric_tokens,
        rhythm_events=events,
        quantization_profiles=quant_profiles,
        analytics=analytics,
        warnings=warnings,
        capability_status=CapabilityStatus(
            source_separation=source_separation_status,
            asr="enabled" if faster_whisper_available() else source,
            section_detection="heuristic",
            notes=capability_notes,
        ),
    )
