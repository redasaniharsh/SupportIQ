import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeIncident } from "../services/ai";
import { ApiError } from "../types/common";
import type { AnalyzeResponse } from "../types/ai";

export const AI_STAGES = [
  "🔎 Searching historical incidents...",
  "📚 Searching knowledge base...",
  "🧠 Synthesizing evidence...",
];

interface UseAIAnalysisResult {
  data: AnalyzeResponse | null;
  loading: boolean;
  error: ApiError | null;
  stage: string;
  analyze: () => void;
}

export function useAIAnalysis(incidentId: string | undefined): UseAIAnalysisResult {
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearStageInterval = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const analyze = useCallback(() => {
    if (!incidentId) return;
    setLoading(true);
    setError(null);
    setData(null);
    setStageIndex(0);
    clearStageInterval();
    intervalRef.current = setInterval(() => {
      setStageIndex((i) => (i + 1 < AI_STAGES.length ? i + 1 : i));
    }, 1400);

    analyzeIncident(incidentId)
      .then((res) => {
        setData(res);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err : new ApiError("UNKNOWN_ERROR", "AI analysis failed"));
      })
      .finally(() => {
        clearStageInterval();
        setLoading(false);
      });
  }, [incidentId]);

  useEffect(() => () => clearStageInterval(), []);

  const stage = loading ? AI_STAGES[stageIndex] : "✅ Analysis ready";

  return { data, loading, error, stage, analyze };
}
