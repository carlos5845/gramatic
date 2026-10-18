import os
import torch
import numpy as np
import pandas as pd
from src.metrics import compute_ged_metrics, compute_hf_metrics_fn
from src.data_preprocessing import (
    load_ged_tsv,
    analyze_corpus_statistics,
    validate_text_entry,
    extract_linguistic_features_spacy,
    align_labels_with_bert_subwords
)
from src.baseline import BaselineGEDModel, extract_features_and_labels_from_sentences
from src.gec.prepare_fce import M2Parser, validate_reconstructed_dataset
from src.gec.corrector import GrammarCorrector
from src.gec.train_gec import GECSeq2SeqDataset
from src.gec.evaluate_errant import ERRANTEvaluator
from src.gec.explainer import GrammarExplainer, TAXONOMY_CATEGORIES, validate_explainer_on_sample
from src.pipeline import IntegratedGrammarPipeline
from src.api.app import create_app
from fastapi.testclient import TestClient
from transformers import AutoTokenizer, AutoModelForTokenClassification


def test_quick():
    print("1. Testing validation...")
    val, msg = validate_text_entry("This is a valid English sentence.")
    assert val == True
    val_empty, _ = validate_text_entry("")
    assert val_empty == False
    print("   Validation OK!")

    print("2. Testing TSV loading...")
    dev_sents = load_ged_tsv("en_fce_dev.tsv", is_labelled=True)
    assert len(dev_sents) == 2191
    print(f"   Loaded {len(dev_sents)} sentences.")
    
    print("3. Testing metrics...")
    y_true = [0, 1, 0, 1, 0]
    y_pred = [0, 1, 0, 0, 0]
    m = compute_ged_metrics(y_true, y_pred)
    assert "error_class" in m
    assert m["error_class"]["f0.5"] > 0
    print(f"   Metrics OK: {m['error_class']}")
    
    print("4. Testing linguistic feature extraction and Baseline...")
    sample_sents = dev_sents[:20]
    feats, labels = extract_features_and_labels_from_sentences(sample_sents)
    assert len(feats) == len(labels)
    model = BaselineGEDModel(model_type="logistic_regression")
    model.fit(feats, labels)
    eval_res = model.evaluate(feats, labels)
    print(f"   Baseline fit & eval OK: {eval_res['accuracy']:.4f}")

    print("5. Testing Tokenizer & Subword alignment...")
    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    ds = align_labels_with_bert_subwords(sample_sents, tokenizer, max_length=64)
    assert "input_ids" in ds.column_names
    assert "labels" in ds.column_names
    print(f"   Dataset shape: {len(ds)} items.")

    print("6. Testing M2 Parser & Edit Application (Phase 4)...")
    sample_tokens = ["I", "have", "recieved", "the", "examination", "in", "Septenber", "."]
    sample_edits = [
        {"start": 2, "end": 3, "error_type": "R:SPELL", "correction": "received", "required": "REQUIRED", "comment": "-NONE-", "annotator_id": 0},
        {"start": 6, "end": 7, "error_type": "R:SPELL", "correction": "September", "required": "REQUIRED", "comment": "-NONE-", "annotator_id": 0},
    ]
    corr_tokens, is_valid, applied, issues = M2Parser.apply_edits_for_annotator(sample_tokens, sample_edits, 0)
    assert is_valid == True
    assert corr_tokens == ["I", "have", "received", "the", "examination", "in", "September", "."]
    print("   M2 reconstruction test OK:", " ".join(corr_tokens))

    print("7. Testing GEC GrammarCorrector Inference (Phase 5)...")
    corrector = GrammarCorrector()
    single_res = corrector.correct_sentence("She go to school yesterday .")
    assert len(single_res["corrected"]) > 0
    assert single_res["is_changed"] == True
    print(f"   GEC Single sentence correction OK: '{single_res['original']}' -> '{single_res['corrected']}' ({single_res['inference_time_ms']} ms)")

    batch_res = corrector.correct_batch(["I has a apple .", "This is correct ."])
    assert len(batch_res) == 2
    assert "apple" in batch_res[0]["corrected"]
    print(f"   GEC Batch correction OK: {len(batch_res)} sentences processed.")

    print("8. Testing GEC Dataset formatting (Phase 6)...")
    toy_df = pd.DataFrame({
        "original": ["I has apple .", "They goes ."],
        "corrected": ["I have an apple .", "They go ."]
    })
    t5_tok = AutoTokenizer.from_pretrained("Unbabel/gec-t5_small", local_files_only=True)
    gec_ds = GECSeq2SeqDataset(toy_df, t5_tok, max_source_length=32, max_target_length=32)
    assert len(gec_ds) == 2
    sample_item = gec_ds[0]
    assert "input_ids" in sample_item and "labels" in sample_item
    print("   GEC Seq2Seq Dataset formatting OK!")

    print("9. Testing ERRANT Evaluator & M2 metrics (Phase 7)...")
    errant_eval = ERRANTEvaluator()
    gold_dummy = [{
        "source_tokens": ["I", "has", "an", "apple", "."],
        "source_text": "I has an apple .",
        "annotator_edits": {0: [(1, 2, "R:VERB:SVA", "have")]}
    }]
    hyp_dummy_edits = [[(1, 2, "R:VERB:SVA", "have")]]
    eval_dummy_res = errant_eval.evaluate_m2(gold_dummy, hyp_dummy_edits, ["I have an apple ."])
    assert eval_dummy_res["true_positives"] == 1
    assert eval_dummy_res["precision"] == 1.0
    assert eval_dummy_res["recall"] == 1.0
    assert eval_dummy_res["f0.5"] == 1.0
    print("   ERRANT M2 scoring calculation OK!")

    print("10. Testing Fine-Tuned GEC Model loading...")
    if os.path.exists("models/gec_finetuned_model"):
        ft_corrector = GrammarCorrector("models/gec_finetuned_model")
        ft_out = ft_corrector.correct_sentence("I has a apple .")
        assert len(ft_out["corrected"]) > 0
        print(f"   Fine-Tuned GEC Model OK: '{ft_out['original']}' -> '{ft_out['corrected']}'")
    
    print("11. Testing GrammarExplainer & Taxonomy Rules (Phase 8)...")
    explainer = GrammarExplainer()
    test_exp = explainer.explain_correction("She go to school yesterday and saw two apple .", "She went to school yesterday and saw two apples .")
    assert test_exp["has_corrections"] == True
    assert test_exp["total_edits"] >= 2
    
    cats = [e["category_id"] for e in test_exp["explanations"]]
    assert "VERB_TENSE" in cats or "VERB_AGREEMENT" in cats
    assert "PLURALIZATION_NUMBER" in cats
    
    # Verificar spans de caracteres
    for e in test_exp["explanations"]:
        assert "char_span" in e and "rule_explanation" in e and "example" in e
        assert e["confidence"] in ["high", "medium", "uncertain"]
    
    # Test caso incierto / complejo
    complex_exp = explainer.explain_correction("Because I go .", "This is because I go .")
    assert complex_exp["total_edits"] > 0
    print(f"   GrammarExplainer & Rules OK: {len(test_exp['explanations'])} edits parsed with pedagogical explanations.")
    
    print("12. Testing IntegratedGrammarPipeline (Phase 9)...")
    pipeline = IntegratedGrammarPipeline(lazy_load=False)
    pipe_res = pipeline.process_text("She go to school yesterday and saw two apple .")
    assert pipe_res["success"] == True
    assert pipe_res["is_changed"] == True
    assert "ged_results" in pipe_res and "explanations" in pipe_res and "reconciliation" in pipe_res
    
    rec_summary = pipe_res["reconciliation"]
    assert "concordance_count" in rec_summary
    assert "concordance_rate" in rec_summary
    assert rec_summary["total_gec_edits"] >= 1
    
    # Probar validaciones del pipeline
    empty_res = pipeline.process_text("")
    assert empty_res["success"] == False
    assert empty_res["error_type"] == "EMPTY_INPUT"
    
    long_res = pipeline.process_text("word " * 600, max_chars=100)
    assert long_res["success"] == False
    assert long_res["error_type"] == "INPUT_TOO_LONG"
    
    invalid_res = pipeline.process_text("привет мир как дела")
    assert invalid_res["success"] == False
    assert invalid_res["error_type"] == "INVALID_LANGUAGE_INPUT"
    print(f"   IntegratedGrammarPipeline OK: Success={pipe_res['success']}, Edits={pipe_res['total_corrections_made']}, ConcordanceRate={rec_summary['concordance_rate']:.2%}")
    
    print("13. Testing FastAPI REST API Endpoints with TestClient (Phase 9)...")
    test_app = create_app()
    client = TestClient(test_app)
    
    # Root
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["status"] == "online"
    
    # Health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"
    assert "bert_ged" in r_health.json()["models_loaded"]
    
    # Taxonomy
    r_tax = client.get("/api/v1/taxonomy")
    assert r_tax.status_code == 200
    assert len(r_tax.json()) >= 10
    
    # Detect endpoint
    r_det = client.post("/api/v1/detect", json={"text": "She go to school ."})
    assert r_det.status_code == 200
    assert r_det.json()["success"] == True
    assert len(r_det.json()["sentences"]) > 0
    
    # Correct endpoint
    r_corr = client.post("/api/v1/correct", json={"text": "She go to school ."})
    assert r_corr.status_code == 200
    assert r_corr.json()["success"] == True
    assert len(r_corr.json()["corrected"]) > 0
    
    # Explain endpoint
    r_exp = client.post("/api/v1/explain", json={"text": "She go to school yesterday ."})
    assert r_exp.status_code == 200
    assert r_exp.json()["success"] == True
    
    # Analyze endpoint (full pipeline)
    r_ana = client.post("/api/v1/analyze", json={"text": "She go to school yesterday and saw two apple ."})
    assert r_ana.status_code == 200
    ana_data = r_ana.json()
    assert ana_data["success"] == True
    assert ana_data["is_changed"] == True
    assert len(ana_data["explanations"]) >= 1
    assert "reconciliation" in ana_data
    
    # Error cases: Empty input (400)
    r_err_empty = client.post("/api/v1/analyze", json={"text": "   "})
    assert r_err_empty.status_code == 400
    assert r_err_empty.json()["error_type"] == "EMPTY_INPUT"
    
    # Error cases: Non-English input (400)
    r_err_lang = client.post("/api/v1/analyze", json={"text": "这是非英语文本测试。"})
    assert r_err_lang.status_code == 400
    assert r_err_lang.json()["error_type"] == "INVALID_LANGUAGE_INPUT"
    
    # Error cases: Schema validation error (422)
    r_err_val = client.post("/api/v1/analyze", json={})
    assert r_err_val.status_code == 422
    assert r_err_val.json()["error_type"] == "VALIDATION_ERROR"
    
    print("   FastAPI REST API & Endpoints OK: All routes and error handlers validated.")
    
    print("\nAll unit and integration tests passed successfully!")


if __name__ == "__main__":
    test_quick()
