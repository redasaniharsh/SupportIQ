import { useState, type FormEvent } from "react";
import type { IncidentResolveInput } from "../types/incident";

export default function ResolveModal({
  onClose,
  onSubmit,
  submitting,
  errorMessage,
}: {
  onClose: () => void;
  onSubmit: (input: IncidentResolveInput) => void;
  submitting: boolean;
  errorMessage: string | null;
}) {
  const [rootCause, setRootCause] = useState("");
  const [resolutionDescription, setResolutionDescription] = useState("");
  const [resolvedBy, setResolvedBy] = useState("");

  const canSubmit = rootCause.trim().length >= 3 && resolutionDescription.trim().length >= 3 && resolvedBy.trim().length > 0;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit({
      root_cause: rootCause.trim(),
      resolution_description: resolutionDescription.trim(),
      resolved_by: resolvedBy.trim(),
    });
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="resolve-modal-title">
      <div className="modal-box">
        <h2 id="resolve-modal-title">✅ Resolve Incident</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="root-cause">Root Cause *</label>
            <textarea
              id="root-cause"
              value={rootCause}
              onChange={(e) => setRootCause(e.target.value)}
              placeholder="What caused this incident?"
              required
            />
          </div>
          <div className="form-field">
            <label htmlFor="resolution-description">Resolution Description *</label>
            <textarea
              id="resolution-description"
              value={resolutionDescription}
              onChange={(e) => setResolutionDescription(e.target.value)}
              placeholder="What was done to resolve it?"
              required
            />
          </div>
          <div className="form-field">
            <label htmlFor="resolved-by">Resolved By *</label>
            <input
              id="resolved-by"
              type="text"
              value={resolvedBy}
              onChange={(e) => setResolvedBy(e.target.value)}
              placeholder="Your name or agent ID"
              required
            />
          </div>
          {errorMessage && <p className="field-error" role="alert">⚠️ {errorMessage}</p>}
          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={!canSubmit || submitting}>
              {submitting ? "Resolving..." : "Resolve Incident"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
