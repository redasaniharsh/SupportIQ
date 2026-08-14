import { useCallback, useEffect, useState } from "react";
import { listKnowledgeArticles } from "../services/knowledge";
import type { PaginatedResponse } from "../types/common";
import { ApiError } from "../types/common";
import type { KnowledgeArticle, KnowledgeFilters } from "../types/knowledge";

interface UseKnowledgeResult {
  data: PaginatedResponse<KnowledgeArticle> | null;
  loading: boolean;
  error: ApiError | null;
  refetch: () => void;
}

export function useKnowledge(filters: KnowledgeFilters): UseKnowledgeResult {
  const [data, setData] = useState<PaginatedResponse<KnowledgeArticle> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [tick, setTick] = useState(0);

  const filtersKey = JSON.stringify(filters);

  const fetchData = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listKnowledgeArticles(filters)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof ApiError ? err : new ApiError("UNKNOWN_ERROR", "Failed to load knowledge base"));
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
