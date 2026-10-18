"use client";

import React from "react";
import { Send, Trash2, Lightbulb, Play, Sparkles } from "lucide-react";

export interface ExampleSentence {
  title: string;
  category: string;
  text: string;
}

export const SAMPLE_SENTENCES: ExampleSentence[] = [
  {
    title: "Concordancia Sujeto-Verbo",
    category: "subject_verb_agreement",
    text: "She go to school every day and study hard .",
  },
  {
    title: "Tiempos Verbales y Pasado",
    category: "verb_tense",
    text: "Yesterday I meet him and we eat dinner together .",
  },
  {
    title: "Artículos y Pluralización",
    category: "articles_determiners",
    text: "I bought a expensive shoes at the new store .",
  },
  {
    title: "Errores Múltiples FCE",
    category: "complex",
    text: "He dont knows where is the station and he ask for help .",
  },
  {
    title: "Oración Correcta (Control)",
    category: "clean",
    text: "Although the weather was cold, they enjoyed the beautiful afternoon.",
  },
];

interface TextInputAreaProps {
  inputText: string;
  setInputText: (text: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  maxChars?: number;
}

export const TextInputArea: React.FC<TextInputAreaProps> = ({
  inputText,
  setInputText,
  onAnalyze,
  isLoading,
  maxChars = 2000,
}) => {
  const charCount = inputText.length;
  const isOverLimit = charCount > maxChars;
  const isEmpty = inputText.trim().length === 0;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      if (!isEmpty && !isOverLimit && !isLoading) {
        onAnalyze();
      }
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5">
      {/* Header with Title & Quick Examples */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-800 text-sm sm:text-base">
            Texto en inglés para analizar
          </span>
          <span className="text-xs text-slate-400">
            (oraciones o párrafos)
          </span>
        </div>

        {/* Quick Example Selector */}
        <div className="flex items-center space-x-1.5 flex-wrap gap-y-1">
          <span className="text-xs text-slate-500 flex items-center space-x-1 mr-1">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
            <span className="hidden sm:inline">Ejemplos:</span>
          </span>
          {SAMPLE_SENTENCES.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => setInputText(ex.text)}
              className="text-xs px-2.5 py-1 bg-slate-100 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 text-slate-600 rounded-lg border border-slate-200 transition-colors cursor-pointer"
            >
              {ex.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Textarea */}
      <div className="relative">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe o pega aquí tu texto en inglés para detectar errores con BERT, corregir con T5 y obtener explicaciones pedagógicas con ERRANT..."
          rows={5}
          className={`w-full p-3.5 text-base text-slate-800 bg-slate-50/50 rounded-xl border ${
            isOverLimit
              ? "border-rose-400 focus:ring-rose-200"
              : "border-slate-200 focus:border-indigo-500 focus:ring-indigo-100"
          } focus:outline-hidden focus:ring-3 transition-all resize-y`}
        />

        {/* Clear Button */}
        {inputText.length > 0 && (
          <button
            onClick={() => setInputText("")}
            className="absolute top-3 right-3 p-1.5 text-slate-400 hover:text-slate-600 bg-white/80 rounded-md transition-colors"
            title="Limpiar texto"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Footer Controls: Counter & Action Button */}
      <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100">
        <div className="flex items-center space-x-3 text-xs">
          <span
            className={`font-medium ${
              isOverLimit ? "text-rose-600 font-bold" : "text-slate-400"
            }`}
          >
            {charCount} / {maxChars} caracteres
          </span>
          <span className="text-slate-300 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">
            Atajo: <kbd className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded border border-slate-200 text-[10px]">Ctrl+Enter</kbd>
          </span>
        </div>

        <button
          onClick={onAnalyze}
          disabled={isEmpty || isOverLimit || isLoading}
          className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all shadow-sm ${
            isEmpty || isOverLimit || isLoading
              ? "bg-slate-200 text-slate-400 cursor-not-allowed"
              : "bg-linear-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white shadow-indigo-200 hover:shadow-md cursor-pointer"
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Analizando con BERT & T5...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Analizar Texto</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
