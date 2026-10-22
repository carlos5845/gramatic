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
            className={`inline-flex items-center px-2 py-0.5 mx-0.5 text-xs font-black rounded-full cursor-pointer transition-all border-1.5 border-slate-900 ${
              isSelected
                ? "bg-brutal-yellow text-slate-900 shadow-brutal-xs scale-105"
                : "bg-white text-slate-900 hover:bg-brutal-yellow shadow-brutal-xs"
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
            className={`inline-block px-1.5 py-0.5 mx-0.5 rounded-lg cursor-pointer transition-all border-1.5 border-slate-900 font-bold ${
              isSelected
                ? "bg-rose-500 text-white shadow-brutal-xs scale-105"
                : isDetectedByBoth
                ? "bg-brutal-pinkLight text-slate-900 shadow-brutal-xs hover:bg-brutal-pink"
                : "bg-brutal-yellow text-slate-900 shadow-brutal-xs hover:bg-brutal-yellowHover"
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
        <span key={`text-end-${lastIndex}`} className="text-slate-900 font-medium">
          {originalText.substring(lastIndex)}
        </span>
      );
    }

    return elements;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 my-4">
      {/* Panel Izquierdo: Original con Resaltado Interactivo */}
      <div className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3 pb-2 border-b-2 border-slate-900">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-rose-500 border border-slate-900" />
              <span className="font-black text-slate-900 text-sm">
                Texto con Detecciones
              </span>
            </div>
            <span className="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-300">
              Clic para ver regla
            </span>
          </div>

          <div className="text-base leading-relaxed p-4 bg-slate-50 rounded-2xl border-2 border-slate-900 min-h-[110px]">
            {renderOriginalHighlighted()}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4 mt-3 pt-2 text-xs font-bold text-slate-700 border-t-2 border-slate-100 flex-wrap gap-y-1">
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-md bg-brutal-pinkLight border-1.5 border-slate-900" />
            <span>BERT + T5 Coinciden</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-md bg-brutal-yellow border-1.5 border-slate-900" />
            <span>Sugerido por T5</span>
          </span>
        </div>
      </div>

      {/* Panel Derecho: Texto Corregido */}
      <div className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-3 pb-2 border-b-2 border-slate-900">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-teal-500 border border-slate-900" />
              <span className="font-black text-slate-900 text-sm">
                Texto Corregido (T5 GEC)
              </span>
            </div>
            <span className="text-xs font-black px-2.5 py-0.5 rounded-full bg-brutal-tealLight text-slate-900 border-1.5 border-slate-900 shadow-brutal-xs">
              {explanations.length === 0 ? "Sin Errores" : `${explanations.length} Correcciones`}
            </span>
          </div>

          <div className="text-base font-medium leading-relaxed p-4 bg-teal-50/60 rounded-2xl border-2 border-slate-900 text-slate-900 min-h-[110px]">
            {correctedText}
          </div>
        </div>

        <div className="flex items-center justify-between mt-3 pt-2 text-xs text-slate-700 border-t-2 border-slate-100">
          <span className="flex items-center space-x-1.5 text-teal-800 font-bold">
            <CheckCircle2 className="w-4 h-4 text-teal-600" />
            <span>Gramaticalmente consistente</span>
          </span>
          <button
            onClick={() => navigator.clipboard.writeText(correctedText)}
            className="brutal-btn text-xs font-bold px-3 py-1 bg-white hover:bg-slate-100 text-slate-900 rounded-full border-1.5 border-slate-900 shadow-brutal-xs transition-colors cursor-pointer"
          >
            Copiar Corrección
          </button>
        </div>
      </div>
    </div>
  );
};
