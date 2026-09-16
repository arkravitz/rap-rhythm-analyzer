import { RapRhythmProject } from "../lib/types";

export function StatsPanel({ project }: { project: RapRhythmProject }) {
  const analytics = project.raw_analysis.analytics;
  const capability = project.raw_analysis.capability_status;

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Analytics</p>
          <h2>Flow statistics</h2>
        </div>
      </div>
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">BPM</span>
          <strong>{project.canonical_state.tempo_map.bpm.toFixed(1)}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Syllables / beat</span>
          <strong>{analytics.syllables_per_beat.toFixed(2)}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Syllables / bar</span>
          <strong>{analytics.syllables_per_bar.toFixed(2)}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Dominant subdivision</span>
          <strong>{analytics.dominant_subdivision}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Triplet density</span>
          <strong>{(analytics.triplet_density * 100).toFixed(0)}%</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Syncopation</span>
          <strong>{(analytics.syncopation_estimate * 100).toFixed(0)}%</strong>
        </div>
      </div>
      <div className="list-block">
        <h3>Capabilities</h3>
        <ul>
          <li>Stem separation: {capability.source_separation}</li>
          <li>ASR: {capability.asr}</li>
          <li>Section detection: {capability.section_detection}</li>
        </ul>
      </div>
      {project.raw_analysis.warnings.length > 0 && (
        <div className="list-block warning">
          <h3>Warnings</h3>
          <ul>
            {project.raw_analysis.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
