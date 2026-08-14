import { apiClient } from "./api";
import type { AnalyzeResponse, SimilarIncidentsResponse } from "../types/ai";

export async function analyzeIncident(incidentId: string): Promise<AnalyzeResponse> {
  const { data } = await apiClient.post<AnalyzeResponse>(`/api/incidents/${incidentId}/analyze`);
  return data;
}

export async function getSimilarIncidents(incidentId: string): Promise<SimilarIncidentsResponse> {
  const { data } = await apiClient.get<SimilarIncidentsResponse>(`/api/incidents/${incidentId}/similar`);
  return data;
}
