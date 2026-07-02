"""FastAPI application factory for the AquaMax AI Agent."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.core.exceptions import AquaMaxError
from src.database.connection import init_database
from src.utils.logger import get_logger, setup_logging

from api.routers import chat, leads, products, quotations

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — startup and shutdown logic."""
    # Startup
    setup_logging(settings)
    logger.info("Starting AquaMax AI Agent API...")
    init_database()
    logger.info("Database initialized. API ready.")
    yield
    # Shutdown
    logger.info("Shutting down AquaMax AI Agent API...")


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    app = FastAPI(
        title="AquaMax AI Sales & Support Agent",
        description=(
            "Production-ready AI Agent API for AquaMax Rehab Equipment. "
            "Provides chat, product search, lead capture, and quotation generation."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler for AquaMax errors
    @app.exception_handler(AquaMaxError)
    async def aquamax_exception_handler(request: Request, exc: AquaMaxError):
        logger.error("AquaMaxError: %s | Details: %s", exc.message, exc.details)
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.message,
                "details": exc.details,
                "type": type(exc).__name__,
            },
        )

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "service": "aquamax-agent",
            "version": "1.0.0",
        }

    # Include routers
    app.include_router(chat.router, prefix="/chat", tags=["Chat"])
    app.include_router(leads.router, prefix="/leads", tags=["Leads"])
    app.include_router(products.router, prefix="/products", tags=["Products"])
    app.include_router(quotations.router, prefix="/quotations", tags=["Quotations"])

    return app


app = create_app()
