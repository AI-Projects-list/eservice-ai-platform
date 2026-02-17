# Contributing Guidelines

## Code Quality Standards

### Style Guide

- **Python**: PEP 8 + Black formatter
- **Imports**: Organized with isort
- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style for all modules and classes
- **Line Length**: 120 characters maximum

### Running Code Quality Checks

```bash
# Format code
make format

# Lint code
make lint

# Type checking
make typecheck

# All checks
make format lint typecheck
```

## Testing

### Test Structure

```
tests/
├── test_api/           # API endpoint tests
├── test_services/      # Service layer tests
├── test_llm/           # LLM integration tests
├── test_agents/        # Agent tests
├── test_db/            # Database tests
└── conftest.py        # Shared fixtures
```

### Writing Tests

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_ticket(db_session: AsyncSession):
    """Test ticket creation."""
    from src.db.models.ticket import Ticket
    
    ticket = Ticket(
        ticket_number="TKT-000001",
        customer_id=uuid4(),
        customer_name="John Doe",
        customer_email="john@example.com",
        title="Test Ticket",
        description="Test Description",
        category="test",
        priority="medium"
    )
    
    db_session.add(ticket)
    await db_session.commit()
    
    assert ticket.id is not None
    assert ticket.status == TicketStatus.OPEN
```

### Test Requirements

- Minimum 80% code coverage
- All new features must have tests
- All bug fixes must include regression tests
- Integration tests for API endpoints
- Unit tests for business logic

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific file
pytest tests/test_api/test_tickets.py -v

# Run with markers
pytest -m "not slow"
```

## Git Workflow

### Branch Naming

```
feature/description          # New feature
bugfix/description          # Bug fix
hotfix/description          # Production hotfix
docs/description            # Documentation
refactor/description        # Code refactoring
```

### Commit Messages

```
feat: Add multi-provider LLM support
  - Implement provider factory pattern
  - Add OpenAI and Claude providers
  - Add fallback mechanism

fix: Fix ticket status workflow
  - Resolve issue with status transitions
  - Add validation for invalid transitions

docs: Update API documentation
  - Add RAG endpoint documentation
  - Include example requests/responses

chore: Update dependencies
  - Upgrade FastAPI to 0.104.1
  - Upgrade SQLAlchemy to 2.0.23
```

### Pull Request Process

1. Create feature branch from `develop`
2. Implement feature with tests
3. Ensure all tests pass: `make test-cov`
4. Run code quality: `make lint format typecheck`
5. Push branch and create PR
6. Request review from team members
7. Address review comments
8. Squash commits if needed
9. Merge to `develop` after approval
10. Delete feature branch

## Code Review Checklist

Reviewers should verify:

- [ ] Code follows style guide
- [ ] All tests passing
- [ ] Test coverage maintained or improved
- [ ] Type hints present
- [ ] Docstrings present
- [ ] Error handling appropriate
- [ ] No hardcoded values (use config)
- [ ] Logging added where appropriate
- [ ] Database migrations if needed
- [ ] Design aligns with architecture
- [ ] Performance considered
- [ ] Security considered (no SQL injection, etc.)

## Documentation

### Module Documentation

```python
"""
Brief module description.

This module handles ticket management including:
- CRUD operations
- Status workflow
- SLA tracking

Examples:
    Basic usage::
    
        from src.services.ticket_service import TicketService
        
        service = TicketService(db)
        ticket = await service.create_ticket(...)
"""
```

### Function Documentation

```python
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession
) -> TicketResponse:
    """
    Create a new support ticket.
    
    Args:
        ticket_data: Ticket creation data with validation
        db: Database session
        
    Returns:
        TicketResponse: Created ticket with ID
        
    Raises:
        ValidationError: If input validation fails
        DatabaseError: If database operation fails
        
    Examples:
        >>> ticket_data = TicketCreate(
        ...     customer_id=uuid.uuid4(),
        ...     title="Cannot login",
        ...     description="...",
        ...     category="account",
        ...     priority="high"
        ... )
        >>> ticket = await create_ticket(ticket_data, db)
    """
```

### API Documentation

Update OpenAPI docs in docstrings:

```python
@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db)
) -> TicketResponse:
    """
    Create a new support ticket.
    
    **Expected Status Code**: 201 Created
    
    **Request Body**:
    ```json
    {
        "customer_id": "123e4567-e89b-12d3-a456-426614174000",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "title": "Cannot login to account",
        "description": "...",
        "category": "account-access",
        "priority": "high"
    }
    ```
    
    **Response Body**:
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "ticket_number": "TKT-000001",
        "status": "open",
        ...
    }
    ```
    """
```

## Debugging

### Local Debugging

```bash
# Run with debug mode
DEBUG=true make run-dev

# Use debugger
import pdb; pdb.set_trace()

# Interactive Python shell
ipython
>>> from src.main import app
>>> from src.db.session import database
```

### Remote Debugging

```bash
# In production
kubectl logs -f deployment/eservice-api -n eservice

# Forward Jaeger for tracing
kubectl port-forward svc/jaeger 16686:16686 -n eservice

# View traces at http://localhost:16686
```

## Performance Optimization

### Profiling

```bash
# Profile with cProfile
python -m cProfile -s cumtime -m uvicorn src.main:app

# Use py-spy for live profiling
py-spy record -o profile.svg -- uvicorn src.main:app

# Analyze with snakeviz
snakeviz profile.prof
```

### Load Testing

```bash
# Using k6
k6 run tests/load_tests/api_load.js

# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/v1/health/ping

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/api/v1/tickets
```

## Release Process

### Version Management

```bash
# Update version in src/__init__.py and pyproject.toml
__version__ = "1.1.0"

# Tag release
git tag v1.1.0
git push origin v1.1.0

# CI/CD automatically builds and deploys
```

### Changelog

Update CHANGELOG.md with:
- New features
- Bug fixes
- Breaking changes
- Deprecations

## Ask for Help

- Issues: GitHub Issues for bugs/features
- Discussions: GitHub Discussions for questions
- Slack: #eservice-platform channel
- Email: team@eservice.com
