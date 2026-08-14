import type { IncidentStatus } from "../types/incident";

const STATUS_META: Record<IncidentStatus, { emoji: string; label: string; className: string }> = {
  open: { emoji: "🆕", label: "Open", className: "badge-status-open" },
  in_progress: { emoji: "🟡", label: "In Progress", className: "badge-status-progress" },
  pending: { emoji: "⏳", label: "Pending", className: "badge-status-pending" },
  resolved: { emoji: "✅", label: "Resolved", className: "badge-status-resolved" },
  closed: { emoji: "🔒", label: "Closed", className: "badge-status-closed" },
};

export default function StatusBadge({ status }: { status: IncidentStatus }) {
  const meta = STATUS_META[status] ?? STATUS_META.open;
  return (
    <span className={`badge ${meta.className}`}>
      <span aria-hidden="true">{meta.emoji}</span> {meta.label}
    </span>
  );
}
