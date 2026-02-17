"""
Fixtures and configuration for pytest.
"""

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.pool import StaticPool
import asyncio

from src.db.models.ticket import Base
from src.db.session import DatabaseManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()


@pytest.fixture
def anyio_backend():
    """Specify the backend for anyio tests."""
    return "asyncio"


@pytest.fixture
async def client():
    """Create a test FastAPI client."""
    from fastapi.testclient import TestClient
    from src.main import app
    
    # Override dependencies
    async def override_get_db():
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSession(engine) as session:
            yield session
    
    # from src.db.session import get_db
    # app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)
