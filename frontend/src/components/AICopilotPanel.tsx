import { Link } from "react-router-dom";
import { useAIAnalysis } from "../hooks/useAIAnalysis";
import EvidenceChips from "./EvidenceChips";
import type { ConfidenceLevel } from "../types/ai";

const CONFIDENCE_CLASS: Record<ConfidenceLevel, string> = {
  High: "confidence-high",
  Medium: "confidence-medium",
  Low: "confidence-low",
};

export default function AICopilotPanel({ incidentId }: { incidentId: string }) {
  const { data, loading, error, stage, analyze } = useAIAnalysis(incidentId);

  return (
    <div className="card copilot-panel">
      <h2 className="section-title">AI Copilot</h2>

      {!data && !loading && !error && (
        <>
          <p className="text-muted">Get an evidence-backed analysis of this incident: probable causes, recommended actions, and similar past tickets.</p>
          <button type="button" className="btn btn-primary btn-block" onClick={analyze}>
            Analyze Incident
          </button>
        </>
      )}

      {loading && (
        <div className="state-view state-loading" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <p className="stage-text">{stage}</p>
        </div>
      )}

      {error && !loading && (
        <div className="state-view state-error" role="alert">
          <p>AI service unavailable, retry. ({error.message})</p>
          <button type="button" className="btn btn-secondary" onClick={analyze}>
            Retry Analysis
          </button>
        </div>
      )}

      {data && data.status === "ai_unavailable" && (
        <div className="state-view state-error" role="alert">
          <p>AI service unavailable, retry. {data.message}</p>
          <button type="button" className="btn btn-secondary" onClick={analyze}>
            Retry Analysis
          </button>
        </div>
      )}

      {data && data.status === "ok" && (
        <div>
          <p className="text-muted" style={{ marginTop: 0 }}>
            Model: {data.model} · {data.retrieval_count} evidence sources · {data.latency_ms}ms
          </p>

          <h3 className="section-title">Summary</h3>
          <p>{data.analysis.summary}</p>

          <h3 className="section-title">Classification</h3>
          <p>
            Category: <strong>{data.analysis.category}</strong> · Suggested Priority:{" "}
            <strong>{data.analysis.priority}</strong>
            {data.analysis.escalation_required && <span className="escalation-flag"> · Escalation Recommended</span>}
          </p>

          <h3 className="section-title">Confidence</h3>
          <p>
            {data.confidence.bucket} confidence ({Math.round(data.confidence.evidence_score * 100)}% evidence score)
            {data.confidence.model_reported ? ` · model self-reported: ${data.confidence.model_reported}` : ""}
          </p>
          <div className="confidence-bar-track">
            <div
              className={`confidence-bar-fill ${CONFIDENCE_CLASS[data.confidence.bucket]}`}
              style={{ width: `${Math.max(8, data.confidence.evidence_score * 100)}%` }}
            />
          </div>

          {data.analysis.probable_causes.length > 0 && (
            <>
              <h3 className="section-title">Probable Causes</h3>
              {data.analysis.probable_causes.map((cause, idx) => (
                <div className="cause-item" key={idx}>
                  <p style={{ marginTop: 0 }}>
                    {cause.cause} <span className="text-muted">({cause.likelihood} likelihood)</span>
                  </p>
                  <EvidenceChips evidenceIds={cause.evidence_ids} evidence={data.evidence} />
                </div>
              ))}
            </>
          )}

          {data.analysis.recommended_actions.length > 0 && (
            <>
              <h3 className="section-title">Recommended Actions</h3>
              {[...data.analysis.recommended_actions]
                .sort((a, b) => a.priority_order - b.priority_order)
                .map((action, idx) => (
                  <div className="action-item" key={idx}>
                    <p style={{ marginTop: 0 }}>
                      {action.priority_order}. {action.action}
                    </p>
                    <EvidenceChips evidenceIds={action.evidence_ids} evidence={data.evidence} />
                  </div>
                ))}
            </>
          )}

          {data.analysis.similar_incidents.length > 0 && (
            <>
              <h3 className="section-title">Similar Incidents</h3>
              {data.analysis.similar_incidents.map((sim) => (
                <div className="similar-incident-item" key={sim.incident_id}>
                  <Link to={`/incidents/${sim.incident_id}`}>{sim.incident_id}</Link>
                  <span>{sim.relationship === "duplicate" ? "Likely duplicate" : "Related"}</span>
                </div>
              ))}
            </>
          )}

          {data.analysis.knowledge_articles.length > 0 && (
            <>
              <h3 className="section-title">Knowledge Articles</h3>
              {data.analysis.knowledge_articles.map((kb) => (
                <div className="similar-incident-item" key={kb.article_id}>
                  <Link to={`/knowledge?article=${encodeURIComponent(kb.article_id)}`}>{kb.article_id}</Link>
                  <span className="text-muted">{kb.relevance ?? ""}</span>
                </div>
              ))}
            </>
          )}

          {data.analysis.uncertainties.length > 0 && (
            <>
              <h3 className="section-title">Uncertainties</h3>
              <ul className="uncertainty-list">
                {data.analysis.uncertainties.map((u, idx) => (
                  <li key={idx}>{u}</li>
                ))}
              </ul>
            </>
          )}

          <h3 className="section-title">Final Recommendation</h3>
          <p>{data.analysis.final_recommendation}</p>

          <button type="button" className="btn btn-secondary btn-block mt-4" onClick={analyze}>
            Re-run Analysis
          </button>
        </div>
      )}

      <p className="copilot-disclaimer">AI-generated assistance. Verify before applying.</p>
    </div>
  );
}
