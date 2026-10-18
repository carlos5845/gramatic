"""
Módulo API FastAPI para Detección (GED), Corrección (GEC) y Explicación Gramatical.
"""

from .app import app, create_app, get_pipeline
from .schemas import (
    TextAnalysisRequest,
    AnalysisResponseSchema,
    DetectionOnlyResponseSchema,
    CorrectionOnlyResponseSchema,
    TaxonomyCategorySchema,
    HealthResponseSchema,
    ErrorResponseSchema
)

__all__ = [
    "app",
    "create_app",
    "get_pipeline",
    "TextAnalysisRequest",
    "AnalysisResponseSchema",
    "DetectionOnlyResponseSchema",
    "CorrectionOnlyResponseSchema",
    "TaxonomyCategorySchema",
    "HealthResponseSchema",
    "ErrorResponseSchema",
]
