import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.graph import DiseaseResearchAgent
from app.agents.nodes import DiseaseAgentNodes
from app.api.routes import diagnosis, health
from app.core.config import Settings, get_settings
from app.services.diagnosis_service import DiagnosisService
from app.services.groq_service import GroqService
from app.services.plant_disease_model import ModelLoadError, PlantDiseaseModel
from app.services.web_search_service import WebSearchService


settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class RequestTooLargeError(Exception):
    pass


class RequestBodyLimitMiddleware:
    """Reject oversized bodies, including chunked requests, before route handling."""

    def __init__(self, app, max_body_size: int) -> None:
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    await self._send_too_large(scope, receive, send)
                    return
            except ValueError:
                pass

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_size:
                    raise RequestTooLargeError
            return message

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except RequestTooLargeError:
            if response_started:
                raise
            await self._send_too_large(scope, receive, send)

    @staticmethod
    async def _send_too_large(scope, receive, send) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "success": False,
                "error": {
                    "code": "request_too_large",
                    "message": "The request body exceeds the allowed size.",
                },
            },
        )
        await response(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_settings: Settings = settings
    app_settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)

    plant_model = PlantDiseaseModel(
        model_path=app_settings.resolved_model_path,
        labels_path=app_settings.resolved_class_labels_path,
        low_confidence_threshold=app_settings.low_confidence_threshold,
        executor_workers=app_settings.max_concurrent_inferences,
    )
    try:
        await plant_model.load_async()
        logger.info("Plant disease model loaded on %s", plant_model.device)
    except ModelLoadError:
        logger.exception("Plant disease model failed to load")

    groq_service = GroqService(app_settings)
    web_search_service = WebSearchService(app_settings)
    if groq_service.configured:
        logger.info("Groq synthesis enabled with model %s", app_settings.groq_model)
    else:
        logger.warning("GROQ_API_KEY is not configured; explanations will be unavailable")
    nodes = DiseaseAgentNodes(
        web_search_service,
        groq_service,
        app_settings.low_confidence_threshold,
        app_settings.research_country,
    )
    disease_agent = DiseaseResearchAgent(nodes)

    app.state.settings = app_settings
    app.state.plant_model = plant_model
    app.state.groq_service = groq_service
    app.state.web_search_service = web_search_service
    app.state.disease_agent = disease_agent
    app.state.diagnosis_service = DiagnosisService(plant_model, disease_agent, app_settings)
    try:
        yield
    finally:
        await asyncio.gather(
            groq_service.close(),
            web_search_service.close(),
            return_exceptions=True,
        )
        plant_model.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Plant leaf diagnosis using the immutable TorchScript classifier, parallel live evidence "
        "research, pesticide-source validation, and Groq synthesis."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(RequestBodyLimitMiddleware, max_body_size=settings.max_request_size_bytes)
if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(diagnosis.router, prefix=settings.api_prefix)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": "request_error", "message": str(exc.detail)},
        },
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [".".join(str(part) for part in error["loc"][1:]) for error in exc.errors()]
    missing_image = any(field == "image" for field in fields)
    message = "An image file is required." if missing_image else "The request data is invalid."
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {"code": "validation_error", "message": message, "fields": fields},
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled request failure")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "internal_error", "message": "An internal error occurred."},
        },
    )
