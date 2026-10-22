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
    <div className="min-h-screen flex flex-col bg-brutal-bg">
      {/* Header */}
      <Header
        backendHealth={backendHealth}
        healthLoading={healthLoading}
        onRefreshHealth={fetchHealth}
        onOpenTaxonomy={() => setIsTaxonomyOpen(true)}
      />

      {/* Main Chat Conversation Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Error Alert */}
        {errorMessage && (
          <div className="p-4 rounded-3xl bg-rose-100 border-2 border-slate-900 text-slate-900 flex items-start space-x-3 shadow-brutal animate-in fade-in">
            <div className="w-8 h-8 rounded-xl bg-rose-400 border-1.5 border-slate-900 flex items-center justify-center text-slate-900 shrink-0 shadow-brutal-xs">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div className="flex-1 text-sm font-medium">
              <div className="font-black text-slate-900 text-base">
                Aviso del Sistema
              </div>
              <p className="mt-0.5 text-slate-800">{errorMessage}</p>
              <div className="mt-2 text-xs text-slate-900 bg-white p-2.5 rounded-xl border-1.5 border-slate-900 font-mono shadow-brutal-xs">
                Inicia el backend ejecutando <span className="font-bold text-rose-700">python main.py --mode api</span> en la terminal.
              </div>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="brutal-btn text-xs font-black px-3 py-1 bg-white hover:bg-slate-100 rounded-full border-1.5 border-slate-900 shadow-brutal-xs cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        )}

        {/* Chatbot Thread */}
        <div className="space-y-6">
          {/* Welcome Bot Message (Always visible or starting point) */}
          <div className="flex items-start space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-brutal-blue border-2 border-slate-900 flex items-center justify-center text-white shrink-0 shadow-brutal-xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex-1 bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5">
              <div className="flex items-center space-x-2 mb-1">
                <span className="font-black text-slate-900 text-sm">UwUAI Coach</span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brutal-yellow border border-slate-900">
                  Bot Activo
                </span>
              </div>
              <p className="text-sm font-medium text-slate-800 leading-relaxed">
                ¡Hola! Soy tu tutor interactivo de gramática en inglés. Escribe o pega cualquier oración abajo para que analice errores a nivel de token (BERT), genere correcciones contextuales (T5) y te explique las reglas pedagógicas con ejemplos (ERRANT).
              </p>
            </div>
          </div>

          {/* User Message Bubble (if text analyzed) */}
          {analysisResult && (
            <div className="flex items-start justify-end space-x-3">
              <div className="bg-brutal-yellow rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5 max-w-2xl text-right">
                <div className="text-[11px] font-black uppercase text-slate-700 mb-1">
                  Tu Oración Enviada:
                </div>
                <p className="text-base font-bold text-slate-900 text-left">
                  "{analysisResult.original_text}"
                </p>
              </div>
              <div className="w-10 h-10 rounded-2xl bg-slate-900 border-2 border-slate-900 flex items-center justify-center text-white shrink-0 shadow-brutal-xs font-black text-sm">
                TÚ
              </div>
            </div>
          )}

          {/* Bot Analysis Response Bubble */}
          {analysisResult && (
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 rounded-2xl bg-brutal-blue border-2 border-slate-900 flex items-center justify-center text-white shrink-0 shadow-brutal-xs">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="flex-1 space-y-5">
                {/* Result Summary Bubble */}
                <div className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-4 sm:p-5">
                  <div className="flex items-center justify-between mb-2 pb-2 border-b-2 border-slate-900 flex-wrap gap-2">
                    <span className="font-black text-slate-900 text-base flex items-center space-x-2">
                      <CheckCircle2 className="w-5 h-5 text-teal-600" />
                      <span>Informe de Diagnóstico Gramatical</span>
                    </span>
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-brutal-tealLight text-slate-900 border-1.5 border-slate-900 shadow-brutal-xs">
                      {analysisResult.is_changed
                        ? `${analysisResult.total_corrections_made} correcciones realizadas`
                        : "Texto correcto sin modificaciones"}
                    </span>
                  </div>

                  {/* Top Metrics */}
                  <MetricsBar analysis={analysisResult} />

                  {/* Interactive Highlighter */}
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

                  {/* Reconciliation */}
                  <ReconciliationBadge
                    reconciliation={analysisResult.reconciliation}
                  />
                </div>

                {/* Pedagogical Explanations Section */}
                <div
                  ref={explanationsContainerRef}
                  className="bg-white rounded-3xl border-2 border-slate-900 shadow-brutal p-5 sm:p-6"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b-2 border-slate-900">
                    <div>
                      <h3 className="text-base font-black text-slate-900 flex items-center space-x-2">
                        <BookOpen className="w-5 h-5 text-brutal-blue" />
                        <span>Tarjetas de Aprendizaje Pedagógico</span>
                      </h3>
                      <p className="text-xs font-semibold text-slate-600">
                        Reglas gramaticales violadas y ejemplos contrastivos
                      </p>
                    </div>

                    {/* Filter by Category */}
                    {availableCategories.length > 1 && (
                      <div className="flex items-center space-x-2 text-xs">
                        <Filter className="w-3.5 h-3.5 text-slate-900" />
                        <span className="text-slate-900 font-bold">Filtrar:</span>
                        <select
                          value={selectedCategoryFilter}
                          onChange={(e) => setSelectedCategoryFilter(e.target.value)}
                          className="px-3 py-1.5 bg-white border-2 border-slate-900 rounded-full text-slate-900 font-bold shadow-brutal-xs focus:outline-hidden cursor-pointer"
                        >
                          <option value="all">Todas ({analysisResult.explanations.length})</option>
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
                    <div className="py-10 text-center text-slate-600">
                      <CheckCircle2 className="w-10 h-10 text-teal-600 mx-auto mb-2" />
                      <p className="font-black text-slate-900 text-base">
                        {analysisResult.is_changed
                          ? "No hay explicaciones para el filtro actual."
                          : "¡Texto gramaticalmente impecable!"}
                      </p>
                      <p className="text-xs font-semibold text-slate-600 mt-1">
                        {analysisResult.is_changed
                          ? "Selecciona 'Todas' para ver el resto de correcciones."
                          : "El modelo T5 no identificó modificaciones necesarias."}
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
            </div>
          )}
        </div>

        {/* Chatbot Bottom Input Box */}
        <div className="pt-2">
          <TextInputArea
            inputText={inputText}
            setInputText={setInputText}
            onAnalyze={handleAnalyze}
            isLoading={isAnalyzing}
            maxChars={2000}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 mt-8 text-center text-xs text-slate-700">
        <div className="max-w-5xl mx-auto px-4 space-y-1">
          <p className="font-black text-slate-900">
            GrammarAI • Tutor Inteligente de Inglés (L2)
          </p>
          <p className="font-semibold text-slate-600">
            Diseño Neobrutalismo Suave • BERT (GED) + T5 (GEC) + ERRANT Rules Engine
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
