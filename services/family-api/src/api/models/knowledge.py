"""
Knowledge Base Models for Core Prompts and Skills

Pydantic models for managing core system prompts, skills, and version history.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==============================================================================
# Core Prompt Models
# ==============================================================================

class PromptVersion(BaseModel):
    """Single version of a core prompt"""
    timestamp: datetime = Field(
        description="When this version was created (ISO 8601 format)"
    )
    filename: str = Field(
        description="Filename of the version file (e.g., 2025-11-26T10-30-00Z.md)"
    )
    author: str = Field(
        description="Username who created this version"
    )
    change_summary: str = Field(
        description="Brief description of what changed in this version"
    )
    size_bytes: int = Field(
        description="File size in bytes"
    )
    token_estimate: int = Field(
        description="Estimated token count for LLM context"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-26T10:30:00Z",
                "filename": "2025-11-26T10-30-00Z.md",
                "author": "admin",
                "change_summary": "Updated safety guidelines for children",
                "size_bytes": 4521,
                "token_estimate": 1130
            }
        }


class PromptVersionManifest(BaseModel):
    """Manifest tracking all versions of a core prompt"""
    versions: List[PromptVersion] = Field(
        default_factory=list,
        description="List of all versions, most recent first"
    )
    retention_policy: str = Field(
        default="keep_last_10",
        description="Version retention policy"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "versions": [
                    {
                        "timestamp": "2025-11-26T10:30:00Z",
                        "filename": "2025-11-26T10-30-00Z.md",
                        "author": "admin",
                        "change_summary": "Updated safety guidelines",
                        "size_bytes": 4521,
                        "token_estimate": 1130
                    }
                ],
                "retention_policy": "keep_last_10"
            }
        }


class CorePromptMetadata(BaseModel):
    """Metadata about a core system prompt"""
    name: str = Field(
        description="Prompt name (FAMILY_ASSISTANT, PRINCIPLES, or RULES)"
    )
    display_name: str = Field(
        description="Human-readable display name"
    )
    description: str = Field(
        description="What this prompt controls"
    )
    file_path: str = Field(
        description="Relative path to the current version file"
    )
    current_version: Optional[PromptVersion] = Field(
        default=None,
        description="Metadata about current version"
    )
    version_count: int = Field(
        default=0,
        description="Total number of versions available"
    )
    last_modified: Optional[datetime] = Field(
        default=None,
        description="When the prompt was last modified"
    )
    size_bytes: int = Field(
        default=0,
        description="Current file size in bytes"
    )
    token_estimate: int = Field(
        default=0,
        description="Estimated token count for current version"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "FAMILY_ASSISTANT",
                "display_name": "Family Assistant Core",
                "description": "Primary system prompt defining the AI assistant's personality and capabilities",
                "file_path": "core/FAMILY_ASSISTANT.md",
                "current_version": {
                    "timestamp": "2025-11-26T10:30:00Z",
                    "filename": "current",
                    "author": "admin",
                    "change_summary": "Initial version",
                    "size_bytes": 4521,
                    "token_estimate": 1130
                },
                "version_count": 3,
                "last_modified": "2025-11-26T10:30:00Z",
                "size_bytes": 4521,
                "token_estimate": 1130
            }
        }


class CorePromptDetail(BaseModel):
    """Complete details of a core prompt including content"""
    metadata: CorePromptMetadata = Field(
        description="Prompt metadata"
    )
    content: str = Field(
        description="Current markdown content of the prompt"
    )
    versions: List[PromptVersion] = Field(
        default_factory=list,
        description="Available version history"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "name": "FAMILY_ASSISTANT",
                    "display_name": "Family Assistant Core",
                    "description": "Primary system prompt",
                    "file_path": "core/FAMILY_ASSISTANT.md",
                    "version_count": 3,
                    "size_bytes": 4521,
                    "token_estimate": 1130
                },
                "content": "# Family Assistant\n\nYou are a helpful...",
                "versions": []
            }
        }


# ==============================================================================
# Request Models
# ==============================================================================

class CorePromptUpdateRequest(BaseModel):
    """Request to update a core prompt"""
    content: str = Field(
        description="New markdown content for the prompt"
    )
    change_summary: str = Field(
        description="Brief description of changes made",
        min_length=5,
        max_length=200
    )
    author: str = Field(
        default="admin",
        description="Username making the change"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "# Family Assistant\n\nUpdated system prompt...",
                "change_summary": "Added new safety guidelines for children",
                "author": "admin"
            }
        }


class CorePromptRollbackRequest(BaseModel):
    """Request to rollback to a previous version"""
    version_timestamp: str = Field(
        description="ISO 8601 timestamp of version to restore (e.g., 2025-11-26T10-30-00Z)"
    )
    reason: str = Field(
        description="Why this rollback is being performed",
        min_length=5,
        max_length=200
    )
    author: str = Field(
        default="admin",
        description="Username performing the rollback"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "version_timestamp": "2025-11-26T10:30:00Z",
                "reason": "Reverting problematic changes that affected safety filters",
                "author": "admin"
            }
        }


# ==============================================================================
# Response Models
# ==============================================================================

class CorePromptUpdateResponse(BaseModel):
    """Response after updating a core prompt"""
    success: bool
    name: str = Field(description="Name of updated prompt")
    previous_version: PromptVersion = Field(
        description="Metadata of version that was replaced"
    )
    new_version: PromptVersion = Field(
        description="Metadata of newly created version"
    )
    message: str = Field(
        description="Human-readable status message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "name": "FAMILY_ASSISTANT",
                "previous_version": {
                    "timestamp": "2025-11-25T15:00:00Z",
                    "filename": "2025-11-25T15-00-00Z.md",
                    "author": "admin",
                    "change_summary": "Previous version",
                    "size_bytes": 4200,
                    "token_estimate": 1050
                },
                "new_version": {
                    "timestamp": "2025-11-26T10:30:00Z",
                    "filename": "2025-11-26T10-30-00Z.md",
                    "author": "admin",
                    "change_summary": "Updated safety guidelines",
                    "size_bytes": 4521,
                    "token_estimate": 1130
                },
                "message": "Successfully updated FAMILY_ASSISTANT and created version backup"
            }
        }


class CorePromptRollbackResponse(BaseModel):
    """Response after rolling back to a previous version"""
    success: bool
    name: str = Field(description="Name of prompt that was rolled back")
    restored_version: PromptVersion = Field(
        description="Version that was restored"
    )
    backup_version: PromptVersion = Field(
        description="Backup created of version before rollback"
    )
    message: str = Field(
        description="Human-readable status message"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "name": "FAMILY_ASSISTANT",
                "restored_version": {
                    "timestamp": "2025-11-25T15:00:00Z",
                    "filename": "2025-11-25T15-00-00Z.md",
                    "author": "admin",
                    "change_summary": "Stable version",
                    "size_bytes": 4200,
                    "token_estimate": 1050
                },
                "backup_version": {
                    "timestamp": "2025-11-26T10:30:00Z",
                    "filename": "2025-11-26T10-30-00Z.md",
                    "author": "admin",
                    "change_summary": "Pre-rollback backup",
                    "size_bytes": 4521,
                    "token_estimate": 1130
                },
                "message": "Successfully rolled back FAMILY_ASSISTANT to version from 2025-11-25T15:00:00Z"
            }
        }


# ==============================================================================
# List Response Models
# ==============================================================================

class CorePromptsListResponse(BaseModel):
    """Response listing all core prompts"""
    prompts: List[CorePromptMetadata] = Field(
        description="List of all core prompts with metadata"
    )
    total_count: int = Field(
        description="Total number of core prompts"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "prompts": [
                    {
                        "name": "FAMILY_ASSISTANT",
                        "display_name": "Family Assistant Core",
                        "description": "Primary system prompt",
                        "file_path": "core/FAMILY_ASSISTANT.md",
                        "version_count": 3,
                        "size_bytes": 4521,
                        "token_estimate": 1130
                    }
                ],
                "total_count": 3
            }
        }


class PromptVersionsListResponse(BaseModel):
    """Response listing all versions of a specific prompt"""
    name: str = Field(description="Name of the prompt")
    versions: List[PromptVersion] = Field(
        description="List of all versions, most recent first"
    )
    total_count: int = Field(
        description="Total number of versions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "FAMILY_ASSISTANT",
                "versions": [
                    {
                        "timestamp": "2025-11-26T10:30:00Z",
                        "filename": "2025-11-26T10-30-00Z.md",
                        "author": "admin",
                        "change_summary": "Updated safety guidelines",
                        "size_bytes": 4521,
                        "token_estimate": 1130
                    }
                ],
                "total_count": 3
            }
        }
