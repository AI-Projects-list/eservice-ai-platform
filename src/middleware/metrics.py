"""
Middleware for metrics collection and monitoring.
"""

import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger(__name__)

# Define Prometheus metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

active_requests = Gauge(
    "http_requests_active",
    "Active HTTP requests",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        """Track request metrics."""
        active_requests.inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path
            method = request.method
            status = response.status_code
            
            request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            
            logger.info("Request processed",
                       method=method,
                       endpoint=endpoint,
                       status=status,
                       duration_ms=duration * 1000)
            
            return response
        
        finally:
            active_requests.dec()
