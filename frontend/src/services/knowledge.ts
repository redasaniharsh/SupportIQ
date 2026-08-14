import { apiClient } from "./api";
import type { PaginatedResponse } from "../types/common";
import type { KnowledgeArticle, KnowledgeFilters } from "../types/knowledge";

export async function listKnowledgeArticles(filters: KnowledgeFilters): Promise<PaginatedResponse<KnowledgeArticle>> {
  const params: Record<string, string | number> = {};
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params[key] = value as string | number;
    }
  });
  const { data } = await apiClient.get<PaginatedResponse<KnowledgeArticle>>("/api/knowledge", { params });
  return data;
}

export async function getKnowledgeArticle(articleId: string): Promise<KnowledgeArticle> {
  const { data } = await apiClient.get<KnowledgeArticle>(`/api/knowledge/${articleId}`);
  return data;
}
