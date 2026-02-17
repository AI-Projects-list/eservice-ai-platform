"""
Configuration management for eService AI Platform.

Uses Pydantic Settings for environment variable management with type validation.
Supports multiple environments: development, staging, production.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    
    See .env.example for all available settings.
    """
    
    # Application
    APP_NAME: str = "eService AI Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PRODUCTION: bool = False
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 4
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY: str = "your-api-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/eservice"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    DATABASE_TIMEOUT: int = 30
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    REDIS_TIMEOUT: int = 5
    CACHE_DEFAULT_TTL: int = 3600  # 1 hour
    CACHE_MAX_TTL: int = 86400  # 24 hours
    
    # Message Queue (RabbitMQ)
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_PREFETCH_COUNT: int = 10
    RABBITMQ_TIMEOUT: int = 10
    
    # Celery Task Queue
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TIMEOUT: int = 300  # 5 minutes
    
    # LLM Providers
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_ORG_ID: Optional[str] = None
    OPENAI_DEFAULT_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TIMEOUT: int = 30
    
    CLAUDE_API_KEY: str = ""
    CLAUDE_DEFAULT_MODEL: str = "claude-3-opus-20240229"
    CLAUDE_TEMPERATURE: float = 0.7
    CLAUDE_MAX_TOKENS: int = 2048
    CLAUDE_TIMEOUT: int = 30
    
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    
    # LLM Default Configuration
    ACTIVE_LLM_PROVIDER: str = "openai"  # openai, claude, azure
    LLM_FALLBACK_PROVIDER: Optional[str] = "claude"
    LLM_ENABLE_FUNCTION_CALLING: bool = True
    LLM_ENABLE_STREAMING: bool = False
    
    # Vector Database (RAG)
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-west2-gcp"
    PINECONE_INDEX_NAME: str = "eservice-knowledge-base"
    
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_DATABASE: str = "eservice"
    MILVUS_COLLECTION: str = "knowledge_base"
    
    VECTOR_DB_TYPE: str = "milvus"  # milvus or pinecone
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # RAG Configuration
    TOP_K_RETRIEVAL: int = 5  # Number of documents to retrieve
    SIMILARITY_THRESHOLD: float = 0.6
    ENABLE_RERANKING: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Observability - Jaeger Tracing
    JAEGER_ENABLED: bool = True
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    JAEGER_SAMPLER_TYPE: str = "probabilistic"
    JAEGER_SAMPLER_RATE: float = 0.1
    
    # Observability - Prometheus
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 8001
    
    # Observability - Logging
    LOG_FORMAT: str = "json"  # json or text
    STRUCTURED_LOGGING: bool = True
    LOG_SQL_QUERIES: bool = False
    
    # Observability - ELK Stack
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX: str = "eservice-logs"
    
    # Feature Flags
    ENABLE_AI_RESPONSES: bool = True
    ENABLE_AUTO_ROUTING: bool = True
    ENABLE_KNOWLEDGE_BASE: bool = True
    ENABLE_ANALYTICS: bool = True
    
    # Request/Response
    MAX_REQUEST_SIZE: int = 10_485_760  # 10 MB
    REQUEST_TIMEOUT: int = 30
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # API Documentation
    DOCS_ENABLED: bool = True
    REDOC_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application configuration
    """
    return Settings()


# Create global settings instance
settings = get_settings()
