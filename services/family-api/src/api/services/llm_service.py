import httpx
import logging
import json
import os
import glob
import re
from typing import Dict, Any, Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM backend (llama.cpp)."""

    def __init__(self):
        self.base_url = settings.llamacpp_base_url
        self.model = settings.llamacpp_model
        self.timeout = 60.0  # Seconds
        # Initialize managers lazily or via dependency injection pattern if possible
        # For now, we'll create them when needed or rely on the global instances if we were inside a route
        # But since this is a service class, we might need to instantiate them.
        # However, MemoryManager needs async init. We'll handle this in the chat method.
        self.memory_manager = None

    async def _get_memory_manager(self):
        """Get or create memory manager."""
        if not self.memory_manager:
            from api.services.memory_manager import create_memory_manager
            self.memory_manager = await create_memory_manager()
        return self.memory_manager

    async def chat(self, message: str, user_id: str, thread_id: str, user_profile: dict = None) -> Dict:
        """
        Send a chat message to the LLM and get a response.
        """
        try:
            # Get memory manager
            memory_manager = await self._get_memory_manager()
            
            # Import prompt builder here to avoid circular imports if any
            from api.services.prompt_builder import assemble_full_prompt
            
            # Generate dynamic system prompt
            # We use the user_id to fetch the real profile and context
            system_prompt = await assemble_full_prompt(
                user_id=user_id,
                conversation_id=thread_id,
                memory_manager=memory_manager,
                query=message, # Use message as query for semantic search
                minimal=False
            )

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
                "stream": False
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Return content AS IS, including <think> tags
                    return {
                        "response": content,
                        "memories_used": 0  # Placeholder, could be updated if we track this from PromptBuilder
                    }
                else:
                    print(f"LLM Error: {response.status_code} - {response.text}")
                    return {
                        "response": "I'm having trouble thinking right now. Please try again later.",
                        "memories_used": 0
                    }
                    
        except Exception as e:
            logger.error(f"Error in LLM chat: {str(e)}")
            return {
                "response": "I encountered an error while processing your request.",
                "error": str(e),
                "memories_used": 0
            }
