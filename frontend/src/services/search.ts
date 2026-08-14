import { apiClient } from "./api";
import type { SearchResponse } from "../types/search";

export async function globalSearch(q: string, page = 1, pageSize = 20): Promise<SearchResponse> {
  const { data } = await apiClient.get<SearchResponse>("/api/search", {
    params: { q, page, page_size: pageSize },
  });
  return data;
}
