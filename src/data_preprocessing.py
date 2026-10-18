import os
import re
from typing import List, Dict, Tuple, Any, Optional
import spacy
from datasets import Dataset, DatasetDict
from transformers import PreTrainedTokenizerFast, AutoTokenizer


# Mapeo oficial de etiquetas
LABEL2ID = {"c": 0, "i": 1}
ID2LABEL = {0: "c", 1: "i"}


def validate_text_entry(text: str) -> Tuple[bool, str]:
    """
    Valida que la entrada no esté vacía y que corresponda a texto en inglés válido.
    Retorna (es_valido, mensaje_error).
    """
    if not text or not text.strip():
        return False, "La entrada está vacía o contiene solo espacios en blanco."
    
    # Comprobar proporción de caracteres alfabéticos latinos / ASCII
    cleaned = text.strip()
    alpha_chars = [c for c in cleaned if c.isalpha()]
    if not alpha_chars:
        return False, "La entrada no contiene caracteres alfabéticos legibles."
        
    ascii_latin_ratio = sum(1 for c in alpha_chars if ord(c) < 256) / len(alpha_chars)
    if ascii_latin_ratio < 0.80:
        return False, "La entrada contiene una proporción alta de caracteres fuera del alfabeto latino/inglés."
        
    return True, "Entrada válida."


