import os
import joblib
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

from src.metrics import compute_ged_metrics
from src.data_preprocessing import extract_linguistic_features_spacy, load_ged_tsv


def token_to_features(sent_feats: List[Dict[str, Any]], i: int) -> Dict[str, Any]:
    """
    Construye el vector de características enriquecido para el token i en una oración,
    incluyendo propiedades morfosintácticas y contexto de ventana [-2, -1, +1, +2].
    """
    token = sent_feats[i]
    total_len = len(sent_feats)
    
    feats = {
        "bias": 1.0,
        "word.lower": token["text"].lower(),
        "word.isupper": token["is_upper"],
        "word.istitle": token["is_title"],
        "word.isdigit": token["is_digit"],
        "word.ispunct": token["is_punct"],
        "word.isstop": token["is_stop"],
        "word.len": token["len"],
        "word.shape": token["shape"],
        "word.prefix_1": token["prefix"][:1],
        "word.prefix_2": token["prefix"][:2],
        "word.prefix_3": token["prefix"],
        "word.suffix_1": token["suffix"][-1:],
        "word.suffix_2": token["suffix"][-2:],
        "word.suffix_3": token["suffix"],
        "pos": token["pos"],
        "tag": token["tag"],
        "dep": token["dep"],
        "head_pos": token["head_pos"],
        "rel_pos": i / max(1, total_len),
        "is_first": (i == 0),
        "is_last": (i == total_len - 1)
    }
    
    # Contexto previo: token i-1
    if i > 0:
        prev_tok = sent_feats[i-1]
        feats.update({
            "-1:word.lower": prev_tok["text"].lower(),
            "-1:pos": prev_tok["pos"],
            "-1:tag": prev_tok["tag"],
            "-1:dep": prev_tok["dep"],
            "-1:word.istitle": prev_tok["is_title"],
            "-1:word.isupper": prev_tok["is_upper"],
            "-1:word.isstop": prev_tok["is_stop"],
            "bigram_prev_pos": f"{prev_tok['pos']}_{token['pos']}",
            "bigram_prev_tag": f"{prev_tok['tag']}_{token['tag']}"
        })
    else:
        feats["BOS"] = True  # Beginning of sentence
        
    # Contexto previo: token i-2
    if i > 1:
        prev2_tok = sent_feats[i-2]
        feats.update({
            "-2:word.lower": prev2_tok["text"].lower(),
            "-2:pos": prev2_tok["pos"],
            "-2:tag": prev2_tok["tag"]
        })
        
    # Contexto posterior: token i+1
    if i < total_len - 1:
        next_tok = sent_feats[i+1]
        feats.update({
            "+1:word.lower": next_tok["text"].lower(),
            "+1:pos": next_tok["pos"],
            "+1:tag": next_tok["tag"],
            "+1:dep": next_tok["dep"],
            "+1:word.istitle": next_tok["is_title"],
            "+1:word.isupper": next_tok["is_upper"],
            "+1:word.isstop": next_tok["is_stop"],
            "bigram_next_pos": f"{token['pos']}_{next_tok['pos']}",
            "bigram_next_tag": f"{token['tag']}_{next_tok['tag']}"
        })
    else:
        feats["EOS"] = True  # End of sentence
        
    # Contexto posterior: token i+2
    if i < total_len - 2:
        next2_tok = sent_feats[i+2]
        feats.update({
            "+2:word.lower": next2_tok["text"].lower(),
            "+2:pos": next2_tok["pos"],
            "+2:tag": next2_tok["tag"]
        })
        
    return feats


def extract_features_and_labels_from_sentences(
    sentences: List[Dict[str, Any]], 
    nlp=None
) -> Tuple[List[Dict[str, Any]], Optional[List[int]]]:
    """
    Extrae las características para todos los tokens del conjunto de oraciones.
    """
    sent_linguistic_feats = extract_linguistic_features_spacy(sentences, nlp=nlp)
    
    all_features = []
    all_labels = []
    has_labels = "label_ids" in sentences[0] if len(sentences) > 0 else False
    
    for s_idx, sent_feats in enumerate(sent_linguistic_feats):
        for i in range(len(sent_feats)):
            feat_dict = token_to_features(sent_feats, i)
            all_features.append(feat_dict)
            if has_labels:
                all_labels.append(sentences[s_idx]["label_ids"][i])
                
    return all_features, (all_labels if has_labels else None)


class BaselineGEDModel:
    """
    Modelo de referencia (Baseline) para detección de errores gramaticales basado en
    características lingüísticas + clasificador lineal (Logistic Regression / SVM).
    """
    def __init__(self, model_type: str = "logistic_regression", class_weight: str = "balanced", C: float = 1.0):
        self.model_type = model_type
        self.class_weight = class_weight
        self.C = C
        self.vectorizer = DictVectorizer(sparse=True)
        
        if model_type == "logistic_regression":
            self.classifier = LogisticRegression(
                C=self.C,
                class_weight=self.class_weight,
                max_iter=1000,
                solver="lbfgs",
                random_state=42
            )
        elif model_type == "svm":
            self.classifier = LinearSVC(
                C=self.C,
                class_weight=self.class_weight,
                max_iter=2000,
                random_state=42
            )
        else:
            raise ValueError(f"Tipo de modelo no reconocido: {model_type}")
            
        self.is_fitted = False
        
    def fit(self, X_features: List[Dict[str, Any]], y: List[int]):
        """
        Ajusta el vectorizador y el clasificador con las características lingüísticas.
        """
        X_vec = self.vectorizer.fit_transform(X_features)
        self.classifier.fit(X_vec, y)
        self.is_fitted = True
        return self
        
    def predict(self, X_features: List[Dict[str, Any]]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("El modelo no ha sido entrenado todavía.")
        X_vec = self.vectorizer.transform(X_features)
        return self.classifier.predict(X_vec)
        
    def predict_proba(self, X_features: List[Dict[str, Any]]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("El modelo no ha sido entrenado todavía.")
        X_vec = self.vectorizer.transform(X_features)
        if hasattr(self.classifier, "predict_proba"):
            return self.classifier.predict_proba(X_vec)
        else:
            # Para SVM (decision_function transformada a probabilidad con sigmoid)
            df = self.classifier.decision_function(X_vec)
            prob_i = 1.0 / (1.0 + np.exp(-df))
            return np.vstack([1.0 - prob_i, prob_i]).T
            
    def evaluate(self, X_features: List[Dict[str, Any]], y_true: List[int]) -> Dict[str, Any]:
        """
        Evalúa el modelo calculando Precision, Recall, F1, F0.5 y Matriz de confusión.
        """
        y_pred = self.predict(X_features)
        return compute_ged_metrics(y_true, y_pred.tolist())
        
    def save(self, output_dir: str, prefix: str = "baseline"):
        os.makedirs(output_dir, exist_ok=True)
        model_path = os.path.join(output_dir, f"{prefix}_{self.model_type}.joblib")
        joblib.dump({"vectorizer": self.vectorizer, "classifier": self.classifier, "model_type": self.model_type}, model_path)
        return model_path
        
    @classmethod
    def load(cls, model_path: str):
        data = joblib.load(model_path)
        instance = cls(model_type=data["model_type"])
        instance.vectorizer = data["vectorizer"]
        instance.classifier = data["classifier"]
        instance.is_fitted = True
        return instance
