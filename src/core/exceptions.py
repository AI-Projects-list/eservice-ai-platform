"""
Custom exceptions for eService AI Platform.

Provides a consistent exception handling pattern with proper HTTP status codes
and structured error responses.
"""

from typing import Any, Optional


class EServiceException(Exception):
    """Base exception for all eService errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(EServiceException):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class AuthenticationError(EServiceException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(EServiceException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class NotFoundError(EServiceException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: Any) -> None:
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
        )


class ConflictError(EServiceException):
    """Raised when a conflict occurs (e.g., duplicate key)."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=details,
        )


class RateLimitError(EServiceException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )


class LLMProviderError(EServiceException):
    """Raised when LLM provider request fails."""
    
    def __init__(
        self,
        provider: str,
        message: str,
        status_code: int = 500,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(
            message=f"LLM Provider {provider} error: {message}",
            error_code="LLM_PROVIDER_ERROR",
            status_code=status_code,
            details={"provider": provider, **(details or {})},
        )


class RAGError(EServiceException):
    """Raised when RAG retrieval fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(
            message=message,
            error_code="RAG_ERROR",
            status_code=500,
            details=details,
        )


class DatabaseError(EServiceException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


class CacheError(EServiceException):
    """Raised when cache operation fails."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            status_code=500,
            details=details,
        )


class TimeoutError(EServiceException):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: float) -> None:
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_seconds}s",
            error_code="TIMEOUT",
            status_code=504,
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        )
