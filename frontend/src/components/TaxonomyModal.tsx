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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl border-3 border-slate-900 shadow-brutal-lg w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b-2 border-slate-900 flex items-center justify-between bg-brutal-yellow">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-white border-2 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-900">
                Taxonomía Pedagógica de Errores
              </h2>
              <p className="text-xs font-semibold text-slate-800">
                Clasificación lingüística adaptada con ERRANT para estudiantes L2
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="brutal-btn p-2 text-slate-900 bg-white hover:bg-slate-100 rounded-xl border-2 border-slate-900 shadow-brutal-xs transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b-2 border-slate-900 bg-slate-50">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-900 absolute left-3 top-1/2 -translate-y-1/2 font-bold" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar categoría gramatical o concepto..."
              className="w-full pl-9 pr-3 py-2 text-sm font-medium bg-white border-2 border-slate-900 rounded-xl shadow-brutal-xs focus:outline-hidden"
            />
          </div>
        </div>

        {/* Categories List */}
        <div className="p-5 overflow-y-auto space-y-3 flex-1 bg-slate-50/50">
          {loading ? (
            <div className="py-12 text-center text-slate-600 font-bold">
              <div className="w-6 h-6 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <span>Cargando categorías...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-slate-600 font-bold">
              No se encontraron categorías con el término ingresado.
            </div>
          ) : (
            filtered.map((cat, idx) => (
              <div
                key={cat.id}
                className="p-4 bg-white rounded-2xl border-2 border-slate-900 shadow-brutal-xs hover:shadow-brutal transition-all"
              >
                <div className="flex items-center justify-between mb-1 flex-wrap gap-1">
                  <div className="flex items-center space-x-2">
                    <span className="w-6 h-6 rounded-lg bg-brutal-yellow text-slate-900 text-xs font-black border-1.5 border-slate-900 flex items-center justify-center shadow-brutal-xs">
                      {idx + 1}
                    </span>
                    <span className="font-black text-slate-900 text-sm">
                      {cat.name_es}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-slate-900 bg-brutal-tealLight px-2.5 py-0.5 rounded-full border-1.5 border-slate-900">
                    {cat.name_en}
                  </span>
                </div>
                <p className="text-xs text-slate-700 mt-1 leading-relaxed pl-8 font-medium">
                  {cat.description_es}
                </p>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t-2 border-slate-900 bg-white flex justify-end">
          <button
            onClick={onClose}
            className="brutal-btn px-5 py-2 bg-brutal-blue hover:bg-brutal-blueHover text-white text-xs font-black rounded-xl border-2 border-slate-900 shadow-brutal-xs transition-colors cursor-pointer"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
};
