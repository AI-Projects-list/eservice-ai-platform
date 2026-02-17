"""
Database connection and session management.

Provides async database session management using SQLAlchemy 2.0
with proper connection pooling and lifecycle management.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from src.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connection lifecycle."""
    
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_local: type[AsyncSession] | None = None
    
    async def connect(self) -> None:
        """Initialize database connection pool."""
        try:
            # Create async engine with connection pooling
            pool_class = NullPool if settings.PRODUCTION else QueuePool
            
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True,  # Verify connections before using
                connect_args={
                    "timeout": settings.DATABASE_TIMEOUT,
                    "command_timeout": settings.DATABASE_TIMEOUT,
                },
                poolclass=pool_class,
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("Database connection established",
                       url=settings.DATABASE_URL,
                       pool_size=settings.DATABASE_POOL_SIZE)
            
        except Exception as exc:
            logger.error("Failed to connect to database", error=str(exc))
            raise
    
    async def disconnect(self) -> None:
        """Close database connection pool."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session.
        
        Yields:
            AsyncSession: Database session for queries
        """
        async with AsyncSession(self.engine, expire_on_commit=False) as session:
            try:
                yield session
            except Exception as exc:
                await session.rollback()
                logger.error("Database session error", error=str(exc))
                raise
            finally:
                await session.close()


# Global database manager instance
database = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database session.
    
    Usage in FastAPI endpoints:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSession(database.engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception as exc:
            await session.rollback()
            logger.error("Database session error in endpoint", error=str(exc))
            raise
        finally:
            await session.close()
