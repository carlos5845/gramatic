import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.pipeline import IntegratedGrammarPipeline
from src.gec.explainer import TAXONOMY_CATEGORIES
from src.api.schemas import (
    TextAnalysisRequest,
    AnalysisResponseSchema,
    DetectionOnlyResponseSchema,
    CorrectionOnlyResponseSchema,
    TaxonomyCategorySchema,
    HealthResponseSchema,
    ErrorResponseSchema
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Instancia global del pipeline (singleton)
_pipeline_instance: Optional[IntegratedGrammarPipeline] = None


def get_pipeline() -> IntegratedGrammarPipeline:
    """Obtiene o inicializa el pipeline integrado singleton."""
    global _pipeline_instance
    if _pipeline_instance is None:
        logger.info("Cargando pipeline integrado en la API...")
        _pipeline_instance = IntegratedGrammarPipeline(lazy_load=False)
    return _pipeline_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación FastAPI: precarga de modelos al inicio."""
    logger.info("Iniciando servicio API de Detección, Corrección y Explicación Gramatical...")
    # Precargar pipeline para evitar latencia en la primera petición
    try:
        get_pipeline()
    except Exception as e:
        logger.warning(f"No se pudieron precargar todos los modelos al inicio: {e}")
    yield
    logger.info("Deteniendo servicio API...")


def create_app() -> FastAPI:
    """Fábrica para crear la aplicación FastAPI con todas las rutas y middlewares."""
    app = FastAPI(
        title="Grammar Error Detection & Correction API (GED + GEC + Explain)",
        description=(
            "API REST para el análisis integral de textos en inglés: detección de errores gramaticales "
            "a nivel de token con BERT (GED), corrección generativa con T5 (GEC), explicaciones pedagógicas "
            "estructuradas con ERRANT y reconciliación cruzada de resultados."
        ),
        version="1.0.0",
        lifespan=lifespan
    )

    # Middleware CORS para permitir solicitudes desde cualquier origen (e.g. interfaces web)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------
    # Manejadores de Excepciones Estructurados
    # -------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Error de validación en la solicitud: {exc}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT if hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT") else 422,
            content={
                "success": False,
                "error_type": "VALIDATION_ERROR",
                "error_message": "Los datos de la solicitud no cumplen con el formato o restricciones requeridas.",
                "detail": exc.errors()
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_type": "HTTP_ERROR",
                "error_message": exc.detail if isinstance(exc.detail, str) else "Error HTTP en la solicitud.",
                "detail": exc.detail
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Error interno no controlado: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_type": "INTERNAL_SERVER_ERROR",
                "error_message": "Ocurrió un error interno durante el procesamiento del texto.",
                "detail": str(exc)
            }
        )

    # -------------------------------------------------------------
    # Endpoints
    # -------------------------------------------------------------
    @app.get("/", summary="Bienvenida y Estado de la API")
    async def root():
        return {
            "name": "Grammar Detection, Correction & Explanation API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_url": "/health",
            "status": "online"
        }

    @app.get("/health", response_model=HealthResponseSchema, summary="Estado de Salud y Modelos")
    async def health_check():
        pipeline = get_pipeline()
        device_str = str(pipeline.detector.device) if pipeline._detector else "unknown"
        return HealthResponseSchema(
            status="healthy",
            version="1.0.0",
            device=device_str,
            models_loaded={
                "bert_ged": pipeline.bert_model_path,
                "t5_gec": pipeline.gec_model_path,
                "explainer_errant": "spaCy en_core_web_sm + ERRANT v2.x"
            }
        )

    @app.post(
        "/api/v1/analyze",
        response_model=AnalysisResponseSchema,
        summary="Análisis Completo (GED + GEC + Explicación + Reconciliación)",
        responses={
            400: {"model": ErrorResponseSchema, "description": "Entrada vacía o lenguaje inválido"},
            422: {"model": ErrorResponseSchema, "description": "Error en validación de esquema"},
            500: {"model": ErrorResponseSchema, "description": "Error interno del servidor"}
        }
    )
    async def analyze_text(request: TextAnalysisRequest):
        pipeline = get_pipeline()
        result = pipeline.process_text(
            text=request.text,
            include_ged=request.include_ged if request.include_ged is not None else True,
            include_gec=request.include_gec if request.include_gec is not None else True,
            include_explanations=request.include_explanations if request.include_explanations is not None else True
        )

        if not result.get("success", False):
            error_type = result.get("error_type", "BAD_REQUEST")
            error_msg = result.get("error_message", "Error en la solicitud.")
            status_code = status.HTTP_400_BAD_REQUEST
            if error_type == "INPUT_TOO_LONG":
                status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "error_type": error_type,
                    "error_message": error_msg,
                    "detail": result.get("original_text", "")
                }
            )

        return result

    @app.post(
        "/api/v1/detect",
        response_model=DetectionOnlyResponseSchema,
        summary="Detección de Errores por Token (BERT GED)",
        responses={400: {"model": ErrorResponseSchema}}
    )
    async def detect_tokens(request: TextAnalysisRequest):
        pipeline = get_pipeline()
        t0 = time.perf_counter()
        ged_res = pipeline.detector.detect_errors_in_text(request.text)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        
        if not ged_res.get("success", False):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error_type": "GED_ERROR",
                    "error_message": ged_res.get("error_message", "Error en detección"),
                    "detail": request.text
                }
            )
            
        return DetectionOnlyResponseSchema(
            success=True,
            text=request.text,
            total_errors=ged_res.get("total_errors", 0),
            sentences=ged_res.get("sentences", []),
            inference_time_ms=elapsed_ms
        )

    @app.post(
        "/api/v1/correct",
        response_model=CorrectionOnlyResponseSchema,
        summary="Corrección Gramatical Rápida (T5 GEC)",
        responses={400: {"model": ErrorResponseSchema}}
    )
    async def correct_text(request: TextAnalysisRequest):
        pipeline = get_pipeline()
        cleaned = request.text.strip()
        if not cleaned:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error_type": "EMPTY_INPUT",
                    "error_message": "El texto está vacío.",
                    "detail": ""
                }
            )
            
        corr_res = pipeline.corrector.correct_sentence(cleaned)
        return CorrectionOnlyResponseSchema(
            success=True,
            original=corr_res["original"],
            corrected=corr_res["corrected"],
            is_changed=corr_res["is_changed"],
            inference_time_ms=corr_res["inference_time_ms"]
        )

    @app.post(
        "/api/v1/explain",
        summary="Corrección y Explicaciones Pedagógicas",
        responses={400: {"model": ErrorResponseSchema}}
    )
    async def explain_text(request: TextAnalysisRequest):
        pipeline = get_pipeline()
        res = pipeline.process_text(
            text=request.text,
            include_ged=False,
            include_gec=True,
            include_explanations=True
        )
        if not res.get("success", False):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error_type": res.get("error_type", "EXPLAIN_ERROR"),
                    "error_message": res.get("error_message", "Error al procesar explicaciones"),
                    "detail": request.text
                }
            )
        return res

    @app.get(
        "/api/v1/taxonomy",
        response_model=List[TaxonomyCategorySchema],
        summary="Taxonomía Pedagógica de Errores Gramaticales"
    )
    async def get_taxonomy():
        return [
            TaxonomyCategorySchema(
                id=cat_id,
                name_es=info["name_es"],
                name_en=info["name_en"],
                description_es=info["description_es"]
            )
            for cat_id, info in TAXONOMY_CATEGORIES.items()
        ]

    @app.get("/app", summary="Interfaz Web Next.js")
    async def get_web_app():
        frontend_index = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/out/index.html"))
        if os.path.exists(frontend_index):
            return FileResponse(frontend_index)
        raise HTTPException(
            status_code=404,
            detail="Interfaz web no compilada. Ejecuta 'npm run build' dentro del directorio 'frontend/'."
        )

    # Montar activos estáticos de Next.js (_next) si están disponibles
    frontend_out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/out"))
    next_static_dir = os.path.join(frontend_out_dir, "_next")
    if os.path.exists(next_static_dir):
        app.mount("/_next", StaticFiles(directory=next_static_dir), name="next_static")

    return app


app = create_app()
