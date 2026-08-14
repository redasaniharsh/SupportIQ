export interface KnowledgeArticle {
  article_id: string;
  title: string;
  category: string;
  service?: string | null;
  symptoms: string[];
  root_causes: string[];
  troubleshooting_steps: string[];
  resolution: string;
  escalation_conditions: string[];
  version: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface KnowledgeFilters {
  category?: string;
  service?: string;
  search?: string;
  page?: number;
  page_size?: number;
}
