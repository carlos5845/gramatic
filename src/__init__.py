"""
Detecction_English: Grammatical Error Detection (GED) and Correction (GEC) System.
Fase 2: Preprocesamiento y análisis lingüístico
Fase 3: Modelos Baseline y Fine-tuning de BERT (bert-base-cased)
Fase 4: Preparación del corpus FCE (M2 BEA19)
Fase 5: Integración del modelo GEC Seq2Seq (T5)
Fase 6: Ajuste fino de GEC (T5 Fine-Tuning)
Fase 7: Evaluación experimental consolidada (ERRANT M2)
Fase 8: Clasificación y explicación pedagógica de correcciones
Fase 9: Integración de detector, corrector, explicaciones y API FastAPI
"""

from .inference import GrammaticalErrorDetector
from .pipeline import IntegratedGrammarPipeline

__all__ = [
    "GrammaticalErrorDetector",
    "IntegratedGrammarPipeline",
]
