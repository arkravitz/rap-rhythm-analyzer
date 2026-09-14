import { RapRhythmProject } from "../lib/types";

export function SectionOverview({ project }: { project: RapRhythmProject }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Sections</p>
          <h2>Suggested structure</h2>
        </div>
      </div>
      <div className="section-list">
        {project.raw_analysis.sections.map((section) => (
          <article key={section.id} className="section-card">
            <strong>{section.label}</strong>
            <span>
              {section.start_seconds.toFixed(1)}s to {section.end_seconds.toFixed(1)}s
            </span>
            <span>confidence {Math.round(section.confidence * 100)}%</span>
          </article>
        ))}
      </div>
    </section>
  );
}
