"""
Prompt Builder - Dynamic System Prompt Assembly

Builds context-aware system prompts by combining:
- Core system prompt (FAMILY_ASSISTANT.md)
- Role-specific behavior (parent/teenager/child)
- Active skills context
- Memory context
- Language preferences
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import re

from api.services.memory_manager import MemoryContext, UserContext


class PromptBuilder:
    """Dynamically assembles system prompts based on context"""

    def __init__(self, prompts_dir: Optional[Path] = None):
        if prompts_dir is None:
            # Default to prompts directory in project root
            project_root = Path(__file__).parent.parent.parent
            prompts_dir = project_root / "prompts"

        self.prompts_dir = prompts_dir
        self.cache: Dict[str, str] = {}  # Cache loaded prompt files

    def load_file(self, filepath: Path) -> str:
        """Load prompt file with caching"""
        cache_key = str(filepath)

        if cache_key in self.cache:
            return self.cache[cache_key]

        if not filepath.exists():
            return ""

        content = filepath.read_text(encoding="utf-8")
        self.cache[cache_key] = content
        return content

    def load_core_prompt(self) -> str:
        """Load FAMILY_ASSISTANT.md base prompt"""
        return self.load_file(self.prompts_dir / "core" / "FAMILY_ASSISTANT.md")

    def load_principles(self) -> str:
        """Load PRINCIPLES.md"""
        return self.load_file(self.prompts_dir / "core" / "PRINCIPLES.md")

    def load_rules(self) -> str:
        """Load RULES.md"""
        return self.load_file(self.prompts_dir / "core" / "RULES.md")

    def load_role_prompt(self, role: str) -> str:
        """
        Load role-specific prompt (parent/teenager/child/grandparent)
        """
        role_file = self.prompts_dir / "roles" / f"{role}.md"
        return self.load_file(role_file)

    def load_skill_prompts(self, skills: List[str]) -> str:
        """Load and combine active skill prompts"""
        if not skills:
            return ""

        skill_prompts = []
        for skill in skills:
            skill_file = self.prompts_dir / "skills" / f"{skill}.md"
            content = self.load_file(skill_file)
            if content:
                skill_prompts.append(content)

        return "\n\n".join(skill_prompts) if skill_prompts else ""

    def load_language_context(self, language: str) -> str:
        """Load bilingual context"""
        # For now, return general bilingual context
        return self.load_file(
            self.prompts_dir / "languages" / "bilingual_context.md"
        )

    def inject_memory_context(
        self,
        memory_context: MemoryContext
    ) -> str:
        """Format memory context for prompt injection"""

        context_parts = []

        # Recent conversation context
        if memory_context.immediate_context:
            recent_messages = memory_context.immediate_context[:5]
            context_parts.append("## Recent Conversation Context\n")
            for msg in recent_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                context_parts.append(f"**{role}**: {content}\n")

        # User preferences
        if memory_context.user_preferences:
            context_parts.append("\n## User Preferences\n")
            for key, value in memory_context.user_preferences.items():
                context_parts.append(f"- {key}: {value}\n")

        # Relevant memories
        if memory_context.semantic_memories:
            context_parts.append("\n## Relevant Memories\n")
            for memory in memory_context.semantic_memories[:3]:
                content = memory.get("content", "")
                score = memory.get("score", 0)
                context_parts.append(
                    f"- (relevance: {score:.2f}) {content}\n"
                )

        return "".join(context_parts) if context_parts else ""

    def inject_user_context(self, user_context: UserContext) -> str:
        """Format user context for prompt injection"""

        return f"""
## Current User Context

