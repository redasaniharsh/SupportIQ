import { apiClient } from "./api";
import type { PaginatedResponse } from "../types/common";
import type {
  Comment,
  CommentCreateInput,
  Incident,
  IncidentCreateInput,
  IncidentFilters,
  IncidentResolveInput,
  IncidentUpdateInput,
} from "../types/incident";

export async function listIncidents(filters: IncidentFilters): Promise<PaginatedResponse<Incident>> {
  const params: Record<string, string | number> = {};
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params[key] = value as string | number;
    }
  });
  const { data } = await apiClient.get<PaginatedResponse<Incident>>("/api/incidents", { params });
  return data;
}

export async function getIncident(incidentId: string): Promise<Incident> {
  const { data } = await apiClient.get<Incident>(`/api/incidents/${incidentId}`);
  return data;
}

export async function createIncident(input: IncidentCreateInput): Promise<Incident> {
  const { data } = await apiClient.post<Incident>("/api/incidents", input);
  return data;
}

export async function updateIncident(incidentId: string, input: IncidentUpdateInput): Promise<Incident> {
  const { data } = await apiClient.patch<Incident>(`/api/incidents/${incidentId}`, input);
  return data;
}

export async function resolveIncident(incidentId: string, input: IncidentResolveInput): Promise<Incident> {
  const { data } = await apiClient.post<Incident>(`/api/incidents/${incidentId}/resolve`, input);
  return data;
}

export async function listComments(incidentId: string): Promise<PaginatedResponse<Comment>> {
  const { data } = await apiClient.get<PaginatedResponse<Comment>>(`/api/incidents/${incidentId}/comments`, {
    params: { page: 1, page_size: 100 },
  });
  return data;
}

export async function createComment(incidentId: string, input: CommentCreateInput): Promise<Comment> {
  const { data } = await apiClient.post<Comment>(`/api/incidents/${incidentId}/comments`, input);
  return data;
}
