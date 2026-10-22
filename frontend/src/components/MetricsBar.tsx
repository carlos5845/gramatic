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
      <div className="bg-white p-3.5 rounded-2xl border-2 border-slate-900 shadow-brutal-sm flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-brutal-pinkLight border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
          <AlertCircle className="w-5 h-5 text-rose-600" />
        </div>
        <div>
          <div className="text-xl font-black text-slate-900">{gedErrors}</div>
          <div className="text-[11px] text-slate-600 font-bold">Tokens BERT</div>
        </div>
      </div>

      {/* GEC Corrections */}
      <div className="bg-white p-3.5 rounded-2xl border-2 border-slate-900 shadow-brutal-sm flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-brutal-blueLight border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
          <CheckCircle className="w-5 h-5 text-brutal-blue" />
        </div>
        <div>
          <div className="text-xl font-black text-slate-900">{gecEdits}</div>
          <div className="text-[11px] text-slate-600 font-bold">Ediciones T5</div>
        </div>
      </div>

      {/* Concordance Rate */}
      <div className="bg-white p-3.5 rounded-2xl border-2 border-slate-900 shadow-brutal-sm flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-brutal-tealLight border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
          <ArrowRightLeft className="w-5 h-5 text-teal-700" />
        </div>
        <div>
          <div className="text-xl font-black text-slate-900">{concordanceRate}%</div>
          <div className="text-[11px] text-slate-600 font-bold">Concordancia</div>
        </div>
      </div>

      {/* Inference Time */}
      <div className="bg-white p-3.5 rounded-2xl border-2 border-slate-900 shadow-brutal-sm flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-brutal-yellow border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shadow-brutal-xs">
          <Zap className="w-5 h-5 text-slate-900" />
        </div>
        <div>
          <div className="text-xl font-black text-slate-900">{timeMs} ms</div>
          <div className="text-[11px] text-slate-600 font-bold">Latencia</div>
        </div>
      </div>
    </div>
  );
};
