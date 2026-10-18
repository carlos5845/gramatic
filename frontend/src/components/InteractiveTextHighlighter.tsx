"use client";

import React from "react";
import { EditExplanation, GEDResults } from "../types/api";
import { AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";

interface InteractiveTextHighlighterProps {
  originalText: string;
  correctedText: string;
  explanations: EditExplanation[];
  gedResults?: GEDResults;
  selectedEditIndex: number | null;
  onSelectEdit: (index: number | null) => void;
}

export const InteractiveTextHighlighter: React.FC<InteractiveTextHighlighterProps> = ({
  originalText,
  correctedText,
  explanations,
  selectedEditIndex,
  onSelectEdit,
}) => {
  // Construir fragmentos del texto original con spans resaltados
  const renderOriginalHighlighted = () => {
    if (!explanations || explanations.length === 0) {
      return <span className="text-slate-800">{originalText}</span>;
    }

    // Ordenar explicaciones por posición inicial
    const sortedEdits = [...explanations].sort(
      (a, b) => a.char_span.start - b.char_span.start
    );

    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedEdits.forEach((edit, idx) => {
      const { start, end } = edit.char_span;

      // Texto plano previo a la edición
      if (start > lastIndex) {
        elements.push(
          <span key={`text-${lastIndex}-${start}`} className="text-slate-800">
            {originalText.substring(lastIndex, start)}
          </span>
        );
      }

      const isSelected = selectedEditIndex === edit.edit_index;
      const isDetectedByBoth = edit.ged_match_status === "detected_by_both";

      // Fragmento de error (si start == end es una inserción)
      if (start === end) {
        elements.push(
          <span
            key={`insert-marker-${edit.edit_index}`}
            onClick={() => onSelectEdit(isSelected ? null : edit.edit_index)}
            className={`inline-flex items-center px-1.5 py-0.5 mx-0.5 text-xs font-semibold rounded cursor-pointer transition-all ${
              isSelected
                ? "bg-amber-400 text-slate-900 ring-2 ring-amber-500 scale-105"
                : "bg-amber-100 text-amber-800 hover:bg-amber-200 border border-amber-300"
            }`}
            title={`Falta una palabra aquí: "${edit.corrected_fragment}" (${edit.category_name})`}
          >
            + [{edit.corrected_fragment}]
          </span>
        );
      } else {
        const errorFragment = originalText.substring(start, end);
        elements.push(
          <mark
            key={`edit-${edit.edit_index}-${start}`}
            onClick={() => onSelectEdit(isSelected ? null : edit.edit_index)}
            className={`inline-block px-1 py-0.5 mx-0.5 rounded cursor-pointer transition-all ${
              isSelected
                ? "bg-rose-500 text-white font-semibold ring-2 ring-rose-600 scale-105"
                : isDetectedByBoth
                ? "bg-rose-100 text-rose-900 border-b-2 border-rose-500 hover:bg-rose-200"
                : "bg-amber-100 text-amber-900 border-b-2 border-amber-500 hover:bg-amber-200"
            }`}
            title={`Error detectado: "${errorFragment}" ➔ "${edit.corrected_fragment}" (${edit.category_name})`}
          >
            {errorFragment}
          </mark>
        );
      }

      lastIndex = Math.max(lastIndex, end);
    });

    // Texto remanente
    if (lastIndex < originalText.length) {
      elements.push(
        <span key={`text-end-${lastIndex}`} className="text-slate-800">
          {originalText.substring(lastIndex)}
        </span>
      );
    }

    return elements;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 my-4">
      {/* Panel Izquierdo: Original con Resaltado Interactivo */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span className="font-semibold text-slate-800 text-sm">
                Texto Original con Detecciones
              </span>
            </div>
            <span className="text-xs text-slate-400">
              Haz clic en cualquier palabra resaltada
            </span>
          </div>

          <div className="text-base leading-relaxed p-3.5 bg-slate-50/70 rounded-xl border border-slate-100 min-h-[110px]">
            {renderOriginalHighlighted()}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4 mt-3 pt-2 text-xs text-slate-500 border-t border-slate-100 flex-wrap gap-y-1">
          <span className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded-xs bg-rose-100 border border-rose-400" />
            <span>BERT + T5 Coinciden</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-3 h-3 rounded-xs bg-amber-100 border border-amber-400" />
            <span>Sugerido por T5</span>
          </span>
        </div>
      </div>

      {/* Panel Derecho: Texto Corregido */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span className="font-semibold text-slate-800 text-sm">
                Texto Corregido (T5 GEC)
              </span>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              {explanations.length === 0 ? "Sin Errores" : `${explanations.length} Correcciones`}
            </span>
          </div>

          <div className="text-base leading-relaxed p-3.5 bg-emerald-50/40 rounded-xl border border-emerald-100 text-slate-900 min-h-[110px]">
            {correctedText}
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 pt-2 text-xs text-slate-500 border-t border-slate-100">
          <span className="flex items-center space-x-1 text-emerald-700 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Gramaticalmente consistente</span>
          </span>
          <button
            onClick={() => navigator.clipboard.writeText(correctedText)}
            className="text-xs text-indigo-600 hover:text-indigo-800 font-medium cursor-pointer"
          >
            Copiar Corrección
          </button>
        </div>
      </div>
    </div>
  );
};
