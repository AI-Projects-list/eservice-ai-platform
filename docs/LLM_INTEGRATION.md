# LLM Integration Guide

## Overview

The eService AI Platform supports multiple LLM providers through a pluggable architecture. This enables:

- **Provider Flexibility**: Switch between OpenAI, Claude, Azure OpenAI
- **Cost Optimization**: Compare provider costs and select most economical
- **Redundancy**: Automatic fallback to backup provider
- **A/B Testing**: Compare model outputs before production rollout
- **Token Tracking**: Monitor usage and costs per provider

## Supported Providers

### 1. OpenAI

#### Setup

```bash
# Install OpenAI SDK
pip install openai

# Set environment variables
export OPENAI_API_KEY="sk-..."
export OPENAI_DEFAULT_MODEL="gpt-4"
export OPENAI_TEMPERATURE="0.7"
export OPENAI_MAX_TOKENS="2048"
```

#### Configuration

```python
# src/config.py
OPENAI_API_KEY = "sk-..."
OPENAI_BASE_URL = None  # Use https://api.openai.com/v1 if not set
OPENAI_ORG_ID = None    # Optional: For organization accounts
OPENAI_DEFAULT_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0.7
OPENAI_MAX_TOKENS = 2048
OPENAI_TIMEOUT = 30
```

#### Usage

```python
from src.llm.providers import LLMProviderFactory

# Get OpenAI provider
provider = LLMProviderFactory.get_provider("openai")

# Generate text
response = await provider.generate("What is machine learning?")
print(response)

# Generate with function calling
messages = [
    {"role": "user", "content": "Book a hotel in New York"}
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "book_hotel",
            "description": "Book a hotel",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "nights": {"type": "integer"}
                },
                "required": ["city", "nights"]
            }
        }
    }
]

result = await provider.generate_with_functions(messages, tools)
# Returns: {"type": "function_call", "function": "book_hotel", "arguments": {...}}
```

### 2. Claude (Anthropic)

#### Setup

```bash
# Set environment variables
export CLAUDE_API_KEY="sk-ant-..."
export CLAUDE_DEFAULT_MODEL="claude-3-opus-20240229"
```

#### Implementation Notes

Claude integration is extensible. Implementation follows:

```python
class ClaudeProvider(BaseLLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Implementation using Anthropic SDK
        pass
    
    async def generate_with_functions(self, messages: list, tools: list) -> dict:
        # Claude uses tool_use for function calling
        pass
```

### 3. Azure OpenAI

#### Setup

```bash
# Set environment variables
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
```

## Provider Selection

### Automatic Selection

```python
from src.llm.providers import LLMProviderFactory

# Uses ACTIVE_LLM_PROVIDER from config
provider = LLMProviderFactory.get_provider()
```

### Explicit Selection

```python
# Request specific provider
provider = LLMProviderFactory.get_provider("openai")
response = await provider.generate("Hello, world!")

# Use fallback if primary unavailable
try:
    provider = LLMProviderFactory.get_provider("openai")
except LLMProviderError:
    provider = LLMProviderFactory.get_fallback_provider()
```

## Prompt Engineering

### Templates

Store reusable prompt templates:

```python
# src/llm/prompt_templates.py
TICKET_CLASSIFICATION_PROMPT = """
Analyze the following customer support ticket and classify it.

Title: {ticket_title}
Description: {ticket_description}

Classify into one of: urgent, normal, low-priority

Respond with JSON:
{{
  "classification": "urgent|normal|low-priority",
  "confidence": 0.0-1.0,
  "reason": "explanation"
}}
"""

# Usage
from src.llm.prompt_templates import TICKET_CLASSIFICATION_PROMPT

prompt = TICKET_CLASSIFICATION_PROMPT.format(
    ticket_title=ticket.title,
    ticket_description=ticket.description
)

response = await provider.generate(prompt)
```

### Chain-of-Thought Prompting

```python
COT_PROMPT = """
You are a customer support AI assistant.

Think step-by-step:
1. Understand the customer's problem
2. Identify the root cause
3. Suggest relevant knowledge articles
4. Provide the solution

Customer Question: {question}

Let's think step by step...
"""
```

## Function Calling (Agent Tools)

### Defining Tools

```python
# src/llm/tools.py
TICKET_MANAGEMENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a support ticket",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"]
                    }
                },
                "required": ["customer_id", "title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search knowledge base articles",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    }
]
```

### Using Function Calling

