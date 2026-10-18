import os
import sys
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import spacy
import errant
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ==============================================================================
# TAXONOMÍA PEDAGÓGICA Y REGLAS EXPLICATIVAS PARA APRENDICES DE INGLÉS
# ==============================================================================

TAXONOMY_CATEGORIES = {
    "VERB_TENSE": {
        "id": "VERB_TENSE",
        "name_es": "Tiempos Verbales",
        "name_en": "Verb Tense & Aspect",
        "description_es": "Uso inadecuado del tiempo verbal según el marco temporal o aspecto de la oración."
    },
    "VERB_AGREEMENT": {
        "id": "VERB_AGREEMENT",
        "name_es": "Concordancia Sujeto-Verbo",
        "name_en": "Subject-Verb Agreement",
        "description_es": "Falta de coincidencia en número o persona entre el sujeto y el verbo principal."
    },
    "VERB_FORM": {
        "id": "VERB_FORM",
        "name_es": "Forma Verbal (Infinitivo / Gerundio / Participio)",
        "name_en": "Verb Form (Infinitive / Gerund / Participle)",
        "description_es": "Uso erróneo de infinitivos, gerundios (-ing), participios o formas base tras modales o preposiciones."
    },
    "ARTICLES_DETERMINERS": {
        "id": "ARTICLES_DETERMINERS",
        "name_es": "Artículos y Determinantes",
        "name_en": "Articles & Determiners",
        "description_es": "Omisión, exceso o elección incorrecta de artículos (a/an/the) o determinantes (this/that/some/any)."
    },
    "PREPOSITIONS": {
        "id": "PREPOSITIONS",
        "name_es": "Preposiciones",
        "name_en": "Prepositions",
        "description_es": "Selección inadecuada u omisión de preposiciones en complementos y régimen verbal."
    },
    "PLURALIZATION_NUMBER": {
        "id": "PLURALIZATION_NUMBER",
        "name_es": "Pluralización y Número Gramatical",
        "name_en": "Noun Number & Pluralization",
        "description_es": "Confusión entre singular y plural en sustantivos contables o incontables."
    },
    "WORD_ORDER": {
        "id": "WORD_ORDER",
        "name_es": "Orden de Palabras",
        "name_en": "Word Order",
        "description_es": "Posición incorrecta de elementos en la oración (adjetivos antes del sustantivo, adverbios, preguntas)."
    },
    "SPELLING": {
        "id": "SPELLING",
        "name_es": "Ortografía (Spelling)",
        "name_en": "Spelling",
        "description_es": "Errores tipográficos, letras omitidas o duplicadas en la grafía de las palabras."
    },
    "ORTHOGRAPHY_PUNCTUATION": {
        "id": "ORTHOGRAPHY_PUNCTUATION",
        "name_es": "Puntuación y Mayúsculas",
        "name_en": "Punctuation & Capitalization",
        "description_es": "Uso indebido de mayúsculas, puntos, comas o apóstrofes de posesión."
    },
    "PRONOUNS": {
        "id": "PRONOUNS",
        "name_es": "Pronombres",
        "name_en": "Pronouns",
        "description_es": "Elección incorrecta de pronombres de sujeto, objeto, posesivos o relativos."
    },
    "ADJECTIVES_ADVERBS": {
        "id": "ADJECTIVES_ADVERBS",
        "name_es": "Adjetivos y Adverbios",
        "name_en": "Adjectives & Adverbs",
        "description_es": "Confusión entre adjetivos y adverbios, o errores en formas comparativas y superlativas."
    },
    "VOCABULARY_LEXICAL": {
        "id": "VOCABULARY_LEXICAL",
        "name_es": "Vocabulario y Selección Léxica",
        "name_en": "Vocabulary & Word Choice",
        "description_es": "Uso de falsos amigos o palabras con significado inadecuado en el contexto."
    },
    "COMPLEX_STYLISTIC": {
        "id": "COMPLEX_STYLISTIC",
        "name_es": "Reestructuración y Fluidez Estilística",
        "name_en": "Style & Sentence Restructuring",
        "description_es": "Reorganización sintáctica para mejorar la naturalidad y claridad de la expresión."
    },
    "UNCERTAIN": {
        "id": "UNCERTAIN",
        "name_es": "Caso Complejo o Incierto",
        "name_en": "Uncertain / Context-Dependent Change",
        "description_es": "Modificación dependiente de matices contextuales o múltiples interpretaciones válidas."
    }
}


