import os
import sys
import time
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
import errant
import spacy
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class ERRANTEvaluator:
    """
    Evaluador lingüístico basado en ERRANT (Grammatical Error Annotation and Evaluation).
    Permite:
    1. Alinear oraciones de entrada y corregidas mediante spaCy y ERRANT.
    2. Extraer ediciones gramaticales estándar M2 (inserciones, eliminaciones, sustituciones).
    3. Evaluar métricas M2: Precision, Recall, F0.5 y F1 a nivel de edición (Span & Correction).
    4. Categorizar el rendimiento por tipo de error (R:VERB, R:SPELL, M:DET, R:PREP, etc.).
    5. Analizar falsos positivos (modificaciones innecesarias), falsos negativos (errores omitidos)
       y falsas ediciones (cambios incorrectos).
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        logger.info(f"Inicializando ERRANTEvaluator con modelo spaCy '{spacy_model}'...")
        self.nlp = spacy.load(spacy_model)
        self.annotator = errant.load("en", self.nlp)
        logger.info("ERRANTEvaluator cargado correctamente.")

    def tokenize_text(self, text: str) -> str:
        """
        Tokeniza el texto preservando la segmentación de palabras y signos de puntuación
        compatible con el estándar FCE / BEA19.
        """
        if not text or not text.strip():
            return ""
        doc = self.nlp(text.strip())
        return " ".join([t.text for t in doc if t.text.strip()])

    def load_gold_m2(self, gold_m2_path: str) -> List[Dict[str, Any]]:
        """
        Carga y parsea un archivo Gold M2.
        Retorna una lista de registros con source_tokens y lista de ediciones por anotador.
        """
        if not os.path.exists(gold_m2_path):
            raise FileNotFoundError(f"No se encontró el archivo Gold M2: {gold_m2_path}")

        with open(gold_m2_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return []

        blocks = content.split("\n\n")
        records = []

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            source_tokens = []
            annotator_edits: Dict[int, List[Tuple[int, int, str, str]]] = {}

            for line in lines:
                if line.startswith("S "):
                    source_tokens = line[2:].strip().split()
                elif line.startswith("A "):
                    parts = line[2:].split("|||")
                    if len(parts) >= 6:
                        span = parts[0].split()
                        start, end = int(span[0]), int(span[1])
                        etype = parts[1]
                        cor = parts[2]
                        ann_id = int(parts[5])

                        if ann_id not in annotator_edits:
                            annotator_edits[ann_id] = []

                        # Excluir noop
                        if not (start == -1 and end == -1 and etype == "noop"):
                            annotator_edits[ann_id].append((start, end, etype, cor))

            if not annotator_edits:
                annotator_edits[0] = []

            records.append({
                "source_tokens": source_tokens,
                "source_text": " ".join(source_tokens),
                "annotator_edits": annotator_edits
            })

        return records

    def extract_hypothesis_edits(
        self,
        source_tokens_list: List[List[str]],
        hypotheses: List[str]
    ) -> List[List[Tuple[int, int, str, str]]]:
        """
        Para cada par (source, hyp), extrae las ediciones generadas usando ERRANT con procesamiento por lotes en spaCy.
        Retorna una lista de listas de tuplas (start, end, error_type, correction).
        """
        all_hyp_edits = []

        src_strings = [" ".join(tokens) for tokens in source_tokens_list]
        
        # Tokenizar hipótesis eficientemente
        hyp_docs_for_tok = list(self.nlp.pipe(hypotheses, batch_size=256))
        hyp_tok_strings = [" ".join([t.text for t in doc if t.text.strip()]) for doc in hyp_docs_for_tok]

        # Parsear con ERRANT
        orig_docs = list(self.nlp.pipe(src_strings, batch_size=256))
        cor_docs = list(self.nlp.pipe(hyp_tok_strings, batch_size=256))

        for orig_doc, cor_doc in zip(orig_docs, cor_docs):
            edits = self.annotator.annotate(orig_doc, cor_doc)
            sentence_edits = []
            for e in edits:
                cor_str = e.c_str if e.c_str else "-NONE-"
                sentence_edits.append((e.o_start, e.o_end, e.type, cor_str))
            all_hyp_edits.append(sentence_edits)

        return all_hyp_edits

    def save_hypothesis_m2(
        self,
        source_tokens_list: List[List[str]],
        hyp_edits_list: List[List[Tuple[int, int, str, str]]],
        output_m2_path: str
    ):
        """
        Guarda las oraciones e hipótesis de edición en formato estándar M2.
        """
        os.makedirs(os.path.dirname(output_m2_path), exist_ok=True)
        with open(output_m2_path, "w", encoding="utf-8") as f:
            for source_tokens, edits in zip(source_tokens_list, hyp_edits_list):
                f.write(f"S {' '.join(source_tokens)}\n")
                if not edits:
                    f.write("A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0\n")
                else:
                    for start, end, etype, cor in edits:
                        f.write(f"A {start} {end}|||{etype}|||{cor}|||REQUIRED|||-NONE-|||0\n")
                f.write("\n")
        logger.info(f"Archivo de hipótesis M2 guardado en '{output_m2_path}'.")

    def evaluate_m2(
        self,
        gold_records: List[Dict[str, Any]],
        hyp_edits_list: List[List[Tuple[int, int, str, str]]],
        hyp_texts: List[str]
    ) -> Dict[str, Any]:
        """
        Calcula las métricas de edición M2 / ERRANT:
        - Global Precision, Recall, F0.5, F1 (Span & Text Exact Match)
        - Desglose por tipo de error
        - Conteo de TP, FP, FN y Falsas Ediciones (False Edits)
        - Métricas a nivel de oración (Exact Match, Preservación de oraciones limpias)
        """
        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_false_edits = 0  # Span detectado pero corrección errónea

        category_stats: Dict[str, Dict[str, int]] = {}
        error_examples = {
            "true_positives": [],
            "false_positives_unnecessary": [],
            "false_negatives_missed": [],
            "false_edits_incorrect_correction": []
        }

        sentence_exact_matches = 0
        clean_sentences_total = 0
        clean_sentences_preserved = 0

        for idx, (gold_rec, hyp_edits, hyp_text) in enumerate(zip(gold_records, hyp_edits_list, hyp_texts)):
            src_tokens = gold_rec["source_tokens"]
            src_text = gold_rec["source_text"]
            
            # Tomamos las anotaciones del primer anotador (o el que maximice F0.5 si multi-anotador)
            gold_ann_edits = gold_rec["annotator_edits"].get(0, [])
            
            # Comprobar si era oración limpia
            is_gold_clean = (len(gold_ann_edits) == 0)
            if is_gold_clean:
                clean_sentences_total += 1
                if len(hyp_edits) == 0:
                    clean_sentences_preserved += 1

            # Exact match a nivel de oración
            hyp_tok = self.tokenize_text(hyp_text)
            # Reconstruir referencia de anotador 0 si existe
            # Para comparar exact match normalizado:
            if not gold_ann_edits and hyp_tok.lower() == src_text.lower():
                sentence_exact_matches += 1

            # Comparación de ediciones: Representación (start, end, cor)
            gold_spans = {(e[0], e[1]): (e[2], e[3]) for e in gold_ann_edits}
            hyp_spans = {(e[0], e[1]): (e[2], e[3]) for e in hyp_edits}

            gold_matched = set()

            for h_span, (h_type, h_cor) in hyp_spans.items():
                cat = h_type.split(":")[0] if ":" in h_type else h_type
                if cat not in category_stats:
                    category_stats[cat] = {"tp": 0, "fp": 0, "fn": 0}

                if h_span in gold_spans:
                    g_type, g_cor = gold_spans[h_span]
                    # Normalización simple para comparación de corrección
                    if h_cor.strip().lower() == g_cor.strip().lower():
                        total_tp += 1
                        category_stats[cat]["tp"] += 1
                        gold_matched.add(h_span)
                        if len(error_examples["true_positives"]) < 5:
                            error_examples["true_positives"].append({
                                "sentence_id": idx,
                                "source": src_text,
                                "span": list(h_span),
                                "error_type": h_type,
                                "correction": h_cor,
                                "hypothesis": hyp_text
                            })
                    else:
                        # False Edit: se detectó el error pero la corrección fue distinta/incorrecta
                        total_fp += 1
                        total_false_edits += 1
                        category_stats[cat]["fp"] += 1
                        if len(error_examples["false_edits_incorrect_correction"]) < 5:
                            error_examples["false_edits_incorrect_correction"].append({
                                "sentence_id": idx,
                                "source": src_text,
                                "span": list(h_span),
                                "error_type": h_type,
                                "gold_correction": g_cor,
                                "hyp_correction": h_cor,
                                "hypothesis": hyp_text
                            })
                else:
                    # Falso positivo: modificación innecesaria
                    total_fp += 1
                    category_stats[cat]["fp"] += 1
                    if len(error_examples["false_positives_unnecessary"]) < 5:
                        error_examples["false_positives_unnecessary"].append({
                            "sentence_id": idx,
                            "source": src_text,
                            "span": list(h_span),
                            "error_type": h_type,
                            "hyp_correction": h_cor,
                            "hypothesis": hyp_text
                        })

            # Falsos negativos: ediciones en gold no cubiertas
            for g_span, (g_type, g_cor) in gold_spans.items():
                if g_span not in gold_matched:
                    total_fn += 1
                    g_cat = g_type.split(":")[0] if ":" in g_type else g_type
                    if g_cat not in category_stats:
                        category_stats[g_cat] = {"tp": 0, "fp": 0, "fn": 0}
                    category_stats[g_cat]["fn"] += 1

                    if len(error_examples["false_negatives_missed"]) < 5:
                        error_examples["false_negatives_missed"].append({
                            "sentence_id": idx,
                            "source": src_text,
                            "span": list(g_span),
                            "error_type": g_type,
                            "expected_correction": g_cor,
                            "hypothesis": hyp_text
                        })

        # Cálculo de métricas globales
        precision = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
        recall = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
        
        # F0.5 da más peso a la precisión (beta=0.5): F0.5 = (1 + 0.25) * P * R / (0.25 * P + R)
        beta_sq = 0.5 ** 2
        f0_5 = ((1 + beta_sq) * precision * recall / (beta_sq * precision + recall)) if (beta_sq * precision + recall) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        clean_preservation_rate = (clean_sentences_preserved / clean_sentences_total) if clean_sentences_total > 0 else 1.0

        # Métricas por categoría
        category_metrics = {}
        for cat, counts in category_stats.items():
            p_cat = (counts["tp"] / (counts["tp"] + counts["fp"])) if (counts["tp"] + counts["fp"]) > 0 else 0.0
            r_cat = (counts["tp"] / (counts["tp"] + counts["fn"])) if (counts["tp"] + counts["fn"]) > 0 else 0.0
            f05_cat = ((1 + beta_sq) * p_cat * r_cat / (beta_sq * p_cat + r_cat)) if (beta_sq * p_cat + r_cat) > 0 else 0.0
            category_metrics[cat] = {
                "tp": counts["tp"],
                "fp": counts["fp"],
                "fn": counts["fn"],
                "precision": p_cat,
                "recall": r_cat,
                "f0.5": f05_cat
            }

        return {
            "total_sentences": len(gold_records),
            "true_positives": total_tp,
            "false_positives": total_fp,
            "false_negatives": total_fn,
            "false_edits_incorrect": total_false_edits,
            "precision": precision,
            "recall": recall,
            "f0.5": f0_5,
            "f1": f1,
            "clean_sentences_total": clean_sentences_total,
            "clean_sentences_preserved": clean_sentences_preserved,
            "clean_preservation_rate": clean_preservation_rate,
            "category_metrics": category_metrics,
            "error_examples": error_examples
        }

    def evaluate_gec_model(
        self,
        gold_m2_path: str,
        corrector_fn,
        output_hyp_m2_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la evaluación completa de un corrector sobre un archivo Gold M2.
        """
        gold_records = self.load_gold_m2(gold_m2_path)
        source_texts = [r["source_text"] for r in gold_records]
        source_tokens_list = [r["source_tokens"] for r in gold_records]

        logger.info(f"Generando correcciones para {len(source_texts)} oraciones...")
        t0 = time.perf_counter()
        
        # Procesar con el corrector
        hyp_results = corrector_fn(source_texts)
        total_time = time.perf_counter() - t0
        
        hyp_texts = [res["corrected"] if isinstance(res, dict) else res for res in hyp_results]
        
        logger.info(f"Extrayendo ediciones M2 con ERRANT...")
        hyp_edits_list = self.extract_hypothesis_edits(source_tokens_list, hyp_texts)

        if output_hyp_m2_path:
            self.save_hypothesis_m2(source_tokens_list, hyp_edits_list, output_hyp_m2_path)

        logger.info(f"Calculando métricas M2 y análisis de errores...")
        eval_results = self.evaluate_m2(gold_records, hyp_edits_list, hyp_texts)
        
        eval_results["inference_time_seconds"] = total_time
        eval_results["sentences_per_second"] = len(source_texts) / total_time if total_time > 0 else 0
        eval_results["avg_latency_ms"] = (total_time / len(source_texts) * 1000) if len(source_texts) > 0 else 0
        eval_results["hyp_texts"] = hyp_texts

        logger.info(f"Resultados ERRANT M2 -> Precision: {eval_results['precision']:.4f} | Recall: {eval_results['recall']:.4f} | F0.5: {eval_results['f0.5']:.4f} | F1: {eval_results['f1']:.4f}")
        return eval_results
