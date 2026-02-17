# API Documentation

## Base URL

```
https://api.eservice.app/api/v1
```

For local development:
```
http://localhost:8000/api/v1
```

## Authentication

All API requests (except health checks) require JWT Bearer token:

```bash
Authorization: Bearer <your-jwt-token>
```

### Obtaining a Token

```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}

# Response
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 1800
}
```

## Ticket Management

### Create Ticket

```bash
POST /tickets
Authorization: Bearer <token>
Content-Type: application/json

{
  "customer_id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "title": "Cannot login to account",
  "description": "I'm unable to log in to my account even with correct credentials",
  "category": "account-access",
  "priority": "high"
}

# Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ticket_number": "TKT-000001",
  "customer_id": "123e4567-e89b-12d3-a456-426614174000",
  "customer_name": "John Doe",
  "title": "Cannot login to account",
  "status": "open",
  "priority": "high",
  "created_at": "2024-02-17T10:30:00Z",
  "updated_at": "2024-02-17T10:30:00Z",
  "ai_confidence_score": null
}
```

### Get Ticket

```bash
GET /tickets/{ticket_id}
Authorization: Bearer <token>

# Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ticket_number": "TKT-000001",
  ...
}
```

### List Tickets

```bash
GET /tickets?status=open&priority=high&skip=0&limit=10
Authorization: Bearer <token>

# Response (200 OK)
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "ticket_number": "TKT-000001",
    ...
  },
  ...
]
```

### Update Ticket

```bash
PUT /tickets/{ticket_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "in_progress",
  "priority": "critical",
  "assigned_agent_id": "agent-uuid"
}

# Response (200 OK)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "priority": "critical",
  ...
}
```

## AI Chat & Q&A

### Send Chat Message

```bash
POST /ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_question": "How do I reset my password?",
  "session_id": "session-123",
  "use_rag": true,
  "model": "gpt-4"
}

# Response (200 OK)
{
  "response": "To reset your password, please follow these steps: 1. Click on 'Forgot Password' on the login page...",
  "confidence_score": 0.92,
  "sources": [
    "kb-article-1",
    "kb-article-5"
  ],
  "model_used": "gpt-4",
  "processing_time_ms": 1250.5
}
```

### RAG Document Retrieval

```bash
POST /ai/rag/retrieve
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "How to enable two-factor authentication",
  "top_k": 5,
  "similarity_threshold": 0.6
}

# Response (200 OK)
{
  "results": [
    {
      "id": "kb-001",
      "title": "Setting up Two-Factor Authentication",
      "content": "Two-factor authentication (2FA) adds an extra layer of security...",
      "similarity_score": 0.96
    },
    {
      "id": "kb-002",
      "title": "Security Best Practices",
      "content": "We recommend enabling 2FA for all accounts...",
      "similarity_score": 0.87
    }
  ],
  "retrieval_time_ms": 145.3
}
```

### Submit Feedback

```bash
POST /ai/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
  "response_id": "resp-123",
  "helpful": true,
  "comments": "Very helpful response"
}

# Response (200 OK)
{
  "status": "feedback_received"
}
```

## Knowledge Base

### Create Knowledge Article

```bash
POST /knowledge-base/articles
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "How to Reset Your Password",
  "content": "Follow these steps to reset your password...",
  "category": "account-management",
  "tags": ["password", "account", "security"]
}

# Response (201 Created)
{
  "id": "kb-001",
  "title": "How to Reset Your Password",
  "category": "account-management",
  "created_at": "2024-02-17T10:30:00Z"
}
```

### List Knowledge Articles

```bash
GET /knowledge-base/articles?category=account-management&skip=0&limit=10
Authorization: Bearer <token>

# Response (200 OK)
[
  {
    "id": "kb-001",
    "title": "How to Reset Your Password",
    "category": "account-management",
    "created_at": "2024-02-17T10:30:00Z"
  },
  ...
]
```

## Analytics

### Get System Metrics

```bash
GET /analytics/metrics?days=30
Authorization: Bearer <token>

# Response (200 OK)
{
  "total_tickets": 1250,
  "resolved_tickets": 1100,
  "avg_resolution_time_hours": 4.5,
  "customer_satisfaction": 4.7,
  "ai_effectiveness": 0.87
}
```

## Health Checks

### Ping (Liveness)

```bash
GET /health/ping

# Response (200 OK)
{
  "status": "alive"
}
```

### Ready (Readiness)

```bash
GET /health/ready

# Response (200 OK)
{
  "status": "ready",
  "dependencies": "all_ok"
}
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request parameters",
  "details": {
    "field": "priority",
    "issue": "Invalid enum value"
  }
}
```

### HTTP Status Codes

- **200 OK** - Request successful
- **201 Created** - Resource created
- **204 No Content** - Success with no content
- **400 Bad Request** - Invalid input (validation error)
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **409 Conflict** - Resource conflict (duplicate)
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - Service temporarily unavailable

## Rate Limiting

All API endpoints are rate-limited to **1000 requests per minute** per API key.

Headers returned:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1634567890
```

## Pagination

List endpoints support pagination:

```bash
GET /tickets?skip=0&limit=20

# Response includes
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

## API Documentation

Interactive API documentation available at:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`
