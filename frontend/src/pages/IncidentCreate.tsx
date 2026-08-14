import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createIncident } from "../services/incidents";
import { ApiError } from "../types/common";
import { CATEGORY_OPTIONS, PRIORITY_OPTIONS, TEAM_OPTIONS } from "../constants";
import type { Priority } from "../types/incident";

export default function IncidentCreate() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState<Priority | "">("");
  const [team, setTeam] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (title.trim().length < 3) {
      setError("Title must be at least 3 characters.");
      return;
    }
    if (!description.trim()) {
      setError("Description is required.");
      return;
    }
    setSubmitting(true);
    try {
      const created = await createIncident({
        title: title.trim(),
        description: description.trim(),
        category: { name: category || "General" },
        priority: priority || undefined,
        assignment: team ? { team } : undefined,
      });
      navigate(`/incidents/${created.incident_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create incident.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>+ New Incident</h1>
          <p className="page-subtitle">Report a new technical issue for triage.</p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 720 }}>
        <p className="hint-note">AI will analyze this incident after creation.</p>

        <form onSubmit={onSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="title">Title *</label>
            <input
              id="title"
              type="text"
              required
              minLength={3}
              maxLength={300}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. VPN connection failure after password reset"
            />
          </div>

          <div className="form-field">
            <label htmlFor="description">Description *</label>
            <textarea
              id="description"
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the symptoms, when it started, and any error messages..."
            />
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="category">Category (optional)</label>
              <select id="category" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">General (default)</option>
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="priority">Priority (optional)</label>
              <select id="priority" value={priority} onChange={(e) => setPriority(e.target.value as Priority | "")}>
                <option value="">P3 (default)</option>
                {PRIORITY_OPTIONS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="team">Team (optional)</label>
              <select id="team" value={team} onChange={(e) => setTeam(e.target.value)}>
                <option value="">Unassigned</option>
                {TEAM_OPTIONS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="field-error" role="alert">{error}</p>}

          <div className="modal-actions" style={{ justifyContent: "flex-start" }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Creating..." : "Create Incident"}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)} disabled={submitting}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
