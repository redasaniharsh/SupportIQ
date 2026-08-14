import { useCallback, useEffect, useState } from "react";
import { getDashboardStats } from "../services/dashboard";
import { ApiError } from "../types/common";
import type { DashboardStats } from "../types/dashboard";

interface UseDashboardStatsResult {
  data: DashboardStats | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useDashboardStats(): UseDashboardStatsResult {
  const [data, setData] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [tick, setTick] = useState(0);

  const fetchData = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getDashboardStats()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err : new ApiError("UNKNOWN_ERROR", "Failed to load dashboard"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tick]);

  useEffect(() => fetchData(), [fetchData]);

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  return { data, loading, error, refetch };
}
