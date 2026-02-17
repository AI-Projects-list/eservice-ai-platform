"""
Ticket management API endpoints.

Provides full CRUD operations for support tickets with filtering,
sorting, and advanced search capabilities.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from pydantic import BaseModel, Field

from src.db.session import get_db
from src.db.models.ticket import Ticket, TicketStatus, TicketPriority
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Pydantic schemas for request/response
class TicketCreate(BaseModel):
    """Request model for creating a new ticket."""
    customer_id: UUID
    customer_name: str
    customer_email: str
    title: str
    description: str
    category: str
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    """Request model for updating a ticket."""
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[UUID] = None
    description: Optional[str] = None


class TicketResponse(BaseModel):
    """Response model for ticket data."""
    id: UUID
    ticket_number: str
    customer_id: UUID
    customer_name: str
    title: str
    status: TicketStatus
    priority: TicketPriority
    created_at: str
    updated_at: str
    ai_confidence_score: Optional[float] = None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Create a new support ticket.
    
    Args:
        ticket_data: Ticket creation data
        db: Database session
        
    Returns:
        TicketResponse: Created ticket details
    """
    try:
        # Generate ticket number (simplified - use sequence in production)
        result = await db.execute(select(Ticket))
        ticket_count = len(result.fetchall())
        ticket_number = f"TKT-{ticket_count + 1:06d}"
        
        ticket = Ticket(
            ticket_number=ticket_number,
            customer_id=ticket_data.customer_id,
            customer_name=ticket_data.customer_name,
            customer_email=ticket_data.customer_email,
            title=ticket_data.title,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=ticket_data.priority,
        )
        
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        logger.info("Ticket created", ticket_id=str(ticket.id), ticket_number=ticket.ticket_number)
        
        return TicketResponse.from_attributes(ticket)
    
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to create ticket", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to create ticket")


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Get ticket by ID.
    
    Args:
        ticket_id: Ticket UUID
        db: Database session
        
    Returns:
        TicketResponse: Ticket details
    """
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return TicketResponse.from_attributes(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Update a ticket.
    
    Args:
        ticket_id: Ticket UUID
        ticket_data: Update data
        db: Database session
        
    Returns:
        TicketResponse: Updated ticket details
    """
    try:
        result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Update fields
        update_data = ticket_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ticket, field, value)
        
        await db.commit()
        await db.refresh(ticket)
        
        logger.info("Ticket updated", ticket_id=str(ticket.id))
        
        return TicketResponse.from_attributes(ticket)
    
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to update ticket", ticket_id=str(ticket_id), error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to update ticket")


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    customer_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> list[TicketResponse]:
    """
    List tickets with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        status: Filter by status
        priority: Filter by priority
        customer_id: Filter by customer
        db: Database session
        
    Returns:
        List of TicketResponse objects
    """
    query = select(Ticket)
    
    # Apply filters
    filters = []
    if status:
        filters.append(Ticket.status == status)
    if priority:
        filters.append(Ticket.priority == priority)
    if customer_id:
        filters.append(Ticket.customer_id == customer_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Order and paginate
    query = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    tickets = result.scalars().all()
    
    return [TicketResponse.from_attributes(t) for t in tickets]
