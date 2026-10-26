# Rap Rhythm Analyzer

Local-first web app for studying rap and sung-rap vocal rhythm from audio files. It analyzes one song at a time, estimates a beat and bar grid, derives syllable-like rhythmic events, gives you an editable piano-roll style rhythm workspace plus a secondary notation summary, and exports the edited result.

## What v1 does

- Upload one local audio file up to 6 minutes
- Optionally paste raw lyrics to improve syllable labels
- Optionally request stem separation when Demucs is installed
- Detect BPM, beats, downbeats, bar boundaries, and lightweight section suggestions
- Estimate syllable/event onsets, durations, rests, accents, subdivision candidates, and confidence flags
- Edit the canonical rhythm state in the browser
- Save/load project JSON
- Export JSON, MIDI, MusicXML, and PDF study sheets
- Run fully locally with no cloud or paid API dependency

## Architecture

### Backend

- Framework: FastAPI
- Core analysis libraries: `librosa`, `numpy`, `scipy`, `soundfile`
- Export libraries: `mido`, `reportlab`
- Optional local extras:
  - `demucs` for stem separation
  - `faster-whisper` for local ASR
  - `pyphen` for better syllabification

Main backend modules:

- [`backend/app/main.py`](backend/app/main.py): API endpoints and app setup
- [`backend/app/models/schema.py`](backend/app/models/schema.py): project/intermediate representation
- [`backend/app/analysis/pipeline.py`](backend/app/analysis/pipeline.py): orchestration
- [`backend/app/analysis/beat_grid.py`](backend/app/analysis/beat_grid.py): BPM, beat, downbeat, bar detection
- [`backend/app/analysis/rhythm.py`](backend/app/analysis/rhythm.py): onset detection, event generation, quantization suggestions
- [`backend/app/exports/exporters.py`](backend/app/exports/exporters.py): JSON, MIDI, MusicXML, PDF export

### Frontend

- Framework: React + Vite + TypeScript
- Waveform playback: `wavesurfer.js`
- Notation rendering: `vexflow`
- Primary editing surface: custom SVG rhythm grid

Main frontend modules:

- [`frontend/src/App.tsx`](frontend/src/App.tsx): top-level workflow and state
- [`frontend/src/components/GridEditor.tsx`](frontend/src/components/GridEditor.tsx): primary editable rhythm grid
- [`frontend/src/components/NotationSummary.tsx`](frontend/src/components/NotationSummary.tsx): rhythm-only staff summary
- [`frontend/src/lib/project.ts`](frontend/src/lib/project.ts): client-side canonical-state editing helpers

## Project data model

The project JSON keeps both raw and edited views:

- `metadata`
- `audio`
- `lyrics_text`
- `raw_analysis`
- `canonical_state`
- `ui_state`

Inside the analysis/canonical state, the key objects are:

- `tempo_map`
- `sections`
- `lyric_tokens`
- `rhythm_events`
- `quantization_profiles`
- `analytics`
- `bar_edits`

This is designed so later versions can add comparison features, recurring motif detection, ahead/behind-the-beat analysis, and other metrics without replacing the base file format.

## Recommended environment

- macOS
- Python `3.11` or `3.12` recommended
- Node.js `20+`
- `ffmpeg` recommended if you plan to use heavier audio workflows

Python `3.14` is not the target for the audio stack here. Some audio packages may lag support, so stick to Python `3.11` or `3.12` for the first install.

## Setup

### 1. Backend

Conda path:

```bash
conda env create -p ./.conda/rap-rhythm-analyzer -f environment.yml
conda activate ./.conda/rap-rhythm-analyzer
```

If you prefer `venv` instead:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Optional local extras:

```bash
pip install -r requirements-optional.txt
```

Run the backend:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## First-run workflow

1. Start backend and frontend.
2. Open the app in the browser.
3. Upload a song file.
4. Paste raw lyrics if you have them.
5. Enable stem separation only if you installed Demucs.
6. Run analysis.
7. Review BPM, sections, and warnings.
8. Edit rhythm blocks in the grid.
9. Fine-tune event labels, durations, bar edges, BPM, and downbeat alignment.
10. Export JSON, MIDI, MusicXML, or PDF.

## Demo path

The app includes a `Load demo` button that creates a local demo project without requiring audio. Use that first if you want to inspect the UI, edit flow blocks, and test exports before installing heavier analysis extras.

## Analysis behavior and graceful fallbacks

Default behavior without optional extras:

- Beat/bar grid uses `librosa`
- Section suggestions are heuristic
- Onsets are detected from the vocal-like signal or full mix
- If lyrics are pasted, syllable labels come from the pasted text
- If lyrics are not pasted and ASR is not installed, the app still produces rhythm events with fallback labels

Improved behavior with optional extras installed:

- `demucs`: better beat anchoring and vocal extraction
- `faster-whisper`: local word timestamps for better event labels/timing
- `pyphen`: cleaner syllable splitting
- `torchcodec`: required by current `torchaudio` save behavior used by Demucs in some environments

If you enable stem separation and see a `No module named 'torchcodec'` error, install the optional backend extras inside your app environment:

```bash
conda activate ./.conda/rap-rhythm-analyzer
pip install -r backend/requirements-optional.txt
```

## Current limitations

- Downbeat/bar inference is heuristic and assumes mostly `4/4`
- The default non-ASR path is rhythm-useful but not transcript-accurate
- The notation view is a readable summary, not a full music engraving engine
- Multi-vocal/polyphonic material is out of scope for v1
- Dense melisma is not deeply modeled yet
- Manual grid correction is present, but not yet as fast as a DAW piano roll

## Verification

Backend tests run in CI on Python 3.12:

```bash
pip install -r backend/requirements.txt pytest
PYTHONPATH=backend pytest backend/tests -q
```

The frontend builds with `npm install && npm run build` inside `frontend/`.

## Test cases and workflows

Use these to evaluate the app after install:

1. Boom bap verse with pasted lyrics: check beat/bar locking and syllable density.
2. Triplet-heavy trap verse without lyrics: check onset detection, triplet density, and manual correction flow.
3. Sung-rap hook with Demucs enabled: compare full-mix vs separated-vocal analysis.
4. Export loop: analyze, edit 3-4 events, save project JSON, reload it, then export MIDI and PDF.

## Future improvements

- Stronger downbeat/bar modeling with a dedicated local downbeat model
- Better word-to-syllable forced alignment
- Region-level re-analysis instead of full-song reruns
- Ahead/behind-the-beat timing metrics
- Motif and cadence pattern detection
- Richer notation engraving and optional PNG export
