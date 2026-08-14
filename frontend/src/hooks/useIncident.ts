import { useCallback, useEffect, useState } from "react";
import { getIncident, listComments } from "../services/incidents";
import { ApiError } from "../types/common";
import type { Comment, Incident } from "../types/incident";

interface UseIncidentResult {
  incident: Incident | null;
  comments: Comment[];
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useIncident(incidentId: string | undefined): UseIncidentResult {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [tick, setTick] = useState(0);

  const fetchData = useCallback(() => {
    if (!incidentId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([getIncident(incidentId), listComments(incidentId)])
      .then(([incidentRes, commentsRes]) => {
        if (!cancelled) {
          setIncident(incidentRes);
          setComments(commentsRes.items);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err : new ApiError("UNKNOWN_ERROR", "Failed to load incident"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incidentId, tick]);

  useEffect(() => fetchData(), [fetchData]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return { incident, comments, loading, error, refetch };
}
