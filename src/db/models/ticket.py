"""
SQLAlchemy ORM models for core entities.

Implements domain models with proper relationships, indexing,
and constraints for high-performance querying.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    Text, Enum, ForeignKey, Index, ARRAY, UUID
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB
import uuid
import enum

Base = declarative_base()


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Ticket priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base):
    """
    Support ticket model.
    
    Represents a customer service request with full lifecycle management.
    Includes SLA tracking, resolution history, and AI analysis results.
    """
    __tablename__ = "tickets"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Customer info
    customer_id = Column(UUID, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    
    # Ticket content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    
    # Status tracking
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)
    priority = Column(Enum(TicketPriority), nullable=False, index=True)
    
    # Assignment
    assigned_agent_id = Column(UUID, nullable=True, index=True)
    assigned_department_id = Column(UUID, nullable=True, index=True)
    
    # AI Analysis
    ai_classification = Column(JSONB, nullable=True)  # AI categorization results
    ai_suggested_response = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, nullable=True)
    ai_analysis_model = Column(String(100), nullable=True)
    
    # SLA
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True, index=True)
    sla_due_date = Column(DateTime, nullable=True, index=True)
    sla_breached = Column(Boolean, default=False, index=True)
    
    # Metadata
    tags = Column(ARRAY(String), default=[], nullable=False)
    attachments_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_tickets_customer_status", "customer_id", "status"),
        Index("idx_tickets_created_status", "created_at", "status"),
        Index("idx_tickets_assigned_status", "assigned_agent_id", "status"),
    )


class KnowledgeBase(Base):
    """
    Knowledge base article model for RAG system.
    
    Stores searchable articles used for intelligent Q&A,
    including vector embeddings for semantic search.
    """
    __tablename__ = "knowledge_base"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=False, index=True)
    tags = Column(ARRAY(String), default=[], nullable=False)
    keywords = Column(ARRAY(String), default=[], nullable=False)
    
    # RAG/Vector Search
    embedding_id = Column(String(255), nullable=True, unique=True)
    embedding_model = Column(String(100), nullable=True)
    
    # Metadata
    author_id = Column(UUID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)
    
    # Analytics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    unhelpful_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_kb_published_category", "published", "category"),
        Index("idx_kb_updated_published", "updated_at", "published"),
    )


class LLMProvider(Base):
    """
    LLM provider configuration and credentials.
    
    Supports multiple providers (OpenAI, Claude, Azure) with
    individual model configurations for A/B testing.
    """
    __tablename__ = "llm_providers"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(50), nullable=False, unique=True)  # openai, claude, azure
    
    # Credentials (encrypted in production)
    api_key = Column(String(500), nullable=False)
    api_endpoint = Column(String(500), nullable=True)
    
    # Configuration
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    top_p = Column(Float, default=1.0)
    timeout = Column(Integer, default=30)
    
    # Feature flags
    enabled = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)
    
    # A/B Testing
    traffic_percentage = Column(Integer, default=0)  # 0-100
    
    # Analytics
    total_requests = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    average_latency_ms = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """
    Audit log for compliance and debugging.
    
    Tracks all mutations to critical data for security
    and compliance requirements.
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Action
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(UUID, nullable=False, index=True)
    
    # Changes
    changes = Column(JSONB, nullable=True)  # Before/after values
    
    # User info
    user_id = Column(UUID, nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_created", "created_at"),
    )
