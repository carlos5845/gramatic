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
    <div className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5">
      {/* Quick Example Selector (Pill chips from reference image) */}
      <div className="mb-3">
        <div className="flex items-center space-x-1.5 flex-wrap gap-1.5">
          <span className="text-xs font-bold text-slate-800 flex items-center space-x-1 mr-1 px-2 py-0.5 bg-brutal-yellow rounded-full border-1.5 border-slate-900 shadow-brutal-xs">
            <Lightbulb className="w-3.5 h-3.5 text-slate-900" />
            <span>Ejemplos rápidos:</span>
          </span>
          {SAMPLE_SENTENCES.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => setInputText(ex.text)}
              className="brutal-btn text-xs font-bold px-3 py-1 bg-white hover:bg-brutal-pinkLight text-slate-900 rounded-full border-1.5 border-slate-900 shadow-brutal-xs transition-colors cursor-pointer"
            >
              {ex.title}
            </button>
          ))}
        </div>
      </div>

      {/* Chatbot Textarea Container */}
      <div className="relative bg-slate-50 rounded-2xl border-2 border-slate-900 p-3 shadow-inner">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe o pega aquí tu texto en inglés para que el asistente analice errores, los corrija y te enseñe la regla..."
          rows={3}
          className={`w-full text-base font-medium text-slate-900 bg-transparent placeholder:text-slate-400 focus:outline-hidden transition-all resize-none`}
        />

        {/* Clear Button */}
        {inputText.length > 0 && (
          <button
            onClick={() => setInputText("")}
            className="brutal-btn absolute top-3 right-3 p-1.5 text-slate-700 hover:text-slate-950 bg-white rounded-lg border-1.5 border-slate-900 shadow-brutal-xs transition-colors cursor-pointer"
            title="Limpiar texto"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Footer Controls (Chatbot Action Bar) */}
      <div className="flex items-center justify-between mt-3 pt-2">
        <div className="flex items-center space-x-2 text-xs">
          <span
            className={`px-2 py-0.5 rounded-full border-1.5 border-slate-900 font-bold ${
              isOverLimit ? "bg-rose-200 text-rose-900" : "bg-white text-slate-700 shadow-brutal-xs"
            }`}
          >
            {charCount}/{maxChars}
          </span>
          <span className="text-slate-500 font-semibold hidden sm:inline">
            <kbd className="px-1.5 py-0.5 bg-white text-slate-800 rounded border-1.5 border-slate-900 shadow-brutal-xs text-[10px] font-bold">Ctrl+Enter</kbd> para enviar
          </span>
        </div>

        <button
          onClick={onAnalyze}
          disabled={isEmpty || isOverLimit || isLoading}
          className={`brutal-btn flex items-center space-x-2 px-5 py-2.5 rounded-2xl font-black text-sm border-2 border-slate-900 transition-all ${
            isEmpty || isOverLimit || isLoading
              ? "bg-slate-200 text-slate-500 border-slate-400 cursor-not-allowed"
              : "bg-brutal-blue text-white shadow-brutal hover:bg-brutal-blueHover cursor-pointer"
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Analizando...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Enviar Oración</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
