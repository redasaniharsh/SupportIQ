import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { globalSearch } from "../services/search";
import { ApiError } from "../types/common";
import type { SearchResponse } from "../types/search";
import { StateGate } from "../components/StateViews";
import PriorityBadge from "../components/PriorityBadge";
import StatusBadge from "../components/StatusBadge";

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const [input, setInput] = useState(q);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setInput(q);
    if (!q) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    globalSearch(q)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Search failed.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [q]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim()) setSearchParams({ q: input.trim() });
  }

  const totalResults = (data?.incidents.total ?? 0) + (data?.knowledge_articles.total ?? 0);

  return (
    <div>
      <div className="page-header">
        <h1>🔎 Search</h1>
      </div>

      <form className="filters-bar" onSubmit={onSubmit}>
        <div className="form-field" style={{ minWidth: 300 }}>
          <label htmlFor="global-search-page-input">Search incidents and knowledge base</label>
          <input
            id="global-search-page-input"
            type="search"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Search everything..."
          />
        </div>
        <button type="submit" className="btn btn-primary">
          Search
        </button>
      </form>

      {!q && <p className="text-muted">Enter a search term above.</p>}

      {q && (
        <StateGate loading={loading} error={error} isEmpty={!!data && totalResults === 0} emptyMessage={`📭 No results for "${q}".`}>
          {data && (
            <>
              <div className="search-section">
                <h2 className="section-title">🔎 Incidents ({data.incidents.total})</h2>
                {data.incidents.items.length === 0 ? (
                  <p className="text-muted">No matching incidents.</p>
                ) : (
                  <ul className="list-simple">
                    {data.incidents.items.map((inc) => (
                      <li key={inc.incident_id}>
                        <Link to={`/incidents/${inc.incident_id}`} className="list-simple-title">
                          {inc.incident_id} — {inc.title}
                        </Link>
                        <PriorityBadge priority={inc.priority} />
                        <StatusBadge status={inc.status} />
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="search-section">
                <h2 className="section-title">📚 Knowledge Base ({data.knowledge_articles.total})</h2>
                {data.knowledge_articles.items.length === 0 ? (
                  <p className="text-muted">No matching articles.</p>
                ) : (
                  <ul className="list-simple">
                    {data.knowledge_articles.items.map((article) => (
                      <li key={article.article_id}>
                        <Link to={`/knowledge?article=${encodeURIComponent(article.article_id)}`} className="list-simple-title">
                          📚 {article.title}
                        </Link>
                        <span className="text-muted">{article.category}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </StateGate>
      )}
    </div>
  );
}
