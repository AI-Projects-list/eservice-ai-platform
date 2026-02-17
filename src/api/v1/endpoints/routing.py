"""
Intelligent ticket routing endpoints.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.db.session import get_db
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class RoutingRequest(BaseModel):
    """Request model for intelligent routing."""
    ticket_id: UUID
    use_ai: bool = True


class RoutingResult(BaseModel):
    """Response model for routing result."""
    ticket_id: UUID
    assigned_agent_id: UUID
    assigned_department: str
    confidence_score: float


@router.post("/suggest", response_model=RoutingResult)
async def suggest_routing(
    request: RoutingRequest,
    db: AsyncSession = Depends(get_db)
) -> RoutingResult:
    """Suggest optimal agent/department for ticket using AI models."""
    logger.info("Routing suggestion requested", ticket_id=str(request.ticket_id))
    raise HTTPException(status_code=501, detail="Not implemented")
