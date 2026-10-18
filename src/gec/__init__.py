"""
Módulo GEC (Grammatical Error Correction).
Fase 4: Preparación del corpus FCE para corrección gramatical (Conversión M2 a pares).
Fase 5: Integración del modelo de corrección gramatical (Inferencia, baseline y benchmark).
Fase 6: Ajuste fino del modelo GEC (Fine-tuning Seq2Seq T5 y control de sobreajuste).
Fase 7: Evaluación experimental de GED y GEC (Métricas ERRANT M2, análisis de errores y consolidación).
Fase 8: Clasificación y explicación pedagógica de correcciones gramaticales.
"""

from .prepare_fce import M2Parser, process_fce_corpus, generate_quality_report, validate_reconstructed_dataset
from .corrector import GrammarCorrector
from .benchmark import evaluate_initial_benchmark, evaluate_unnecessary_corrections, evaluate_fce_baseline
from .train_gec import GECSeq2SeqDataset, train_gec_model, plot_gec_training_curves
from .evaluate_errant import ERRANTEvaluator
from .experiment_evaluator import run_full_experimental_evaluation, plot_experimental_comparison
from .explainer import GrammarExplainer, TAXONOMY_CATEGORIES, validate_explainer_on_sample

__all__ = [
    "M2Parser",
    "process_fce_corpus",
    "generate_quality_report",
    "validate_reconstructed_dataset",
    "GrammarCorrector",
    "evaluate_initial_benchmark",
    "evaluate_unnecessary_corrections",
    "evaluate_fce_baseline",
    "GECSeq2SeqDataset",
    "train_gec_model",
    "plot_gec_training_curves",
    "ERRANTEvaluator",
    "run_full_experimental_evaluation",
    "plot_experimental_comparison",
    "GrammarExplainer",
    "TAXONOMY_CATEGORIES",
    "validate_explainer_on_sample",
]
