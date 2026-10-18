export interface GEDToken {
  token: string;
  label: "c" | "i";
  is_error: boolean;
  error_probability: number;
  start_char: number;
  end_char: number;
  reconciled_with_gec?: boolean;
}

export interface GEDSentence {
  sentence_index: number;
  sentence_text: string;
  tokens: GEDToken[];
  error_count: number;
}

export interface GEDResults {
  total_errors: number;
  sentences: GEDSentence[];
}

export interface CharSpan {
  start: number;
  end: number;
}

export interface TokenSpan {
  start: number;
  end: number;
}

export interface PedagogicalExample {
  incorrect: string;
  correct: string;
}

export interface EditExplanation {
  edit_index: number;
  token_span: TokenSpan;
  char_span: CharSpan;
  original_fragment: string;
  corrected_fragment: string;
  category_id: string;
  category_name: string;
  category_name_en: string;
  errant_type: string;
  operation: "insertion" | "deletion" | "substitution";
  confidence: "high" | "medium" | "uncertain";
  summary: string;
  rule_explanation: string;
  example: PedagogicalExample;
  is_detected_by_ged: boolean;
  ged_match_status: "detected_by_both" | "corrected_only_by_gec";
  matched_ged_tokens: string[];
}

export interface ReconciliationSummary {
  total_ged_errors: number;
  total_gec_edits: number;
  concordance_count: number;
  gec_only_count: number;
  ged_only_count: number;
  concordance_rate: number;
  notes: string;
}

export interface AnalysisResponse {
  success: boolean;
  original_text: string;
  corrected_text: string;
  is_changed: boolean;
  total_errors_detected: number;
  total_corrections_made: number;
  ged_results: GEDResults;
  explanations: EditExplanation[];
  reconciliation: ReconciliationSummary;
  taxonomy_breakdown: Record<string, number>;
  inference_time_ms: number;
  error_type?: string;
  error_message?: string;
}

export interface DetectionOnlyResponse {
  success: boolean;
  text: string;
  total_errors: number;
  sentences: GEDSentence[];
  inference_time_ms?: number;
  error_type?: string;
  error_message?: string;
}

export interface CorrectionOnlyResponse {
  success: boolean;
  original: string;
  corrected: string;
  is_changed: boolean;
  inference_time_ms: number;
  error_type?: string;
  error_message?: string;
}

export interface TaxonomyCategory {
  id: string;
  name_es: string;
  name_en: string;
  description_es: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  device: string;
  models_loaded: {
    bert_ged: string;
    t5_gec: string;
    explainer_errant: string;
  };
}

export interface ApiError {
  success: false;
  error_type: string;
  error_message: string;
  detail?: any;
}
