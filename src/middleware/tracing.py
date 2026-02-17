"""
Middleware for distributed tracing and correlation IDs.
"""

import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        """Add tracing context to requests."""
        
        # Get or create correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request_id = request.headers.get("X-Request-ID", correlation_id)
        
        # Create span for this request
        with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.path", request.url.path)
            span.set_attribute("correlation_id", correlation_id)
            span.set_attribute("request_id", request_id)
            
            # Add headers to response
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = request_id
            
            return response
