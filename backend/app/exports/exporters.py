from __future__ import annotations

from io import BytesIO
from typing import Iterable
from xml.etree.ElementTree import Element, SubElement, tostring

from app.models.schema import RapRhythmProject, RhythmEvent
from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def export_project_json(project: RapRhythmProject) -> bytes:
    return project.model_dump_json(indent=2).encode("utf-8")


def export_project_midi(project: RapRhythmProject) -> bytes:
    midi = MidiFile(ticks_per_beat=480)
    track = MidiTrack()
    midi.tracks.append(track)
    track.append(
        MetaMessage(
            "set_tempo", tempo=bpm2tempo(project.canonical_state.tempo_map.bpm), time=0
        )
    )
    pitch = 60
    cursor_ticks = 0
    events = sorted(
        project.canonical_state.rhythm_events,
        key=lambda item: item.quantized_start_beats,
    )
    for event in events:
        start_ticks = int(round(event.quantized_start_beats * 480))
        duration_ticks = max(60, int(round(event.quantized_duration_beats * 480)))
        track.append(
            Message(
                "note_on",
                note=pitch,
                velocity=80,
                time=max(0, start_ticks - cursor_ticks),
            )
        )
        track.append(Message("note_off", note=pitch, velocity=0, time=duration_ticks))
        cursor_ticks = start_ticks + duration_ticks
    handle = BytesIO()
    midi.save(file=handle)
    return handle.getvalue()


def _measure_events(
    events: Iterable[RhythmEvent], beats_per_bar: int
) -> dict[int, list[RhythmEvent]]:
    measures: dict[int, list[RhythmEvent]] = {}
    for event in events:
        measures.setdefault(event.bar_index + 1, []).append(event)
    for measure_events in measures.values():
        measure_events.sort(key=lambda item: item.quantized_start_beats)
    return measures


