"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, RefreshCw, BookOpen, Sparkles, Cpu } from "lucide-react";
import { HealthResponse } from "../types/api";

interface HeaderProps {
  backendHealth: HealthResponse | null;
  healthLoading: boolean;
  onRefreshHealth: () => void;
  onOpenTaxonomy: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  backendHealth,
  healthLoading,
  onRefreshHealth,
  onOpenTaxonomy,
}) => {
  const isHealthy = backendHealth?.status === "healthy";

  return (
    <header className="sticky top-0 z-30 pt-3 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto bg-white border-2 border-slate-900 rounded-2xl shadow-brutal px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-brutal-blue border-2 border-slate-900 flex items-center justify-center text-white shadow-brutal-xs">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-black tracking-tight text-slate-900">
                UwUAI
              </span>
              <span className="px-2 py-0.5 text-[11px] font-bold bg-brutal-yellow text-slate-900 rounded-full border-1.5 border-slate-900 shadow-brutal-xs">
                BERT + T5
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-600 hidden sm:block">
              Asistente Pedagógico Conversacional de Inglés L2
            </p>
          </div>
        </div>

        {/* Actions & Status */}
        <div className="flex items-center space-x-2.5">
          {/* Taxonomy Button */}
          <button
            onClick={onOpenTaxonomy}
            className="brutal-btn flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-slate-900 bg-brutal-yellow hover:bg-brutal-yellowHover rounded-xl border-2 border-slate-900 shadow-brutal-xs cursor-pointer"
            title="Ver Taxonomía Gramatical Pedagógica"
          >
            <BookOpen className="w-3.5 h-3.5 text-slate-900" />
            <span className="hidden md:inline">Taxonomía</span>
          </button>

          {/* Backend Status Badge */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-xl border-2 border-slate-900 shadow-brutal-xs text-xs">
            {healthLoading ? (
              <span className="flex items-center text-amber-700 space-x-1.5 font-bold">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span className="hidden sm:inline">Conectando...</span>
              </span>
            ) : isHealthy ? (
              <span className="flex items-center text-emerald-800 space-x-1.5 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-slate-900 animate-pulse" />
                <span>Online</span>
              </span>
            ) : (
              <span className="flex items-center text-rose-700 space-x-1.5 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 border border-slate-900" />
                <span>Offline</span>
              </span>
            )}
            <button
              onClick={onRefreshHealth}
              disabled={healthLoading}
              title="Refrescar estado"
              className="text-slate-500 hover:text-slate-900 transition-colors p-0.5 rounded cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