class GrammarExplainer:
    """
    Módulo de Clasificación y Explicación Pedagógica de Correcciones Gramaticales.
    
    Transforma ediciones abstractas en explicaciones pedagógicas comprensibles para estudiantes
    de inglés como segunda lengua (L2).
    
    Capacidades:
    1. Alineación precisa entre oraciones originales y corregidas (token-level y character spans).
    2. Integración con ERRANT para extracción lingüística de tipos de edición M2.
    3. Mapeo a taxonomía educativa simplificada y comprensible.
    4. Generación de reglas, consejos pedagógicos y ejemplos ilustrativos.
    5. Manejo prudente de casos inciertos y estilísticos para evitar explicaciones dogmáticas.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        logger.info(f"Cargando modelo lingüístico spaCy '{spacy_model}' y ERRANT...")
        self.nlp = spacy.load(spacy_model)
        self.annotator = errant.load("en", self.nlp)
        logger.info("GrammarExplainer inicializado con éxito.")

    def _find_char_offsets(self, full_text: str, token_str: str, search_from: int = 0) -> Tuple[int, int]:
        """
        Encuentra los offsets de caracteres exactos de un fragmento de texto en la oración completa.
        """
        if not token_str or token_str == "-NONE-":
            return search_from, search_from

        pos = full_text.find(token_str, search_from)
        if pos != -1:
            return pos, pos + len(token_str)
        
        # Búsqueda insensible a mayúsculas si no se encuentra exacto
        pos_lower = full_text.lower().find(token_str.lower(), search_from)
        if pos_lower != -1:
            return pos_lower, pos_lower + len(token_str)

        return search_from, search_from + len(token_str)

    def _classify_and_build_explanation(
        self,
        errant_type: str,
        orig_fragment: str,
        corr_fragment: str,
        orig_tokens: List[Any],
        corr_tokens: List[Any]
    ) -> Dict[str, Any]:
        """
        Aplica el motor de reglas pedagógicas para asociar el tipo ERRANT y contexto sintáctico
        con una categoría de la taxonomía, regla gramatical, ejemplo y nivel de certeza.
        """
        op_prefix = errant_type.split(":")[0] if ":" in errant_type else "R"
        core_type = ":".join(errant_type.split(":")[1:]) if ":" in errant_type else errant_type
        
        orig_clean = orig_fragment.strip()
        corr_clean = corr_fragment.strip()

        # Determinar tipo de operación básica
        if op_prefix == "M" or not orig_clean:
            operation = "insertion"
            action_desc = f"Añadir '{corr_clean}'"
        elif op_prefix == "U" or not corr_clean:
            operation = "deletion"
            action_desc = f"Eliminar '{orig_clean}'"
        else:
            operation = "substitution"
            action_desc = f"Cambiar '{orig_clean}' por '{corr_clean}'"

        # -------------------------------------------------------------
        # 1. Concordancia Sujeto-Verbo (Subject-Verb Agreement)
        # -------------------------------------------------------------
        if core_type in ["VERB:SVA", "SVA"] or (
            core_type.startswith("VERB") and (
                (orig_clean.lower() in ["is", "was", "has", "does"] and corr_clean.lower() in ["are", "were", "have", "do"]) or
                (orig_clean.lower() in ["are", "were", "have", "do"] and corr_clean.lower() in ["is", "was", "has", "does"])
            )
        ):
            category = "VERB_AGREEMENT"
            confidence = "high"
            summary = f"Concordancia entre el sujeto y el verbo ({action_desc})."
            rule = (
                "En inglés, el verbo debe coincidir en número (singular o plural) con su sujeto. "
                "Para la tercera persona singular (he, she, it), se utiliza 'is', 'was', 'has' o terminación '-s/-es' en presente simple, "
                "mientras que para sujetos plurales (they, we, you) se utiliza 'are', 'were', 'have' o la forma base."
            )
            example = {
                "incorrect": f"She {orig_clean} happy." if orig_clean else "They is here.",
                "correct": f"She {corr_clean} happy." if corr_clean else "They are here."
            }

        # -------------------------------------------------------------
        # 2. Tiempos Verbales (Verb Tense & Aspect)
        # -------------------------------------------------------------
        elif core_type in ["VERB:TENSE", "TENSE"]:
            category = "VERB_TENSE"
            confidence = "high"
            summary = f"Ajuste del tiempo verbal ({action_desc})."
            rule = (
                "El tiempo verbal debe corresponder al marco temporal de la oración. "
                "Si la acción ocurrió en el pasado y está concluida, se requiere pasado simple (-ed o forma irregular). "
                "Si describe hábitos o verdades generales, se emplea el presente simple."
            )
            example = {
                "incorrect": f"Yesterday I {orig_clean} to school." if orig_clean else "Yesterday I go home.",
                "correct": f"Yesterday I {corr_clean} to school." if corr_clean else "Yesterday I went home."
            }

        # -------------------------------------------------------------
        # 3. Formas Verbales (Infinitivo / Gerundio / Participio / Modal + Base)
        # -------------------------------------------------------------
        elif core_type in ["VERB:FORM", "FORM"]:
            category = "VERB_FORM"
            confidence = "high"
            summary = f"Uso de la forma verbal adecuada ({action_desc})."
            rule = (
                "Verifica la estructura verbal requerida: tras verbos modales (can, should, must) se usa el infinitivo sin 'to' (forma base). "
                "Tras preposiciones o verbos de preferencia (enjoy, avoid), frecuentemente se requiere gerundio (-ing). "
                "Tras 'to' con intención de propósito, se suele emplear infinitivo."
            )
            example = {
                "incorrect": f"I decided {orig_clean}." if orig_clean else "I look forward to see you.",
                "correct": f"I decided {corr_clean}." if corr_clean else "I look forward to seeing you."
            }

        # -------------------------------------------------------------
        # 4. Artículos y Determinantes (Articles & Determiners)
        # -------------------------------------------------------------
        elif core_type in ["DET", "ART"]:
            category = "ARTICLES_DETERMINERS"
            confidence = "high" if orig_clean.lower() in ["a", "an", "the", ""] and corr_clean.lower() in ["a", "an", "the", ""] else "medium"
            if operation == "insertion":
                summary = f"Inserción del artículo o determinante necesario '{corr_clean}'."
                rule = (
                    "Los sustantivos contables en singular generalmente requieren un artículo o determinante antes de ellos (a/an/the/my). "
                    "Se usa 'a' antes de sonido consonante y 'an' antes de sonido vocal."
                )
            elif operation == "deletion":
                summary = f"Eliminación del artículo innecesario '{orig_clean}'."
                rule = (
                    "En inglés no se utiliza artículo determinado 'the' al hablar de conceptos generales o sustantivos incontables en sentido amplio."
                )
            else:
                summary = f"Corrección del artículo o determinante ({action_desc})."
                rule = (
                    "Usa 'a' / 'an' para elementos indefinidos o mencionados por primera vez, y 'the' para elementos específicos o ya conocidos por el interlocutor."
                )
            example = {
                "incorrect": "I saw apple on table.",
                "correct": "I saw an apple on the table."
            }

        # -------------------------------------------------------------
        # 5. Preposiciones (Prepositions)
        # -------------------------------------------------------------
        elif core_type in ["PREP"]:
            category = "PREPOSITIONS"
            confidence = "high" if corr_clean.lower() in ["in", "on", "at", "to", "for", "with", "by", "from", "of", "about"] else "medium"
            summary = f"Elección de la preposición adecuada ({action_desc})."
            rule = (
                "Las preposiciones en inglés suelen depender del régimen del verbo o adjetivo que las precede (collocations), "
                "o del tipo de complemento (lugar, tiempo, medio). "
                "Por ejemplo: 'interested in', 'depend on', 'arrive at/in', 'good at'."
            )
            example = {
                "incorrect": f"I am interested {orig_clean or 'about'} this topic.",
                "correct": f"I am interested {corr_clean or 'in'} this topic."
            }

        # -------------------------------------------------------------
        # 6. Pluralización y Número Gramatical (Noun Number)
        # -------------------------------------------------------------
        elif core_type in ["NOUN:NUM", "NUM"]:
            category = "PLURALIZATION_NUMBER"
            confidence = "high"
            summary = f"Número gramatical del sustantivo ({action_desc})."
            rule = (
                "Asegúrate de que los sustantivos contables estén en plural cuando vayan precedidos de cuantificadores plurales (two, many, several, all) "
                "o en singular cuando se refieran a un único elemento. Los sustantivos incontables (information, advice) no llevan '-s'."
            )
            example = {
                "incorrect": f"I have two {orig_clean or 'book'}.",
                "correct": f"I have two {corr_clean or 'books'}."
            }

        # -------------------------------------------------------------
        # 7. Ortografía (Spelling)
        # -------------------------------------------------------------
        elif core_type in ["SPELL"]:
            category = "SPELLING"
            confidence = "high"
            summary = f"Corrección ortográfica de la palabra ({action_desc})."
            rule = (
                f"La palabra '{orig_clean}' contiene un error de escritura. La grafía correcta en inglés estándar es '{corr_clean}'."
            )
            example = {
                "incorrect": orig_clean,
                "correct": corr_clean
            }

        # -------------------------------------------------------------
        # 8. Puntuación, Mayúsculas y Ortotipografía (Punctuation & Capitalization)
        # -------------------------------------------------------------
        elif core_type in ["ORTH", "PUNCT", "NOUN:POSS"]:
            category = "ORTHOGRAPHY_PUNCTUATION"
            confidence = "high"
            if core_type == "NOUN:POSS" or "'" in orig_clean or "'" in corr_clean:
                summary = f"Uso del apóstrofe posesivo ({action_desc})."
                rule = "El genitivo sajón utiliza \"'s\" para denotar posesión o pertenencia en sustantivos singulares."
            elif any(c.isupper() for c in corr_clean) and not any(c.isupper() for c in orig_clean):
                summary = f"Uso de mayúscula inicial en nombres propios o inicio de oración."
                rule = "En inglés, los nombres propios, días de la semana, meses, nacionalidades e inicios de oración deben comenzar con mayúscula."
            else:
                summary = f"Ajuste de puntuación o espaciado ({action_desc})."
                rule = "Los signos de puntuación delimitan proposiciones para garantizar la coherencia sintáctica."
            example = {
                "incorrect": orig_clean or "john 's car",
                "correct": corr_clean or "John's car"
            }

        # -------------------------------------------------------------
        # 9. Orden de Palabras (Word Order)
        # -------------------------------------------------------------
        elif core_type in ["WO"]:
            category = "WORD_ORDER"
            confidence = "high"
            summary = f"Reordenamiento sintáctico de los términos ({action_desc})."
            rule = (
                "En inglés, el orden estándar es Sujeto + Verbo + Objeto. "
                "Los adjetivos atributivos se colocan antes del sustantivo al que modifican (e.g., 'a red car', no 'a car red')."
            )
            example = {
                "incorrect": orig_clean or "a car red",
                "correct": corr_clean or "a red car"
            }

        # -------------------------------------------------------------
        # 10. Pronombres (Pronouns)
        # -------------------------------------------------------------
        elif core_type in ["PRON"]:
            category = "PRONOUNS"
            confidence = "high"
            summary = f"Corrección del pronombre ({action_desc})."
            rule = (
                "Usa pronombres de sujeto (I, he, she, they) en la posición de agente, pronombres de objeto (me, him, her, them) tras verbos y preposiciones, "
                "y pronombres posesivos (my, his, her, their) para indicar pertenencia."
            )
            example = {
                "incorrect": f"She told {orig_clean or 'I'}.",
                "correct": f"She told {corr_clean or 'me'}."
            }

        # -------------------------------------------------------------
        # 11. Adjetivos y Adverbios (Adjectives & Adverbs)
        # -------------------------------------------------------------
        elif core_type in ["ADJ", "ADV", "ADJ:FORM"]:
            category = "ADJECTIVES_ADVERBS"
            confidence = "high"
            summary = f"Uso adecuado de adjetivo/adverbio ({action_desc})."
            rule = (
                "Los adjetivos modifican sustantivos ('quick response'), mientras que los adverbios modifican verbos, adjetivos u otros adverbios ('respond quickly'). "
                "Comprueba también las terminaciones comparativas (-er / more) y superlativas (-est / most)."
            )
            example = {
                "incorrect": f"He drives {orig_clean or 'careful'}.",
                "correct": f"He drives {corr_clean or 'carefully'}."
            }

        # -------------------------------------------------------------
        # 12. Vocabulario y Selección Léxica
        # -------------------------------------------------------------
        elif core_type in ["VERB", "NOUN", "CONJ", "MORPH", "PART"]:
            category = "VOCABULARY_LEXICAL"
            confidence = "medium"
            summary = f"Selección de vocabulario más preciso ({action_desc})."
            rule = (
                f"El término '{orig_clean}' fue sustituido por '{corr_clean}' para alinearse con los patrones léxicos habituales en este contexto."
            )
            example = {
                "incorrect": orig_clean,
                "correct": corr_clean
            }

        # -------------------------------------------------------------
        # 13. Casos Complejos / Inciertos / Reestructuración Estilística
        # -------------------------------------------------------------
        else:
            category = "UNCERTAIN" if core_type in ["UNK", "OTHER"] else "COMPLEX_STYLISTIC"
            confidence = "uncertain"
            summary = f"Ajuste sintáctico o estilístico ({action_desc})."
            rule = (
                "Este cambio corresponde a una reestructuración de la frase o a una elección estilística. "
                "En inglés existen múltiples formas de expresar la misma idea; la sugerencia busca mejorar la claridad o naturalidad general."
            )
            example = {
                "incorrect": orig_clean or "Frase original",
                "correct": corr_clean or "Frase reestructurada"
            }

        cat_meta = TAXONOMY_CATEGORIES.get(category, TAXONOMY_CATEGORIES["UNCERTAIN"])

        return {
            "category_id": category,
            "category_name_es": cat_meta["name_es"],
            "category_name_en": cat_meta["name_en"],
            "errant_raw_type": errant_type,
            "operation": operation,
            "original_fragment": orig_clean,
            "corrected_fragment": corr_clean,
            "summary_es": summary,
            "rule_explanation_es": rule,
            "example": example,
            "confidence": confidence
        }

    def explain_correction(
        self,
        original_text: str,
        corrected_text: str
    ) -> Dict[str, Any]:
        """
        Analiza y genera explicaciones detalladas para todas las diferencias entre
        el texto original y el texto corregido.
        
        Retorna un diccionario estructurado listo para interfaces de usuario y reportes.
        """
        orig_clean = original_text.strip()
        corr_clean = corrected_text.strip()

        if not orig_clean or not corr_clean or orig_clean == corr_clean:
            return {
                "original_text": orig_clean,
                "corrected_text": corr_clean,
                "has_corrections": False,
                "total_edits": 0,
                "explanations": [],
                "taxonomy_breakdown": {}
            }

        # Tokenizar y procesar con spaCy y ERRANT
        orig_doc = self.annotator.parse(orig_clean)
        corr_doc = self.annotator.parse(corr_clean)

        edits = self.annotator.annotate(orig_doc, corr_doc)
        
        explanations = []
        taxonomy_breakdown: Dict[str, int] = {}
        search_char_pos = 0

        for edit_idx, edit in enumerate(edits):
            orig_fragment = edit.o_str if edit.o_str else ""
            corr_fragment = edit.c_str if edit.c_str else ""

            # Calcular offsets de caracteres en el texto original
            if orig_fragment:
                char_start, char_end = self._find_char_offsets(orig_clean, orig_fragment, search_char_pos)
                search_char_pos = char_end
            else:
                # Inserción: ubicar en el punto del token de inserción
                prev_tok_end = 0
                if edit.o_start > 0 and edit.o_start <= len(orig_doc):
                    prev_tok = orig_doc[edit.o_start - 1]
                    prev_tok_end = prev_tok.idx + len(prev_tok.text)
                char_start = prev_tok_end
                char_end = prev_tok_end

            exp_data = self._classify_and_build_explanation(
                errant_type=edit.type,
                orig_fragment=orig_fragment,
                corr_fragment=corr_fragment,
                orig_tokens=edit.o_toks,
                corr_tokens=edit.c_toks
            )

            cat_id = exp_data["category_id"]
            taxonomy_breakdown[cat_id] = taxonomy_breakdown.get(cat_id, 0) + 1

            explanations.append({
                "edit_index": edit_idx + 1,
                "token_span": {
                    "start": edit.o_start,
                    "end": edit.o_end
                },
                "char_span": {
                    "start": char_start,
                    "end": char_end
                },
                "original_fragment": orig_fragment,
                "corrected_fragment": corr_fragment,
                "category_id": exp_data["category_id"],
                "category_name": exp_data["category_name_es"],
                "category_name_en": exp_data["category_name_en"],
                "errant_type": exp_data["errant_raw_type"],
                "operation": exp_data["operation"],
                "confidence": exp_data["confidence"],
                "summary": exp_data["summary_es"],
                "rule_explanation": exp_data["rule_explanation_es"],
                "example": exp_data["example"]
            })

        return {
            "original_text": orig_clean,
            "corrected_text": corr_clean,
            "has_corrections": len(explanations) > 0,
            "total_edits": len(explanations),
            "explanations": explanations,
            "taxonomy_breakdown": taxonomy_breakdown
        }

    def explain_and_correct(
        self,
        text: str,
        corrector_instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la corrección con el modelo GEC (si se proporciona) y devuelve
        inmediatamente la explicación pedagógica de todos los cambios realizados.
        """
        if corrector_instance is not None:
            res = corrector_instance.correct_sentence(text)
            corrected_text = res["corrected"]
            latency_ms = res["inference_time_ms"]
        else:
            corrected_text = text
            latency_ms = 0.0

        explanation_result = self.explain_correction(text, corrected_text)
        explanation_result["inference_time_ms"] = latency_ms
        return explanation_result


