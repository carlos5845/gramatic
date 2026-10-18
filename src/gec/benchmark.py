import os
import sys
import json
import time
import re
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.gec.corrector import GrammarCorrector, run_initial_tests_suite

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def normalize_tokens_for_eval(text: str) -> str:
    """
    Normaliza el texto para comparación lingüística justa:
    Separa palabras y signos de puntuación como tokens y convierte a minúsculas,
    evitando que discrepancias superficiales de espaciado alrededor de signos de puntuación
    (comunes entre formato M2 y T5) penalicen indebidamente la coincidencia semántica.
    """
    if not text:
        return ""
    tokens = re.findall(r"\w+|[^\w\s]", str(text).lower())
    return " ".join(tokens)


def evaluate_initial_benchmark(corrector: GrammarCorrector, output_dir: str = "reports") -> pd.DataFrame:
    """
    Ejecuta la suite de pruebas lingüísticas iniciales (Fase 5.4 y 5.5)
    y guarda los resultados en CSV y JSON.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = run_initial_tests_suite(corrector)
    df = pd.DataFrame(results)

    csv_path = os.path.join(output_dir, "gec_initial_benchmark.csv")
    json_path = os.path.join(output_dir, "gec_initial_benchmark.json")

    df.to_csv(csv_path, index=False, encoding="utf-8")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    logger.info(f"Resultados del benchmark inicial guardados en '{csv_path}' y '{json_path}'.")
    return df


def evaluate_unnecessary_corrections(
    corrector: GrammarCorrector,
    fce_dev_gec_path: str = "data/gec/fce_dev_gec.csv",
    num_samples: Optional[int] = 200,
    batch_size: int = 16
) -> Dict[str, Any]:
    """
    Evalúa la tasa de correcciones innecesarias (False Positive Rate / Over-correction)
    sobre oraciones de FCE Dev que no contienen errores gramaticales (Fase 5.6).
    Calcula tanto la métrica textual estricta como la normalizada lingüísticamente.
    """
    if not os.path.exists(fce_dev_gec_path):
        raise FileNotFoundError(f"No se encontró el archivo: {fce_dev_gec_path}")

    df = pd.read_csv(fce_dev_gec_path)
    unchanged_df = df[df["is_changed"] == False]
    
    if len(unchanged_df) == 0:
        logger.warning("No se encontraron oraciones sin cambios en el archivo.")
        return {}

    sample_df = unchanged_df.head(num_samples) if num_samples else unchanged_df
    sentences = sample_df["original"].tolist()

    logger.info(f"Evaluando {len(sentences)} oraciones correctas para detectar sobre-correcciones innecesarias...")
    t0 = time.time()
    batch_results = corrector.correct_batch(sentences, batch_size=batch_size)
    total_time = time.time() - t0

    preserved_raw = 0
    preserved_normalized = 0
    altered_normalized = 0
    examples_altered = []

    for item in batch_results:
        orig = item["original"].strip()
        corr = item["corrected"].strip()
        
        orig_norm = normalize_tokens_for_eval(orig)
        corr_norm = normalize_tokens_for_eval(corr)
        
        if orig == corr:
            preserved_raw += 1
        
        if orig_norm == corr_norm:
            preserved_normalized += 1
        else:
            altered_normalized += 1
            if len(examples_altered) < 10:
                examples_altered.append({
                    "original": orig,
                    "model_output": corr,
                    "normalized_original": orig_norm,
                    "normalized_output": corr_norm
                })

    preservation_rate_raw = (preserved_raw / len(sentences)) * 100.0 if sentences else 0.0
    preservation_rate_norm = (preserved_normalized / len(sentences)) * 100.0 if sentences else 0.0
    false_positive_rate_norm = (altered_normalized / len(sentences)) * 100.0 if sentences else 0.0

    eval_stats = {
        "total_correct_sentences_evaluated": len(sentences),
        "preserved_unchanged_raw_text": preserved_raw,
        "preserved_unchanged_normalized": preserved_normalized,
        "altered_unnecessarily_normalized": altered_normalized,
        "preservation_rate_raw_pct": round(preservation_rate_raw, 2),
        "preservation_rate_normalized_pct": round(preservation_rate_norm, 2),
        "false_positive_rate_normalized_pct": round(false_positive_rate_norm, 2),
        "total_eval_time_seconds": round(total_time, 2),
        "avg_latency_ms": round((total_time / max(1, len(sentences))) * 1000.0, 2),
        "examples_altered": examples_altered
    }

    logger.info(f"Preservación Normalizada: {preservation_rate_norm:.2f}% | Sobre-corrección Normalizada: {false_positive_rate_norm:.2f}% | Latencia: {eval_stats['avg_latency_ms']:.2f} ms")
    return eval_stats


def evaluate_fce_baseline(
    corrector: GrammarCorrector,
    fce_dev_gec_path: str = "data/gec/fce_dev_gec.csv",
    num_samples: Optional[int] = None,
    batch_size: int = 16,
    output_dir: str = "reports"
) -> Dict[str, Any]:
    """
    Establece la línea base completa del modelo preentrenado sobre FCE Dev (Fase 5.7).
    Calcula:
    - Exact Match (coincidencia exacta estricta y normalizada)
    - Tasa de corrección exitosa en oraciones con error
    - Tasa de preservación de oraciones limpias
    - Latencia de inferencia y throughput (oraciones/segundo)
    """
    if not os.path.exists(fce_dev_gec_path):
        raise FileNotFoundError(f"No se encontró el archivo: {fce_dev_gec_path}")

    df = pd.read_csv(fce_dev_gec_path)
    if num_samples:
        eval_df = df.head(num_samples)
    else:
        eval_df = df

    logger.info(f"Evaluando línea base de '{corrector.model_name}' sobre {len(eval_df)} oraciones de FCE Dev...")
    
    originals = eval_df["original"].tolist()
    golds = eval_df["corrected"].tolist()
    is_changed_gold = eval_df["is_changed"].tolist()

    t0 = time.time()
    predictions = corrector.correct_batch(originals, batch_size=batch_size)
    total_time = time.time() - t0

    exact_matches_raw = 0
    exact_matches_norm = 0
    gold_changed_count = 0
    pred_changed_count = 0
    correctly_edited_norm = 0
    clean_preserved_norm = 0
    clean_total = 0

    detailed_results = []

    for i, pred in enumerate(predictions):
        orig = originals[i].strip()
        gold = golds[i].strip()
        hyp = pred["corrected"].strip()
        gold_has_error = is_changed_gold[i]

        is_em_raw = (hyp == gold)
        if is_em_raw:
            exact_matches_raw += 1

        hyp_norm = normalize_tokens_for_eval(hyp)
        gold_norm = normalize_tokens_for_eval(gold)
        orig_norm = normalize_tokens_for_eval(orig)

        is_em_norm = (hyp_norm == gold_norm)
        if is_em_norm:
            exact_matches_norm += 1

        if gold_has_error:
            gold_changed_count += 1
            if hyp_norm != orig_norm:
                pred_changed_count += 1
            if is_em_norm:
                correctly_edited_norm += 1
        else:
            clean_total += 1
            if hyp_norm == orig_norm:
                clean_preserved_norm += 1

        detailed_results.append({
            "sentence_id": int(eval_df.iloc[i]["sentence_id"]),
            "original": orig,
            "gold_corrected": gold,
            "hypothesis": hyp,
            "gold_has_error": bool(gold_has_error),
            "model_changed": bool(hyp_norm != orig_norm),
            "exact_match_normalized": bool(is_em_norm),
            "exact_match_raw": bool(is_em_raw),
            "inference_time_ms": pred["inference_time_ms"]
        })

    exact_match_norm_pct = (exact_matches_norm / len(eval_df)) * 100.0
    exact_match_raw_pct = (exact_matches_raw / len(eval_df)) * 100.0
    clean_preservation_norm_pct = (clean_preserved_norm / clean_total * 100.0) if clean_total > 0 else 100.0
    error_sentence_em_norm_pct = (correctly_edited_norm / gold_changed_count * 100.0) if gold_changed_count > 0 else 0.0

    baseline_metrics = {
        "model_name": corrector.model_name,
        "dataset": "FCE Dev (v2.1 BEA19)",
        "total_sentences": len(eval_df),
        "error_sentences_count": gold_changed_count,
        "clean_sentences_count": clean_total,
        "exact_match_normalized_pct": round(exact_match_norm_pct, 2),
        "exact_match_raw_pct": round(exact_match_raw_pct, 2),
        "exact_match_error_sentences_normalized_pct": round(error_sentence_em_norm_pct, 2),
        "clean_sentence_preservation_normalized_pct": round(clean_preservation_norm_pct, 2),
        "total_eval_time_seconds": round(total_time, 2),
        "avg_inference_latency_ms": round((total_time / len(eval_df)) * 1000.0, 2),
        "throughput_sentences_per_sec": round(len(eval_df) / max(0.001, total_time), 2),
        "device": str(corrector.device)
    }

    os.makedirs(output_dir, exist_ok=True)
    baseline_json_path = os.path.join(output_dir, "gec_baseline_evaluation.json")
    with open(baseline_json_path, "w", encoding="utf-8") as f:
        json.dump(baseline_metrics, f, indent=4, ensure_ascii=False)

    logger.info(f"Línea Base Registrada: EM Normalizado = {exact_match_norm_pct:.2f}% | Preservación = {clean_preservation_norm_pct:.2f}% | Throughput = {baseline_metrics['throughput_sentences_per_sec']:.2f} sent/s.")
    return baseline_metrics


if __name__ == "__main__":
    corrector = GrammarCorrector()
    print("\n" + "=" * 60)
    print(">>> FASE 5.4 & 5.5: Benchmark Inicial Lingüístico")
    print("=" * 60)
    bench_df = evaluate_initial_benchmark(corrector)
    for idx, r in bench_df.iterrows():
        print(f"[{r['category']}] ({r['inference_time_ms']} ms)")
        print(f"  SRC: {r['original_text']}")
        print(f"  OUT: {r['corrected_text']}")
        print(f"  EXP: {r['expected_intent']}\n")

    print("\n" + "=" * 60)
    print(">>> FASE 5.6: Detección de Correcciones Innecesarias")
    print("=" * 60)
    fp_stats = evaluate_unnecessary_corrections(corrector)
    print(json.dumps(fp_stats, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print(">>> FASE 5.7: Evaluación de Línea Base en FCE Dev")
    print("=" * 60)
    base_stats = evaluate_fce_baseline(corrector)
    print(json.dumps(base_stats, indent=2, ensure_ascii=False))
