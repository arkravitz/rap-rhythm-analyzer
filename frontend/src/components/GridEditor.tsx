import { useEffect, useMemo, useRef, useState } from "react";

import { RapRhythmProject, RhythmEvent } from "../lib/types";

type DragMode = "move" | "resize";

interface GridEditorProps {
  project: RapRhythmProject;
  currentTime: number;
  onSelectEvent: (eventId: string) => void;
  onUpdateEvent: (eventId: string, patch: Partial<RhythmEvent>) => void;
}

interface DragState {
  eventId: string;
  mode: DragMode;
  originX: number;
  originalStart: number;
  originalDuration: number;
}

const BEATS_PER_BAR = 4;

export function GridEditor({ project, currentTime, onSelectEvent, onUpdateEvent }: GridEditorProps) {
  const editorRef = useRef<HTMLDivElement | null>(null);
  const [dragState, setDragState] = useState<DragState | null>(null);
  const events = useMemo(
    () => [...project.canonical_state.rhythm_events].sort((a, b) => a.quantized_start_beats - b.quantized_start_beats),
    [project.canonical_state.rhythm_events]
  );
  const totalBars = Math.max(project.canonical_state.tempo_map.bars.length, 1);
  const beatWidth = 56 * project.ui_state.zoom;
  const width = totalBars * BEATS_PER_BAR * beatWidth;
  const height = 220;

  useEffect(() => {
    if (!dragState) {
      return;
    }
    const handleMove = (event: PointerEvent) => {
      const deltaBeats = (event.clientX - dragState.originX) / beatWidth;
      if (dragState.mode === "move") {
        onUpdateEvent(dragState.eventId, {
          quantized_start_beats: Math.max(0, dragState.originalStart + deltaBeats)
        });
      } else {
        onUpdateEvent(dragState.eventId, {
          quantized_duration_beats: Math.max(0.125, dragState.originalDuration + deltaBeats)
        });
      }
    };
    const handleUp = () => setDragState(null);
    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp, { once: true });
    return () => {
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };
  }, [beatWidth, dragState, onUpdateEvent]);

  const playheadX = (currentTime / (60 / project.canonical_state.tempo_map.bpm)) * beatWidth;

  return (
    <section className="panel panel-grid">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Primary editor</p>
          <h2>Rhythm grid</h2>
        </div>
        <p className="muted">Drag a block to move it. Drag its right edge to change duration.</p>
      </div>
      <div className="grid-scroll" ref={editorRef}>
        <svg width={width} height={height} role="img" aria-label="Editable rhythm grid">
          <rect x={0} y={0} width={width} height={height} fill="#111827" rx={16} />
          {Array.from({ length: totalBars * BEATS_PER_BAR * 4 + 1 }, (_, index) => {
            const x = (index * beatWidth) / 4;
            const isBar = index % (BEATS_PER_BAR * 4) === 0;
            const isBeat = index % 4 === 0;
            return (
              <line
                key={index}
                x1={x}
                x2={x}
                y1={24}
                y2={height - 20}
                stroke={isBar ? "#f59e0b" : isBeat ? "#60a5fa" : "#334155"}
                strokeWidth={isBar ? 2 : 1}
                opacity={isBar ? 0.7 : isBeat ? 0.55 : 0.35}
              />
            );
          })}
          {project.canonical_state.tempo_map.bars.map((bar) => (
            <text key={bar.index} x={bar.index * BEATS_PER_BAR * beatWidth + 8} y={18} fill="#fef3c7" fontSize={12}>
              {bar.index + 1}
            </text>
          ))}
          <line x1={playheadX} x2={playheadX} y1={12} y2={height - 10} stroke="#fef08a" strokeWidth={2} />
          {events.map((event, index) => {
            const x = event.quantized_start_beats * beatWidth;
            const y = 46 + (index % 6) * 24;
            const blockWidth = Math.max(12, event.quantized_duration_beats * beatWidth);
            const isSelected = event.id === project.ui_state.selected_event_id;
            const accentColor = `rgba(${Math.round(170 + event.accent * 60)}, ${Math.round(
              70 + event.accent * 80
            )}, 44, ${event.low_confidence && project.ui_state.show_confidence_overlay ? 0.55 : 0.92})`;
            return (
              <g key={event.id}>
                <rect
                  x={x}
                  y={y}
                  width={blockWidth}
                  height={18}
                  rx={6}
                  fill={accentColor}
                  stroke={isSelected ? "#fef3c7" : event.low_confidence ? "#ef4444" : "#1f2937"}
                  strokeWidth={isSelected ? 2 : 1}
                  onPointerDown={(pointerEvent) => {
                    onSelectEvent(event.id);
                    const bounds = (pointerEvent.target as SVGRectElement).getBoundingClientRect();
                    const mode: DragMode = pointerEvent.clientX > bounds.right - 10 ? "resize" : "move";
                    setDragState({
                      eventId: event.id,
                      mode,
                      originX: pointerEvent.clientX,
                      originalStart: event.quantized_start_beats,
                      originalDuration: event.quantized_duration_beats
                    });
                  }}
                />
                <text x={x + 6} y={y + 13} fill="#fff7ed" fontSize={10} pointerEvents="none">
                  {event.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