**User ID**: {user_context.user_id}
**Role**: {user_context.role}
**Age Group**: {user_context.age_group or 'not specified'}
**Language Preference**: {user_context.language_preference}
**Privacy Level**: {user_context.privacy_level}
**Active Skills**: {', '.join(user_context.active_skills) if user_context.active_skills else 'none'}
"""

    def build(
        self,
        user_context: UserContext,
        memory_context: Optional[MemoryContext] = None,
        include_principles: bool = True,
        include_rules: bool = True
    ) -> str:
        """
        Assemble complete system prompt

        Assembly order:
        1. Core system prompt (FAMILY_ASSISTANT.md)
        2. Principles (optional, PRINCIPLES.md)
        3. Rules (optional, RULES.md)
        4. Role-specific behavior
        5. Active skills context
        6. Language/bilingual context
        7. User context
        8. Memory context
        """

        prompt_parts = []

        # 1. Core system prompt
        core_prompt = self.load_core_prompt()
        if core_prompt:
            prompt_parts.append(core_prompt)

        # 2. Principles (optional for brevity)
        if include_principles:
            principles = self.load_principles()
            if principles:
                prompt_parts.append("\n---\n")
                prompt_parts.append(principles)

        # 3. Rules (optional for brevity)
        if include_rules:
            rules = self.load_rules()
            if rules:
                prompt_parts.append("\n---\n")
                prompt_parts.append(rules)

        # 4. Role-specific behavior
        role_prompt = self.load_role_prompt(user_context.role)
        if role_prompt:
            prompt_parts.append("\n---\n")
            prompt_parts.append("# ACTIVE ROLE CONTEXT\n")
            prompt_parts.append(role_prompt)

        # 5. Active skills
        if user_context.active_skills:
            skills_prompt = self.load_skill_prompts(user_context.active_skills)
            if skills_prompt:
                prompt_parts.append("\n---\n")
                prompt_parts.append("# ACTIVE SKILLS\n")
                prompt_parts.append(skills_prompt)

        # 6. Language/bilingual context
        if user_context.language_preference in ["es", "bilingual"]:
            language_context = self.load_language_context(
                user_context.language_preference
            )
            if language_context:
                prompt_parts.append("\n---\n")
                prompt_parts.append("# LANGUAGE CONTEXT\n")
                prompt_parts.append(language_context)

        # 7. User context
        user_context_str = self.inject_user_context(user_context)
        prompt_parts.append("\n---\n")
        prompt_parts.append(user_context_str)

        # 8. Memory context
        if memory_context:
            memory_context_str = self.inject_memory_context(memory_context)
            if memory_context_str:
                prompt_parts.append("\n---\n")
                prompt_parts.append("# CONVERSATION CONTEXT\n")
                prompt_parts.append(memory_context_str)

        # Final assembly
        full_prompt = "".join(prompt_parts)

        return full_prompt

    def build_minimal(
        self,
        user_context: UserContext,
        memory_context: Optional[MemoryContext] = None
    ) -> str:
        """
        Build minimal prompt (core + role + memory only)
        For faster inference and lower token usage
        """

        prompt_parts = []

        # Core prompt (condensed)
        prompt_parts.append(self._get_condensed_core_prompt())

        # Role-specific behavior
        role_prompt = self.load_role_prompt(user_context.role)
        if role_prompt:
            prompt_parts.append("\n---\n")
            prompt_parts.append(role_prompt)

        # User context
        user_context_str = self.inject_user_context(user_context)
        prompt_parts.append("\n---\n")
        prompt_parts.append(user_context_str)

        # Memory context
        if memory_context:
            memory_context_str = self.inject_memory_context(memory_context)
            if memory_context_str:
                prompt_parts.append("\n---\n")
                prompt_parts.append(memory_context_str)

        return "".join(prompt_parts)

    def _get_condensed_core_prompt(self) -> str:
        """Condensed version of core prompt for minimal mode"""
        return """# Family Assistant

You are a family-centric AI assistant that helps families manage daily life with
intelligence, warmth, and cultural awareness.

Core Principles:
- Family-first: Privacy, safety, and respect
- Bilingual: Natural Spanish-English code-switching
- Role-aware: Adapt to user age and role
- Proactive: Anticipate needs, provide helpful suggestions
- Memory: Remember context across conversations

