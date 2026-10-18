"use client";

import React from "react";
import { AlertCircle, CheckCircle, Zap, ShieldCheck, ArrowRightLeft } from "lucide-react";
import { AnalysisResponse } from "../types/api";

interface MetricsBarProps {
  analysis: AnalysisResponse | null;
}

export const MetricsBar: React.FC<MetricsBarProps> = ({ analysis }) => {
  if (!analysis) return null;

  const gedErrors = analysis.total_errors_detected;
  const gecEdits = analysis.total_corrections_made;
  const concordanceRate = Math.round(analysis.reconciliation.concordance_rate * 100);
  const timeMs = analysis.inference_time_ms;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
      {/* GED Errors */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xl font-bold text-slate-800">{gedErrors}</div>
          <div className="text-xs text-slate-500 font-medium">Errores BERT (GED)</div>
        </div>
      </div>

      {/* GEC Corrections */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
          <CheckCircle className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xl font-bold text-slate-800">{gecEdits}</div>
          <div className="text-xs text-slate-500 font-medium">Ediciones T5 (GEC)</div>
        </div>
      </div>

      {/* Concordance Rate */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
          <ArrowRightLeft className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xl font-bold text-slate-800">{concordanceRate}%</div>
          <div className="text-xs text-slate-500 font-medium">Concordancia BERT/GEC</div>
        </div>
      </div>

      {/* Inference Time */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
          <Zap className="w-5 h-5" />
        </div>
        <div>
          <div className="text-xl font-bold text-slate-800">{timeMs} ms</div>
          <div className="text-xs text-slate-500 font-medium">Tiempo de Inferencia</div>
        </div>
      </div>
    </div>
  );
};
