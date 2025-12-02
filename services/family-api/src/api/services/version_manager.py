"""
Version Manager - Core Prompt Version Control

Manages version history and rollback for core system prompts (FAMILY_ASSISTANT, PRINCIPLES, RULES).
Uses file-based versioning with JSON manifest for tracking.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import shutil
import re

from api.models.knowledge import (
    PromptVersion,
    PromptVersionManifest,
    CorePromptMetadata,
    CorePromptUpdateRequest,
    CorePromptRollbackRequest,
    CorePromptUpdateResponse,
    CorePromptRollbackResponse
)


class VersionManager:
    """Manages version history for core prompts"""

    # Valid core prompt names
    VALID_PROMPTS = ["FAMILY_ASSISTANT", "PRINCIPLES", "RULES"]

    # Retention policy
    MAX_VERSIONS = 10

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize version manager with prompts directory"""
        if prompts_dir is None:
            # Default to prompts directory in project root
            import os
            env_prompts_dir = os.getenv("PROMPTS_DIR")
            if env_prompts_dir:
                prompts_dir = Path(env_prompts_dir)
            else:
                project_root = Path(__file__).parent.parent.parent
                prompts_dir = project_root / "prompts"

        self.prompts_dir = prompts_dir
        self.core_dir = prompts_dir / "core"
        self.versions_dir = self.core_dir / ".versions"

        # Ensure directories exist
        self.core_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _validate_prompt_name(self, name: str) -> None:
        """Validate prompt name is one of the valid core prompts"""
        if name not in self.VALID_PROMPTS:
            raise ValueError(f"Invalid prompt name: {name}. Must be one of {self.VALID_PROMPTS}")

    def _get_prompt_file(self, name: str) -> Path:
        """Get path to current version of prompt"""
        return self.core_dir / f"{name}.md"

    def _get_version_dir(self, name: str) -> Path:
        """Get path to version history directory for prompt"""
        version_dir = self.versions_dir / name
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir

    def _get_manifest_file(self, name: str) -> Path:
        """Get path to manifest.json for prompt"""
        return self._get_version_dir(name) / "manifest.json"

    def _load_manifest(self, name: str) -> PromptVersionManifest:
        """Load version manifest, create if doesn't exist"""
        manifest_file = self._get_manifest_file(name)

        if not manifest_file.exists():
            manifest = PromptVersionManifest(versions=[], retention_policy="keep_last_10")
            self._save_manifest(name, manifest)
            return manifest

        try:
            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            return PromptVersionManifest(**data)
        except Exception as e:
            # If manifest is corrupted, create new one
            print(f"Warning: Corrupted manifest for {name}, creating new: {e}")
            manifest = PromptVersionManifest(versions=[], retention_policy="keep_last_10")
            self._save_manifest(name, manifest)
            return manifest

    def _save_manifest(self, name: str, manifest: PromptVersionManifest) -> None:
        """Save version manifest to JSON file"""
        manifest_file = self._get_manifest_file(name)
        manifest_file.write_text(
            json.dumps(manifest.model_dump(), indent=2, default=str),
            encoding="utf-8"
        )

    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return len(content) // 4

    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime as ISO 8601 without colons (filesystem-safe)"""
        # Format: 2025-11-26T10-30-00Z
        return dt.strftime("%Y-%m-%dT%H-%M-%SZ")

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse filesystem-safe timestamp back to datetime"""
        # Handle both formats: 2025-11-26T10-30-00Z and 2025-11-26T10:30:00Z
        timestamp_str = timestamp_str.replace("-", ":", 2)  # Replace first two hyphens after T
        if timestamp_str.endswith("Z"):
            return datetime.fromisoformat(timestamp_str[:-1])
        return datetime.fromisoformat(timestamp_str)

    def create_version(
        self,
        name: str,
        content: str,
        author: str,
        change_summary: str
    ) -> PromptVersion:
        """
        Create a new version by backing up current content

        Args:
            name: Prompt name (FAMILY_ASSISTANT, PRINCIPLES, or RULES)
            content: Current content to be backed up
            author: Username creating the version
            change_summary: Description of changes

        Returns:
            PromptVersion with metadata about created version
        """
        self._validate_prompt_name(name)

        # Create version metadata
        now = datetime.utcnow()
        timestamp_str = self._format_timestamp(now)
        filename = f"{timestamp_str}.md"
        size_bytes = len(content.encode("utf-8"))
        token_estimate = self._estimate_tokens(content)

        # Save version file
        version_dir = self._get_version_dir(name)
        version_file = version_dir / filename
        version_file.write_text(content, encoding="utf-8")

        # Create version metadata
        version = PromptVersion(
            timestamp=now,
            filename=filename,
            author=author,
            change_summary=change_summary,
            size_bytes=size_bytes,
            token_estimate=token_estimate
        )

        # Update manifest
        manifest = self._load_manifest(name)
        manifest.versions.insert(0, version)  # Most recent first

        # Apply retention policy
        if len(manifest.versions) > self.MAX_VERSIONS:
            # Remove old versions
            for old_version in manifest.versions[self.MAX_VERSIONS:]:
                old_file = version_dir / old_version.filename
                if old_file.exists():
                    old_file.unlink()
            manifest.versions = manifest.versions[:self.MAX_VERSIONS]

        self._save_manifest(name, manifest)

        return version

    def get_versions(self, name: str) -> List[PromptVersion]:
        """Get all versions for a prompt, most recent first"""
        self._validate_prompt_name(name)
        manifest = self._load_manifest(name)
        return manifest.versions

    def get_version_content(self, name: str, timestamp: str) -> Optional[str]:
        """
        Get content of a specific version

        Args:
            name: Prompt name
            timestamp: ISO 8601 timestamp (e.g., "2025-11-26T10:30:00Z" or "2025-11-26T10-30-00Z")

        Returns:
            Content of the version, or None if not found
        """
        self._validate_prompt_name(name)

        # Normalize timestamp format
        timestamp_normalized = timestamp.replace(":", "-").replace("T", "T", 1)
        if not timestamp_normalized.endswith("Z"):
            timestamp_normalized += "Z"

        filename = f"{timestamp_normalized}.md"
        version_file = self._get_version_dir(name) / filename

        if not version_file.exists():
            return None

        return version_file.read_text(encoding="utf-8")

    def get_current_content(self, name: str) -> str:
        """Get current content of a prompt"""
        self._validate_prompt_name(name)
        prompt_file = self._get_prompt_file(name)

        if not prompt_file.exists():
            return ""

        return prompt_file.read_text(encoding="utf-8")

    def update_prompt(
        self,
        name: str,
        request: CorePromptUpdateRequest
    ) -> CorePromptUpdateResponse:
        """
        Update a core prompt, creating a version backup of current content

        Args:
            name: Prompt name
            request: Update request with new content, change summary, and author

        Returns:
            Response with previous and new version metadata
        """
        self._validate_prompt_name(name)

        # Get current content for backup
        current_content = self.get_current_content(name)
        current_size = len(current_content.encode("utf-8")) if current_content else 0
        current_tokens = self._estimate_tokens(current_content) if current_content else 0

        # Create version of current content (before update)
        previous_version = PromptVersion(
            timestamp=datetime.utcnow(),
            filename="current",
            author="system",
            change_summary="Pre-update backup",
            size_bytes=current_size,
            token_estimate=current_tokens
        )

        if current_content:
            # Only create backup if there's existing content
            previous_version = self.create_version(
                name=name,
                content=current_content,
                author=request.author,
                change_summary=f"Pre-update backup: {request.change_summary}"
            )

        # Write new content
        prompt_file = self._get_prompt_file(name)
        prompt_file.write_text(request.content, encoding="utf-8")

        # Create new version metadata
        new_size = len(request.content.encode("utf-8"))
        new_tokens = self._estimate_tokens(request.content)
        new_version = PromptVersion(
            timestamp=datetime.utcnow(),
            filename="current",
            author=request.author,
            change_summary=request.change_summary,
            size_bytes=new_size,
            token_estimate=new_tokens
        )

        return CorePromptUpdateResponse(
            success=True,
            name=name,
            previous_version=previous_version,
            new_version=new_version,
            message=f"Successfully updated {name} and created version backup"
        )

    def rollback(
        self,
        name: str,
        request: CorePromptRollbackRequest
    ) -> CorePromptRollbackResponse:
        """
        Rollback to a previous version

        Args:
            name: Prompt name
            request: Rollback request with version timestamp and reason

        Returns:
            Response with restored and backup version metadata
        """
        self._validate_prompt_name(name)

        # Get content of version to restore
        restored_content = self.get_version_content(name, request.version_timestamp)
        if restored_content is None:
            raise ValueError(f"Version not found: {request.version_timestamp}")

        # Get current content for backup
        current_content = self.get_current_content(name)

        # Create backup of current state before rollback
        backup_version = self.create_version(
            name=name,
            content=current_content,
            author=request.author,
            change_summary=f"Pre-rollback backup: {request.reason}"
        )

        # Restore old version as current
        prompt_file = self._get_prompt_file(name)
        prompt_file.write_text(restored_content, encoding="utf-8")

        # Find metadata of restored version
        manifest = self._load_manifest(name)
        restored_version = None
        for version in manifest.versions:
            timestamp_str = self._format_timestamp(version.timestamp)
            if timestamp_str.startswith(request.version_timestamp.replace(":", "-").split("Z")[0]):
                restored_version = version
                break

        if restored_version is None:
            # Create version object from content
            restored_version = PromptVersion(
                timestamp=self._parse_timestamp(request.version_timestamp),
                filename=f"{request.version_timestamp.replace(':', '-')}.md",
                author="unknown",
                change_summary="Restored version",
                size_bytes=len(restored_content.encode("utf-8")),
                token_estimate=self._estimate_tokens(restored_content)
            )

        return CorePromptRollbackResponse(
            success=True,
            name=name,
            restored_version=restored_version,
            backup_version=backup_version,
            message=f"Successfully rolled back {name} to version from {request.version_timestamp}"
        )

    def get_prompt_metadata(self, name: str) -> CorePromptMetadata:
        """Get metadata about a core prompt"""
        self._validate_prompt_name(name)

        # Get current file info
        prompt_file = self._get_prompt_file(name)
        current_content = self.get_current_content(name)
        size_bytes = len(current_content.encode("utf-8")) if current_content else 0
        token_estimate = self._estimate_tokens(current_content) if current_content else 0

        # Get version history
        versions = self.get_versions(name)
        version_count = len(versions)

        # Get most recent version as current version
        current_version = None
        last_modified = None
        if versions:
            latest = versions[0]
            current_version = latest
            last_modified = latest.timestamp
        elif prompt_file.exists():
            # File exists but no versions yet
            stat = prompt_file.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            current_version = PromptVersion(
                timestamp=last_modified,
                filename="current",
                author="system",
                change_summary="Initial version",
                size_bytes=size_bytes,
                token_estimate=token_estimate
            )

        # Display names and descriptions
        display_names = {
            "FAMILY_ASSISTANT": "Family Assistant Core",
            "PRINCIPLES": "Core Principles",
            "RULES": "Behavioral Rules"
        }

        descriptions = {
            "FAMILY_ASSISTANT": "Primary system prompt defining the AI assistant's personality and capabilities",
            "PRINCIPLES": "Core principles guiding the assistant's behavior and decision-making",
            "RULES": "Specific rules and constraints for safe, appropriate interactions"
        }

        return CorePromptMetadata(
            name=name,
            display_name=display_names.get(name, name),
            description=descriptions.get(name, f"Core system prompt: {name}"),
            file_path=f"core/{name}.md",
            current_version=current_version,
            version_count=version_count,
            last_modified=last_modified,
            size_bytes=size_bytes,
            token_estimate=token_estimate
        )

    def list_core_prompts(self) -> List[CorePromptMetadata]:
        """List all core prompts with metadata"""
        return [self.get_prompt_metadata(name) for name in self.VALID_PROMPTS]