Always prioritize safety, privacy, and age-appropriate interactions.
"""

    def estimate_token_count(self, prompt: str) -> int:
        """
        Rough estimate of token count (1 token ≈ 4 characters)
        """
        return len(prompt) // 4

    def get_prompt_summary(self, prompt: str) -> Dict[str, Any]:
        """Get summary statistics about assembled prompt"""

        sections = prompt.split("---")

        return {
            "total_length": len(prompt),
            "estimated_tokens": self.estimate_token_count(prompt),
            "section_count": len(sections),
            "has_memory_context": "CONVERSATION CONTEXT" in prompt,
            "has_language_context": "LANGUAGE CONTEXT" in prompt,
            "has_skills": "ACTIVE SKILLS" in prompt
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_prompt_builder(prompts_dir: Optional[Path] = None) -> PromptBuilder:
    """Factory function to create PromptBuilder"""
    return PromptBuilder(prompts_dir=prompts_dir)


async def build_user_context_from_db(
    user_id: str,
    memory_manager
) -> UserContext:
    """
    Build UserContext from database profile

    Args:
        user_id: User ID
        memory_manager: MemoryManager instance for database access
    """

    # Get user profile from database
    profile = await memory_manager.get_user_profile(user_id)

    if not profile:
        # Default context if user not found
        return UserContext(
            user_id=user_id,
            role="parent",
            language_preference="en"
        )

    return UserContext(
        user_id=profile.get("id", user_id),
        role=profile.get("role", "parent"),
        age_group=profile.get("age_group"),
        language_preference=profile.get("language_preference", "en"),
        active_skills=profile.get("active_skills", []),
        privacy_level="family"
    )


async def assemble_full_prompt(
    user_id: str,
    conversation_id: str,
    memory_manager,
    query: Optional[str] = None,
    minimal: bool = False
) -> str:
    """
    Complete workflow to assemble system prompt

    Args:
        user_id: User ID
        conversation_id: Conversation ID
        memory_manager: MemoryManager instance
        query: Optional query for semantic memory search
        minimal: Use minimal prompt (faster, lower tokens)

    Returns:
        Assembled system prompt ready for LLM
    """

    # Build user context from database
    user_context = await build_user_context_from_db(user_id, memory_manager)

    # Get memory context
    memory_context = await memory_manager.get_context(
        user_id,
        conversation_id,
        query
    )

    # Build prompt
    prompt_builder = create_prompt_builder()

    if minimal:
        prompt = prompt_builder.build_minimal(user_context, memory_context)
    else:
        prompt = prompt_builder.build(user_context, memory_context)

    return prompt


# ============================================================================
# Testing and Debug Functions
# ============================================================================

def test_prompt_builder():
    """Test prompt builder with sample contexts"""

    # Create test user context
    user_context = UserContext(
        user_id="test-user-123",
        role="parent",
        age_group="adult",
        language_preference="es",
        active_skills=["calendar", "reminders"],
        privacy_level="family"
    )

    # Create test memory context
    memory_context = MemoryContext(
        user_id="test-user-123",
        conversation_id="test-conv-456",
        immediate_context=[
            {"role": "user", "content": "Hola, necesito ayuda con el calendario"},
            {"role": "assistant", "content": "¡Claro! ¿Qué necesitas agregar?"}
        ],
        user_preferences={"tone": "friendly", "verbosity": "concise"}
    )

    # Build prompt
    builder = create_prompt_builder()

    print("=" * 80)
    print("FULL PROMPT BUILD")
    print("=" * 80)

    full_prompt = builder.build(user_context, memory_context)
    summary = builder.get_prompt_summary(full_prompt)

    print(f"\nPrompt Summary:")
    print(f"  Length: {summary['total_length']} chars")
    print(f"  Estimated Tokens: {summary['estimated_tokens']}")
    print(f"  Sections: {summary['section_count']}")
    print(f"  Has Memory: {summary['has_memory_context']}")
    print(f"  Has Language Context: {summary['has_language_context']}")
    print(f"  Has Skills: {summary['has_skills']}")

    print("\n" + "=" * 80)
    print("MINIMAL PROMPT BUILD")
    print("=" * 80)

    minimal_prompt = builder.build_minimal(user_context, memory_context)
    minimal_summary = builder.get_prompt_summary(minimal_prompt)

    print(f"\nMinimal Prompt Summary:")
    print(f"  Length: {minimal_summary['total_length']} chars")
    print(f"  Estimated Tokens: {minimal_summary['estimated_tokens']}")
    print(f"  Token Reduction: {(1 - minimal_summary['estimated_tokens'] / summary['estimated_tokens']) * 100:.1f}%")

    print("\n" + "=" * 80)
    print("SAMPLE MINIMAL PROMPT")
    print("=" * 80)
    print(minimal_prompt[:1000])
    print("\n... (truncated) ...")


if __name__ == "__main__":
    test_prompt_builder()
