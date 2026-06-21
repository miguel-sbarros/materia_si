"""Fábrica da aplicação FastAPI. Routers ficam finos; lógica vive nos services."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analytics,
    catalog,
    conversations,
    copilot,
    deals,
    health,
    imports,
    leads,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Captus CRM API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(catalog.router)
    app.include_router(leads.router)
    app.include_router(deals.router)
    app.include_router(imports.router)
    app.include_router(conversations.router)
    app.include_router(copilot.router)
    app.include_router(analytics.router)
    return app


app = create_app()
