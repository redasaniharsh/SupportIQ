import { Link } from "react-router-dom";
import { useDashboardStats } from "../hooks/useDashboardStats";
import { useIncidents } from "../hooks/useIncidents";
import { StateGate } from "../components/StateViews";
import PriorityBadge from "../components/PriorityBadge";
import StatusBadge from "../components/StatusBadge";
import type { Priority } from "../types/incident";
import { formatDateShort, titleCase } from "../utils/format";

function BreakdownBars({ title, icon, data }: { title: string; icon: string; data: Record<string, number> }) {
  const entries = Object.entries(data).filter(([key]) => key);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (entries.length === 0) {
    return (
      <div className="card">
        <h3 className="section-title">
          {icon} {title}
        </h3>
        <p className="text-muted">📭 No data yet.</p>
      </div>
    );
  }
  return (
    <div className="card">
      <h3 className="section-title">
        {icon} {title}
      </h3>
      <div className="bar-chart">
        {entries
          .sort((a, b) => b[1] - a[1])
          .map(([key, value]) => (
            <div className="bar-row" key={key}>
              <span className="bar-label">{titleCase(key)}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${(value / max) * 100}%` }} />
              </div>
              <span className="bar-count">{value}</span>
            </div>
          ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: stats, loading, error, refetch } = useDashboardStats();
  const { data: recentIncidents, loading: recentLoading } = useIncidents({ page: 1, page_size: 5 });
  const { data: resolvedIncidents, loading: resolvedLoading } = useIncidents({
    page: 1,
    page_size: 5,
    status: "resolved",
  });

  const highPriorityCount = (stats?.by_priority.P1 ?? 0) + (stats?.by_priority.P2 ?? 0);
  const inProgressCount = stats?.by_status.in_progress ?? 0;
  const pendingCount = stats?.by_status.pending ?? 0;
  const resolvedCount = (stats?.by_status.resolved ?? 0) + (stats?.by_status.closed ?? 0);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Overview of incident volume, priority, and resolution health.</p>
        </div>
      </div>

      <StateGate loading={loading} error={error?.message ?? null} onRetry={refetch}>
        {stats && (
          <>
            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-icon" aria-hidden="true">
                  🎫
                </div>
                <div className="stat-value">{stats.total_incidents}</div>
                <div className="stat-label">Total Incidents</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" aria-hidden="true">
                  🔴
                </div>
                <div className="stat-value">{highPriorityCount}</div>
                <div className="stat-label">High Priority (P1/P2)</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" aria-hidden="true">
                  🟡
                </div>
                <div className="stat-value">{inProgressCount}</div>
                <div className="stat-label">In Progress</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" aria-hidden="true">
                  ⏳
                </div>
                <div className="stat-value">{pendingCount}</div>
                <div className="stat-label">Pending</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon" aria-hidden="true">
                  ✅
                </div>
                <div className="stat-value">{resolvedCount}</div>
                <div className="stat-label">Resolved / Closed</div>
              </div>
            </div>

            <div className="dashboard-grid">
              <BreakdownBars title="By Status" icon="📊" data={stats.by_status} />
              <BreakdownBars title="By Priority" icon="🚨" data={stats.by_priority} />
              <BreakdownBars title="By Category" icon="🗂️" data={stats.by_category} />
              <BreakdownBars title="By Team" icon="👥" data={stats.by_team} />
            </div>
          </>
        )}
      </StateGate>

      <div className="dashboard-grid">
        <div className="card">
          <h3 className="section-title">🕑 Recent Incidents</h3>
          <StateGate
            loading={recentLoading}
            error={null}
            isEmpty={!!recentIncidents && recentIncidents.items.length === 0}
            emptyMessage="📭 No incidents yet."
          >
            <ul className="list-simple">
              {recentIncidents?.items.map((inc) => (
                <li key={inc.incident_id}>
                  <Link to={`/incidents/${inc.incident_id}`} className="list-simple-title">
                    {inc.incident_id} — {inc.title}
                  </Link>
                  <PriorityBadge priority={inc.priority as Priority} />
                  <StatusBadge status={inc.status} />
                </li>
              ))}
            </ul>
          </StateGate>
        </div>

        <div className="card">
          <h3 className="section-title">✅ Recently Resolved</h3>
          <StateGate
            loading={resolvedLoading}
            error={null}
            isEmpty={!!resolvedIncidents && resolvedIncidents.items.length === 0}
            emptyMessage="📭 Nothing resolved yet."
          >
            <ul className="list-simple">
              {resolvedIncidents?.items.map((inc) => (
                <li key={inc.incident_id}>
                  <Link to={`/incidents/${inc.incident_id}`} className="list-simple-title">
                    {inc.incident_id} — {inc.title}
                  </Link>
                  <span className="text-muted">{formatDateShort(inc.resolution.resolved_at)}</span>
                </li>
              ))}
            </ul>
          </StateGate>
        </div>
      </div>
    </div>
  );
}
