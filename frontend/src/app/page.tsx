"use client";

import React, { useState, useEffect, useRef } from "react";
import { Header } from "../components/Header";
import { TextInputArea, SAMPLE_SENTENCES } from "../components/TextInputArea";
import { MetricsBar } from "../components/MetricsBar";
import { InteractiveTextHighlighter } from "../components/InteractiveTextHighlighter";
import { DiffViewer } from "../components/DiffViewer";
import { ExplanationCard } from "../components/ExplanationCard";
import { ReconciliationBadge } from "../components/ReconciliationBadge";
import { TaxonomyModal } from "../components/TaxonomyModal";
import {
  AnalysisResponse,
  HealthResponse,
} from "../types/api";
import { analyzeText, checkBackendHealth } from "../lib/api";
import {
  AlertTriangle,
  Sparkles,
  BookOpen,
  Filter,
  CheckCircle2,
  RefreshCw,
  Terminal,
} from "lucide-react";

export default function Home() {
  const [inputText, setInputText] = useState(
    "She go to school yesterday and saw two apple ."
  );
  const [analysisResult, setAnalysisResult] =
    useState<AnalysisResponse | null>(null);
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(
    null
  );
  const [healthLoading, setHealthLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedEditIndex, setSelectedEditIndex] = useState<number | null>(
    null
  );
  const [selectedCategoryFilter, setSelectedCategoryFilter] =
    useState<string>("all");
  const [isTaxonomyOpen, setIsTaxonomyOpen] = useState(false);

  const explanationsContainerRef = useRef<HTMLDivElement>(null);

  // Comprobar estado del backend al montar
  const fetchHealth = async () => {
    setHealthLoading(true);
    try {
      const health = await checkBackendHealth();
      setBackendHealth(health);
    } catch (err: any) {
      setBackendHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  // Manejador del análisis de texto
  const handleAnalyze = async () => {
    if (!inputText.trim()) return;

    setIsAnalyzing(true);
    setErrorMessage(null);
    setSelectedEditIndex(null);

    try {
      const result = await analyzeText(inputText);
      setAnalysisResult(result);
    } catch (err: any) {
      console.error("Error al analizar texto:", err);
      const msg =
        err.message ||
        "No se pudo conectar con el servidor de análisis. Asegúrate de que FastAPI esté ejecutándose en http://127.0.0.1:8000.";
      setErrorMessage(msg);
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Filtrado de explicaciones
  const filteredExplanations = analysisResult?.explanations.filter((exp) => {
    if (selectedCategoryFilter === "all") return true;
    return exp.category_id === selectedCategoryFilter;
  }) || [];

  // Categorías presentes en los resultados actuales
  const availableCategories = Array.from(
    new Set(analysisResult?.explanations.map((e) => e.category_id) || [])
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <Header
        backendHealth={backendHealth}
        healthLoading={healthLoading}
        onRefreshHealth={fetchHealth}
        onOpenTaxonomy={() => setIsTaxonomyOpen(true)}
      />

      {/* Main Content Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error Alert */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start space-x-3 shadow-xs animate-in fade-in">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1 text-sm">
              <div className="font-semibold text-rose-900">
                Error en el análisis de texto
              </div>
              <p className="mt-0.5">{errorMessage}</p>
              <div className="mt-2 text-xs text-rose-700 bg-rose-100/60 p-2 rounded-lg font-mono">
                Consejo: Inicia el backend ejecutando <span className="font-bold">python main.py --mode api</span> en la terminal.
              </div>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-500 hover:text-rose-700 text-xs font-semibold px-2 py-1 rounded"
            >
              Cerrar
            </button>
          </div>
        )}

        {/* Input Text Area Section */}
        <TextInputArea
          inputText={inputText}
          setInputText={setInputText}
          onAnalyze={handleAnalyze}
          isLoading={isAnalyzing}
          maxChars={2000}
        />

        {/* Analysis Results Display */}
        {analysisResult && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Top Metrics Bar */}
            <MetricsBar analysis={analysisResult} />

            {/* Interactive Highlighter Section (Original vs Corrected) */}
            <InteractiveTextHighlighter
              originalText={analysisResult.original_text}
              correctedText={analysisResult.corrected_text}
              explanations={analysisResult.explanations}
              gedResults={analysisResult.ged_results}
              selectedEditIndex={selectedEditIndex}
              onSelectEdit={(idx) => setSelectedEditIndex(idx)}
            />

            {/* Diff Viewer */}
            <DiffViewer
              originalText={analysisResult.original_text}
              correctedText={analysisResult.corrected_text}
              explanations={analysisResult.explanations}
            />

            {/* Reconciliation Insights */}
            <ReconciliationBadge
              reconciliation={analysisResult.reconciliation}
            />

            {/* Pedagogical Explanations Section */}
            <div
              ref={explanationsContainerRef}
              className="bg-white rounded-3xl border border-slate-200 shadow-sm p-5 sm:p-6"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-lg font-bold text-slate-800 flex items-center space-x-2">
                    <BookOpen className="w-5 h-5 text-indigo-600" />
                    <span>Explicaciones Pedagógicas Gramaticales</span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    Reglas estructuradas y ejemplos basados en la taxonomía de aprendizaje de inglés
                  </p>
                </div>

                {/* Filter by Category */}
                {availableCategories.length > 1 && (
                  <div className="flex items-center space-x-2 text-xs">
                    <Filter className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-500 font-medium">Filtrar:</span>
                    <select
                      value={selectedCategoryFilter}
                      onChange={(e) => setSelectedCategoryFilter(e.target.value)}
                      className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 font-medium focus:outline-hidden focus:ring-2 focus:ring-indigo-100"
                    >
                      <option value="all">Todas las categorías ({analysisResult.explanations.length})</option>
                      {availableCategories.map((catId) => {
                        const count = analysisResult.explanations.filter(
                          (e) => e.category_id === catId
                        ).length;
                        const catName =
                          analysisResult.explanations.find((e) => e.category_id === catId)
                            ?.category_name || catId;
                        return (
                          <option key={catId} value={catId}>
                            {catName} ({count})
                          </option>
                        );
                      })}
                    </select>
                  </div>
                )}
              </div>

              {filteredExplanations.length === 0 ? (
                <div className="py-12 text-center text-slate-400">
                  <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2 opacity-80" />
                  <p className="font-semibold text-slate-700 text-base">
                    {analysisResult.is_changed
                      ? "No hay explicaciones que coincidan con el filtro seleccionado."
                      : "¡Texto Gramaticalmente Impecable!"}
                  </p>
                  <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                    {analysisResult.is_changed
                      ? "Selecciona 'Todas las categorías' para ver los demás cambios."
                      : "El modelo no encontró errores gramaticales que requieran corrección."}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredExplanations.map((exp) => (
                    <ExplanationCard
                      key={exp.edit_index}
                      explanation={exp}
                      isSelected={selectedEditIndex === exp.edit_index}
                      onSelect={() =>
                        setSelectedEditIndex(
                          selectedEditIndex === exp.edit_index ? null : exp.edit_index
                        )
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-1">
          <p className="font-medium text-slate-700">
            GrammarAI • Sistema Inteligente de Detección, Corrección y Explicación Gramatical
          </p>
          <p className="text-slate-400">
            Arquitectura Neuronal Híbrida: Fine-Tuned BERT-base (GED) + T5 Seq2Seq (GEC) + ERRANT v2.x Rule-Engine
          </p>
        </div>
      </footer>

      {/* Taxonomy Modal */}
      <TaxonomyModal
        isOpen={isTaxonomyOpen}
        onClose={() => setIsTaxonomyOpen(false)}
      />
    </div>
  );
}