```python
async def agent_interaction(user_question: str, provider: BaseLLMProvider):
    messages = [
        {"role": "user", "content": user_question}
    ]
    
    # Call with tools
    result = await provider.generate_with_functions(
        messages,
        TICKET_MANAGEMENT_TOOLS
    )
    
    if result["type"] == "function_call":
        function_name = result["function"]
        arguments = result["arguments"]
        
        # Execute the function
        if function_name == "create_ticket":
            ticket = await create_ticket(**arguments)
            return ticket
        
        elif function_name == "search_knowledge_base":
            docs = await search_kb(**arguments)
            return docs
    
    # Text response
    return result["content"]
```

## Cost Optimization

### Token Counting

```python
from src.llm.token_counter import count_tokens

message = "This is a test message"
model = "gpt-4"

tokens = count_tokens(message, model)
# Estimate: ~5 tokens

# Calculate cost
cost = (tokens / 1000) * OPENAI_PRICING["gpt-4"]["input"]
```

### Provider Cost Comparison

```python
# Track costs per provider
provider_stats = {
    "openai": {
        "total_tokens": 50000,
        "cost": 1.50,
        "requests": 1000,
        "avg_latency_ms": 450
    },
    "claude": {
        "total_tokens": 45000,
        "cost": 1.35,
        "requests": 950,
        "avg_latency_ms": 520
    }
}

# Select most cost-effective provider
best_provider = min(
    provider_stats.items(),
    key=lambda x: x[1]["cost"] / x[1]["requests"]
)
```

## RAG (Retrieval-Augmented Generation)

### Integration with LLM

```python
from src.rag.retrieval import retrieve_documents

async def answer_with_rag(question: str):
    # Retrieve relevant documents
    documents = await retrieve_documents(
        query=question,
        top_k=5,
        similarity_threshold=0.6
    )
    
    # Build context
    context = "\n\n".join([
        f"Source {i+1}: {doc['content']}"
        for i, doc in enumerate(documents)
    ])
    
    # Build prompt with context
    prompt = f"""Based on the following documents, answer the question.

Documents:
{context}

Question: {question}

Answer:"""
    
    # Generate response
    answer = await provider.generate(prompt)
    
    return {
        "answer": answer,
        "sources": [doc["id"] for doc in documents]
    }
```

## Monitoring & Analytics

### Token Usage Tracking

```python
# Automatically tracked in database
from src.db.models.ticket import LLMProvider

provider_record = await db.get(LLMProvider, provider_id)
print(f"Total tokens used: {provider_record.total_tokens_used}")
print(f"Total cost: ${provider_record.total_tokens_used / 1000 * rate}")
print(f"Average latency: {provider_record.average_latency_ms}ms")
```

### Error Rate Monitoring

```python
# Monitor provider reliability
error_rate = (provider_record.error_count / 
              provider_record.total_requests) * 100

if error_rate > 5:
    # Switch to fallback provider
    logger.warn(f"Provider {provider_name} has high error rate: {error_rate}%")
    provider = LLMProviderFactory.get_fallback_provider()
```

## Testing

### Mock Provider for Tests

```python
class MockLLMProvider(BaseLLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        return "Mock response"
    
    async def generate_with_functions(self, messages: list, tools: list) -> dict:
        return {
            "type": "message",
            "content": "Mock function call response"
        }

# In tests
from unittest.mock import patch

@patch('src.llm.providers.LLMProviderFactory.get_provider')
async def test_chat_endpoint(mock_get_provider):
    mock_provider = MockLLMProvider()
    mock_get_provider.return_value = mock_provider
    
    response = await client.post("/api/v1/ai/chat", 
        json={"customer_question": "Hello?"})
    
    assert response.status_code == 200
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   Status: 401 Unauthorized
   Cause: Invalid or expired API key
   Solution: Update OPENAI_API_KEY in .env
   ```

2. **Rate Limit Exceeded**
   ```
   Status: 429 Too Many Requests
   Cause: Too many requests to provider
   Solution: Implement backoff + retry, use cheaper model (gpt-3.5)
   ```

3. **Timeout Errors**
   ```
   Status: 504 Gateway Timeout
   Cause: Slow response from LLM provider
   Solution: Increase OPENAI_TIMEOUT, optimize prompts, use streaming
   ```

## Best Practices

1. **Always handle provider errors** with fallback mechanisms
2. **Cache prompt responses** to reduce costs
3. **Monitor token usage** to optimize costs
4. **Use function calling** for structured agent behavior
5. **Implement rate limiting** for external API calls
6. **Test with mock providers** before production deployment
7. **Log all LLM interactions** for debugging and improvement
