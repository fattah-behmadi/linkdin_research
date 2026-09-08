"""Application factory: lifespan, middleware, error translation, routes."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import SearchBackend, Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.db.session import create_schema, get_engine
from app.search.client import create_client
from app.search.index import ensure_index

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = get_settings()
    await create_schema(get_engine())

    if settings.search_backend is SearchBackend.ELASTICSEARCH:
        app.state.elasticsearch = create_client(settings)
        try:
            await ensure_index(app.state.elasticsearch, settings.elasticsearch_index)
        except Exception as error:
            logger.warning("Elasticsearch is not ready yet: %s", error)
    else:
        app.state.elasticsearch = None

    yield

    if app.state.elasticsearch is not None:
        await app.state.elasticsearch.close()
    await get_engine().dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.debug)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        summary="Search and filtering over a LinkedIn profile dataset.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, error: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
