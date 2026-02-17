"""
eService AI Platform - Main Application Entry Point

This module initializes the FastAPI application with all middleware,
exception handlers, routes, and observability infrastructure.

Architecture:
- Asynchronous request handling with uvicorn
- OpenTelemetry instrumentation for observability
- Prometheus metrics collection
- Structured logging with correlation IDs
- Exception handling with proper HTTP status codes
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import traces, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import make_asgi_app
import structlog

from src.config import settings
from src.core.logger import setup_logging
from src.core.exceptions import EServiceException
from src.middleware.metrics import MetricsMiddleware
from src.middleware.tracing import TracingMiddleware
from src.middleware.errors import error_handler
from src.db.session import database
from src.cache.redis_client import redis_client
from src.api.v1 import endpoints as v1_endpoints

# Configure structured logging
setup_logging(settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for resources:
    - Database connection pool
    - Redis cache connections
    - Message queue consumers
    - Observability exporters
    """
    # Startup
    logger.info("Starting eService Platform", 
                version=settings.VERSION,
                environment=settings.ENVIRONMENT)
    
    # Initialize database
    await database.connect()
    logger.info("Database connected", 
                host=settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "localhost")
    
    # Initialize Redis
    await redis_client.connect()
    logger.info("Redis cache initialized")
    
    # Start message queue consumers
    # TODO: Initialize Celery/RabbitMQ consumers
    
    yield
    
    # Shutdown
    logger.info("Shutting down eService Platform")
    
    # Close database
    await database.disconnect()
    logger.info("Database disconnected")
    
    # Close Redis
    await redis_client.disconnect()
    logger.info("Redis disconnected")
    
    # Close message queue consumers
    # TODO: Graceful shutdown of task consumers


def create_app() -> FastAPI:
    """
    Application factory function.
    
    Creates and configures the FastAPI application with:
    - Custom exception handlers
    - CORS middleware
    - Request/response logging
    - Metrics collection
    - Distributed tracing
    """
    
    # Initialize FastAPI app
    app = FastAPI(
        title="eService AI Platform",
        description="Intelligent customer service system with LLM/RAG integration",
        version=settings.VERSION,
        docs_url="/docs" if not settings.PRODUCTION else None,
        redoc_url="/redoc" if not settings.PRODUCTION else None,
        openapi_url="/openapi.json" if not settings.PRODUCTION else None,
        lifespan=lifespan,
    )
    
    # Setup observability (Jaeger tracing)
    if settings.JAEGER_ENABLED:
        jaeger_exporter = JaegerExporter(
            agent_host_name=settings.JAEGER_HOST,
            agent_port=settings.JAEGER_PORT,
        )
        traces.set_tracer_provider(TracerProvider())
        traces.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        logger.info("Jaeger tracing enabled", 
                   host=settings.JAEGER_HOST,
                   port=settings.JAEGER_PORT)
    
    # Setup Prometheus metrics
    prometheus_reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[prometheus_reader]))
    
    # Mount Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TracingMiddleware)
    
    # Global exception handler
    @app.exception_handler(EServiceException)
    async def eservice_exception_handler(request: Request, exc: EServiceException):
        logger.error("Application exception",
                    error_code=exc.error_code,
                    message=exc.message,
                    status_code=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception",
                    exception_type=type(exc).__name__,
                    error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
        )
    
    # Include API routes
    app.include_router(
        v1_endpoints.health.router,
        prefix="/api/v1/health",
        tags=["health"],
    )
    app.include_router(
        v1_endpoints.tickets.router,
        prefix="/api/v1/tickets",
        tags=["tickets"],
    )
    app.include_router(
        v1_endpoints.knowledge_base.router,
        prefix="/api/v1/knowledge-base",
        tags=["knowledge-base"],
    )
    app.include_router(
        v1_endpoints.ai_chat.router,
        prefix="/api/v1/ai",
        tags=["ai"],
    )
    app.include_router(
        v1_endpoints.routing.router,
        prefix="/api/v1/routing",
        tags=["routing"],
    )
    app.include_router(
        v1_endpoints.analytics.router,
        prefix="/api/v1/analytics",
        tags=["analytics"],
    )
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.PRODUCTION,
        workers=settings.WORKERS if settings.PRODUCTION else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )
