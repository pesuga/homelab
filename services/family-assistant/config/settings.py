"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # LLM Configuration
    ollama_base_url: str = "http://100.72.98.106:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_temperature: float = 0.7
    ollama_max_tokens: int = 2048

    # PostgreSQL
    postgres_host: str = "postgres.homelab.svc.cluster.local"
    postgres_port: int = 5432
    postgres_user: str = "homelab"
    postgres_password: str
    postgres_db: str = "homelab"

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_async_url(self) -> str:
        """Get async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_host: str = "redis.homelab.svc.cluster.local"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Mem0
    mem0_api_url: str = "http://mem0.homelab.svc.cluster.local:8080"
    mem0_api_key: Optional[str] = None

    # Qdrant
    qdrant_url: str = "http://qdrant.homelab.svc.cluster.local:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "family_assistant_memories"

    # N8n
    n8n_base_url: str = "http://100.81.76.55:30678"
    n8n_webhook_path: str = "/webhook"
    n8n_api_key: Optional[str] = None

    # Authentik (SSO) - Phase 2
    authentik_url: Optional[str] = None
    authentik_client_id: Optional[str] = None
    authentik_client_secret: Optional[str] = None

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_workers: int = 4
    api_reload: bool = False
    log_level: str = "info"

    # Security
    secret_key: str
    encryption_key: Optional[str] = None

    # Observability
    enable_metrics: bool = True
    enable_audit_log: bool = True

    # Development
    debug: bool = False
    testing: bool = False


# Global settings instance
settings = Settings()
