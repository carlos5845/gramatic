import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_preprocessing import validate_text_entry
from src.inference import GrammaticalErrorDetector
from src.gec.corrector import GrammarCorrector
from src.gec.explainer import GrammarExplainer, TAXONOMY_CATEGORIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class IntegratedGrammarPipeline:
    """
    Pipeline Integrado de Detección (GED), Corrección (GEC) y Explicación Pedagógica.
    
    Orquesta el flujo de análisis completo:
    1. Validación sintáctica y lingüística del texto de entrada.
    2. Detección de errores a nivel de token mediante BERT (GED).
    3. Corrección de errores gramaticales mediante modelo Seq2Seq T5 (GEC).
    4. Clasificación taxonómica y generación de explicaciones pedagógicas comprensibles con ERRANT.
    5. Reconciliación cruzada entre detecciones de BERT y ediciones propuestas por GEC.
    """

    def __init__(
        self,
        bert_model_path: str = "models/bert_best_model",
        gec_model_path: Optional[str] = None,
        device: Optional[str] = None,
        lazy_load: bool = False
    ):
        self.bert_model_path = bert_model_path
        
        # Determinar ruta de GEC: priorizar modelo ajustado si existe
        if gec_model_path is None:
            finetuned_path = "models/gec_finetuned_model"
            if os.path.exists(os.path.join(finetuned_path, "model.safetensors")) or os.path.exists(os.path.join(finetuned_path, "pytorch_model.bin")):
                self.gec_model_path = finetuned_path
            else:
                self.gec_model_path = "Unbabel/gec-t5_small"
        else:
            self.gec_model_path = gec_model_path

        self.device = device
        self._detector: Optional[GrammaticalErrorDetector] = None
        self._corrector: Optional[GrammarCorrector] = None
        self._explainer: Optional[GrammarExplainer] = None

        if not lazy_load:
            self._initialize_components()

    def _initialize_components(self):
        """Inicializa los tres modelos del pipeline."""
        logger.info("Inicializando componentes del Pipeline Integrado...")
        
        if self._detector is None:
            logger.info(f"Cargando Detector GED BERT desde '{self.bert_model_path}'...")
            self._detector = GrammaticalErrorDetector(model_path=self.bert_model_path, device=self.device)
            
        if self._corrector is None:
            logger.info(f"Cargando Corrector GEC T5 desde '{self.gec_model_path}'...")
            self._corrector = GrammarCorrector(model_name_or_path=self.gec_model_path, device=self.device)
            
        if self._explainer is None:
            logger.info("Cargando Explicador Pedagógico ERRANT...")
            self._explainer = GrammarExplainer()
            
        logger.info("Pipeline Integrado inicializado con éxito.")

    @property
    def detector(self) -> GrammaticalErrorDetector:
        if self._detector is None:
            self._initialize_components()
        return self._detector

    @property
    def corrector(self) -> GrammarCorrector:
        if self._corrector is None:
            self._initialize_components()
        return self._corrector

    @property
    def explainer(self) -> GrammarExplainer:
        if self._explainer is None:
            self._initialize_components()
        return self._explainer

    def reconcile_ged_and_gec(
        self,
        ged_sentences: List[Dict[str, Any]],
        gec_explanations: List[Dict[str, Any]],
        original_text: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Reconcilia los hallazgos del detector BERT (GED) con las ediciones del corrector T5 (GEC).
        
        Comportamiento:
        - Para cada edición de GEC, comprueba si coincide o solapa espacialmente con algún token
          marcado como error ('i') por BERT.
        - Asigna el estado de concordancia:
          * 'detected_by_both': BERT detectó el error y GEC propuso una corrección.
          * 'corrected_only_by_gec': GEC corrigió un fragmento que BERT clasificó como correcto ('c').
        - Para tokens marcados por BERT que no fueron modificados por GEC:
          * 'flagged_by_ged_unmodified_by_gec': BERT detectó posible error pero GEC lo mantuvo inalterado.
          
        Retorna:
        - Lista de explicaciones enriquecidas con metadatos de reconciliación.
        - Resumen estadístico de concordancia.
        """
        # Extraer todos los tokens con error marcados por BERT y sus spans de caracteres
        ged_error_spans = []
        all_ged_tokens = []
        
        for sent in ged_sentences:
            for tok in sent.get("tokens", []):
                all_ged_tokens.append(tok)
                if tok.get("is_error", False):
                    ged_error_spans.append({
                        "token": tok["token"],
                        "start_char": tok["start_char"],
                        "end_char": tok["end_char"],
                        "error_probability": tok.get("error_probability", 0.0),
                        "matched_by_gec": False
                    })

        reconciled_explanations = []
        concordance_count = 0
        gec_only_count = 0

        for exp in gec_explanations:
            edit_start = exp["char_span"]["start"]
            edit_end = exp["char_span"]["end"]
            
            # Buscar solapamiento con tokens de error de GED
            matching_ged_tokens = []
            for ged_span in ged_error_spans:
                # Comprobar solapamiento de intervalos [a1, b1] y [a2, b2]
                overlap = max(0, min(edit_end, ged_span["end_char"]) - max(edit_start, ged_span["start_char"]))
                # También considerar inserciones donde edit_start == edit_end
                if overlap > 0 or (edit_start == edit_end and ged_span["start_char"] <= edit_start <= ged_span["end_char"]):
                    matching_ged_tokens.append(ged_span["token"])
                    ged_span["matched_by_gec"] = True

            is_detected_by_ged = len(matching_ged_tokens) > 0
            if is_detected_by_ged:
                ged_match_status = "detected_by_both"
                concordance_count += 1
            else:
                ged_match_status = "corrected_only_by_gec"
                gec_only_count += 1

            enriched_exp = dict(exp)
            enriched_exp["is_detected_by_ged"] = is_detected_by_ged
            enriched_exp["ged_match_status"] = ged_match_status
            enriched_exp["matched_ged_tokens"] = matching_ged_tokens
            reconciled_explanations.append(enriched_exp)

        # Actualizar estado en tokens de GED
        for sent in ged_sentences:
            for tok in sent.get("tokens", []):
                t_start = tok["start_char"]
                t_end = tok["end_char"]
                modified = any(
                    max(0, min(e["char_span"]["end"], t_end) - max(e["char_span"]["start"], t_start)) > 0
                    for e in gec_explanations
                )
                tok["reconciled_with_gec"] = modified

        ged_only_count = sum(1 for span in ged_error_spans if not span["matched_by_gec"])
        total_ged_errors = len(ged_error_spans)
        total_gec_edits = len(gec_explanations)

        total_unique_signals = total_gec_edits + ged_only_count
        concordance_rate = (concordance_count / total_unique_signals) if total_unique_signals > 0 else 1.0

        reconciliation_summary = {
            "total_ged_errors": total_ged_errors,
            "total_gec_edits": total_gec_edits,
            "concordance_count": concordance_count,
            "gec_only_count": gec_only_count,
            "ged_only_count": ged_only_count,
            "concordance_rate": round(float(concordance_rate), 4),
            "notes": (
                "Concordancia evaluada sin asumir dependencia estricta: "
                "GEC puede formular correcciones no señaladas por BERT (e.g. fluidez léxica o inserciones), "
                "mientras que BERT puede señalar anomalías locales no corregidas por el modelo generativo."
            )
        }

        return reconciled_explanations, reconciliation_summary

    def process_text(
        self,
        text: str,
        max_chars: int = 2000,
        include_ged: bool = True,
        include_gec: bool = True,
        include_explanations: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo sobre el texto proporcionado.
        
        Pasos:
        1. Validación sintáctica y lingüística del texto.
        2. Inferencia GED (clasificación de tokens por BERT).
        3. Inferencia GEC (corrección Seq2Seq T5).
        4. Extracción de ediciones y generación de explicaciones pedagógicas (ERRANT).
        5. Reconciliación cruzada de hallazgos GED vs GEC.
        """
        t0 = time.perf_counter()
        
        # 1. Validación de entrada
        if not text or not text.strip():
            return {
                "success": False,
                "error_type": "EMPTY_INPUT",
                "error_message": "La entrada está vacía o contiene solo espacios en blanco.",
                "original_text": text
            }

        if len(text) > max_chars:
            return {
                "success": False,
                "error_type": "INPUT_TOO_LONG",
                "error_message": f"El texto excede el límite máximo permitido de {max_chars} caracteres (longitud actual: {len(text)}).",
                "original_text": text[:100] + "..."
            }

        is_valid, validation_msg = validate_text_entry(text)
        if not is_valid:
            return {
                "success": False,
                "error_type": "INVALID_LANGUAGE_INPUT",
                "error_message": validation_msg,
                "original_text": text
            }

        cleaned_text = text.strip()

        # 2. Detección con BERT (GED)
        ged_data = {"sentences": [], "total_errors": 0}
        if include_ged:
            try:
                ged_data = self.detector.detect_errors_in_text(cleaned_text)
                if not ged_data.get("success", False):
                    return {
                        "success": False,
                        "error_type": "GED_INFERENCE_ERROR",
                        "error_message": ged_data.get("error_message", "Error durante la detección con BERT."),
                        "original_text": cleaned_text
                    }
            except Exception as e:
                logger.error(f"Fallo en detección GED: {e}", exc_info=True)
                return {
                    "success": False,
                    "error_type": "GED_INFERENCE_ERROR",
                    "error_message": f"Error en inferencia BERT GED: {str(e)}",
                    "original_text": cleaned_text
                }

        # 3. Corrección con T5 (GEC)
        corrected_text = cleaned_text
        is_changed = False
        gec_time_ms = 0.0
        
        if include_gec:
            try:
                # Segmentar texto por oraciones para procesar con GEC de forma consistente
                doc_sents = [s.text.strip() for s in self.detector.nlp(cleaned_text).sents if s.text.strip()]
                if not doc_sents:
                    doc_sents = [cleaned_text]

                corrected_sentences = []
                for s in doc_sents:
                    corr_res = self.corrector.correct_sentence(s)
                    corrected_sentences.append(corr_res["corrected"])
                    gec_time_ms += corr_res.get("inference_time_ms", 0.0)

                corrected_text = " ".join(corrected_sentences).strip()
                is_changed = (cleaned_text != corrected_text)
            except Exception as e:
                logger.error(f"Fallo en corrección GEC: {e}", exc_info=True)
                return {
                    "success": False,
                    "error_type": "GEC_INFERENCE_ERROR",
                    "error_message": f"Error en inferencia T5 GEC: {str(e)}",
                    "original_text": cleaned_text
                }

        # 4. Explicaciones pedagógicas con ERRANT
        explanations = []
        taxonomy_breakdown = {}
        if include_explanations and is_changed:
            try:
                exp_res = self.explainer.explain_correction(cleaned_text, corrected_text)
                explanations = exp_res.get("explanations", [])
                taxonomy_breakdown = exp_res.get("taxonomy_breakdown", {})
            except Exception as e:
                logger.error(f"Fallo en generación de explicaciones: {e}", exc_info=True)
                # No abortar completamente el flujo, degradar de forma segura
                explanations = []

        # 5. Reconciliación GED vs GEC
        reconciled_explanations, reconciliation_summary = self.reconcile_ged_and_gec(
            ged_sentences=ged_data.get("sentences", []),
            gec_explanations=explanations,
            original_text=cleaned_text
        )

        total_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "success": True,
            "original_text": cleaned_text,
            "corrected_text": corrected_text,
            "is_changed": is_changed,
            "total_errors_detected": ged_data.get("total_errors", 0),
            "total_corrections_made": len(reconciled_explanations),
            "ged_results": {
                "total_errors": ged_data.get("total_errors", 0),
                "sentences": ged_data.get("sentences", [])
            },
            "explanations": reconciled_explanations,
            "reconciliation": reconciliation_summary,
            "taxonomy_breakdown": taxonomy_breakdown,
            "inference_time_ms": total_time_ms
        }
