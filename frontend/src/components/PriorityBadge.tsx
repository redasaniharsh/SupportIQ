import type { Priority } from "../types/incident";

const PRIORITY_META: Record<Priority, { emoji: string; label: string; className: string }> = {
  P1: { emoji: "🔴", label: "P1 - Critical", className: "badge-p1" },
  P2: { emoji: "🟠", label: "P2 - High", className: "badge-p2" },
  P3: { emoji: "🟡", label: "P3 - Medium", className: "badge-p3" },
  P4: { emoji: "🟢", label: "P4 - Low", className: "badge-p4" },
};

export default function PriorityBadge({ priority }: { priority: Priority }) {
  const meta = PRIORITY_META[priority] ?? PRIORITY_META.P3;
  return (
    <span className={`badge ${meta.className}`} title={meta.label}>
      <span aria-hidden="true">{meta.emoji}</span> {priority}
    </span>
  );
}
