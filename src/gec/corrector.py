import os
import time
import logging
from typing import List, Dict, Any, Optional, Union
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class GrammarCorrector:
    """
    Módulo de Inferencia para Corrección Gramatical de Texto (GEC).
    Basado en modelos Seq2Seq preentrenados (e.g. Unbabel/gec-t5_small).
    Proporciona corrección de oraciones individuales y procesamiento por lotes (batching),
    con medición precisa de tiempos de inferencia y detección de modificaciones.
    """

    def __init__(
        self,
        model_name_or_path: str = "Unbabel/gec-t5_small",
        device: Optional[str] = None,
        use_half_precision: bool = False
    ):
        self.model_name = model_name_or_path
        
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Cargando modelo GEC '{self.model_name}' en dispositivo: {self.device}...")
        
        # Intentar cargar con local_files_only primero si ya está en caché para evitar demoras de red
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, local_files_only=True)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

        if use_half_precision and self.device.type == "cuda":
            self.model = self.model.half()

        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Modelo GEC inicializado correctamente. Parámetros: {sum(p.numel() for p in self.model.parameters()):,}")

    def correct_sentence(
        self,
        sentence: str,
        max_length: int = 128,
        num_beams: int = 4
    ) -> Dict[str, Any]:
        """
        Corrige una única oración en inglés.
        
        Retorna:
        - original: texto de entrada
        - corrected: texto generado por el modelo
        - is_changed: booleano indicando si el texto fue modificado
        - inference_time_ms: tiempo de inferencia en milisegundos
        """
        if not sentence or not sentence.strip():
            return {
                "original": sentence,
                "corrected": sentence,
                "is_changed": False,
                "inference_time_ms": 0.0
            }

        cleaned_text = sentence.strip()
        t0 = time.perf_counter()

        inputs = self.tokenizer(
            cleaned_text,
            return_tensors="pt",
            max_length=max_length,
            truncation=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True
            )

        corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "original": cleaned_text,
            "corrected": corrected,
            "is_changed": (cleaned_text.lower().replace(" ", "") != corrected.lower().replace(" ", "") or cleaned_text != corrected),
            "inference_time_ms": round(elapsed_ms, 2)
        }

    def correct_batch(
        self,
        sentences: List[str],
        batch_size: int = 16,
        max_length: int = 128,
        num_beams: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Corrige un lote de oraciones optimizando la inferencia en GPU/CPU.
        """
        results = []
        if not sentences:
            return results

        for i in range(0, len(sentences), batch_size):
            batch_texts = [s.strip() for s in sentences[i:i + batch_size]]
            t0 = time.perf_counter()

            inputs = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True
                )

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            per_item_ms = elapsed_ms / max(1, len(batch_texts))

            decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)

            for original, corrected in zip(batch_texts, decoded):
                corr_clean = corrected.strip()
                is_changed = (original.lower().replace(" ", "") != corr_clean.lower().replace(" ", "") or original != corr_clean)
                results.append({
                    "original": original,
                    "corrected": corr_clean,
                    "is_changed": is_changed,
                    "inference_time_ms": round(per_item_ms, 2)
                })

        return results


def run_initial_tests_suite(corrector: GrammarCorrector) -> List[Dict[str, Any]]:
    """
    Diseña y ejecuta la suite de pruebas iniciales con oraciones representativas:
    - Oraciones correctas (sin error)
    - Errores de concordancia (Subject-Verb Agreement)
    - Errores de tiempos verbales (Verb Tense / Aspect)
    - Errores de artículos y determinantes (Articles / Determiners)
    - Errores de preposiciones (Prepositions)
    - Errores múltiples / complejos
    """
    test_cases = [
        # 1. Oraciones correctas
        {
            "category": "Correct Sentence",
            "description": "Oración simple correcta sin errores",
            "input": "This is a completely correct sentence .",
            "expected_intent": "Conservar el texto sin alteraciones innecesarias"
        },
        {
            "category": "Correct Sentence",
            "description": "Oración formal correcta con cláusula subordinada",
            "input": "I am writing to inform you that I have received the package .",
            "expected_intent": "Conservar el texto idéntico"
        },
        # 2. Concordancia sujeto-verbo (SVA)
        {
            "category": "Subject-Verb Agreement",
            "description": "Error en tercera persona singular (She go -> She goes)",
            "input": "She go to work by bus every morning .",
            "expected_intent": "Corregir 'go' por 'goes'"
        },
        {
            "category": "Subject-Verb Agreement",
            "description": "Sujeto plural con verbo singular (They is -> They are)",
            "input": "They is very happy with the results of the project .",
            "expected_intent": "Corregir 'is' por 'are'"
        },
        # 3. Tiempos verbales (Verb Tense)
        {
            "category": "Verb Tense",
            "description": "Tiempo pasado con marcador temporal (saw/saws -> saw, go yesterday -> went)",
            "input": "Yesterday I see my old friend at the train station .",
            "expected_intent": "Corregir 'see' por 'saw'"
        },
        {
            "category": "Verb Tense",
            "description": "Incoherencia en tiempo verbal compuesto",
            "input": "He has went to London three times this year .",
            "expected_intent": "Corregir 'went' por 'gone'"
        },
        # 4. Artículos y determinantes (Articles / Determiners)
        {
            "category": "Articles & Determiners",
            "description": "Artículo indefinido incorrecto antes de vocal (a apple -> an apple)",
            "input": "I would like to eat a apple and a orange .",
            "expected_intent": "Corregir 'a apple' por 'an apple' y 'a orange' por 'an orange'"
        },
        {
            "category": "Articles & Determiners",
            "description": "Omisión de artículo determinado o indefinido",
            "input": "Because I intend to take examination in September .",
            "expected_intent": "Insertar artículo 'an examination'"
        },
        # 5. Preposiciones (Prepositions)
        {
            "category": "Prepositions",
            "description": "Preposición dependiente incorrecta (interested on -> interested in)",
            "input": "I am very interested on learning foreign languages .",
            "expected_intent": "Corregir 'interested on' por 'interested in'"
        },
        {
            "category": "Prepositions",
            "description": "Preposición de lugar incorrecta (stay at cabins -> stay in cabins)",
            "input": "I would prefer to stay at log cabins rather than tents .",
            "expected_intent": "Corregir 'at' por 'in'"
        },
        # 6. Errores múltiples / complejos
        {
            "category": "Multiple Errors",
            "description": "Múltiples errores: ortografía + tiempo verbal + preposición",
            "input": "I saws the show 's advertisement hanging up of a wall in London .",
            "expected_intent": "Corregir 'saws' -> 'saw', 'up of' -> 'on'"
        },
        {
            "category": "Multiple Errors",
            "description": "Múltiples errores: doble negación + concordancia + plural incorrecto",
            "input": "She dont has no time to do her homeworks .",
            "expected_intent": "Corregir 'dont has no' -> 'does not have any' y 'homeworks' -> 'homework'"
        }
    ]

    results = []
    logger.info(f"Ejecutando suite de {len(test_cases)} pruebas iniciales...")

    for tc in test_cases:
        res = corrector.correct_sentence(tc["input"])
        results.append({
            "category": tc["category"],
            "description": tc["description"],
            "original_text": tc["input"],
            "corrected_text": res["corrected"],
            "expected_intent": tc["expected_intent"],
            "is_changed": res["is_changed"],
            "inference_time_ms": res["inference_time_ms"]
        })

    return results
