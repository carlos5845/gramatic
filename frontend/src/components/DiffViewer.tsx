"use client";

import React, { useState } from "react";
import { EditExplanation } from "../types/api";
import { GitCompare, Eye, ArrowRight } from "lucide-react";

interface DiffViewerProps {
  originalText: string;
  correctedText: string;
  explanations: EditExplanation[];
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  originalText,
  correctedText,
  explanations,
}) => {
  const [viewMode, setViewMode] = useState<"inline" | "split">("inline");

  if (explanations.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-5 my-4 text-center">
        <p className="text-sm text-slate-500">
          No se detectaron diferencias entre el texto original y el corregido. El texto es gramaticalmente correcto.
        </p>
      </div>
    );
  }

  // Inline unified representation
  const renderInlineDiff = () => {
    const sortedEdits = [...explanations].sort(
      (a, b) => a.char_span.start - b.char_span.start
    );

    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedEdits.forEach((edit) => {
      const { start, end } = edit.char_span;
      if (start > lastIndex) {
        elements.push(
          <span key={`diff-txt-${lastIndex}`} className="text-slate-700">
            {originalText.substring(lastIndex, start)}
          </span>
        );
      }

      if (start === end) {
        // Insertion
        elements.push(
          <ins
            key={`diff-ins-${edit.edit_index}`}
            className="bg-emerald-100 text-emerald-800 px-1 py-0.5 rounded no-underline font-semibold mx-0.5"
          >
            +{edit.corrected_fragment}
          </ins>
        );
      } else {
        // Deletion + Insertion or Substitution
        const origFrag = originalText.substring(start, end);
        elements.push(
          <span key={`diff-sub-${edit.edit_index}`} className="inline-flex items-center mx-1">
            <del className="bg-rose-100 text-rose-700 px-1 py-0.5 rounded mr-1 line-through">
              {origFrag}
            </del>
            <ins className="bg-emerald-100 text-emerald-800 px-1 py-0.5 rounded no-underline font-semibold">
              {edit.corrected_fragment}
            </ins>
          </span>
        );
      }

      lastIndex = Math.max(lastIndex, end);
    });

    if (lastIndex < originalText.length) {
      elements.push(
        <span key={`diff-txt-end`} className="text-slate-700">
          {originalText.substring(lastIndex)}
        </span>
      );
    }

    return elements;
  };

  return (
    <div className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5 my-4">
      <div className="flex items-center justify-between mb-3 pb-2 border-b-2 border-slate-900 flex-wrap gap-2">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-brutal-yellow border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
            <GitCompare className="w-4 h-4 text-slate-900" />
          </div>
          <span className="font-black text-slate-900 text-sm">
            Comparativa de Ediciones (Diff)
          </span>
        </div>

        {/* Neobrutalist Segment Control (as in reference image) */}
        <div className="flex items-center border-2 border-slate-900 rounded-full bg-white p-0.5 shadow-brutal-xs text-xs">
          <button
            onClick={() => setViewMode("inline")}
            className={`px-3 py-1 rounded-full font-bold transition-all cursor-pointer ${
              viewMode === "inline"
                ? "bg-teal-500 text-white shadow-xs"
                : "text-slate-700 hover:text-slate-900"
            }`}
          >
            Vista Unificada
          </button>
          <button
            onClick={() => setViewMode("split")}
            className={`px-3 py-1 rounded-full font-bold transition-all cursor-pointer ${
              viewMode === "split"
                ? "bg-teal-500 text-white shadow-xs"
                : "text-slate-700 hover:text-slate-900"
            }`}
          >
            Vista Dividida
          </button>
        </div>
      </div>

      {viewMode === "inline" ? (
        <div className="p-4 bg-slate-50 rounded-2xl border-2 border-slate-900 text-base leading-relaxed text-slate-900">
          {renderInlineDiff()}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="p-3.5 bg-rose-50/70 rounded-2xl border-2 border-slate-900">
            <div className="text-xs font-black text-rose-800 mb-1">Texto Original:</div>
            <div className="text-slate-900 font-medium">{originalText}</div>
          </div>
          <div className="p-3.5 bg-teal-50/70 rounded-2xl border-2 border-slate-900">
            <div className="text-xs font-black text-teal-800 mb-1">Texto Corregido:</div>
            <div className="text-slate-900 font-bold">{correctedText}</div>
          </div>
        </div>
      )}
    </div>
  );
};
