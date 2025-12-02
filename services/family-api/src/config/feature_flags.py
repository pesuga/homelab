"""Feature flag system for gradual rollout of Family Assistant features."""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum


class FlagStatus(str, Enum):
    """Feature flag status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    LIMITED = "limited"
    BETA = "beta"


class TargetType(str, Enum):
    """Feature flag targeting types."""
    ALL_USERS = "all_users"
    SPECIFIC_USERS = "specific_users"
    USER_ROLES = "user_roles"
    PERCENTAGE = "percentage"
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"


@dataclass
class FeatureFlag:
    """Individual feature flag configuration."""
    key: str
    name: str
    description: str
    status: FlagStatus = FlagStatus.DISABLED
    target_type: TargetType = TargetType.ALL_USERS
    target_config: Dict[str, Any] = field(default_factory=dict)
    rollout_percentage: Optional[int] = None
    enabled_users: List[str] = field(default_factory=list)
    enabled_roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureFlagManager:
    """Manager for feature flags with dynamic evaluation."""

    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_default_flags()
        self._load_environment_overrides()

    def _load_default_flags(self):
        """Load default feature flag configuration."""

        # Core Features
        self.register_flag(FeatureFlag(
            key="multimodal_content",
            name="Multimodal Content Support",
            description="Enable processing of images, audio, and documents",
            status=FlagStatus.ENABLED,
            target_type=TargetType.ALL_USERS,
            metadata={
                "content_types": ["image", "audio", "document"],
                "max_file_size_mb": 50,
                "processing_timeout_seconds": 300
            }
        ))

        # AI Model Features
        self.register_flag(FeatureFlag(
            key="vision_analysis",
            name="AI Vision Analysis",
            description="Enable AI-powered image analysis and description",
            status=FlagStatus.BETA,
            target_type=TargetType.PERCENTAGE,
            rollout_percentage=50,
            metadata={
                "supported_formats": ["jpg", "png", "gif", "webp"],
                "max_resolution": "4K",
                "requires_gpu": True
            }
        ))

        self.register_flag(FeatureFlag(
            key="speech_transcription",
            name="Speech Transcription",
            description="Enable audio-to-text transcription",
            status=FlagStatus.ENABLED,
            target_type=TargetType.ALL_USERS,
            metadata={
                "supported_formats": ["mp3", "wav", "ogg", "m4a"],
                "max_duration_minutes": 30,
                "language_detection": True
            }
        ))

        self.register_flag(FeatureFlag(
            key="document_extraction",
            name="Document Text Extraction",
            description="Enable OCR and text extraction from documents",
            status=FlagStatus.ENABLED,
            target_type=TargetType.ALL_USERS,
            metadata={
                "supported_formats": ["pdf", "docx", "txt", "rtf"],
                "max_pages": 100,
                "table_extraction": True
            }
        ))

        # Family & Privacy Features
        self.register_flag(FeatureFlag(
            key="content_filtering",
            name="Content Safety Filtering",
            description="Enable automatic content safety analysis and filtering",
            status=FlagStatus.ENABLED,
            target_type=TargetType.ALL_USERS,
            metadata={
                "safety_categories": ["violence", "adult_content", "hate_speech"],
                "threshold": 0.7,
                "auto_reject": False
            }
        ))

        self.register_flag(FeatureFlag(
            key="family_sharing",
            name="Family Content Sharing",
            description="Enable sharing content between family members",
            status=FlagStatus.ENABLED,
            target_type=TargetType.USER_ROLES,
            target_config={"roles": ["parent", "teenager"]},
            enabled_roles=["parent", "teenager"],
            metadata={
                "auto_share_with_parents": True,
                "consent_required": True,
                "age_restrictions": {"child": 13, "teenager": 16}
            }
        ))

        self.register_flag(FeatureFlag(
            key="advanced_memory",
            name="Advanced Memory System",
            description="Enable enhanced conversation memory and context retention",
            status=FlagStatus.BETA,
            target_type=TargetType.PERCENTAGE,
            rollout_percentage=25,
            metadata={
                "memory_days": 90,
                "context_window": 50,
                "semantic_search": True
            }
        ))

        # Integration Features
        self.register_flag(FeatureFlag(
            key="telegram_bot",
            name="Telegram Bot Integration",
            description="Enable Telegram bot for family assistant access",
            status=FlagStatus.ENABLED,
            target_type=TargetType.ALL_USERS,
            metadata={
                "supported_message_types": ["text", "photo", "voice", "document"],
                "rate_limit_per_minute": 30,
                "family_group_support": True
            }
        ))

        self.register_flag(FeatureFlag(
            key="api_webhooks",
            name="API Webhooks",
            description="Enable webhook integration for external services",
            status=FlagStatus.DISABLED,
            target_type=TargetType.USER_ROLES,
            target_config={"roles": ["parent"]},
            enabled_roles=["parent"],
            metadata={
                "max_webhooks_per_user": 10,
                "retry_attempts": 3,
                "auth_required": True
            }
        ))

        # Performance Features
        self.register_flag(FeatureFlag(
            key="caching_enabled",
            name="Response Caching",
            description="Enable intelligent response caching for performance",
            status=FlagStatus.ENABLED,
            target_type=TargetType.ALL_USERS,
            metadata={
                "cache_ttl_minutes": 15,
                "max_cache_size_mb": 100,
                "cache_hit_ratio_target": 0.6
            }
        ))

        self.register_flag(FeatureFlag(
            key="batch_processing",
            name="Batch Content Processing",
            description="Enable processing multiple content items simultaneously",
            status=FlagStatus.LIMITED,
            target_type=TargetType.PERCENTAGE,
            rollout_percentage=30,
            metadata={
                "max_batch_size": 5,
                "concurrent_limit": 3,
                "timeout_per_item_seconds": 120
            }
        ))

        # Advanced Features
        self.register_flag(FeatureFlag(
            key="content_summarization",
            name="AI Content Summarization",
            description="Enable automatic content summarization",
            status=FlagStatus.BETA,
            target_type=TargetType.USER_ROLES,
            target_config={"roles": ["parent"]},
            enabled_roles=["parent"],
            metadata={
                "max_summary_length": 500,
                "extract_key_points": True,
                "support_multiple_formats": True
            }
        ))

        self.register_flag(FeatureFlag(
            key="emotional_analysis",
            name="Emotional Analysis",
            description="Enable emotional tone analysis of conversations",
            status=FlagStatus.DISABLED,
            target_type=TargetType.PERCENTAGE,
            rollout_percentage=0,
            metadata={
                "emotion_categories": ["happy", "sad", "angry", "excited", "worried"],
                "confidence_threshold": 0.8,
                "historical_tracking": True
            }
        ))

    def _load_environment_overrides(self):
        """Load feature flag overrides from environment variables."""

        # Environment variable format: FEATURE_FLAG_KEY=STATUS
        for env_var, value in os.environ.items():
            if env_var.startswith("FEATURE_"):
                flag_key = env_var[8:].lower()  # Remove "FEATURE_" prefix

                if flag_key in self.flags:
                    try:
                        status = FlagStatus(value.lower())
                        self.flags[flag_key].status = status
                        self.flags[flag_key].updated_at = datetime.now(timezone.utc)
                        print(f"✅ Override from environment: {flag_key} = {status}")
                    except ValueError:
                        print(f"⚠️ Invalid status for {flag_key}: {value}")

    def register_flag(self, flag: FeatureFlag):
        """Register a new feature flag."""
        self.flags[flag.key] = flag

    def is_enabled(self, flag_key: str, user_context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a feature flag is enabled for a given user context."""

        if flag_key not in self.flags:
            return False

        flag = self.flags[flag_key]

        # Basic status check
        if flag.status == FlagStatus.DISABLED:
            return False
        elif flag.status == FlagStatus.ENABLED:
            return True
        elif flag.status == FlagStatus.BETA:
            # Beta features need explicit targeting
            pass

        # Apply targeting rules
        if not user_context:
            return flag.status == FlagStatus.ENABLED

        return self._evaluate_targeting(flag, user_context)

    def _evaluate_targeting(self, flag: FeatureFlag, user_context: Dict[str, Any]) -> bool:
        """Evaluate targeting rules for a feature flag."""

        if flag.target_type == TargetType.ALL_USERS:
            return flag.status != FlagStatus.DISABLED

        elif flag.target_type == TargetType.SPECIFIC_USERS:
            user_id = user_context.get("user_id")
            return user_id in flag.enabled_users

        elif flag.target_type == TargetType.USER_ROLES:
            user_role = user_context.get("role")
            return user_role in flag.enabled_roles

        elif flag.target_type == TargetType.PERCENTAGE:
            if not flag.rollout_percentage:
                return False

            user_id = user_context.get("user_id", "")
            # Simple hash-based rollout
            hash_value = hash(user_id) % 100
            return hash_value < flag.rollout_percentage

        elif flag.target_type == TargetType.WHITELIST:
            user_id = user_context.get("user_id")
            return user_id in flag.enabled_users

        elif flag.target_type == TargetType.BLACKLIST:
            user_id = user_context.get("user_id")
            return user_id not in flag.enabled_users

        return False

    def get_enabled_features(self, user_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get list of enabled features for a user context."""
        return [key for key in self.flags.keys() if self.is_enabled(key, user_context)]

    def get_flag_config(self, flag_key: str) -> Optional[FeatureFlag]:
        """Get the full configuration for a feature flag."""
        return self.flags.get(flag_key)

    def update_flag(self, flag_key: str, **kwargs):
        """Update a feature flag configuration."""
        if flag_key in self.flags:
            flag = self.flags[flag_key]
            for key, value in kwargs.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)
            flag.updated_at = datetime.now(timezone.utc)

    def get_flag_statistics(self) -> Dict[str, Any]:
        """Get statistics about feature flag usage."""
        stats = {
            "total_flags": len(self.flags),
            "enabled": 0,
            "disabled": 0,
            "beta": 0,
            "limited": 0,
            "by_target_type": {},
            "recently_updated": []
        }

        for flag in self.flags.values():
            # Status counts
            if flag.status == FlagStatus.ENABLED:
                stats["enabled"] += 1
            elif flag.status == FlagStatus.DISABLED:
                stats["disabled"] += 1
            elif flag.status == FlagStatus.BETA:
                stats["beta"] += 1
            elif flag.status == FlagStatus.LIMITED:
                stats["limited"] += 1

            # Target type counts
            target_type = flag.target_type.value
            stats["by_target_type"][target_type] = stats["by_target_type"].get(target_type, 0) + 1

            # Recently updated (last 24 hours)
            if (datetime.now(timezone.utc) - flag.updated_at).days <= 1:
                stats["recently_updated"].append({
                    "key": flag.key,
                    "name": flag.name,
                    "updated_at": flag.updated_at.isoformat()
                })

        return stats

    def export_config(self) -> Dict[str, Any]:
        """Export feature flag configuration for backup/migration."""
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "flags": {
                key: {
                    "name": flag.name,
                    "description": flag.description,
                    "status": flag.status.value,
                    "target_type": flag.target_type.value,
                    "target_config": flag.target_config,
                    "rollout_percentage": flag.rollout_percentage,
                    "enabled_users": flag.enabled_users,
                    "enabled_roles": flag.enabled_roles,
                    "metadata": flag.metadata,
                    "created_at": flag.created_at.isoformat(),
                    "updated_at": flag.updated_at.isoformat()
                }
                for key, flag in self.flags.items()
            }
        }

    def import_config(self, config_data: Dict[str, Any]):
        """Import feature flag configuration from backup."""
        if "flags" not in config_data:
            raise ValueError("Invalid config format: missing 'flags' section")

        for key, flag_data in config_data["flags"].items():
            flag = FeatureFlag(
                key=key,
                name=flag_data["name"],
                description=flag_data["description"],
                status=FlagStatus(flag_data["status"]),
                target_type=TargetType(flag_data["target_type"]),
                target_config=flag_data.get("target_config", {}),
                rollout_percentage=flag_data.get("rollout_percentage"),
                enabled_users=flag_data.get("enabled_users", []),
                enabled_roles=flag_data.get("enabled_roles", []),
                metadata=flag_data.get("metadata", {}),
                created_at=datetime.fromisoformat(flag_data["created_at"]),
                updated_at=datetime.fromisoformat(flag_data["updated_at"])
            )
            self.flags[key] = flag


# Global feature flag manager instance
feature_flags = FeatureFlagManager()