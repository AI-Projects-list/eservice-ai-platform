"""
Structured logging configuration for eService AI Platform.

Provides JSON structured logging with correlation IDs for distributed tracing
and advanced filtering/searching in ELK Stack.
"""

import logging
import sys
from typing import Any

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with structlog and standard logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Convert string log level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        BoundLogger: Configured structlog logger
    """
    return structlog.get_logger(name)


def correlate_request(request_id: str) -> structlog.BoundLogger:
    """
    Add correlation ID to logger context for distributed tracing.
    
    Args:
        request_id: Unique request ID
        
    Returns:
        BoundLogger: Logger bound with correlation ID
    """
    logger = structlog.get_logger()
    return logger.bind(request_id=request_id)
