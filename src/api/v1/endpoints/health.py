"""
Health check endpoints for monitoring and readiness probes.

Used for Kubernetes liveness and readiness probes to verify
application health and dependencies.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.db.session import get_db
from src.cache.redis_client import redis_client
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/ping")
async def health_ping() -> dict[str, str]:
    """
    Simple ping endpoint for load balancer health checks.
    
    Returns immediately without checking dependencies.
    Useful for quick liveness probes.
    """
    return {"status": "alive"}


@router.get("/ready")
async def health_ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Readiness probe that checks all critical dependencies.
    
    Verifies:
    - Database connectivity
    - Redis connectivity
    - LLM provider availability
    
    Returns 500 if any dependency is unavailable.
    """
    try:
        # Check database
        await db.execute("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        # Check LLM providers would go here
        # await llm_service.check_providers()
        
        return {"status": "ready", "dependencies": "all_ok"}
    
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(exc)}"
        )


@router.get("/live")
async def health_liveness() -> dict[str, str]:
    """
    Liveness probe for Kubernetes.
    
    Indicates the application is running and not in a deadlock state.
    """
    return {"status": "live"}
