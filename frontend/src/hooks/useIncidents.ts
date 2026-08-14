import { useCallback, useEffect, useState } from "react";
import { listIncidents } from "../services/incidents";
import type { PaginatedResponse } from "../types/common";
import { ApiError } from "../types/common";
import type { Incident, IncidentFilters } from "../types/incident";

interface UseIncidentsResult {
  data: PaginatedResponse<Incident> | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useIncidents(filters: IncidentFilters): UseIncidentsResult {
  const [data, setData] = useState<PaginatedResponse<Incident> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [tick, setTick] = useState(0);

  const filtersKey = JSON.stringify(filters);

  const fetchData = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listIncidents(filters)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err : new ApiError("UNKNOWN_ERROR", "Failed to load incidents"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey, tick]);

  useEffect(() => fetchData(), [fetchData]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return { data, loading, error, refetch };
}
