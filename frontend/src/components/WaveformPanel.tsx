import { useMemo } from "react";

import { useWaveSurfer } from "../hooks/useWavesurfer";

interface WaveformPanelProps {
  audioUrl?: string;
  currentTime: number;
  onTimeUpdate: (time: number) => void;
}

export function WaveformPanel({ audioUrl, currentTime, onTimeUpdate }: WaveformPanelProps) {
  const { containerRef, isPlaying, duration, togglePlayback, seekTo } = useWaveSurfer({
    audioUrl,
    onTimeUpdate
  });

  const timeText = useMemo(() => {
    const format = (value: number) => `${Math.floor(value / 60)}:${`${Math.floor(value % 60)}`.padStart(2, "0")}`;
    return `${format(currentTime)} / ${format(duration)}`;
  }, [currentTime, duration]);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Playback</p>
          <h2>Waveform and transport</h2>
        </div>
        <div className="transport-row">
          <button className="button button-primary" onClick={togglePlayback} disabled={!audioUrl}>
            {isPlaying ? "Pause" : "Play"}
          </button>
          <button className="button" onClick={() => seekTo(Math.max(0, currentTime - 5))} disabled={!audioUrl}>
            -5s
          </button>
          <button className="button" onClick={() => seekTo(currentTime + 5)} disabled={!audioUrl}>
            +5s
          </button>
          <span className="time-readout">{timeText}</span>
        </div>
      </div>
      <div className="waveform-shell">
        <div ref={containerRef} />
      </div>
    </section>
  );
}
