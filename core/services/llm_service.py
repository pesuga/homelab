"""
LLM Service

Integration with Ollama for local LLM inference with family context support.
"""

import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5-coder:14b"
    timeout: int = 60
    max_tokens: int = 2048
    temperature: float = 0.7

class LLMMessage(BaseModel):
    role: str  # system, user, assistant
    content: str
    family_context: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    response_time: float
    family_member: Optional[str] = None

class LLMService:
    """Service for LLM interactions with family context awareness."""

    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )

    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def _build_system_prompt(self, family_context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt with family context."""
        base_prompt = """You are a helpful AI assistant for a family. You are:

🏠 **FAMILY AI ASSISTANT**
- Private, trustworthy, and family-safe
- Supportive of bilingual families (Spanish/English)
- Respectful of family values and parental guidance
- Focused on helpful, educational, and positive interactions

🌟 **YOUR ROLE**
- Provide helpful assistance for daily family life
- Support learning and education
- Help with organization and planning
- Be supportive and understanding

💬 **COMMUNICATION STYLE**
- Use clear, simple language appropriate for all family members
- Be warm, friendly, and patient
- Adapt to the user's age and role in the family
- Support both Spanish and English naturally"""

        if not family_context:
            return base_prompt

        # Add family-specific context
        family_name = family_context.get("family_name", "the family")
        primary_language = family_context.get("primary_language", "es")
        member_role = family_context.get("member_role", "parent")
        member_name = family_context.get("member_name", "")

        context_prompt = f"""

👥 **FAMILY CONTEXT**
- Family: {family_name}
- Speaking to: {member_name} ({member_role})
- Primary Language: {primary_language}
- Bilingual Support: Spanish/English"""

        # Add role-specific guidance
        if member_role == "parent":
            context_prompt += """
🎯 **FOR PARENTS**
- Provide practical parenting advice when requested
- Offer educational support for children
- Help with family organization and scheduling
- Respect parental authority and decisions"""

        elif member_role == "teenager":
            context_prompt += """
🎯 **FOR TEENAGERS**
- Be relatable and understanding
- Support homework and learning
- Offer advice on personal development
- Respect their growing independence"""

        elif member_role == "child":
            context_prompt += """
🎯 **FOR CHILDREN**
- Use simple, clear language
- Be encouraging and positive
- Help with learning and curiosity
- Ensure safety and appropriateness"""

        elif member_role == "grandparent":
            context_prompt += """
🎯 **FOR GRANDPARENTS**
- Be respectful and warm
- Support intergenerational connections
- Help with technology questions
- Honor their wisdom and experience"""

        return base_prompt + context_prompt

    def _format_messages(
        self,
        messages: List[LLMMessage],
        family_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Format messages for Ollama API."""
        formatted = []

        # Add system prompt first
        system_prompt = self._build_system_prompt(family_context)
        formatted.append({"role": "system", "content": system_prompt})

        # Add conversation history
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })

        return formatted

    async def generate(
        self,
        messages: List[LLMMessage],
        family_context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Generate response from LLM."""
        import time
        start_time = time.time()

        try:
            # Format messages for API
            formatted_messages = self._format_messages(messages, family_context)

            # Prepare request
            payload = {
                "model": model or self.config.default_model,
                "messages": formatted_messages,
                "stream": stream,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }

            # Make request
            response = await self.client.post(
                "/api/chat",
                json=payload
            )

            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")

                return LLMResponse(
                    content=content,
                    model=model or self.config.default_model,
                    usage=data.get("usage", {}),
                    response_time=response_time,
                    family_member=family_context.get("member_name") if family_context else None
                )
            else:
                logger.error(f"LLM request failed: {response.status_code} - {response.text}")
                raise Exception(f"LLM service error: {response.status_code}")

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def generate_simple(
        self,
        prompt: str,
        family_context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> str:
        """Simple prompt-response generation."""
        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.generate(messages, family_context, model)
        return response.content

    async def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available."""
        try:
            response = await self.client.post("/api/show", json={"name": model})
            return response.status_code == 200
        except:
            return False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()