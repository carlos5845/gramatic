import numpy as np
from sklearn.metrics import precision_recall_fscore_support, fbeta_score, confusion_matrix, classification_report
from typing import Dict, List, Tuple, Any, Optional


def compute_ged_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
    """
    Calcula métricas clave para la detección de errores gramaticales (GED).
    Se enfoca en la clase de error 'i' (incorrecto, etiqueta 1) frente a 'c' (correcto, etiqueta 0).
    
    Métricas calculadas:
    - Precision (clase 'i' y global)
    - Recall (clase 'i' y global)
    - F1-score (clase 'i' y global)
    - F0.5-score (clase 'i', pondera más la precisión beta=0.5)
    - Matriz de confusión: [[TN, FP], [FN, TP]]
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Métricas específicas para la clase 1 ('i')
    prec_i, rec_i, f1_i, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[1], average=None, zero_division=0
    )
    p_i = float(prec_i[0]) if len(prec_i) > 0 else 0.0
    r_i = float(rec_i[0]) if len(rec_i) > 0 else 0.0
    f1_val_i = float(f1_i[0]) if len(f1_i) > 0 else 0.0
    
    # F0.5 score para la clase 1 ('i')
    f05_val_i = float(fbeta_score(y_true, y_pred, beta=0.5, pos_label=1, zero_division=0))
    
    # Métricas macro y weighted
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average='macro', zero_division=0
    )
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, average='weighted', zero_division=0
    )
    
    # Matriz de confusión
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)
    
    accuracy = float((tp + tn) / len(y_true)) if len(y_true) > 0 else 0.0
    
    return {
        "accuracy": accuracy,
        "error_class": {
            "precision": p_i,
            "recall": r_i,
            "f1": f1_val_i,
            "f0.5": f05_val_i,
            "support": int(np.sum(y_true == 1))
        },
        "macro_avg": {
            "precision": float(prec_macro),
            "recall": float(rec_macro),
            "f1": float(f1_macro)
        },
        "weighted_avg": {
            "precision": float(prec_weighted),
            "recall": float(rec_weighted),
            "f1": float(f1_weighted)
        },
        "confusion_matrix": {
            "matrix": cm.tolist(),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "classification_report": classification_report(
            y_true, y_pred, target_names=["c (Correct)", "i (Incorrect)"], zero_division=0
        )
    }


def compute_hf_metrics_fn(eval_preds) -> Dict[str, float]:
    """
    Función de métricas compatible con Hugging Face Trainer para Token Classification.
    Filtra los tokens especiales y subwords ignorados (con etiqueta -100).
    """
    logits, labels = eval_preds
    if isinstance(logits, tuple):
        logits = logits[0]
        
    predictions = np.argmax(logits, axis=2)
    
    # Filtrar tokens con label == -100
    true_labels = []
    pred_labels = []
    
    for i in range(len(labels)):
        for j in range(len(labels[i])):
            if labels[i][j] != -100:
                true_labels.append(labels[i][j])
                pred_labels.append(predictions[i][j])
                
    if len(true_labels) == 0:
        return {"f0.5": 0.0, "f1": 0.0, "precision": 0.0, "recall": 0.0}
        
    metrics = compute_ged_metrics(true_labels, pred_labels)
    
    return {
        "precision_i": metrics["error_class"]["precision"],
        "recall_i": metrics["error_class"]["recall"],
        "f1_i": metrics["error_class"]["f1"],
        "f0.5_i": metrics["error_class"]["f0.5"],
        "macro_f1": metrics["macro_avg"]["f1"],
        "accuracy": metrics["accuracy"]
    }
