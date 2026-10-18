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
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-linear-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-100">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold bg-linear-to-r from-indigo-700 to-violet-600 bg-clip-text text-transparent">
                GrammarAI
              </span>
              <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">
                BERT + T5 + ERRANT
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Detección, Corrección y Explicaciones Pedagógicas de Gramática en Inglés
            </p>
          </div>
        </div>

        {/* Actions & Status */}
        <div className="flex items-center space-x-3">
          {/* Taxonomy Button */}
          <button
            onClick={onOpenTaxonomy}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors border border-slate-200"
            title="Ver Taxonomía Gramatical Pedagógica"
          >
            <BookOpen className="w-4 h-4 text-slate-500" />
            <span className="hidden md:inline">Taxonomía Gramatical</span>
          </button>

          {/* Backend Status Badge */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs">
            <span className="text-slate-500 font-medium hidden sm:inline">Backend:</span>
            {healthLoading ? (
              <span className="flex items-center text-amber-600 space-x-1">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Verificando...</span>
              </span>
            ) : isHealthy ? (
              <span className="flex items-center text-emerald-600 space-x-1 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>En línea ({backendHealth?.device || "CPU/GPU"})</span>
              </span>
            ) : (
              <span className="flex items-center text-rose-600 space-x-1 font-semibold">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                <span>Desconectado</span>
              </span>
            )}
            <button
              onClick={onRefreshHealth}
              disabled={healthLoading}
              title="Actualizar estado del servidor"
              className="text-slate-400 hover:text-slate-600 transition-colors p-0.5 rounded"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${healthLoading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
