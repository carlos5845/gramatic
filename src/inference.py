import os
import torch
from typing import List, Dict, Any, Optional
import spacy
from transformers import AutoModelForTokenClassification, AutoTokenizer

from src.data_preprocessing import ID2LABEL, validate_text_entry


class GrammaticalErrorDetector:
    """
    Detector de Errores Gramaticales para inferencia sobre texto libre o secuencias de tokens.
    Conserva los offsets de caracteres exactos (start_char, end_char) para facilitar el
    resaltado visual de errores en interfaces de usuario.
    """
    def __init__(self, model_path: str = "models/bert_best_model", device: Optional[str] = None):
        self.model_path = model_path
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
            
        print(f"[*] Cargando detector GED desde '{model_path}' en dispositivo: {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        self.nlp = spacy.load("en_core_web_sm", disable=["ner"])
        
    def detect_errors_in_text(self, text: str) -> Dict[str, Any]:
        """
        Procesa un texto completo:
        1. Valida la entrada.
        2. Segmenta en oraciones con spaCy.
        3. Tokeniza respetando posiciones originales.
        4. Clasifica cada token como 'c' (correcto) o 'i' (incorrecto).
        5. Retorna la estructura con tokens, etiquetas y offsets de caracteres.
        """
        is_valid, msg = validate_text_entry(text)
        if not is_valid:
            return {
                "success": False,
                "error_message": msg,
                "text": text,
                "sentences": []
            }
            
        doc = self.nlp(text)
        sentence_results = []
        
        for sent_idx, sent in enumerate(doc.sents):
            tokens = [t.text for t in sent]
            offsets = [(t.idx, t.idx + len(t.text)) for t in sent]
            
            if not tokens:
                continue
                
            encoding = self.tokenizer(
                [tokens],
                is_split_into_words=True,
                return_tensors="pt",
                truncation=True,
                max_length=128
            )
            
            input_ids = encoding["input_ids"].to(self.device)
            attention_mask = encoding["attention_mask"].to(self.device)
            
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits[0]
                probabilities = torch.softmax(logits, dim=-1).cpu().numpy()
                preds = torch.argmax(logits, dim=-1).cpu().numpy()
                
            word_ids = encoding.word_ids(batch_index=0)
            
            token_preds = {}
            token_probs = {}
            for idx, word_idx in enumerate(word_ids):
                if word_idx is not None and word_idx not in token_preds:
                    token_preds[word_idx] = ID2LABEL[preds[idx]]
                    token_probs[word_idx] = float(probabilities[idx][1]) # Probabilidad de error ('i')
                    
            detected_tokens = []
            for i in range(len(tokens)):
                label = token_preds.get(i, "c")
                prob_error = token_probs.get(i, 0.0)
                detected_tokens.append({
                    "token": tokens[i],
                    "label": label,
                    "is_error": (label == "i"),
                    "error_probability": prob_error,
                    "start_char": offsets[i][0],
                    "end_char": offsets[i][1]
                })
                
            sentence_results.append({
                "sentence_index": sent_idx,
                "sentence_text": sent.text,
                "tokens": detected_tokens,
                "error_count": sum(1 for t in detected_tokens if t["is_error"])
            })
            
        total_errors = sum(s["error_count"] for s in sentence_results)
        
        return {
            "success": True,
            "text": text,
            "total_errors": total_errors,
            "sentences": sentence_results
        }
