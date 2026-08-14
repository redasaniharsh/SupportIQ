import type { Incident } from "./incident";
import type { KnowledgeArticle } from "./knowledge";

export interface SearchResponse {
  query: string;
  incidents: { items: Incident[]; total: number };
  knowledge_articles: { items: KnowledgeArticle[]; total: number };
  page: number;
  page_size: number;
}
