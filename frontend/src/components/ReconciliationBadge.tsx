"use client";

import React from "react";
import { ReconciliationSummary } from "../types/api";
import { ArrowRightLeft, ShieldCheck, Info } from "lucide-react";

interface ReconciliationBadgeProps {
  reconciliation: ReconciliationSummary;
}

export const ReconciliationBadge: React.FC<ReconciliationBadgeProps> = ({
  reconciliation,
}) => {
  const {
    total_ged_errors,
    total_gec_edits,
    concordance_count,
    gec_only_count,
    ged_only_count,
    concordance_rate,
    notes,
  } = reconciliation;

  const pct = Math.round(concordance_rate * 100);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sm:p-5 my-4">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <ArrowRightLeft className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold text-slate-800 text-sm">
            Reconciliación de Modelos (BERT GED vs. T5 GEC)
          </span>
        </div>
        <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
          {pct}% Concordancia
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
        <div className="p-3 bg-emerald-50/50 rounded-xl border border-emerald-100 text-center">
          <div className="text-lg font-bold text-emerald-800">{concordance_count}</div>
          <div className="text-xs text-emerald-700">Detecciones Coincidentes</div>
        </div>
        <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-100 text-center">
          <div className="text-lg font-bold text-amber-800">{gec_only_count}</div>
          <div className="text-xs text-amber-700">Ediciones Exclusivas T5</div>
        </div>
        <div className="p-3 bg-indigo-50/50 rounded-xl border border-indigo-100 text-center">
          <div className="text-lg font-bold text-indigo-800">{ged_only_count}</div>
          <div className="text-xs text-indigo-700">Tokens Marcados BERT</div>
        </div>
      </div>

      <div className="flex items-start space-x-2 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
        <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">{notes}</p>
      </div>
    </div>
  );
};
