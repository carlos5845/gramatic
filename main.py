import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.data_preprocessing import (
    load_ged_tsv,
    analyze_corpus_statistics,
    validate_text_entry,
    prepare_ged_datasets
)
from src.baseline import BaselineGEDModel, extract_features_and_labels_from_sentences
from src.metrics import compute_ged_metrics
from src.train_bert import train_bert_model, predict_unlabelled_tsv
from src.inference import GrammaticalErrorDetector

from src.gec.prepare_fce import process_fce_corpus, generate_quality_report, validate_reconstructed_dataset
from src.gec.corrector import GrammarCorrector
from src.gec.benchmark import evaluate_initial_benchmark, evaluate_unnecessary_corrections, evaluate_fce_baseline
from src.gec.train_gec import train_gec_model
from src.gec.experiment_evaluator import run_full_experimental_evaluation
from src.gec.explainer import GrammarExplainer, validate_explainer_on_sample
from src.pipeline import IntegratedGrammarPipeline


def plot_confusion_matrices(baseline_cm: np.ndarray, bert_cm: np.ndarray, save_path: str = "reports/confusion_matrices.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Baseline
    sns.heatmap(baseline_cm, annot=True, fmt="d", cmap="Blues", ax=axes[0],
                xticklabels=["Correct (c)", "Incorrect (i)"],
                yticklabels=["Correct (c)", "Incorrect (i)"])
    axes[0].set_title("Baseline (Logistic Regression)\nConfusion Matrix")
    axes[0].set_xlabel("Predicted Label")
    axes[0].set_ylabel("True Label")
    
    # BERT
    sns.heatmap(bert_cm, annot=True, fmt="d", cmap="Greens", ax=axes[1],
                xticklabels=["Correct (c)", "Incorrect (i)"],
                yticklabels=["Correct (c)", "Incorrect (i)"])
    axes[1].set_title("BERT (bert-base-cased)\nConfusion Matrix")
    axes[1].set_xlabel("Predicted Label")
    axes[1].set_ylabel("True Label")
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[*] Matriz de confusión comparativa guardada en '{save_path}'")


def run_full_pipeline():
    print("=" * 80)
    print("  DETECCIÓN DE ERRORES GRAMATICALES (GED) - SISTEMA COMPLETO")
    print("  Fase 2: Preprocesamiento & Análisis Lingüístico")
    print("  Fase 3: Baseline (Regresión Logística / SVM) & Fine-Tuning BERT")
    print("=" * 80)
    
    os.makedirs("reports", exist_ok=True)
    os.makedirs("models/baseline", exist_ok=True)
    os.makedirs("models/bert_best_model", exist_ok=True)
    os.makedirs("predictions", exist_ok=True)
    
    train_tsv = "en_fce_train.tsv"
    dev_tsv = "en_fce_dev.tsv"
    realec_dev_tsv = "en_realec_dev.tsv"
    fce_test_tsv = "en_fce_test_unlabelled.tsv"
    realec_test_tsv = "en_realec_test_unlabelled.tsv"
    
    # -------------------------------------------------------------
    # 1. FASE 2: PREPROCESAMIENTO Y ANÁLISIS LINGÜÍSTICO
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 1. FASE 2: Preprocesamiento y Análisis de Datos")
    print("=" * 50)
    
    print("[*] Cargando oraciones y validando formatos...")
    train_sents = load_ged_tsv(train_tsv, is_labelled=True)
    dev_sents = load_ged_tsv(dev_tsv, is_labelled=True)
    realec_dev_sents = load_ged_tsv(realec_dev_tsv, is_labelled=True)
    
    train_stats = analyze_corpus_statistics(train_sents, "FCE Train")
    dev_stats = analyze_corpus_statistics(dev_sents, "FCE Dev")
    realec_stats = analyze_corpus_statistics(realec_dev_sents, "REALEC Dev")
    
    print(f"  - FCE Train:  {train_stats['num_sentences']:,} oraciones | {train_stats['num_tokens']:,} tokens | {train_stats['incorrect_tokens (i)']:,} errores ({train_stats['error_rate']:.2%})")
    print(f"  - FCE Dev:    {dev_stats['num_sentences']:,} oraciones | {dev_stats['num_tokens']:,} tokens | {dev_stats['incorrect_tokens (i)']:,} errores ({dev_stats['error_rate']:.2%})")
    print(f"  - REALEC Dev: {realec_stats['num_sentences']:,} oraciones | {realec_stats['num_tokens']:,} tokens | {realec_stats['incorrect_tokens (i)']:,} errores ({realec_stats['error_rate']:.2%})")
    
    # -------------------------------------------------------------
    # 2. FASE 3: MODELO DE REFERENCIA (BASELINE)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 2. FASE 3: Modelo de Referencia (Baseline con Características Lingüísticas)")
    print("=" * 50)
    
    print("[*] Extrayendo características lingüísticas con spaCy para FCE Dev...")
    X_dev_feats, y_dev = extract_features_and_labels_from_sentences(dev_sents)
    
    print("[*] Extrayendo características lingüísticas con spaCy para FCE Train (muestra representativa)...")
    # Para el baseline usamos un subconjunto representativo de 5.000 oraciones para ajuste rápido o completo
    sample_train_sents = train_sents[:6000]
    X_train_feats, y_train = extract_features_and_labels_from_sentences(sample_train_sents)
    
    print(f"[*] Entrenando Baseline (Regresión Logística con pesos balanceados)...")
    baseline_lr = BaselineGEDModel(model_type="logistic_regression", class_weight="balanced", C=1.0)
    baseline_lr.fit(X_train_feats, y_train)
    baseline_lr.save("models/baseline", prefix="best_baseline")
    
    print("[*] Evaluando Baseline en FCE Dev...")
    baseline_dev_metrics = baseline_lr.evaluate(X_dev_feats, y_dev)
    b_err = baseline_dev_metrics["error_class"]
    print(f"  Baseline FCE Dev -> Precision (i): {b_err['precision']:.4f} | Recall (i): {b_err['recall']:.4f} | F1 (i): {b_err['f1']:.4f} | F0.5 (i): {b_err['f0.5']:.4f}")
    
    # -------------------------------------------------------------
    # 3. FASE 3: FINE-TUNING DEL MODELO BERT (bert-base-cased)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 3. FASE 3: Fine-Tuning de BERT (bert-base-cased)")
    print("=" * 50)
    
    trainer, bert_summary, tokenizer = train_bert_model(
        train_tsv=train_tsv,
        dev_tsv=dev_tsv,
        realec_dev_tsv=realec_dev_tsv,
        model_name="bert-base-cased",
        output_dir="models/bert_best_model",
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        learning_rate=3e-5,
        max_length=80
    )
    
    # -------------------------------------------------------------
    # 4. EVALUACIÓN Y MATRICES DE CONFUSIÓN
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 4. Comparación y Generación de Reportes")
    print("=" * 50)
    
    bert_eval = bert_summary["fce_dev_metrics"]
    baseline_cm_mat = np.array(baseline_dev_metrics["confusion_matrix"]["matrix"])
    
    # Calcular matriz de confusión exacta de BERT sobre FCE dev
    print("[*] Generando predicciones completas de BERT sobre FCE Dev para matriz de confusión...")
    dev_preds_raw = trainer.predict(trainer.eval_dataset)
    dev_logits = dev_preds_raw.predictions
    dev_labels = dev_preds_raw.label_ids
    
    pred_classes = np.argmax(dev_logits, axis=-1)
    
    y_true_all = []
    y_pred_all = []
    for i in range(len(dev_labels)):
        for j in range(len(dev_labels[i])):
            if dev_labels[i][j] != -100:
                y_true_all.append(dev_labels[i][j])
                y_pred_all.append(pred_classes[i][j])
                
    bert_metrics_full = compute_ged_metrics(y_true_all, y_pred_all)
    bert_cm_mat = np.array(bert_metrics_full["confusion_matrix"]["matrix"])
    
    plot_confusion_matrices(baseline_cm_mat, bert_cm_mat, "reports/confusion_matrices.png")
    
    # Tabla comparativa
    comparison_df = pd.DataFrame([
        {
            "Modelo": "Baseline (Regresión Logística + spaCy)",
            "Precision (i)": f"{b_err['precision']:.4f}",
            "Recall (i)": f"{b_err['recall']:.4f}",
            "F1-Score (i)": f"{b_err['f1']:.4f}",
            "F0.5-Score (i)": f"{b_err['f0.5']:.4f}",
            "Accuracy": f"{baseline_dev_metrics['accuracy']:.4f}"
        },
        {
            "Modelo": "BERT (bert-base-cased fine-tuned)",
            "Precision (i)": f"{bert_metrics_full['error_class']['precision']:.4f}",
            "Recall (i)": f"{bert_metrics_full['error_class']['recall']:.4f}",
            "F1-Score (i)": f"{bert_metrics_full['error_class']['f1']:.4f}",
            "F0.5-Score (i)": f"{bert_metrics_full['error_class']['f0.5']:.4f}",
            "Accuracy": f"{bert_metrics_full['accuracy']:.4f}"
        }
    ])
    
    print("\nTABLA COMPARATIVA DE RENDIMIENTO (FCE DEV):")
    print(comparison_df.to_string(index=False))
    
    comparison_df.to_csv("reports/model_comparison.csv", index=False)
    
    # -------------------------------------------------------------
    # 5. GENERACIÓN DE PREDICCIONES PARA TEST SIN ETIQUETAS
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 5. Generación de Predicciones sobre Conjuntos de Prueba")
    print("=" * 50)
    
    if os.path.exists(fce_test_tsv):
        print(f"[*] Prediciendo {fce_test_tsv} -> predictions/en_fce_test_predictions.tsv...")
        predict_unlabelled_tsv("models/bert_best_model", fce_test_tsv, "predictions/en_fce_test_predictions.tsv")
        
    if os.path.exists(realec_test_tsv):
        print(f"[*] Prediciendo {realec_test_tsv} -> predictions/en_realec_test_predictions.tsv...")
        predict_unlabelled_tsv("models/bert_best_model", realec_test_tsv, "predictions/en_realec_test_predictions.tsv")
        
    # -------------------------------------------------------------
    # 6. DEMOSTRACIÓN DE INFERENCIA Y RESALTADO DE ERRORES (UI READY)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 6. Demostración de Inferencia y Offsets para Interfaz de Usuario")
    print("=" * 50)
    
    detector = GrammaticalErrorDetector("models/bert_best_model")
    sample_text = "I saws the show's advertisement hanging up of a wall in London where I was spending my holiday with some friends."
    demo_result = detector.detect_errors_in_text(sample_text)
    
    print(f"\nTexto de entrada: \"{sample_text}\"")
    print(f"Errores detectados: {demo_result['total_errors']}")
    for sent in demo_result["sentences"]:
        for tok in sent["tokens"]:
            if tok["is_error"]:
                print(f"  [ERROR] Token: '{tok['token']}' | Posición: [{tok['start_char']}:{tok['end_char']}] | Probabilidad error: {tok['error_probability']:.2%}")
                
def run_explanation_pipeline():
    print("=" * 80)
    print("  EXPLICACIÓN PEDAGÓGICA DE CORRECCIONES GRAMATICALES (GEC)")
    print("  Fase 8: Clasificación y Explicación de Correcciones para Aprendices de Inglés")
    print("=" * 80)
    
    os.makedirs("reports", exist_ok=True)
    finetuned_path = "models/gec_finetuned_model"
    model_path = finetuned_path if (os.path.exists(os.path.join(finetuned_path, "model.safetensors")) or os.path.exists(os.path.join(finetuned_path, "pytorch_model.bin"))) else "Unbabel/gec-t5_small"
    
    corrector = GrammarCorrector(model_path)
    explainer = GrammarExplainer()
    
    print("\n[*] Validando batería representativa de explicaciones gramaticales...")
    val_summary = validate_explainer_on_sample(explainer, "reports/gec_explanation_validation_report.md")
    print(f"  - Total casos validados: {val_summary['total_test_cases']}")
    print(f"  - Distribución por certeza: {val_summary['confidence_counts']}")
    
    demo_sentences = [
        "She go to school yesterday and saw two apple .",
        "Because I intend to take examination in Septenber .",
        "I am looking forward to hear from you soon ."
    ]
    
    print("\n" + "=" * 50)
    print(">>> Demostración Interactiva de Explicaciones Pedagógicas")
    print("=" * 50)
    for text in demo_sentences:
        res = explainer.explain_and_correct(text, corrector)
        print(f"\n[TEXTO ORIGINAL]:  \"{res['original_text']}\"")
        print(f"[TEXTO CORREGIDO]: \"{res['corrected_text']}\"")
        print(f"Ediciones identificadas: {res['total_edits']} (Latencia: {res['inference_time_ms']} ms)")
        for exp in res["explanations"]:
            print(f"  - [#{exp['edit_index']}] Categoría: {exp['category_name']} ({exp['category_name_en']}) | Certeza: {exp['confidence'].upper()}")
            print(f"    Cambio: '{exp['original_fragment']}' -> '{exp['corrected_fragment']}' [Span: {exp['char_span']['start']}:{exp['char_span']['end']}]")
            print(f"    Explicación: {exp['summary']}")
            print(f"    Regla: {exp['rule_explanation']}")
            print(f"    Ejemplo: [Incorrecto: {exp['example']['incorrect']}] | [Correcto: {exp['example']['correct']}]")
    
    print("\n" + "=" * 80)
    print("  FASE 8 COMPLETADA EXITOSAMENTE")
    print("=" * 80)


def run_gec_pipeline(train_if_needed: bool = True):
    print("=" * 80)
    print("  CORRECCIÓN DE ERRORES GRAMATICALES (GEC) - SISTEMA COMPLETO")
    print("  Fase 4: Preparación del Corpus FCE (M2 to Pairs)")
    print("  Fase 5: Integración del Modelo GEC Seq2Seq, Benchmark y Línea Base")
    print("  Fase 6: Ajuste Fino del Modelo GEC (T5 Fine-Tuning)")
    print("  Fase 7: Evaluación Experimental de GED y GEC (Métricas ERRANT M2)")
    print("  Fase 8: Clasificación y Explicación Pedagógica de Correcciones")
    print("=" * 80)
    
    os.makedirs("data/gec", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("models/gec_finetuned_model", exist_ok=True)
    os.makedirs("predictions", exist_ok=True)

    # -------------------------------------------------------------
    # FASE 4: PREPARACIÓN DEL CORPUS FCE (M2 TO PAIRS)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 1. FASE 4: Preparación y Validación del Corpus FCE")
    print("=" * 50)
    
    dfs, stats = process_fce_corpus(
        train_m2_path="fce.train.gold.bea19.m2",
        dev_m2_path="fce.dev.gold.bea19.m2",
        test_m2_path="fce.test.gold.bea19.m2",
        output_dir="data/gec"
    )
    generate_quality_report(stats, output_report_dir="reports")
    
    for split, df in dfs.items():
        validate_reconstructed_dataset(df)
        print(f"  - Split '{split}': {len(df):,} pares generados ({stats[split]['changed_sentences']:,} con cambios, {stats[split]['unchanged_sentences']:,} sin cambios). Descartados: {stats[split]['discarded_examples']}.")

    # -------------------------------------------------------------
    # FASE 5: INTEGRACIÓN Y EVALUACIÓN DEL MODELO GEC PREENTRENADO
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 2. FASE 5: Integración y Evaluación de Modelo GEC Preentrenado (T5)")
    print("=" * 50)
    
    corrector = GrammarCorrector(model_name_or_path="Unbabel/gec-t5_small")
    
    print("\n[*] Ejecutando suite de pruebas lingüísticas iniciales...")
    bench_df = evaluate_initial_benchmark(corrector, output_dir="reports")
    print(bench_df[["category", "original_text", "corrected_text", "inference_time_ms"]].to_string(index=False))
    
    print("\n[*] Evaluando detección de sobre-correcciones innecesarias en oraciones correctas...")
    fp_stats = evaluate_unnecessary_corrections(corrector, fce_dev_gec_path="data/gec/fce_dev_gec.csv", num_samples=200)
    print(f"  - Tasa de preservación normalizada: {fp_stats['preservation_rate_normalized_pct']:.2f}% | Sobre-corrección: {fp_stats['false_positive_rate_normalized_pct']:.2f}%")
    
    print("\n[*] Estableciendo línea base del modelo preentrenado sobre FCE Dev completo...")
    base_stats = evaluate_fce_baseline(corrector, fce_dev_gec_path="data/gec/fce_dev_gec.csv", output_dir="reports")
    print(f"  - Exact Match Normalizado: {base_stats['exact_match_normalized_pct']:.2f}%")
    print(f"  - Preservación de Oraciones Limpias: {base_stats['clean_sentence_preservation_normalized_pct']:.2f}%")
    print(f"  - Throughput: {base_stats['throughput_sentences_per_sec']:.2f} oraciones/segundo (Latencia: {base_stats['avg_inference_latency_ms']:.2f} ms/oración)")

    # -------------------------------------------------------------
    # FASE 6: AJUSTE FINO DEL MODELO GEC (T5 FINE-TUNING)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 3. FASE 6: Ajuste Fino del Modelo GEC Seq2Seq")
    print("=" * 50)
    
    finetuned_path = "models/gec_finetuned_model"
    model_weights_exist = os.path.exists(os.path.join(finetuned_path, "model.safetensors")) or os.path.exists(os.path.join(finetuned_path, "pytorch_model.bin"))
    
    if not model_weights_exist and train_if_needed:
        print("[*] Iniciando entrenamiento de ajuste fino en FCE Train...")
        train_summary = train_gec_model(
            train_csv="data/gec/fce_train_gec.csv",
            dev_csv="data/gec/fce_dev_gec.csv",
            base_model_name="Unbabel/gec-t5_small",
            output_dir=finetuned_path,
            num_train_epochs=2,
            batch_size=16,
            learning_rate=3e-4
        )
        print(f"[*] Fine-tuning finalizado. Mejor pérdida de validación: {train_summary['best_eval_loss']:.4f}")
    else:
        print(f"[*] Modelo ajustado detectado en '{finetuned_path}'.")

    # -------------------------------------------------------------
    # FASE 7: EVALUACIÓN EXPERIMENTAL DE GED Y GEC (ERRANT M2)
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 4. FASE 7: Evaluación Experimental Consolidada de GED y GEC")
    print("=" * 50)
    
    exp_report = run_full_experimental_evaluation(
        dev_gold_m2="fce.dev.gold.bea19.m2",
        test_gold_m2="fce.test.gold.bea19.m2",
        finetuned_model_path=finetuned_path,
        pretrained_model_name="Unbabel/gec-t5_small",
        ged_eval_path="models/bert_best_model/evaluation_results.json",
        reports_dir="reports",
        predictions_dir="predictions"
    )

    # -------------------------------------------------------------
    # FASE 8: CLASIFICACIÓN Y EXPLICACIÓN PEDAGÓGICA DE CORRECCIONES
    # -------------------------------------------------------------
    print("\n" + "=" * 50)
    print(">>> 5. FASE 8: Clasificación y Explicación Pedagógica de Correcciones")
    print("=" * 50)
    
    explainer = GrammarExplainer()
    val_report = validate_explainer_on_sample(explainer, "reports/gec_explanation_validation_report.md")
    print(f"[*] Batería de validación de explicaciones generada en '{val_report['report_path']}'.")

    # Demostración interactiva con modelo ajustado y explicaciones
    finetuned_corr = GrammarCorrector(finetuned_path)
    sample_sentence = "I saws the show's advertisement hanging up of a wall in London ."
    explanation_demo = explainer.explain_and_correct(sample_sentence, finetuned_corr)
    
    print("\n" + "=" * 50)
    print(">>> Demostración de Corrección y Explicación Pedagógica (Fase 8)")
    print("=" * 50)
    print(f"  Original:  {explanation_demo['original_text']}")
    print(f"  Corregido: {explanation_demo['corrected_text']}")
    print(f"  Ediciones: {explanation_demo['total_edits']} ({explanation_demo['inference_time_ms']} ms)")
    for exp in explanation_demo["explanations"]:
        print(f"  - [{exp['category_name']}] ({exp['confidence'].upper()}): '{exp['original_fragment']}' -> '{exp['corrected_fragment']}'")
        print(f"    Explicación: {exp['summary']}")
        print(f"    Regla: {exp['rule_explanation']}")

    print("\n" + "=" * 80)
    print("  FASES 4, 5, 6, 7 Y 8 COMPLETADAS EXITOSAMENTE")
    print("=" * 80)


def run_integrated_pipeline():
    print("=" * 80)
    print("  PIPELINE INTEGRADO: DETECCIÓN (GED) + CORRECCIÓN (GEC) + EXPLICACIÓN")
    print("  Fase 9: Flujo de Análisis Unificado y Reconciliación de Resultados")
    print("=" * 80)
    
    pipeline = IntegratedGrammarPipeline()
    
    test_cases = [
        "She go to school yesterday and saw two apple .",
        "Because I intend to take examination in Septenber .",
        "He is very interested on learning English because it help him .",
        "The quick brown fox jumps over the lazy dog ."
    ]
    
    print("\n" + "=" * 50)
    print(">>> Demostración del Flujo Unificado y Reconciliación GED-GEC")
    print("=" * 50)
    
    for idx, text in enumerate(test_cases, 1):
        print(f"\n--- CASO #{idx} ---")
        print(f"[ORIGINAL]:   \"{text}\"")
        res = pipeline.process_text(text)
        
        if not res["success"]:
            print(f"[ERROR]: {res['error_type']} - {res['error_message']}")
            continue
            
        print(f"[CORREGIDO]:  \"{res['corrected_text']}\"")
        print(f"[MODIFICADO]: {res['is_changed']} | Errores GED detectados: {res['total_errors_detected']} | Ediciones GEC: {res['total_corrections_made']} | Latencia: {res['inference_time_ms']} ms")
        
        # Mostrar detalle de tokens detectados por BERT
        for sent in res["ged_results"]["sentences"]:
            error_toks = [f"'{t['token']}' ({t['error_probability']:.1%})" for t in sent["tokens"] if t["is_error"]]
            if error_toks:
                print(f"  * Tokens marcados por BERT GED: {', '.join(error_toks)}")
            else:
                print(f"  * Tokens marcados por BERT GED: Ninguno")
                
        # Mostrar explicaciones pedagógicas y reconciliación
        if res["explanations"]:
            print("  * Ediciones y Explicaciones Pedagógicas:")
            for exp in res["explanations"]:
                rec_badge = "[BERT+GEC COINCIDEN]" if exp["is_detected_by_ged"] else "[SOLO GEC]"
                print(f"    - [{exp['category_name']}] ({exp['confidence'].upper()}) {rec_badge}: '{exp['original_fragment']}' -> '{exp['corrected_fragment']}'")
                print(f"      Explicación: {exp['summary']}")
                print(f"      Regla: {exp['rule_explanation']}")
                print(f"      Ejemplo: [Incorrecto: {exp['example']['incorrect']}] | [Correcto: {exp['example']['correct']}]")
                
        rec = res["reconciliation"]
        print(f"  * Resumen de Reconciliación: Concordancia={rec['concordance_count']} | Solo GEC={rec['gec_only_count']} | Solo GED={rec['ged_only_count']} | Tasa Concordancia={rec['concordance_rate']:.1%}")

    print("\n" + "=" * 80)
    print("  FASE 9: PIPELINE INTEGRADO VALIDADO EXITOSAMENTE")
    print("=" * 80)


def run_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    print("=" * 80)
    print("  INICIANDO SERVIDOR API REST FASTAPI (GED + GEC + EXPLAIN)")
    print(f"  Host: {host} | Puerto: {port} | Docs: http://{host}:{port}/docs")
    print("=" * 80)
    import uvicorn
    uvicorn.run("src.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sistema Integral de Detección (GED), Corrección (GEC) y Explicación Gramatical")
    parser.add_argument("--mode", type=str, choices=["all", "ged", "gec", "train_gec", "evaluate", "explain", "pipeline", "api"], default="pipeline",
                        help="Modo: 'pipeline' (Fase 9 integrado), 'api' (Servidor FastAPI), 'ged' (Fases 2-3), 'gec' (Fases 4-8), 'train_gec' (Fase 6), 'evaluate' (Fase 7), 'explain' (Fase 8), o 'all'")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host para el servidor API")
    parser.add_argument("--port", type=int, default=8000, help="Puerto para el servidor API")
    args = parser.parse_args()

    if args.mode == "ged":
        run_full_pipeline()
    elif args.mode == "gec":
        run_gec_pipeline()
    elif args.mode == "train_gec":
        train_gec_model()
    elif args.mode == "evaluate":
        run_full_experimental_evaluation()
    elif args.mode == "explain":
        run_explanation_pipeline()
    elif args.mode == "pipeline":
        run_integrated_pipeline()
    elif args.mode == "api":
        run_api_server(host=args.host, port=args.port)
    else:
        run_full_pipeline()
        run_gec_pipeline()
        run_integrated_pipeline()
