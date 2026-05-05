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


def export_project_musicxml(project: RapRhythmProject) -> bytes:
    tempo_map = project.canonical_state.tempo_map
    beats_per_bar = tempo_map.time_signature_numerator
    root = Element("score-partwise", version="3.1")
    part_list = SubElement(root, "part-list")
    score_part = SubElement(part_list, "score-part", id="P1")
    SubElement(score_part, "part-name").text = "Flow"
    part = SubElement(root, "part", id="P1")

    measures = _measure_events(project.canonical_state.rhythm_events, beats_per_bar)
    divisions = 12
    total_measures = max((bar.index for bar in tempo_map.bars), default=0) + 1
    for measure_number in range(1, total_measures + 1):
        measure = SubElement(part, "measure", number=str(measure_number))
        if measure_number == 1:
            attributes = SubElement(measure, "attributes")
            SubElement(attributes, "divisions").text = str(divisions)
            time = SubElement(attributes, "time")
            SubElement(time, "beats").text = str(beats_per_bar)
            SubElement(time, "beat-type").text = str(
                tempo_map.time_signature_denominator
            )
            clef = SubElement(attributes, "clef")
            SubElement(clef, "sign").text = "percussion"
            SubElement(clef, "line").text = "2"
        if measure_number == 1:
            direction = SubElement(measure, "direction", placement="above")
            direction_type = SubElement(direction, "direction-type")
            metronome = SubElement(direction_type, "metronome")
            SubElement(metronome, "beat-unit").text = "quarter"
            SubElement(metronome, "per-minute").text = f"{tempo_map.bpm:.1f}"

        measure_events = measures.get(measure_number, [])
        cursor_divisions = 0
        measure_capacity = beats_per_bar * divisions
        for event in measure_events:
            event_start = int(
                round(
                    (event.quantized_start_beats - event.bar_index * beats_per_bar)
                    * divisions
                )
            )
            if event_start > cursor_divisions:
                rest_note = SubElement(measure, "note")
                SubElement(rest_note, "rest")
                SubElement(rest_note, "duration").text = str(
                    event_start - cursor_divisions
                )
            note = SubElement(measure, "note")
            pitch = SubElement(note, "pitch")
            SubElement(pitch, "step").text = "C"
            SubElement(pitch, "octave").text = "4"
            duration = max(1, int(round(event.quantized_duration_beats * divisions)))
            SubElement(note, "duration").text = str(duration)
            SubElement(note, "voice").text = "1"
            lyric = SubElement(note, "lyric")
            SubElement(lyric, "text").text = event.label
            cursor_divisions = min(measure_capacity, event_start + duration)
        if cursor_divisions < measure_capacity:
            rest_note = SubElement(measure, "note")
            SubElement(rest_note, "rest")
            SubElement(rest_note, "duration").text = str(
                measure_capacity - cursor_divisions
            )

    return tostring(root, encoding="utf-8", xml_declaration=True)


def export_project_pdf(project: RapRhythmProject) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 40
    cursor_y = height - margin

    pdf.setTitle(f"{project.metadata.name} Study Sheet")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, cursor_y, project.metadata.name)
    cursor_y -= 20
    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        margin,
        cursor_y,
        f"BPM {project.canonical_state.tempo_map.bpm:.1f} | {len(project.canonical_state.tempo_map.bars)} bars | {len(project.canonical_state.rhythm_events)} events",
    )
    cursor_y -= 28

    beats_per_bar = project.canonical_state.tempo_map.time_signature_numerator
    bars = _measure_events(project.canonical_state.rhythm_events, beats_per_bar)
    bar_width = width - margin * 2
    row_height = 58

    for measure_number, events in sorted(bars.items()):
        if cursor_y < margin + row_height:
            pdf.showPage()
            cursor_y = height - margin
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin, cursor_y + 34, f"Bar {measure_number}")
        line_y = cursor_y + 12
        pdf.line(margin, line_y, margin + bar_width, line_y)
        for beat in range(beats_per_bar + 1):
            x = margin + bar_width * beat / beats_per_bar
            pdf.line(x, line_y - 8, x, line_y + 8)
        for event in events:
            start_in_bar = event.quantized_start_beats - event.bar_index * beats_per_bar
            end_in_bar = start_in_bar + event.quantized_duration_beats
            x1 = margin + (start_in_bar / beats_per_bar) * bar_width
            x2 = margin + (min(end_in_bar, beats_per_bar) / beats_per_bar) * bar_width
            pdf.setFillColorRGB(0.77, 0.28 + event.accent * 0.4, 0.22)
            pdf.roundRect(x1, line_y - 6, max(10, x2 - x1), 12, 4, stroke=0, fill=1)
            pdf.setFillColorRGB(0.08, 0.08, 0.08)
            label = event.label[:12]
            label_width = stringWidth(label, "Helvetica", 8)
            pdf.setFont("Helvetica", 8)
            pdf.drawString(x1 + max(2, (x2 - x1 - label_width) / 2), line_y + 14, label)
        cursor_y -= row_height

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def export_bytes(
    project: RapRhythmProject, export_format: str
) -> tuple[bytes, str, str]:
    if export_format == "json":
        return (
            export_project_json(project),
            "application/json",
            f"{project.metadata.name}.json",
        )
    if export_format == "midi":
        return (
            export_project_midi(project),
            "audio/midi",
            f"{project.metadata.name}.mid",
        )
    if export_format == "musicxml":
        return (
            export_project_musicxml(project),
            "application/vnd.recordare.musicxml+xml",
            f"{project.metadata.name}.musicxml",
        )
    if export_format == "pdf":
        return (
            export_project_pdf(project),
            "application/pdf",
            f"{project.metadata.name}.pdf",
        )
    raise ValueError(f"Unsupported export format: {export_format}")
