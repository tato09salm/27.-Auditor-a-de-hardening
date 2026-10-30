from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import (
    audits,
    auth,
    automation,
    dashboard,
    findings,
    logs,
    profiles,
    reports,
    servers,
    settings as settings_router,
    setup,
    users,
)
from app.config import settings
from app.core.middleware import RequestContextMiddleware
from app.database import SessionLocal
from app.services.audit_runner import recover_stale_runs

logger = logging.getLogger("cis_hardening")
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.reports_path.mkdir(parents=True, exist_ok=True)
    try:
        recovered = recover_stale_runs()
        if recovered:
            logger.warning("Se marcaron %s auditorías huérfanas como fallidas.", recovered)
    except SQLAlchemyError:
        logger.exception("No se pudo ejecutar la recuperación de auditorías; ¿migraciones pendientes?")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Plataforma de auditoría de hardening CIS para PYMES.",
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Idempotency-Key", "X-API-Key"],
    expose_headers=["X-Request-ID", "X-Checksum-SHA256"],
    max_age=600,
)
if settings.allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[host.strip() for host in settings.allowed_hosts.split(",") if host.strip()],
    )
app.add_middleware(RequestContextMiddleware)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    code = "http_error"
    extra: dict = {}
    if isinstance(detail, dict):
        code = str(detail.get("code", code))
        message = str(detail.get("message", "Error en la solicitud."))
        extra = {key: value for key, value in detail.items() if key not in {"code", "message"}}
    else:
        message = str(detail)
    body = {"detail": message, "code": code, "request_id": _request_id(request), **extra}
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(part) for part in error.get("loc", []) if part != "body"),
            "message": error.get("msg", "Valor inválido."),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Los datos enviados no son válidos.",
            "code": "validation_error",
            "fields": fields,
            "request_id": _request_id(request),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.exception("Error de base de datos en %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "El servicio de datos no está disponible temporalmente.",
            "code": "database_error",
            "request_id": _request_id(request),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ocurrió un error interno. Consulte el identificador de la solicitud.",
            "code": "internal_error",
            "request_id": _request_id(request),
        },
    )


@app.get("/health", tags=["Salud"], include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@app.get(f"{settings.api_v1_prefix}/health", tags=["Salud"])
def api_health() -> dict[str, str]:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "version": settings.app_version, "database": "ok"}


app.include_router(setup.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(servers.router, prefix=settings.api_v1_prefix)
app.include_router(profiles.router, prefix=settings.api_v1_prefix)
app.include_router(audits.router, prefix=settings.api_v1_prefix)
app.include_router(findings.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(reports.router, prefix=settings.api_v1_prefix)
app.include_router(logs.router, prefix=settings.api_v1_prefix)
app.include_router(settings_router.router, prefix=settings.api_v1_prefix)
app.include_router(automation.router, prefix=settings.api_v1_prefix)
