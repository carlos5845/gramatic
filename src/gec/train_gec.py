import os
import sys
import time
import json
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class GECSeq2SeqDataset(Dataset):
    """
    Dataset para fine-tuning de modelos Seq2Seq en corrección gramatical (GEC).
    Tokeniza las oraciones originales (fuente) y las oraciones corregidas (objetivo),
    manejando el padding y el reemplazo de tokens de relleno por -100 para la pérdida.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        tokenizer: AutoTokenizer,
        max_source_length: int = 128,
        max_target_length: int = 128
    ):
        self.sources = [str(s) if pd.notna(s) else "" for s in df["original"]]
        self.targets = [str(t) if pd.notna(t) else "" for t in df["corrected"]]
        self.tokenizer = tokenizer
        self.max_source_length = max_source_length
        self.max_target_length = max_target_length

    def __len__(self) -> int:
        return len(self.sources)

    def __getitem__(self, idx: int) -> dict:
        source_text = self.sources[idx]
        target_text = self.targets[idx]

        model_inputs = self.tokenizer(
            source_text,
            max_length=self.max_source_length,
            truncation=True,
            padding=False
        )

        labels = self.tokenizer(
            text_target=target_text,
            max_length=self.max_target_length,
            truncation=True,
            padding=False
        )

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs


def plot_gec_training_curves(
    log_history: list,
    save_path: str = "reports/gec_training_curves.png"
):
    """
    Genera y guarda la gráfica de curvas de pérdida (Train Loss vs Eval Loss)
    para supervisar la convergencia y el control de sobreajuste.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    train_losses = []
    eval_losses = []
    
    for entry in log_history:
        if "loss" in entry and "epoch" in entry:
            train_losses.append((entry["epoch"], entry["loss"]))
        if "eval_loss" in entry and "epoch" in entry:
            eval_losses.append((entry["epoch"], entry["eval_loss"]))

    plt.figure(figsize=(8, 5))
    if train_losses:
        epochs_tr, losses_tr = zip(*train_losses)
        plt.plot(epochs_tr, losses_tr, label="Training Loss", color="#1f77b4", marker="o", linestyle="-")
    if eval_losses:
        epochs_ev, losses_ev = zip(*eval_losses)
        plt.plot(epochs_ev, losses_ev, label="Validation Loss (FCE Dev)", color="#d62728", marker="s", linestyle="--")

    plt.title("GEC T5 Fine-Tuning - Curvas de Pérdida (Control de Sobreajuste)", fontsize=12)
    plt.xlabel("Épocas", fontsize=11)
    plt.ylabel("Pérdida (Cross-Entropy Loss)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper right", fontsize=10)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info(f"Curvas de entrenamiento GEC guardadas en '{save_path}'.")


def train_gec_model(
    train_csv: str = "data/gec/fce_train_gec.csv",
    dev_csv: str = "data/gec/fce_dev_gec.csv",
    base_model_name: str = "Unbabel/gec-t5_small",
    output_dir: str = "models/gec_finetuned_model",
    num_train_epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 3e-4,
    weight_decay: float = 0.01,
    max_length: int = 128,
    patience: int = 2
) -> dict:
    """
    Ajusta finamente el modelo GEC Seq2Seq sobre el conjunto FCE Train,
    evaluando y seleccionando el mejor checkpoint en FCE Dev.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO FASE 6: AJUSTE FINO DEL MODELO GEC")
    logger.info(f"Modelo base: {base_model_name}")
    logger.info(f"Directorio de salida: {output_dir}")
    logger.info("=" * 60)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # 1. Cargar datos
    logger.info(f"Cargando datos de entrenamiento desde '{train_csv}' y validación desde '{dev_csv}'...")
    df_train = pd.read_csv(train_csv, keep_default_na=False)
    df_dev = pd.read_csv(dev_csv, keep_default_na=False)
    logger.info(f"Muestras Train: {len(df_train):,} | Muestras Dev: {len(df_dev):,}")

    # 2. Cargar tokenizador y modelo
    logger.info(f"Cargando tokenizador y pesos base de '{base_model_name}'...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(base_model_name, local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name, local_files_only=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(base_model_name)

    # 3. Preparar datasets y data collator
    train_dataset = GECSeq2SeqDataset(df_train, tokenizer, max_length, max_length)
    dev_dataset = GECSeq2SeqDataset(df_dev, tokenizer, max_length, max_length)
    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model, pad_to_multiple_of=8)

    # 4. Configurar argumentos de entrenamiento
    use_fp16 = torch.cuda.is_available()
    training_args = Seq2SeqTrainingArguments(
        output_dir=os.path.join(output_dir, "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        weight_decay=weight_decay,
        save_total_limit=1,
        num_train_epochs=num_train_epochs,
        predict_with_generate=False,
        fp16=use_fp16,
        logging_strategy="steps",
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        report_to="none",
        dataloader_num_workers=0
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=patience)]
    )

    # 5. Ejecutar Fine-Tuning
    start_time = time.time()
    logger.info("Iniciando ciclo de entrenamiento Seq2Seq...")
    train_result = trainer.train()
    total_train_time = time.time() - start_time
    logger.info(f"Entrenamiento completado en {total_train_time:.2f} segundos ({total_train_time/60:.2f} min).")

    # 6. Evaluación final sobre Dev con el mejor modelo
    eval_metrics = trainer.evaluate()
    logger.info(f"Métricas del mejor checkpoint en FCE Dev: {eval_metrics}")

    # 7. Guardar modelo y tokenizador final
    logger.info(f"Guardando el mejor modelo ajustado en '{output_dir}'...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    # 8. Guardar registros del experimento y gráficas
    log_history = trainer.state.log_history
    plot_gec_training_curves(log_history, "reports/gec_training_curves.png")

    summary = {
        "model_name": base_model_name,
        "fine_tuned_save_path": output_dir,
        "hyperparameters": {
            "num_train_epochs": num_train_epochs,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "weight_decay": weight_decay,
            "max_length": max_length,
            "fp16": use_fp16
        },
        "train_runtime_seconds": total_train_time,
        "train_samples_per_second": train_result.metrics.get("train_samples_per_second", 0),
        "best_eval_loss": eval_metrics.get("eval_loss", 0),
        "eval_metrics": eval_metrics,
        "log_history": log_history
    }

    metrics_file = os.path.join(output_dir, "training_metrics.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    logger.info(f"Métricas y registros guardados en '{metrics_file}'.")

    return summary


if __name__ == "__main__":
    train_gec_model()
