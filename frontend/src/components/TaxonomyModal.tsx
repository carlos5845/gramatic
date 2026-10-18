"use client";

import React, { useState, useEffect } from "react";
import { TaxonomyCategory } from "../types/api";
import { getTaxonomyCategories } from "../lib/api";
import { X, BookOpen, Layers, CheckCircle2, Search } from "lucide-react";

interface TaxonomyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const TaxonomyModal: React.FC<TaxonomyModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [categories, setCategories] = useState<TaxonomyCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (isOpen && categories.length === 0) {
      setLoading(true);
      getTaxonomyCategories()
        .then((cats) => setCategories(cats))
        .catch((err) => {
          console.error("Error al cargar taxonomía:", err);
          // Fallback categories if server offline
          setCategories([
            {
              id: "subject_verb_agreement",
              name_es: "Concordancia Sujeto-Verbo",
              name_en: "Subject-Verb Agreement",
              description_es:
                "El verbo debe concordar en número (singular/plural) y persona con el sujeto de la cláusula.",
            },
            {
              id: "verb_tense",
              name_es: "Tiempos Verbales",
              name_en: "Verb Tense",
              description_es:
                "Uso adecuado del tiempo verbal (presente, pasado simple, continuo, perfecto) según el contexto temporal.",
            },
            {
              id: "verb_form",
              name_es: "Formas Verbales e Infinitivos",
              name_en: "Verb Form & Infinitives",
              description_es:
                "Uso de infinitivos (to + base), gerundios (-ing), participios o formas base tras modales y auxiliares.",
            },
            {
              id: "articles_determiners",
              name_es: "Artículos y Determinantes",
              name_en: "Articles & Determiners",
              description_es:
                "Uso de 'a', 'an', 'the' o artículo cero, así como cuantificadores (some, any, much, many, this, that).",
            },
            {
              id: "prepositions",
              name_es: "Preposiciones",
              name_en: "Prepositions",
              description_es:
                "Uso correcto de preposiciones de lugar, tiempo, dirección o régimen verbal (in, on, at, for, to, with, of).",
            },
            {
              id: "noun_number",
              name_es: "Número y Pluralización de Sustantivos",
              name_en: "Noun Number & Plurals",
              description_es:
                "Morfología singular vs plural en sustantivos contables e incontables.",
            },
            {
              id: "word_order",
              name_es: "Orden de Palabras y Sintaxis",
              name_en: "Word Order & Syntax",
              description_es:
                "Posición de adjetivos, adverbios, preguntas indirectas y orden Sujeto-Verbo-Objeto (SVO).",
            },
            {
              id: "spelling_orthography",
              name_es: "Ortografía y Tipografía",
              name_en: "Spelling & Orthography",
              description_es:
                "Errores tipográficos, letras omitidas, duplicadas o confusión de grafías homófonas.",
            },
            {
              id: "punctuation",
              name_es: "Puntuación",
              name_en: "Punctuation",
              description_es:
                "Uso de puntos, comas, signos de interrogación y apóstrofes de posesión o contracción.",
            },
            {
              id: "pronouns",
              name_es: "Pronombres y Posesivos",
              name_en: "Pronouns & Possessives",
              description_es:
                "Concordancia y caso de pronombres sujeto, objeto, posesivos y reflexivos.",
            },
            {
              id: "adjectives_adverbs",
              name_es: "Adjetivos y Adverbios",
              name_en: "Adjectives & Adverbs",
              description_es:
                "Uso de formas comparativas/superlativas y distinción adjetivo vs adverbio (-ly).",
            },
          ]);
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, categories.length]);

  if (!isOpen) return null;

  const filtered = categories.filter(
    (c) =>
      c.name_es.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.name_en.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.description_es.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">
                Taxonomía Pedagógica de Errores Gramaticales
              </h2>
              <p className="text-xs text-slate-500">
                Clasificación lingüística adaptada con ERRANT para estudiantes de inglés (FCE/BEA)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b border-slate-100 bg-slate-50">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar categoría gramatical o concepto..."
              className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-slate-200 rounded-xl focus:outline-hidden focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        </div>

        {/* Categories List */}
        <div className="p-5 overflow-y-auto space-y-3 flex-1">
          {loading ? (
            <div className="py-12 text-center text-slate-400">
              <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <span>Cargando categorías...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              No se encontraron categorías con el término ingresado.
            </div>
          ) : (
            filtered.map((cat, idx) => (
              <div
                key={cat.id}
                className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 hover:border-indigo-300 transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded-md bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <span className="font-semibold text-slate-800 text-sm">
                      {cat.name_es}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                    {cat.name_en}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed pl-7">
                  {cat.description_es}
                </p>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition-colors shadow-xs"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};
