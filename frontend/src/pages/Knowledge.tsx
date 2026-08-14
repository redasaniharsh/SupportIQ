import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useKnowledge } from "../hooks/useKnowledge";
import { StateGate } from "../components/StateViews";
import { getKnowledgeArticle } from "../services/knowledge";
import { ApiError } from "../types/common";
import type { KnowledgeArticle } from "../types/knowledge";
import { formatDateShort } from "../utils/format";

function ArticleDetail({ articleId, onClose }: { articleId: string; onClose: () => void }) {
  const [article, setArticle] = useState<KnowledgeArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getKnowledgeArticle(articleId)
      .then((res) => {
        if (!cancelled) setArticle(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load article.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [articleId]);

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="article-modal-title" onClick={onClose}>
      <div className="modal-box" style={{ maxWidth: 720, maxHeight: "85vh", overflowY: "auto" }} onClick={(e) => e.stopPropagation()}>
        <StateGate loading={loading} error={error}>
          {article && (
            <>
              <div className="page-header" style={{ marginBottom: "var(--space-3)" }}>
                <h2 id="article-modal-title" style={{ margin: 0 }}>
                  📚 {article.title}
                </h2>
                <button type="button" className="icon-btn" aria-label="Close article" onClick={onClose}>
                  ✕
                </button>
              </div>
              <p className="kb-meta">
                {article.category}
                {article.service ? ` · ${article.service}` : ""} · updated {formatDateShort(article.updated_at)} · v
                {article.version}
              </p>

              {article.symptoms.length > 0 && (
                <>
                  <h3 className="section-title">🩺 Symptoms</h3>
                  <ul className="article-list">
                    {article.symptoms.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </>
              )}
              {article.root_causes.length > 0 && (
                <>
                  <h3 className="section-title">🧠 Root Causes</h3>
                  <ul className="article-list">
                    {article.root_causes.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </>
              )}
              {article.troubleshooting_steps.length > 0 && (
                <>
                  <h3 className="section-title">🔧 Troubleshooting Steps</h3>
                  <ol className="article-list">
                    {article.troubleshooting_steps.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ol>
                </>
              )}
              <h3 className="section-title">✅ Resolution</h3>
              <p>{article.resolution}</p>

              {article.escalation_conditions.length > 0 && (
                <>
                  <h3 className="section-title">🚨 Escalation Conditions</h3>
                  <ul className="article-list">
                    {article.escalation_conditions.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </>
              )}
            </>
          )}
        </StateGate>
      </div>
    </div>
  );
}

export default function Knowledge() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get("q") ?? "");
  const search = searchParams.get("q") ?? undefined;
  const openArticleId = searchParams.get("article");

  const { data, loading, error, refetch } = useKnowledge({ page: 1, page_size: 40, search });

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const next = new URLSearchParams(searchParams);
    if (searchInput) next.set("q", searchInput);
    else next.delete("q");
    setSearchParams(next);
  }

  function openArticle(id: string) {
    const next = new URLSearchParams(searchParams);
    next.set("article", id);
    setSearchParams(next);
  }

  function closeArticle() {
    const next = new URLSearchParams(searchParams);
    next.delete("article");
    setSearchParams(next);
  }

  const items = data?.items ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>📚 Knowledge Base</h1>
          <p className="page-subtitle">{data ? `${data.total} articles` : "Troubleshooting articles and playbooks"}</p>
        </div>
      </div>

      <form className="filters-bar" onSubmit={onSubmit}>
        <div className="form-field" style={{ minWidth: 260 }}>
          <label htmlFor="kb-search">Search</label>
          <input
            id="kb-search"
            type="search"
            placeholder="Search articles..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-secondary">
          Search
        </button>
      </form>

      <StateGate
        loading={loading}
        error={error?.message ?? null}
        onRetry={refetch}
        isEmpty={items.length === 0}
        emptyMessage="📭 No knowledge articles found."
      >
        <div className="kb-grid">
          {items.map((article) => (
            <button
              type="button"
              key={article.article_id}
              className="kb-card"
              onClick={() => openArticle(article.article_id)}
              style={{ textAlign: "left", cursor: "pointer" }}
            >
              <div className="kb-meta">{article.category}</div>
              <h3>📚 {article.title}</h3>
              <div className="kb-meta">Updated {formatDateShort(article.updated_at)}</div>
            </button>
          ))}
        </div>
      </StateGate>

      {openArticleId && <ArticleDetail articleId={openArticleId} onClose={closeArticle} />}
    </div>
  );
}
