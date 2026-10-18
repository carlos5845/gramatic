from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TextAnalysisRequest(BaseModel):
    """Solicitud de análisis para texto en inglés."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Texto en inglés a analizar (detección, corrección y explicación).",
        examples=["She go to school yesterday and saw two apple ."]
    )
    include_ged: Optional[bool] = Field(
        default=True,
        description="Si es True, ejecuta la detección de errores por token con BERT."
    )
    include_gec: Optional[bool] = Field(
        default=True,
        description="Si es True, ejecuta la corrección generativa con T5."
    )
    include_explanations: Optional[bool] = Field(
        default=True,
        description="Si es True, extrae ediciones y genera explicaciones pedagógicas."
    )


class GEDTokenSchema(BaseModel):
    token: str
    label: str = Field(description="'c' para correcto, 'i' para incorrecto")
    is_error: bool
    error_probability: float
    start_char: int
    end_char: int
    reconciled_with_gec: Optional[bool] = Field(
        default=False,
        description="Indica si este token se encuentra en una región modificada por el corrector GEC."
    )


class GEDSentenceSchema(BaseModel):
    sentence_index: int
    sentence_text: str
    tokens: List[GEDTokenSchema]
    error_count: int


class GEDResultSchema(BaseModel):
    total_errors: int
    sentences: List[GEDSentenceSchema]


class CharSpanSchema(BaseModel):
    start: int
    end: int


class TokenSpanSchema(BaseModel):
    start: int
    end: int


class PedagogicalExampleSchema(BaseModel):
    incorrect: str
    correct: str


class EditExplanationSchema(BaseModel):
    edit_index: int
    token_span: TokenSpanSchema
    char_span: CharSpanSchema
    original_fragment: str
    corrected_fragment: str
    category_id: str
    category_name: str
    category_name_en: str
    errant_type: str
    operation: str = Field(description="'insertion', 'deletion' o 'substitution'")
    confidence: str = Field(description="'high', 'medium' o 'uncertain'")
    summary: str
    rule_explanation: str
    example: PedagogicalExampleSchema
    is_detected_by_ged: bool = Field(description="Indica si BERT GED marcó error en esta posición.")
    ged_match_status: str = Field(description="'detected_by_both' o 'corrected_only_by_gec'")
    matched_ged_tokens: List[str] = Field(default_factory=list)


class ReconciliationSummarySchema(BaseModel):
    total_ged_errors: int
    total_gec_edits: int
    concordance_count: int
    gec_only_count: int
    ged_only_count: int
    concordance_rate: float
    notes: str


class AnalysisResponseSchema(BaseModel):
    success: bool
    original_text: str
    corrected_text: str
    is_changed: bool
    total_errors_detected: int
    total_corrections_made: int
    ged_results: GEDResultSchema
    explanations: List[EditExplanationSchema]
    reconciliation: ReconciliationSummarySchema
    taxonomy_breakdown: Dict[str, int]
    inference_time_ms: float


class DetectionOnlyResponseSchema(BaseModel):
    success: bool
    text: str
    total_errors: int
    sentences: List[GEDSentenceSchema]
    inference_time_ms: Optional[float] = None


class CorrectionOnlyResponseSchema(BaseModel):
    success: bool
    original: str
    corrected: str
    is_changed: bool
    inference_time_ms: float


class TaxonomyCategorySchema(BaseModel):
    id: str
    name_es: str
    name_en: str
    description_es: str


class HealthResponseSchema(BaseModel):
    status: str
    version: str
    device: str
    models_loaded: Dict[str, str]


class ErrorResponseSchema(BaseModel):
    success: bool = False
    error_type: str
    error_message: str
    detail: Optional[Any] = None
