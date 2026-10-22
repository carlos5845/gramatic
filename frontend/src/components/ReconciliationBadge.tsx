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
    <div className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5 my-4">
      <div className="flex items-center justify-between mb-3 pb-2 border-b-2 border-slate-900">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-brutal-blueLight border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
            <ArrowRightLeft className="w-4 h-4 text-brutal-blue" />
          </div>
          <span className="font-black text-slate-900 text-sm">
            Reconciliación de Modelos (BERT vs. T5)
          </span>
        </div>
        <span className="text-xs font-black px-3 py-1 rounded-full bg-brutal-yellow text-slate-900 border-1.5 border-slate-900 shadow-brutal-xs">
          {pct}% Concordancia
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
        <div className="p-3 bg-teal-50/80 rounded-2xl border-2 border-slate-900 shadow-brutal-xs text-center">
          <div className="text-xl font-black text-slate-900">{concordance_count}</div>
          <div className="text-xs font-bold text-teal-800">Coincidencias</div>
        </div>
        <div className="p-3 bg-amber-50/80 rounded-2xl border-2 border-slate-900 shadow-brutal-xs text-center">
          <div className="text-xl font-black text-slate-900">{gec_only_count}</div>
          <div className="text-xs font-bold text-amber-800">Solo T5</div>
        </div>
        <div className="p-3 bg-blue-50/80 rounded-2xl border-2 border-slate-900 shadow-brutal-xs text-center">
          <div className="text-xl font-black text-slate-900">{ged_only_count}</div>
          <div className="text-xs font-bold text-blue-800">Solo BERT</div>
        </div>
      </div>

      <div className="flex items-start space-x-2 text-xs text-slate-800 bg-slate-50 p-3 rounded-2xl border-1.5 border-slate-900 shadow-brutal-xs">
        <Info className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
        <p className="leading-relaxed font-medium">{notes}</p>
      </div>
    </div>
  );
};
