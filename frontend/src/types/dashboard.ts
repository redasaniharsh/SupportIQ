export interface DashboardStats {
  total_incidents: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_category: Record<string, number>;
  by_team: Record<string, number>;
  avg_resolution_seconds?: number | null;
  knowledge_article_count: number;
  ai_analyses_count: number;
}
