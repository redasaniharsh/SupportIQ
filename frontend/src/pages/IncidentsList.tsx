import { useState } from "react";
import { Link } from "react-router-dom";
import { useIncidents } from "../hooks/useIncidents";
import { StateGate } from "../components/StateViews";
import PriorityBadge from "../components/PriorityBadge";
import StatusBadge from "../components/StatusBadge";
import { CATEGORY_OPTIONS, PRIORITY_OPTIONS, STATUS_OPTIONS } from "../constants";
import { formatDateShort, titleCase } from "../utils/format";
import type { IncidentFilters, IncidentStatus, Priority } from "../types/incident";

const PAGE_SIZE = 20;

export default function IncidentsList() {
  const [filters, setFilters] = useState<IncidentFilters>({ page: 1, page_size: PAGE_SIZE });
  const [searchInput, setSearchInput] = useState("");
  const { data, loading, error, refetch } = useIncidents(filters);

  function updateFilter<K extends keyof IncidentFilters>(key: K, value: IncidentFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  }

  function onSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    updateFilter("search", searchInput || undefined);
  }

  function goToPage(page: number) {
    setFilters((prev) => ({ ...prev, page }));
  }

  const items = data?.items ?? [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>🎫 Incidents</h1>
          <p className="page-subtitle">{data ? `${data.total} total incidents` : "Browse and triage incidents"}</p>
        </div>
        <Link to="/incidents/new" className="btn btn-primary">
          + New Incident
        </Link>
      </div>

      <form className="filters-bar" onSubmit={onSearchSubmit}>
        <div className="form-field" style={{ minWidth: 220 }}>
          <label htmlFor="incident-search">Search</label>
          <input
            id="incident-search"
            type="search"
            placeholder="Search title or description..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        <div className="form-field">
          <label htmlFor="filter-status">Status</label>
          <select
            id="filter-status"
            value={filters.status ?? ""}
            onChange={(e) => updateFilter("status", (e.target.value || undefined) as IncidentStatus | undefined)}
          >
            <option value="">All</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {titleCase(s)}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="filter-priority">Priority</label>
          <select
            id="filter-priority"
            value={filters.priority ?? ""}
            onChange={(e) => updateFilter("priority", (e.target.value || undefined) as Priority | undefined)}
          >
            <option value="">All</option>
            {PRIORITY_OPTIONS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div className="form-field">
          <label htmlFor="filter-category">Category</label>
          <select
            id="filter-category"
            value={filters.category ?? ""}
            onChange={(e) => updateFilter("category", e.target.value || undefined)}
          >
            <option value="">All</option>
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="btn btn-secondary">
          Apply Search
        </button>
      </form>

      <StateGate
        loading={loading}
        error={error?.message ?? null}
        onRetry={refetch}
        isEmpty={items.length === 0}
        emptyMessage="📭 No incidents match these filters."
      >
        <div className="incident-table-wrap">
          <table className="incident-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Team</th>
                <th>Created</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {items.map((inc) => (
                <tr key={inc.incident_id}>
                  <td>
                    <Link to={`/incidents/${inc.incident_id}`}>{inc.incident_id}</Link>
                  </td>
                  <td className="title-cell" title={inc.title}>
                    <Link to={`/incidents/${inc.incident_id}`}>{inc.title}</Link>
                  </td>
                  <td>{inc.category?.name ?? "—"}</td>
                  <td>
                    <PriorityBadge priority={inc.priority} />
                  </td>
                  <td>
                    <StatusBadge status={inc.status} />
                  </td>
                  <td>{inc.assignment?.team ?? "—"}</td>
                  <td>{formatDateShort(inc.created_at)}</td>
                  <td>{formatDateShort(inc.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data && data.total_pages > 1 && (
          <div className="pagination">
            <button
              type="button"
              className="btn btn-sm"
              disabled={data.page <= 1}
              onClick={() => goToPage(data.page - 1)}
            >
              ← Prev
            </button>
            <span>
              Page {data.page} of {data.total_pages}
            </span>
            <button
              type="button"
              className="btn btn-sm"
              disabled={data.page >= data.total_pages}
              onClick={() => goToPage(data.page + 1)}
            >
              Next →
            </button>
          </div>
        )}
      </StateGate>
    </div>
  );
}
