"use client";

import React from "react";
import { EditExplanation } from "../types/api";
import {
  ArrowRight,
  CheckCircle,
  HelpCircle,
  Sparkles,
  Info,
  Check,
  X,
  ShieldCheck,
  Tag,
} from "lucide-react";

interface ExplanationCardProps {
  explanation: EditExplanation;
  isSelected: boolean;
  onSelect: () => void;
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({
  explanation,
  isSelected,
  onSelect,
}) => {
  const {
    edit_index,
    original_fragment,
    corrected_fragment,
    category_name,
    category_name_en,
    operation,
    confidence,
    summary,
    rule_explanation,
    example,
    ged_match_status,
  } = explanation;

  // Badge de certeza
  const renderConfidenceBadge = () => {
    switch (confidence) {
      case "high":
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Certeza Alta</span>
          </span>
        );
      case "medium":
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span>Certeza Media</span>
          </span>
        );
      case "uncertain":
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
            <HelpCircle className="w-3 h-3 text-slate-500" />
            <span>Caso Incierto / Estilo</span>
          </span>
        );
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`bg-white rounded-2xl border transition-all cursor-pointer p-4 sm:p-5 shadow-xs ${
        isSelected
          ? "border-indigo-500 ring-2 ring-indigo-200 shadow-md transform -translate-y-0.5"
          : "border-slate-200 hover:border-indigo-300 hover:shadow-xs"
      }`}
    >
      {/* Header: Category, Edit Number & Badges */}
      <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
        <div className="flex items-center space-x-2">
          <span className="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center text-xs font-bold border border-indigo-100">
            #{edit_index + 1}
          </span>
          <span className="font-semibold text-slate-800 text-sm">
            {category_name}
          </span>
          <span className="text-xs text-slate-400 font-mono hidden sm:inline">
            ({category_name_en})
          </span>
        </div>

        <div className="flex items-center space-x-1.5">
          {ged_match_status === "detected_by_both" ? (
            <span
              className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-medium border border-indigo-200"
              title="Detectado tanto por BERT como por T5"
            >
              BERT + T5
            </span>
          ) : (
            <span
              className="text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-medium border border-amber-200"
              title="Propuesto por el corrector T5 GEC"
            >
              Solo T5
            </span>
          )}
          {renderConfidenceBadge()}
        </div>
      </div>

      {/* Change Fragment Visualizer */}
      <div className="flex items-center space-x-2 p-3 bg-slate-50 rounded-xl border border-slate-100 mb-3 text-sm">
        <div className="flex-1 flex items-center space-x-1.5 min-w-0">
          <span className="text-xs font-bold text-rose-500 uppercase shrink-0">
            Original:
          </span>
          <span className="font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-100 truncate">
            {original_fragment || "∅ (omisión)"}
          </span>
        </div>

        <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />

        <div className="flex-1 flex items-center space-x-1.5 min-w-0">
          <span className="text-xs font-bold text-emerald-600 uppercase shrink-0">
            Sugerencia:
          </span>
          <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 truncate">
            {corrected_fragment || "∅ (eliminar)"}
          </span>
        </div>
      </div>

      {/* Summary & Rule Explanation */}
      <div className="space-y-2 mb-3 text-sm">
        <p className="text-slate-800 font-medium">{summary}</p>
        <div className="flex items-start space-x-2 text-xs text-slate-600 bg-indigo-50/50 p-2.5 rounded-lg border border-indigo-100/60">
          <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{rule_explanation}</p>
        </div>
      </div>

      {/* Pedagogical Example (Incorrect vs Correct) */}
      {example && (
        <div className="p-3 bg-slate-50/80 rounded-xl border border-slate-100 space-y-1.5 text-xs">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Ejemplo Ilustrativo
          </div>
          <div className="flex items-center space-x-2 text-rose-700">
            <X className="w-3.5 h-3.5 text-rose-500 shrink-0" />
            <span className="line-through">{example.incorrect}</span>
          </div>
          <div className="flex items-center space-x-2 text-emerald-700 font-medium">
            <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>{example.correct}</span>
          </div>
        </div>
      )}
    </div>
  );
};
