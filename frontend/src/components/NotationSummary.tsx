import { useEffect, useMemo, useRef, useState } from "react";
import { Formatter, Renderer, Stave, StaveNote, Tuplet, Voice } from "vexflow";

import { RapRhythmProject, RhythmEvent } from "../lib/types";

const BEATS_PER_BAR = 4;

function quantizedDurationToCode(durationBeats: number): string {
  if (Math.abs(durationBeats - 1) < 0.05) {
    return "q";
  }
  if (Math.abs(durationBeats - 0.5) < 0.08) {
    return "8";
  }
  if (Math.abs(durationBeats - 0.25) < 0.05) {
    return "16";
  }
  if (Math.abs(durationBeats - 1 / 3) < 0.05) {
    return "8";
  }
  return durationBeats > 0.6 ? "q" : "8";
}

function makeNote(durationBeats: number, rest = false) {
  const note = new StaveNote({
    keys: ["c/4"],
    duration: `${quantizedDurationToCode(durationBeats)}${rest ? "r" : ""}`,
  });
  return note.setStyle(
    rest ? { fillStyle: "#64748b", strokeStyle: "#64748b" } : {},
  );
}

function splitIntoSupportedDurations(durationBeats: number): number[] {
  const pieces: number[] = [];
  let remaining = Math.max(0, durationBeats);
  const supported = [1, 0.5, 1 / 3, 0.25];
  while (remaining > 0.06) {
    const next = supported.find((value) => remaining >= value - 0.04);
    if (!next) {
      pieces.push(remaining >= 0.375 ? 0.5 : 0.25);
      break;
    }
    pieces.push(next);
    remaining -= next;
  }
  return pieces.length ? pieces : [0.25];
}

function barEvents(project: RapRhythmProject): Map<number, RhythmEvent[]> {
  const measures = new Map<number, RhythmEvent[]>();
  for (const event of project.canonical_state.rhythm_events) {
    const existing = measures.get(event.bar_index) ?? [];
    existing.push(event);
    measures.set(event.bar_index, existing);
  }
  for (const list of measures.values()) {
    list.sort((a, b) => a.quantized_start_beats - b.quantized_start_beats);
  }
  return measures;
}

export function NotationSummary({ project }: { project: RapRhythmProject }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const perRow = Math.max(1, project.ui_state.notation_measures_per_row);
  const measureMap = useMemo(() => barEvents(project), [project]);
  const [notationError, setNotationError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    containerRef.current.innerHTML = "";
    try {
      setNotationError(null);
      const totalMeasures = Math.max(
        project.canonical_state.tempo_map.bars.length,
        1,
      );
      const rows = Math.ceil(totalMeasures / perRow);
      const width = 260 * perRow;
      const height = rows * 140;
      const renderer = new Renderer(
        containerRef.current,
        Renderer.Backends.SVG,
      );
      renderer.resize(width, height);
      const context = renderer.getContext();
      context.setFont("Avenir Next, Helvetica, sans-serif", 10, "");

      for (
        let measureIndex = 0;
        measureIndex < totalMeasures;
        measureIndex += 1
      ) {
        const row = Math.floor(measureIndex / perRow);
        const column = measureIndex % perRow;
        const x = 16 + column * 246;
        const y = 12 + row * 124;
        const stave = new Stave(x, y, 220);
        if (measureIndex === 0) {
          stave.addClef("percussion").addTimeSignature("4/4");
        }
        stave.setContext(context).draw();

        const events = measureMap.get(measureIndex) ?? [];
        const notes: StaveNote[] = [];
        const tuplets: Tuplet[] = [];
        let cursor = 0;
        let runningTriplet: StaveNote[] = [];

        for (const event of events) {
          const startWithinBar = Math.max(
            0,
            event.quantized_start_beats - measureIndex * BEATS_PER_BAR,
          );
          if (startWithinBar > cursor + 0.05) {
            for (const piece of splitIntoSupportedDurations(
              startWithinBar - cursor,
            )) {
              notes.push(makeNote(piece, true));
            }
            runningTriplet = [];
          }
          const durationPieces = splitIntoSupportedDurations(
            Math.max(0.125, event.quantized_duration_beats),
          );
          for (const piece of durationPieces) {
            const note = makeNote(piece, false);
            notes.push(note);
            if (Math.abs(piece - 1 / 3) < 0.05) {
              runningTriplet.push(note);
              if (runningTriplet.length === 3) {
                tuplets.push(new Tuplet([...runningTriplet]));
                runningTriplet = [];
              }
            } else {
              runningTriplet = [];
            }
          }
          cursor = startWithinBar + event.quantized_duration_beats;
        }
        if (cursor < BEATS_PER_BAR - 0.05) {
          for (const piece of splitIntoSupportedDurations(
            BEATS_PER_BAR - cursor,
          )) {
            notes.push(makeNote(piece, true));
          }
        }

        if (notes.length === 0) {
          notes.push(makeNote(1, true));
        }

        const voice = new Voice({ numBeats: 4, beatValue: 4 });
        voice.setStrict(false);
        voice.addTickables(notes);
        new Formatter().joinVoices([voice]).format([voice], 190);
        voice.draw(context, stave);
        tuplets.forEach((tuplet) => tuplet.setContext(context).draw());
      }
    } catch (error) {
      console.error("Notation rendering failed", error);
      setNotationError(error instanceof Error ? error.message : String(error));
    }
  }, [measureMap, perRow, project]);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Secondary view</p>
          <h2>Rhythm notation summary</h2>
        </div>
        <p className="muted">
          Single-pitch staff notation reflects the edited canonical grid.
        </p>
      </div>
      {notationError && (
        <p className="muted">
          Notation view could not render this passage cleanly: {notationError}
        </p>
      )}
      <div className="notation-shell" ref={containerRef} />
    </section>
  );
}
