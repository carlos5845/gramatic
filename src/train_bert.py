import os
import json
import torch
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForTokenClassification,
    set_seed
)
from datasets import DatasetDict

from src.data_preprocessing import LABEL2ID, ID2LABEL, prepare_ged_datasets, load_ged_tsv, align_labels_with_bert_subwords
from src.metrics import compute_hf_metrics_fn, compute_ged_metrics


def train_bert_model(
    train_tsv: str = "en_fce_train.tsv",
    dev_tsv: str = "en_fce_dev.tsv",
    realec_dev_tsv: Optional[str] = "en_realec_dev.tsv",
    model_name: str = "bert-base-cased",
    output_dir: str = "models/bert_best_model",
    num_train_epochs: int = 3,
    per_device_train_batch_size: int = 8,
    per_device_eval_batch_size: int = 16,
    learning_rate: float = 3e-5,
    max_length: int = 80,
    warmup_steps: int = 250,
    weight_decay: float = 0.01,
    seed: int = 42
) -> Tuple[Trainer, Dict[str, Any], Any]:
    """
    Fase 3: Entrenamiento y Fine-Tuning del modelo BERT (bert-base-cased) para Token Classification.
    Configura clasificación binaria por token ('c'=0, 'i'=1), optimiza con AdamW y selecciona
    el mejor modelo basado en F0.5/F1 sobre el conjunto de validación.
    """
    set_seed(seed)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Cargar Tokenizador y Preparar Datasets
    print(f"[*] Cargando tokenizador {model_name} y preparando datos...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    datasets, stats, _ = prepare_ged_datasets(
        train_path=train_tsv,
        dev_path=dev_tsv,
        realec_dev_path=realec_dev_tsv,
        tokenizer_name=model_name,
        max_length=max_length
    )
    
    # 2. Cargar Modelo Preentrenado con Cabeza de Clasificación de Tokens
    print(f"[*] Inicializando AutoModelForTokenClassification ({model_name}) con num_labels=2...")
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )
    
    # 3. Data Collator para padding dinámico si se requiere
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    
    # 4. Configurar Argumentos de Entrenamiento (TrainingArguments)
    training_args = TrainingArguments(
        output_dir=os.path.join(output_dir, "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        gradient_accumulation_steps=4,
        eval_accumulation_steps=10,
        num_train_epochs=num_train_epochs,
        weight_decay=weight_decay,
        warmup_steps=warmup_steps,
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="f0.5_i",
        greater_is_better=True,
        save_total_limit=1,
        seed=seed,
        fp16=torch.cuda.is_available(),
        report_to="none"
    )
    
    # 5. Instanciar Hugging Face Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_hf_metrics_fn
    )
    
    # 6. Entrenar el Modelo
    print(f"[*] Iniciando entrenamiento de BERT por {num_train_epochs} épocas...")
    train_result = trainer.train()
    
    # 7. Evaluar sobre FCE Dev (Validación oficial)
    print("[*] Evaluando mejor modelo sobre FCE Dev...")
    eval_metrics = trainer.evaluate(datasets["validation"])
    print(f"  Resultados FCE Dev -> Precision (i): {eval_metrics.get('eval_precision_i', 0):.4f}, "
          f"Recall (i): {eval_metrics.get('eval_recall_i', 0):.4f}, "
          f"F1 (i): {eval_metrics.get('eval_f1_i', 0):.4f}, "
          f"F0.5 (i): {eval_metrics.get('eval_f0.5_i', 0):.4f}")
    
    # 8. Evaluar Generalización en REALEC Dev (si está disponible)
    realec_metrics = {}
    if "realec_dev" in datasets:
        print("[*] Evaluando generalización sobre REALEC Dev...")
        realec_metrics = trainer.evaluate(datasets["realec_dev"], metric_key_prefix="realec")
        print(f"  Resultados REALEC Dev -> Precision (i): {realec_metrics.get('realec_precision_i', 0):.4f}, "
              f"Recall (i): {realec_metrics.get('realec_recall_i', 0):.4f}, "
              f"F1 (i): {realec_metrics.get('realec_f1_i', 0):.4f}, "
              f"F0.5 (i): {realec_metrics.get('realec_f0.5_i', 0):.4f}")
        
    # 9. Guardar Mejor Modelo, Tokenizador y Configuración
    print(f"[*] Guardando modelo óptimo, tokenizador y configuración en '{output_dir}'...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Guardar resumen de métricas en JSON
    results_summary = {
        "model_name": model_name,
        "hyperparameters": {
            "num_train_epochs": num_train_epochs,
            "learning_rate": learning_rate,
            "train_batch_size": per_device_train_batch_size,
            "max_length": max_length,
            "warmup_steps": warmup_steps,
            "weight_decay": weight_decay
        },
        "fce_dev_metrics": eval_metrics,
        "realec_dev_metrics": realec_metrics,
        "dataset_statistics": stats
    }
    
    with open(os.path.join(output_dir, "evaluation_results.json"), "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=4)
        
    return trainer, results_summary, tokenizer


def predict_unlabelled_tsv(
    model_dir: str,
    input_tsv: str,
    output_tsv: str,
    batch_size: int = 32,
    max_length: int = 128
):
    """
    Genera predicciones con etiquetas ('c' o 'i') para archivos de prueba sin etiquetas.
    Mantiene exactamente la estructura original de líneas y oraciones separadas por líneas en blanco.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForTokenClassification.from_pretrained(model_dir)
    model.eval()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    sentences = load_ged_tsv(input_tsv, is_labelled=False)
    
    all_predictions = []
    
    for sent in sentences:
        tokens = sent["tokens"]
        if not tokens:
            all_predictions.append([])
            continue
            
        encoding = tokenizer(
            [tokens],
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        )
        
        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits[0]
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            
        word_ids = encoding.word_ids(batch_index=0)
        
        token_labels = {}
        for idx, word_idx in enumerate(word_ids):
            if word_idx is not None and word_idx not in token_labels:
                # Asignar la predicción del primer subword al token
                token_labels[word_idx] = ID2LABEL[preds[idx]]
                
        sent_pred_labels = []
        for i in range(len(tokens)):
            label = token_labels.get(i, "c")
            sent_pred_labels.append(label)
            
        all_predictions.append(sent_pred_labels)
        
    # Escribir TSV de salida
    os.makedirs(os.path.dirname(output_tsv) if os.path.dirname(output_tsv) else ".", exist_ok=True)
    with open(output_tsv, "w", encoding="utf-8") as out_f:
        for s_idx, sent in enumerate(sentences):
            preds = all_predictions[s_idx]
            for t, l in zip(sent["tokens"], preds):
                out_f.write(f"{t}\t{l}\n")
            out_f.write("\n")
            
    print(f"[*] Predicciones guardadas exitosamente en {output_tsv}")
