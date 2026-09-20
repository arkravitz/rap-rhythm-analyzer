import { useEffect, useRef, useState } from "react";
import WaveSurfer from "wavesurfer.js";

interface UseWaveSurferOptions {
  audioUrl?: string;
  onTimeUpdate?: (time: number) => void;
}

export function useWaveSurfer({ audioUrl, onTimeUpdate }: UseWaveSurferOptions) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const waveSurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#7ba6f7",
      progressColor: "#f97316",
      cursorColor: "#fef3c7",
      height: 120,
      normalize: true,
      barGap: 1,
      barRadius: 2
    });
    waveSurferRef.current = waveSurfer;
    waveSurfer.on("timeupdate", (time) => onTimeUpdate?.(time));
    waveSurfer.on("play", () => setIsPlaying(true));
    waveSurfer.on("pause", () => setIsPlaying(false));
    waveSurfer.on("ready", () => setDuration(waveSurfer.getDuration()));
    return () => {
      waveSurfer.destroy();
      waveSurferRef.current = null;
    };
  }, [onTimeUpdate]);

  useEffect(() => {
    if (audioUrl && waveSurferRef.current) {
      void waveSurferRef.current.load(audioUrl);
    }
  }, [audioUrl]);

  return {
    containerRef,
    isPlaying,
    duration,
    togglePlayback: () => waveSurferRef.current?.playPause(),
    seekTo: (timeSeconds: number) => {
      const instance = waveSurferRef.current;
      if (!instance || duration === 0) {
        return;
      }
      instance.seekTo(Math.min(1, Math.max(0, timeSeconds / duration)));
    }
  };
}
