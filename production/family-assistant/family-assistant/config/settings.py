"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any
import os
from .feature_flags import feature_flags, FlagStatus


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # LLM Configuration - llama.cpp with Kimi-VL
    llamacpp_base_url: str = "http://100.72.98.106:8080"
    llamacpp_model: str = "Kimi-VL-A3B-Thinking-2506-Q4_K_M"
    llamacpp_temperature: float = 0.7
    llamacpp_max_tokens: int = 2048

    # Backward compatibility for ollama references
    @property
    def ollama_base_url(self) -> str:
        """Backward compatibility: map to llama.cpp URL."""
        return self.llamacpp_base_url

    @property
    def ollama_model(self) -> str:
        """Backward compatibility: map to llama.cpp model."""
        return self.llamacpp_model

    @property
    def ollama_temperature(self) -> float:
        """Backward compatibility: map to llama.cpp temperature."""
        return self.llamacpp_temperature

    @property
    def ollama_max_tokens(self) -> int:
        """Backward compatibility: map to llama.cpp max tokens."""
        return self.llamacpp_max_tokens

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

    # Telegram Bot
    telegram_bot_token: Optional[str] = None

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

    # Feature Flag Configuration
    feature_flag_config_file: Optional[str] = None
    enable_feature_flags_ui: bool = False

    # Multimodal Content Settings (Feature Flag Aware)
    max_file_size_mb: int = 50
    supported_image_formats: str = "jpg,png,gif,webp"
    supported_audio_formats: str = "mp3,wav,ogg,m4a"
    supported_document_formats: str = "pdf,docx,txt,rtf"

    # Processing Settings
    content_processing_timeout_seconds: int = 300
    vision_analysis_enabled: bool = True
    speech_transcription_enabled: bool = True
    document_extraction_enabled: bool = True

    # Privacy & Safety
    content_filtering_enabled: bool = True
    safety_threshold: float = 0.7
    auto_reject_unsafe_content: bool = False

    # Performance & Caching
    response_cache_ttl_minutes: int = 15
    max_cache_size_mb: int = 100
    batch_processing_enabled: bool = False
    max_batch_size: int = 5

    # Family Features
    family_sharing_enabled: bool = True
    advanced_memory_enabled: bool = False
    emotional_analysis_enabled: bool = False

    def get_multimodal_config(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get multimodal configuration based on feature flags."""
        config = {
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": {
                "image": self.supported_image_formats.split(",") if feature_flags.is_enabled("multimodal_content", user_context) else [],
                "audio": self.supported_audio_formats.split(",") if feature_flags.is_enabled("speech_transcription", user_context) else [],
                "document": self.supported_document_formats.split(",") if feature_flags.is_enabled("document_extraction", user_context) else []
            },
            "processing_enabled": {
                "vision": feature_flags.is_enabled("vision_analysis", user_context) and self.vision_analysis_enabled,
                "speech": feature_flags.is_enabled("speech_transcription", user_context) and self.speech_transcription_enabled,
                "extraction": feature_flags.is_enabled("document_extraction", user_context) and self.document_extraction_enabled
            },
            "timeout_seconds": self.content_processing_timeout_seconds
        }

        return config

    def get_privacy_config(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get privacy and safety configuration based on feature flags."""
        return {
            "content_filtering": {
                "enabled": feature_flags.is_enabled("content_filtering", user_context) and self.content_filtering_enabled,
                "threshold": self.safety_threshold,
                "auto_reject": self.auto_reject_unsafe_content
            },
            "family_sharing": {
                "enabled": feature_flags.is_enabled("family_sharing", user_context) and self.family_sharing_enabled
            }
        }

    def get_performance_config(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get performance-related configuration based on feature flags."""
        return {
            "caching": {
                "enabled": feature_flags.is_enabled("caching_enabled", user_context),
                "ttl_minutes": self.response_cache_ttl_minutes,
                "max_size_mb": self.max_cache_size_mb
            },
            "batch_processing": {
                "enabled": feature_flags.is_enabled("batch_processing", user_context) and self.batch_processing_enabled,
                "max_size": self.max_batch_size
            }
        }

    def get_ai_features_config(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get AI features configuration based on feature flags."""
        return {
            "advanced_memory": {
                "enabled": feature_flags.is_enabled("advanced_memory", user_context)
            },
            "content_summarization": {
                "enabled": feature_flags.is_enabled("content_summarization", user_context)
            },
            "emotional_analysis": {
                "enabled": feature_flags.is_enabled("emotional_analysis", user_context)
            }
        }

    def get_integrations_config(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get integration configuration based on feature flags."""
        return {
            "telegram_bot": {
                "enabled": feature_flags.is_enabled("telegram_bot", user_context),
                "base_url": self.n8n_base_url
            },
            "api_webhooks": {
                "enabled": feature_flags.is_enabled("api_webhooks", user_context)
            }
        }

    def get_effective_config(self, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get complete effective configuration for a user context."""
        return {
            "multimodal": self.get_multimodal_config(user_context),
            "privacy": self.get_privacy_config(user_context),
            "performance": self.get_performance_config(user_context),
            "ai_features": self.get_ai_features_config(user_context),
            "integrations": self.get_integrations_config(user_context),
            "enabled_features": feature_flags.get_enabled_features(user_context),
            "feature_flags": {
                key: feature_flags.is_enabled(key, user_context)
                for key in feature_flags.flags.keys()
            }
        }

    def should_process_content_type(self, content_type: str, user_context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a specific content type should be processed for a user."""
        if not feature_flags.is_enabled("multimodal_content", user_context):
            return False

        return {
            "image": feature_flags.is_enabled("vision_analysis", user_context),
            "audio": feature_flags.is_enabled("speech_transcription", user_context),
            "document": feature_flags.is_enabled("document_extraction", user_context)
        }.get(content_type.lower(), False)


# Global settings instance
settings = Settings()
