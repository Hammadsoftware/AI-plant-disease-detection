export type ResearchStatus = "available" | "partial" | "unavailable" | "disabled";
export type SourceType =
  | "government"
  | "university_extension"
  | "international_organization"
  | "peer_reviewed"
  | "research_institution"
  | "other";

export interface PredictionItem {
  class_name: string;
  disease: string;
  confidence: number;
}

export interface Diagnosis {
  class_name: string;
  disease: string;
  confidence: number;
  is_uncertain: boolean;
  top_predictions: PredictionItem[];
  class_probabilities: Record<string, number>;
}

export interface ExplanationDiagnosis {
  disease: string;
  confidence: number;
  confidence_note: string;
}

export interface ManagementRecommendations {
  cultural: string[];
  biological: string[];
  physical: string[];
  chemical: string[];
}

export interface ResearchSource {
  title: string;
  url: string;
  source: string;
  source_type: SourceType;
  snippet: string;
  query: string;
  authoritative: boolean;
}

export interface PesticideRecommendation {
  product_name: string;
  active_ingredient: string;
  pesticide_type: "fungicide" | "insecticide" | "bactericide" | "acaricide" | "other";
  target_disease_or_pest: string;
  registration_status: "verified" | "unverified";
  country: string;
  application_information: string;
  source: ResearchSource;
}

export interface DiseaseExplanation {
  summary: string;
  diagnosis: ExplanationDiagnosis;
  symptoms: string[];
  possible_causes: string[];
  management: ManagementRecommendations;
  pesticides: PesticideRecommendation[];
  prevention: string[];
  recommendations: string[];
  warnings: string[];
  sources: ResearchSource[];
}

export interface ImageReference {
  image_id: string;
  url: string;
  media_type: string;
  width: number;
  height: number;
  kind: string;
}

export interface ResearchBundle {
  topic: "disease" | "treatment" | "pesticide";
  status: ResearchStatus;
  queries: string[];
  sources: ResearchSource[];
  errors: string[];
}

export interface EvidenceClaim {
  category: "disease" | "treatment" | "pesticide";
  claim: string;
  source_urls: string[];
  authoritative: boolean;
}

export interface EvidenceReport {
  status: ResearchStatus;
  claims: EvidenceClaim[];
  sources: ResearchSource[];
  disagreements: string[];
  warnings: string[];
}

export interface DiagnosisResearch {
  disease: ResearchBundle;
  treatment: ResearchBundle;
  pesticide: ResearchBundle;
  evidence: EvidenceReport;
}

export interface DiagnosisResponse {
  success: boolean;
  image: ImageReference | null;
  diagnosis: Diagnosis;
  explanation: DiseaseExplanation | null;
  explanation_error: string | null;
  research_status: ResearchStatus;
  groq_status: "available" | "unavailable" | "disabled";
  research: DiagnosisResearch | null;
  warnings: string[];
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  groq_available: boolean;
  web_search_available: boolean;
  groq_model: string;
  search_provider: string;
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  imagePreview: string;
  filename: string;
  fileSize: number;
  disease: string;
  confidence: number;
  result: DiagnosisResponse;
}

export type ServiceStatus = "idle" | "online" | "unavailable";

export interface ApiErrorShape {
  status: number | null;
  message: string;
}
