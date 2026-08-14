import { useNavigate } from "react-router-dom";
import type { EvidenceRef } from "../types/ai";

export default function EvidenceChips({ evidenceIds, evidence }: { evidenceIds: string[]; evidence: EvidenceRef[] }) {
  const navigate = useNavigate();
  if (!evidenceIds || evidenceIds.length === 0) return null;

  function goTo(ref: EvidenceRef | undefined, fallbackId: string) {
    if (!ref) return;
    if (ref.document_type === "knowledge") {
      navigate(`/knowledge?article=${encodeURIComponent(ref.document_id)}`);
    } else {
      navigate(`/incidents/${encodeURIComponent(ref.document_id)}`);
    }
    void fallbackId;
  }

  return (
    <div>
      {evidenceIds.map((id) => {
        const ref = evidence.find((e) => e.evidence_id === id);
        const label = ref?.title || ref?.document_id || id;
        const icon = ref?.document_type === "knowledge" ? "📚" : "🎫";
        return (
          <button
            key={id}
            type="button"
            className="evidence-chip"
            onClick={() => goTo(ref, id)}
            title={`Evidence ${id}`}
            disabled={!ref}
          >
            <span aria-hidden="true">{icon}</span> {label}
          </button>
        );
      })}
    </div>
  );
}
