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
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5 my-4">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <GitCompare className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold text-slate-800 text-sm">
            Comparativa de Ediciones (Diff)
          </span>
        </div>
        <div className="flex items-center space-x-1 bg-slate-100 p-0.5 rounded-lg text-xs">
          <button
            onClick={() => setViewMode("inline")}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              viewMode === "inline"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Vista Unificada
          </button>
          <button
            onClick={() => setViewMode("split")}
            className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
              viewMode === "split"
                ? "bg-white text-indigo-700 shadow-xs"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Vista Dividida
          </button>
        </div>
      </div>

      {viewMode === "inline" ? (
        <div className="p-3.5 bg-slate-50/70 rounded-xl border border-slate-100 text-base leading-relaxed">
          {renderInlineDiff()}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div className="p-3 bg-rose-50/40 rounded-xl border border-rose-100">
            <div className="text-xs font-semibold text-rose-700 mb-1">Original:</div>
            <div className="text-slate-800">{originalText}</div>
          </div>
          <div className="p-3 bg-emerald-50/40 rounded-xl border border-emerald-100">
            <div className="text-xs font-semibold text-emerald-700 mb-1">Corregido:</div>
            <div className="text-slate-800 font-medium">{correctedText}</div>
          </div>
        </div>
      )}
    </div>
  );
};
