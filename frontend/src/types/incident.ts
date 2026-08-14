export type IncidentStatus = "open" | "in_progress" | "pending" | "resolved" | "closed";
export type Priority = "P1" | "P2" | "P3" | "P4";

export interface CategoryRef {
  id?: number | null;
  name: string;
  service?: string | null;
}

export interface Assignment {
  team?: string | null;
  assignee_id?: string | null;
}

export interface AIInfo {
  last_analysis_id?: string | null;
  analyzed_at?: string | null;
  confidence?: string | null;
}

export interface Resolution {
  root_cause?: string | null;
  description?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
}

export interface Incident {
  incident_id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  priority: Priority;
  category: CategoryRef;
  assignment: Assignment;
  // Backend types this as a loosely-shaped dict server-side; UI only reads
  // the fields declared in AIInfo, so `any` here would hide real errors.
  ai: AIInfo;
  resolution: Resolution;
  created_at: string;
  updated_at: string;
}

export interface IncidentCreateInput {
  title: string;
  description: string;
  category: CategoryRef;
  priority?: Priority;
  assignment?: Assignment | null;
}

export interface IncidentUpdateInput {
  title?: string;
  description?: string;
  status?: IncidentStatus;
  priority?: Priority;
  category?: CategoryRef;
  assignment?: Assignment;
}

export interface IncidentResolveInput {
  root_cause: string;
  resolution_description: string;
  resolved_by: string;
}

export interface IncidentFilters {
  status?: IncidentStatus;
  priority?: Priority;
  category?: string;
  service?: string;
  team?: string;
  assignee_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface Comment {
  comment_id: string;
  incident_id: string;
  author?: string | null;
  author_id?: string | null;
  body: string;
  is_internal: boolean;
  created_at: string;
}

export interface CommentCreateInput {
  body: string;
  author?: string;
  author_id?: string;
  is_internal?: boolean;
}
