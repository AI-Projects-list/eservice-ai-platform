"""
LLM provider integration with multi-provider support.

Implements provider factory pattern for seamless switching between
OpenAI, Claude, Azure OpenAI, and custom models.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
import json
import time

from openai import AsyncOpenAI
import structlog

from src.config import settings
from src.core.exceptions import LLMProviderError

logger = structlog.get_logger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text response from prompt."""
        pass
    
    @abstractmethod
    async def generate_with_functions(self, messages: list, tools: list, **kwargs) -> dict:
        """Generate response with function calling support."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self):
        super().__init__(
            model=settings.OPENAI_DEFAULT_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS
        )
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            organization=settings.OPENAI_ORG_ID,
        )
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API."""
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=settings.OPENAI_TIMEOUT,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info("OpenAI request completed",
                       model=self.model,
                       latency_ms=latency_ms,
                       usage_prompt=response.usage.prompt_tokens,
                       usage_completion=response.usage.completion_tokens)
            
            return response.choices[0].message.content
        
        except Exception as exc:
            logger.error("OpenAI request failed", error=str(exc))
            raise LLMProviderError("openai", str(exc))
    
    async def generate_with_functions(
        self,
        messages: list,
        tools: list,
        **kwargs
    ) -> dict:
        """Generate response with function calling."""
        try:
            start_time = time.time()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=self.temperature,
                timeout=settings.OPENAI_TIMEOUT,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info("OpenAI function call completed",
                       model=self.model,
                       latency_ms=latency_ms)
            
            # Parse tool use if present
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                return {
                    "type": "function_call",
                    "function": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                }
            
            return {
                "type": "message",
                "content": response.choices[0].message.content
            }
        
        except Exception as exc:
            logger.error("OpenAI function call failed", error=str(exc))
            raise LLMProviderError("openai", str(exc))


class ClaudeProvider(BaseLLMProvider):
    """Claude/Anthropic API provider implementation."""
    
    def __init__(self):
        super().__init__(
            model=settings.CLAUDE_DEFAULT_MODEL,
            temperature=settings.CLAUDE_TEMPERATURE,
            max_tokens=settings.CLAUDE_MAX_TOKENS
        )
        # TODO: Initialize Anthropic client
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Claude API."""
        # TODO: Implement Claude integration
        raise NotImplementedError("Claude provider not yet implemented")
    
    async def generate_with_functions(
        self,
        messages: list,
        tools: list,
        **kwargs
    ) -> dict:
        """Generate response with function calling."""
        # TODO: Implement Claude function calling
        raise NotImplementedError("Claude function calling not yet implemented")


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""
    
    _providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
        # "azure": AzureOpenAIProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get LLM provider instance.
        
        Args:
            provider_name: Provider name (openai, claude, azure)
            
        Returns:
            BaseLLMProvider: Provider instance
            
        Raises:
            LLMProviderError: If provider not found or unavailable
        """
        name = provider_name or settings.ACTIVE_LLM_PROVIDER
        
        if name not in cls._providers:
            raise LLMProviderError(
                name,
                f"Unknown provider: {name}",
                status_code=400
            )
        
        try:
            provider_class = cls._providers[name]
            provider = provider_class()
            logger.info("LLM provider initialized", provider=name)
            return provider
        
        except Exception as exc:
            logger.error("Failed to initialize LLM provider",
                        provider=name,
                        error=str(exc))
            raise LLMProviderError(name, str(exc))
    
    @classmethod
    def get_fallback_provider(cls) -> BaseLLMProvider:
        """Get fallback LLM provider."""
        return cls.get_provider(settings.LLM_FALLBACK_PROVIDER)
