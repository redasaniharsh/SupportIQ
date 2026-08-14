export type ConfidenceLevel = "High" | "Medium" | "Low";

export interface ProbableCause {
  cause: string;
  evidence_ids: string[];
  likelihood: ConfidenceLevel;
}

export interface RecommendedAction {
  action: string;
  evidence_ids: string[];
  priority_order: number;
}

export interface SimilarIncidentMention {
  incident_id: string;
  evidence_id: string;
  relationship: "duplicate" | "related";
  rationale?: string | null;
}

export interface KnowledgeArticleMention {
  article_id: string;
  evidence_id: string;
  relevance?: string | null;
}

export interface AIAnalysisResponse {
  summary: string;
  category: string;
  priority: "P1" | "P2" | "P3" | "P4";
  probable_causes: ProbableCause[];
  recommended_actions: RecommendedAction[];
  similar_incidents: SimilarIncidentMention[];
  knowledge_articles: KnowledgeArticleMention[];
  escalation_required: boolean;
  confidence: ConfidenceLevel;
  uncertainties: string[];
  final_recommendation: string;
}

export interface EvidenceRef {
  evidence_id: string;
  document_type: "knowledge" | "historical-tickets";
  document_id: string;
  title?: string | null;
  score?: number | null;
  source?: string | null;
}

export interface ConfidenceInfo {
  model_reported?: string | null;
  evidence_score: number;
  bucket: ConfidenceLevel;
}

export interface AnalyzeSuccessResponse {
  status: "ok";
  analysis_id: string;
  incident_id: string;
  model: string;
  prompt_version: string;
  analysis: AIAnalysisResponse;
  evidence: EvidenceRef[];
  confidence: ConfidenceInfo;
  retrieval_count: number;
  latency_ms: number;
  created_at: string;
}

export interface AnalyzeUnavailableResponse {
  status: "ai_unavailable";
  message: string;
  retryable: boolean;
}

export type AnalyzeResponse = AnalyzeSuccessResponse | AnalyzeUnavailableResponse;

export interface SimilarIncidentItem {
  incident_id: string;
  title: string;
  similarity: number;
  relationship: "duplicate" | "related";
  status?: string | null;
  resolution_summary?: string | null;
}

export interface SimilarIncidentsResponse {
  incident_id: string;
  duplicate_threshold: number;
  related_threshold: number;
  items: SimilarIncidentItem[];
}
