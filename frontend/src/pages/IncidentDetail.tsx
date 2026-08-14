import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { useIncident } from "../hooks/useIncident";
import { StateGate } from "../components/StateViews";
import PriorityBadge from "../components/PriorityBadge";
import StatusBadge from "../components/StatusBadge";
import ResolveModal from "../components/ResolveModal";
import AICopilotPanel from "../components/AICopilotPanel";
import { createComment, resolveIncident } from "../services/incidents";
import { ApiError } from "../types/common";
import { formatDate } from "../utils/format";
import type { IncidentResolveInput } from "../types/incident";

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const { incident, comments, loading, error, refetch } = useIncident(id);
  const [commentBody, setCommentBody] = useState("");
  const [commentAuthor, setCommentAuthor] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [commentError, setCommentError] = useState<string | null>(null);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveSubmitting, setResolveSubmitting] = useState(false);
  const [resolveError, setResolveError] = useState<string | null>(null);

  async function onAddComment(e: FormEvent) {
    e.preventDefault();
    if (!id || !commentBody.trim()) return;
    setCommentSubmitting(true);
    setCommentError(null);
    try {
      await createComment(id, { body: commentBody.trim(), author: commentAuthor.trim() || undefined });
      setCommentBody("");
      refetch();
    } catch (err) {
      setCommentError(err instanceof ApiError ? err.message : "Failed to add comment.");
    } finally {
      setCommentSubmitting(false);
    }
  }

  async function onResolve(input: IncidentResolveInput) {
    if (!id) return;
    setResolveSubmitting(true);
    setResolveError(null);
    try {
      await resolveIncident(id, input);
      setShowResolveModal(false);
      refetch();
    } catch (err) {
      setResolveError(err instanceof ApiError ? err.message : "Failed to resolve incident.");
    } finally {
      setResolveSubmitting(false);
    }
  }

  return (
    <div>
      <StateGate loading={loading} error={error?.message ?? null} onRetry={refetch}>
        {incident && (
          <>
            <div className="page-header">
              <div>
                <h1>
                  {incident.incident_id} — {incident.title}
                </h1>
                <p className="page-subtitle">
                  <PriorityBadge priority={incident.priority} /> <StatusBadge status={incident.status} />
                </p>
              </div>
              {incident.status !== "resolved" && incident.status !== "closed" && (
                <button type="button" className="btn btn-primary" onClick={() => setShowResolveModal(true)}>
                  ✅ Resolve Incident
                </button>
              )}
            </div>

            <div className="detail-grid">
              <div>
                <div className="card">
                  <h3 className="section-title">📋 Details</h3>
                  <p>{incident.description}</p>

                  <div className="fact-grid">
                    <div className="fact-item">
                      <div className="fact-label">Category</div>
                      <div className="fact-value">{incident.category?.name ?? "—"}</div>
                    </div>
                    <div className="fact-item">
                      <div className="fact-label">Service</div>
                      <div className="fact-value">{incident.category?.service ?? "—"}</div>
                    </div>
                    <div className="fact-item">
                      <div className="fact-label">Team</div>
                      <div className="fact-value">{incident.assignment?.team ?? "Unassigned"}</div>
                    </div>
                    <div className="fact-item">
                      <div className="fact-label">Assignee</div>
                      <div className="fact-value">{incident.assignment?.assignee_id ?? "Unassigned"}</div>
                    </div>
                    <div className="fact-item">
                      <div className="fact-label">AI Confidence</div>
                      <div className="fact-value">{incident.ai?.confidence ?? "Not analyzed"}</div>
                    </div>
                  </div>

                  {incident.resolution?.description && (
                    <>
                      <h3 className="section-title">✅ Resolution</h3>
                      <p>
                        <strong>Root cause:</strong> {incident.resolution.root_cause}
                      </p>
                      <p>
                        <strong>Description:</strong> {incident.resolution.description}
                      </p>
                      <p className="text-muted">
                        Resolved by {incident.resolution.resolved_by} on {formatDate(incident.resolution.resolved_at)}
                      </p>
                    </>
                  )}

                  <h3 className="section-title">🕓 Timeline</h3>
                  <ul className="timeline">
                    <li>Created {formatDate(incident.created_at)}</li>
                    <li>Last updated {formatDate(incident.updated_at)}</li>
                    {incident.resolution?.resolved_at && <li>Resolved {formatDate(incident.resolution.resolved_at)}</li>}
                  </ul>
                </div>

                <div className="card mt-4">
                  <h3 className="section-title">💬 Comments ({comments.length})</h3>
                  {comments.length === 0 && <p className="text-muted">📭 No comments yet.</p>}
                  {comments.map((c) => (
                    <div className="comment-item" key={c.comment_id}>
                      <div className="comment-meta">
                        <span>{c.author || c.author_id || "Anonymous"}</span>
                        <span>{formatDate(c.created_at)}</span>
                      </div>
                      <p style={{ margin: 0 }}>{c.body}</p>
                    </div>
                  ))}

                  <form onSubmit={onAddComment} className="mt-4">
                    <div className="form-row">
                      <div className="form-field">
                        <label htmlFor="comment-author">Your name (optional)</label>
                        <input
                          id="comment-author"
                          type="text"
                          value={commentAuthor}
                          onChange={(e) => setCommentAuthor(e.target.value)}
                        />
                      </div>
                    </div>
                    <div className="form-field">
                      <label htmlFor="comment-body">Add a comment</label>
                      <textarea
                        id="comment-body"
                        value={commentBody}
                        onChange={(e) => setCommentBody(e.target.value)}
                        placeholder="Add an update..."
                        required
                      />
                    </div>
                    {commentError && <p className="field-error" role="alert">⚠️ {commentError}</p>}
                    <button type="submit" className="btn btn-secondary" disabled={commentSubmitting || !commentBody.trim()}>
                      {commentSubmitting ? "Posting..." : "Post Comment"}
                    </button>
                  </form>
                </div>
              </div>

              <div>
                <AICopilotPanel incidentId={incident.incident_id} />
              </div>
            </div>
          </>
        )}
      </StateGate>

      {showResolveModal && (
        <ResolveModal
          onClose={() => setShowResolveModal(false)}
          onSubmit={onResolve}
          submitting={resolveSubmitting}
          errorMessage={resolveError}
        />
      )}
    </div>
  );
}