def load_ged_tsv(file_path: str, is_labelled: bool = True) -> List[Dict[str, Any]]:
    """
    Carga un archivo TSV de MultiGED/FCE/REALEC.
    Cada línea contiene: 'token \\t etiqueta' o solo 'token' (si is_labelled=False).
    Las oraciones están separadas por líneas vacías.
    
    Retorna una lista de diccionarios por oración:
    {
        "sentence_id": int,
        "tokens": List[str],
        "labels": List[str] (si is_labelled),
        "label_ids": List[int] (si is_labelled),
        "offsets": List[Tuple[int, int]], # (start_char, end_char)
        "sentence_text": str
    }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
        
    sentences = []
    current_tokens = []
    current_labels = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line:
                if current_tokens:
                    # Construir la oración y calcular offsets
                    sentence_data = _build_sentence_record(
                        current_tokens, 
                        current_labels if is_labelled else None, 
                        len(sentences)
                    )
                    sentences.append(sentence_data)
                    current_tokens = []
                    current_labels = []
            else:
                parts = line.split("\t")
                token = parts[0]
                if is_labelled:
                    label = parts[1] if len(parts) > 1 else "c"
                    current_tokens.append(token)
                    current_labels.append(label)
                else:
                    current_tokens.append(token)
                    
        # Última oración si el archivo no termina en línea vacía
        if current_tokens:
            sentence_data = _build_sentence_record(
                current_tokens, 
                current_labels if is_labelled else None, 
                len(sentences)
            )
            sentences.append(sentence_data)
            
    return sentences


def _build_sentence_record(tokens: List[str], labels: Optional[List[str]], sentence_id: int) -> Dict[str, Any]:
    """
    Reconstruye el texto continuo de la oración y conserva los offsets exactos
    (inicio y fin de cada token) para permitir el resaltado en la interfaz de usuario.
    """
    sentence_text = ""
    offsets = []
    
    for i, token in enumerate(tokens):
        # Determinar si se necesita un espacio antes del token
        # Respetar signos de puntuación pegados cuando corresponda o usar espacio simple
        if i > 0:
            # Si el token es un signo de puntuación común (.,!?;:), usualmente se adhiere
            if token in {".", ",", "!", "?", ";", ":", "'s", "n't", "'m", "'re", "'ve", "'ll", "'d", "%", ")"}:
                pass
            elif tokens[i-1] in {"(", "\"", "“", "‘"}:
                pass
            else:
                sentence_text += " "
                
        start_char = len(sentence_text)
        sentence_text += token
        end_char = len(sentence_text)
        offsets.append((start_char, end_char))
        
    record = {
        "sentence_id": sentence_id,
        "tokens": tokens,
        "offsets": offsets,
        "sentence_text": sentence_text
    }
    
    if labels is not None:
        record["labels"] = labels
        record["label_ids"] = [LABEL2ID.get(l, 0) for l in labels]
        
    return record


def analyze_corpus_statistics(sentences: List[Dict[str, Any]], corpus_name: str = "Corpus") -> Dict[str, Any]:
    """
    Analiza la distribución de clases, cantidad de oraciones y tokens.
    """
    num_sentences = len(sentences)
    num_tokens = sum(len(s["tokens"]) for s in sentences)
    
    has_labels = "label_ids" in sentences[0] if num_sentences > 0 else False
    
    c_count = 0
    i_count = 0
    if has_labels:
        for s in sentences:
            for lid in s["label_ids"]:
                if lid == 1:
                    i_count += 1
                else:
                    c_count += 1
                    
    error_rate = (i_count / num_tokens) if num_tokens > 0 else 0.0
    
    stats = {
        "corpus_name": corpus_name,
        "num_sentences": num_sentences,
        "num_tokens": num_tokens,
        "has_labels": has_labels,
        "correct_tokens (c)": c_count,
        "incorrect_tokens (i)": i_count,
        "error_rate": error_rate,
        "class_weights": {
            0: (num_tokens / (2.0 * c_count)) if c_count > 0 else 1.0,
            1: (num_tokens / (2.0 * i_count)) if i_count > 0 else 1.0
        } if has_labels and c_count > 0 and i_count > 0 else {}
    }
    return stats


def extract_linguistic_features_spacy(sentences: List[Dict[str, Any]], nlp=None) -> List[List[Dict[str, Any]]]:
    """
    Extrae características lingüísticas utilizando spaCy respetando los tokens originales.
    IMPORTANTE: No se aplica lematización destructiva ni eliminación de stopwords,
    manteniendo la información morfosintáctica y posicional.
    """
    if nlp is None:
        nlp = spacy.load("en_core_web_sm", disable=["ner"])
        
    all_sentence_features = []
    
    for s_idx, sent_data in enumerate(sentences):
        tokens = sent_data["tokens"]
        # Crear Doc de spaCy usando directamente los tokens originales (is_split_into_words)
        doc = spacy.tokens.Doc(nlp.vocab, words=tokens)
        
        # Ejecutar los componentes de POS y parser sintáctico
        for name, proc in nlp.pipeline:
            if name not in ["ner"]:
                doc = proc(doc)
                
        sent_feats = []
        for i, token in enumerate(doc):
            feat = {
                "text": token.text,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "head": token.head.text,
                "head_pos": token.head.pos_,
                "is_alpha": token.is_alpha,
                "is_digit": token.is_digit,
                "is_title": token.text.istitle(),
                "is_upper": token.text.isupper(),
                "is_lower": token.text.islower(),
                "is_punct": token.is_punct,
                "is_stop": token.is_stop,
                "len": len(token.text),
                "shape": token.shape_,
                "prefix": token.text[:3].lower(),
                "suffix": token.text[-3:].lower(),
            }
            sent_feats.append(feat)
            
        all_sentence_features.append(sent_feats)
        
    return all_sentence_features


def align_labels_with_bert_subwords(
    sentences: List[Dict[str, Any]], 
    tokenizer: PreTrainedTokenizerFast,
    max_length: int = 128,
    label_all_subwords: bool = False
) -> Dataset:
    """
    Convierte las oraciones a un Dataset de Hugging Face y alinea las etiquetas de MultiGED
    con los subwords generados por el tokenizador de BERT (bert-base-cased).
    
    Reglas de alineación:
    - Tokens especiales ([CLS], [SEP], [PAD]) reciben etiqueta -100 para ignorarlos en la pérdida.
    - El primer subword de un token recibe la etiqueta original (0 o 1).
    - Los subwords subsecuentes reciben -100 (si label_all_subwords=False) para evaluar a nivel de palabra.
    """
    token_list = [s["tokens"] for s in sentences]
    has_labels = "label_ids" in sentences[0]
    labels_list = [s["label_ids"] for s in sentences] if has_labels else None
    
    tokenized_inputs = tokenizer(
        token_list,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        is_split_into_words=True,
        return_offsets_mapping=True,
        return_overflowing_tokens=False
    )
    
    if has_labels:
        aligned_labels = []
        for i, labels in enumerate(labels_list):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            
            for word_idx in word_ids:
                if word_idx is None:
                    # Token especial ([CLS], [SEP], [PAD])
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:
                    # Primer subword del token original
                    if word_idx < len(labels):
                        label_ids.append(labels[word_idx])
                    else:
                        label_ids.append(-100)
                else:
                    # Subwords subsecuentes de la misma palabra
                    if label_all_subwords and word_idx < len(labels):
                        label_ids.append(labels[word_idx])
                    else:
                        label_ids.append(-100)
                previous_word_idx = word_idx
                
            aligned_labels.append(label_ids)
            
        tokenized_inputs["labels"] = aligned_labels
        
    # Convertir a Dataset de Hugging Face
    dataset_dict = {
        "input_ids": tokenized_inputs["input_ids"],
        "attention_mask": tokenized_inputs["attention_mask"],
    }
    if "token_type_ids" in tokenized_inputs:
        dataset_dict["token_type_ids"] = tokenized_inputs["token_type_ids"]
    if has_labels:
        dataset_dict["labels"] = tokenized_inputs["labels"]
        
    return Dataset.from_dict(dataset_dict)


def prepare_ged_datasets(
    train_path: str,
    dev_path: str,
    realec_dev_path: Optional[str] = None,
    tokenizer_name: str = "bert-base-cased",
    max_length: int = 128
) -> Tuple[DatasetDict, Dict[str, Any], Any]:
    """
    Función de orquestación completa para la Fase 2:
    - Carga TSVs
    - Analiza estadísticas
    - Inicializa tokenizador BERT
    - Genera DatasetDict compatible con Hugging Face
    """
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    
    train_sents = load_ged_tsv(train_path, is_labelled=True)
    dev_sents = load_ged_tsv(dev_path, is_labelled=True)
    
    train_stats = analyze_corpus_statistics(train_sents, "FCE Train")
    dev_stats = analyze_corpus_statistics(dev_sents, "FCE Dev")
    
    train_ds = align_labels_with_bert_subwords(train_sents, tokenizer, max_length=max_length)
    dev_ds = align_labels_with_bert_subwords(dev_sents, tokenizer, max_length=max_length)
    
    datasets_map = {
        "train": train_ds,
        "validation": dev_ds
    }
    stats_map = {
        "train": train_stats,
        "validation": dev_stats
    }
    
    if realec_dev_path and os.path.exists(realec_dev_path):
        realec_sents = load_ged_tsv(realec_dev_path, is_labelled=True)
        realec_stats = analyze_corpus_statistics(realec_sents, "REALEC Dev")
        realec_ds = align_labels_with_bert_subwords(realec_sents, tokenizer, max_length=max_length)
        datasets_map["realec_dev"] = realec_ds
        stats_map["realec_dev"] = realec_stats
        
    return DatasetDict(datasets_map), stats_map, tokenizer
