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
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-emerald-300 text-slate-900 border-1.5 border-slate-900 shadow-brutal-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-900" />
            <span>Certeza Alta</span>
          </span>
        );
      case "medium":
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-black bg-brutal-yellow text-slate-900 border-1.5 border-slate-900 shadow-brutal-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-900" />
            <span>Certeza Media</span>
          </span>
        );
      case "uncertain":
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border-1.5 border-slate-900 shadow-brutal-xs">
            <HelpCircle className="w-3 h-3 text-slate-900" />
            <span>Estilo / Incierto</span>
          </span>
        );
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`bg-white rounded-3xl border-2 border-slate-900 transition-all cursor-pointer p-4 sm:p-5 ${
        isSelected
          ? "bg-brutal-pinkLight/25 shadow-brutal-lg ring-2 ring-slate-900 transform -translate-y-1"
          : "shadow-brutal hover:shadow-brutal-lg hover:-translate-y-0.5"
      }`}
    >
      {/* Header: Category, Edit Number & Badges */}
      <div className="flex items-center justify-between gap-2 mb-3 flex-wrap">
        <div className="flex items-center space-x-2">
          <span className="w-7 h-7 rounded-xl bg-brutal-yellow text-slate-900 flex items-center justify-center text-xs font-black border-1.5 border-slate-900 shadow-brutal-xs">
            #{edit_index + 1}
          </span>
          <span className="font-black text-slate-900 text-sm">
            {category_name}
          </span>
          <span className="text-xs text-slate-500 font-mono hidden sm:inline">
            ({category_name_en})
          </span>
        </div>

        <div className="flex items-center space-x-1.5">
          {ged_match_status === "detected_by_both" ? (
            <span
              className="text-[11px] px-2.5 py-0.5 rounded-full bg-brutal-blueLight text-slate-900 font-black border-1.5 border-slate-900 shadow-brutal-xs"
              title="Detectado tanto por BERT como por T5"
            >
              BERT + T5
            </span>
          ) : (
            <span
              className="text-[11px] px-2.5 py-0.5 rounded-full bg-brutal-yellow text-slate-900 font-bold border-1.5 border-slate-900 shadow-brutal-xs"
              title="Propuesto por el corrector T5 GEC"
            >
              Solo T5
            </span>
          )}
          {renderConfidenceBadge()}
        </div>
      </div>

      {/* Change Fragment Visualizer */}
      <div className="flex items-center space-x-2 p-3 bg-slate-50 rounded-2xl border-2 border-slate-900 mb-3 text-sm">
        <div className="flex-1 flex items-center space-x-1.5 min-w-0">
          <span className="text-xs font-black text-rose-700 uppercase shrink-0">
            Original:
          </span>
          <span className="font-bold text-rose-900 bg-rose-100 px-2.5 py-0.5 rounded-lg border-1.5 border-slate-900 truncate shadow-brutal-xs">
            {original_fragment || "∅ (omisión)"}
          </span>
        </div>

        <ArrowRight className="w-4 h-4 text-slate-900 shrink-0 font-bold" />

        <div className="flex-1 flex items-center space-x-1.5 min-w-0">
          <span className="text-xs font-black text-teal-800 uppercase shrink-0">
            Corrección:
          </span>
          <span className="font-black text-teal-900 bg-teal-100 px-2.5 py-0.5 rounded-lg border-1.5 border-slate-900 truncate shadow-brutal-xs">
            {corrected_fragment || "∅ (eliminar)"}
          </span>
        </div>
      </div>

      {/* Summary & Rule Explanation */}
      <div className="space-y-2 mb-3 text-sm">
        <p className="text-slate-900 font-bold">{summary}</p>
        <div className="flex items-start space-x-2 text-xs text-slate-800 bg-brutal-blueLight p-3 rounded-2xl border-1.5 border-slate-900 shadow-brutal-xs">
          <Info className="w-4 h-4 text-brutal-blue shrink-0 mt-0.5" />
          <p className="leading-relaxed font-medium">{rule_explanation}</p>
        </div>
      </div>

      {/* Pedagogical Example (Incorrect vs Correct) */}
      {example && (
        <div className="p-3 bg-slate-50 rounded-2xl border-2 border-slate-900 space-y-2 text-xs">
          <div className="text-[11px] font-black text-slate-700 uppercase tracking-wider">
            Ejemplo de Aprendizaje:
          </div>
          <div className="flex items-center space-x-2 text-rose-900 font-medium">
            <span className="w-4 h-4 rounded-full bg-rose-200 border border-slate-900 flex items-center justify-center shrink-0 text-slate-900">
              <X className="w-2.5 h-2.5" />
            </span>
            <span className="line-through">{example.incorrect}</span>
          </div>
          <div className="flex items-center space-x-2 text-teal-900 font-bold">
            <span className="w-4 h-4 rounded-full bg-teal-200 border border-slate-900 flex items-center justify-center shrink-0 text-slate-900">
              <Check className="w-2.5 h-2.5" />
            </span>
            <span>{example.correct}</span>
          </div>
        </div>
      )}
    </div>
  );
};