def validate_explainer_on_sample(
    explainer: GrammarExplainer,
    output_report_path: str = "reports/gec_explanation_validation_report.md"
) -> Dict[str, Any]:
    """
    Evalúa y valida el módulo de explicaciones sobre una batería diversa de oraciones
    que cubren todas las categorías gramaticales de la taxonomía.
    
    Genera un informe detallado en Markdown y JSON para documentación de calidad.
    """
    test_cases = [
        {
            "category": "VERB_AGREEMENT",
            "original": "She go to school every day by bus .",
            "corrected": "She goes to school every day by bus ."
        },
        {
            "category": "VERB_TENSE",
            "original": "Yesterday I see my old friend at the station .",
            "corrected": "Yesterday I saw my old friend at the station ."
        },
        {
            "category": "VERB_FORM",
            "original": "I am looking forward to hear from you soon .",
            "corrected": "I am looking forward to hearing from you soon ."
        },
        {
            "category": "ARTICLES_DETERMINERS",
            "original": "I bought apple and book yesterday .",
            "corrected": "I bought an apple and a book yesterday ."
        },
        {
            "category": "PREPOSITIONS",
            "original": "He is very interested on learning English .",
            "corrected": "He is very interested in learning English ."
        },
        {
            "category": "PLURALIZATION_NUMBER",
            "original": "There are many car in the street .",
            "corrected": "There are many cars in the street ."
        },
        {
            "category": "SPELLING",
            "original": "I have just recieved your letter .",
            "corrected": "I have just received your letter ."
        },
        {
            "category": "ORTHOGRAPHY_PUNCTUATION",
            "original": "i went to london last summer .",
            "corrected": "I went to London last summer ."
        },
        {
            "category": "PRONOUNS",
            "original": "Her gave me a nice present .",
            "corrected": "She gave me a nice present ."
        },
        {
            "category": "ADJECTIVES_ADVERBS",
            "original": "He drives very careful on the road .",
            "corrected": "He drives very carefully on the road ."
        },
        {
            "category": "WORD_ORDER",
            "original": "I have a car red .",
            "corrected": "I have a red car ."
        },
        {
            "category": "UNCERTAIN_COMPLEX",
            "original": "Because I intend to take examination in Septenber .",
            "corrected": "This is because I intend to take an examination in September ."
        }
    ]

    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    results = []
    category_counts: Dict[str, int] = {}
    confidence_counts: Dict[str, int] = {}

    for case in test_cases:
        exp_res = explainer.explain_correction(case["original"], case["corrected"])
        results.append({
            "expected_focus": case["category"],
            "original": case["original"],
            "corrected": case["corrected"],
            "total_edits": exp_res["total_edits"],
            "explanations": exp_res["explanations"]
        })
        for exp in exp_res["explanations"]:
            cat = exp["category_id"]
            conf = exp["confidence"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

    # Generar informe en Markdown
    md_lines = [
        "# Informe de Validación del Módulo de Clasificación y Explicación Gramatical (Fase 8)",
        "",
        "Este informe documenta la alineación, taxonomía pedagógica y generación de explicaciones para aprendices de inglés (L2).",
        "",
        "### 1. Resumen de Cobertura de la Taxonomía",
        "",
        "| Categoría | Nombre en Español | Nombre en Inglés | Frecuencia en Muestra |",
        "|---|---|---|---|"
    ]

    for cat_id, meta in TAXONOMY_CATEGORIES.items():
        count = category_counts.get(cat_id, 0)
        md_lines.append(f"| `{cat_id}` | {meta['name_es']} | {meta['name_en']} | {count} |")

    md_lines.extend([
        "",
        "### 2. Distribución por Nivel de Certeza Pedagógica",
        "",
        f"- **Alta Certeza (Regla Directa)**: {confidence_counts.get('high', 0)} ediciones",
        f"- **Media Certeza (Colocaciones/Léxico)**: {confidence_counts.get('medium', 0)} ediciones",
        f"- **Casos Inciertos/Estilísticos (Avisos de Flexibilidad)**: {confidence_counts.get('uncertain', 0)} ediciones",
        "",
        "### 3. Casos de Prueba Validados con Explicaciones Generadas",
        ""
    ])

    for r in results:
        md_lines.append(f"#### Foco: `{r['expected_focus']}`")
        md_lines.append(f"- **Original**: `{r['original']}`")
        md_lines.append(f"- **Corregido**: `{r['corrected']}`")
        md_lines.append(f"- **Ediciones identificadas**: {r['total_edits']}")
        for exp in r["explanations"]:
            md_lines.append(f"  - **[#{exp['edit_index']}] {exp['category_name']}** ({exp['confidence'].upper()} confidence):")
            md_lines.append(f"    - *Cambio*: `{exp['original_fragment']}` $\\rightarrow$ `{exp['corrected_fragment']}` (Span: {exp['char_span']['start']}:{exp['char_span']['end']})")
            md_lines.append(f"    - *Resumen*: {exp['summary']}")
            md_lines.append(f"    - *Regla*: {exp['rule_explanation']}")
            md_lines.append(f"    - *Ejemplo*: ❌ *{exp['example']['incorrect']}* | ✔️ *{exp['example']['correct']}*")
        md_lines.append("")

    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    logger.info(f"Informe de validación de explicaciones guardado en '{output_report_path}'.")

    return {
        "total_test_cases": len(test_cases),
        "category_counts": category_counts,
        "confidence_counts": confidence_counts,
        "report_path": output_report_path
    }


if __name__ == "__main__":
    expl = GrammarExplainer()
    val_summary = validate_explainer_on_sample(expl)
    print("Resumen de validación:", val_summary)
