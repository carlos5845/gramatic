import {
  AnalysisResponse,
  DetectionOnlyResponse,
  CorrectionOnlyResponse,
  TaxonomyCategory,
  HealthResponse,
} from "../types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" && window.location.port === "8000"
    ? ""
    : "http://127.0.0.1:8000");

async function handleResponse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({
    success: false,
    error_type: "NETWORK_ERROR",
    error_message: "Respuesta no válida del servidor.",
  }));

  if (!res.ok || data.success === false) {
    const errorMsg =
      data.error_message ||
      (typeof data.detail === "string" ? data.detail : "Error al procesar la solicitud.");
    const err = new Error(errorMsg);
    (err as any).errorType = data.error_type || `HTTP_${res.status}`;
    (err as any).status = res.status;
    (err as any).detail = data.detail;
    throw err;
  }

  return data as T;
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      cache: "no-store",
    });
    return await handleResponse<HealthResponse>(res);
  } catch (error) {
    throw error;
  }
}

export async function getTaxonomyCategories(): Promise<TaxonomyCategory[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/taxonomy`, {
    method: "GET",
    cache: "force-cache",
  });
  return await handleResponse<TaxonomyCategory[]>(res);
}

export async function analyzeText(
  text: string,
  options?: {
    include_ged?: boolean;
    include_gec?: boolean;
    include_explanations?: boolean;
  }
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text,
      include_ged: options?.include_ged ?? true,
      include_gec: options?.include_gec ?? true,
      include_explanations: options?.include_explanations ?? true,
    }),
  });

  return await handleResponse<AnalysisResponse>(res);
}

export async function detectTokensOnly(text: string): Promise<DetectionOnlyResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/detect`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  return await handleResponse<DetectionOnlyResponse>(res);
}

export async function correctTextOnly(text: string): Promise<CorrectionOnlyResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/correct`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  return await handleResponse<CorrectionOnlyResponse>(res);
}
