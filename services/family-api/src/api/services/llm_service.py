import httpx
import logging
import json
import os
import glob
import re
import time
from typing import Dict, Any, Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM backend (llama.cpp) with comprehensive logging."""

    def __init__(self):
        self.base_url = settings.llamacpp_base_url
        print(f"DEBUG: LLMService initialized with base_url={self.base_url}")
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

    async def chat(self, message: str, user_id: str, thread_id: str, user_profile: dict = None,
                   request_start_time: float = None) -> Dict:
        """
        Send a chat message to the LLM and get a response with comprehensive logging.
        """
        # Start timing if not provided
        if request_start_time is None:
            request_start_time = time.time()

        # Initialize logging data
        chat_start_time = time.time()
        performance_data = {}
        memory_context = {}

        try:
            # Get memory manager and time it
            memory_start = time.time()
            memory_manager = await self._get_memory_manager()
            performance_data["memory_manager_init_ms"] = (time.time() - memory_start) * 1000

            # Import prompt builder here to avoid circular imports if any
            from api.services.prompt_builder import assemble_full_prompt

            # Generate dynamic system prompt and time it
            prompt_start = time.time()
            system_prompt = await assemble_full_prompt(
                user_id=user_id,
                conversation_id=thread_id,
                memory_manager=memory_manager,
                query=message, # Use message as query for semantic search
                minimal=False
            )
            performance_data["prompt_assembly_ms"] = (time.time() - prompt_start) * 1000

            # Build request payload
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

            # Prepare request data for logging
            request_data = {
                "endpoint": "/v1/chat/completions",
                "model": self.model,
                "user_message": message,
                "system_prompt": system_prompt,
                "memory_context": {
                    "memories_used": memory_context.get("memories_used", 0),
                    "recent_conversations": memory_context.get("recent_conversations", 0),
                    "user_preferences": memory_context.get("user_preferences", {})
                },
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 1024,
                    "stream": False
                }
            }

            # Make HTTP request and time it
            http_start = time.time()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                print(f"DEBUG: Sending request to {self.base_url}/v1/chat/completions")
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            performance_data["http_request_ms"] = (time.time() - http_start) * 1000

            chat_end_time = time.time()
            performance_data["total_latency_ms"] = (chat_end_time - chat_start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']

                # Extract token usage if available
                token_usage = data.get("usage", {})
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)
                total_tokens = token_usage.get("total_tokens", 0)

                # Prepare response data for logging
                response_data = {
                    "llm_response": content,
                    "finish_reason": data['choices'][0].get('finish_reason', 'stop'),
                    "model_used": self.model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }

                # Calculate generation time
                if total_tokens > 0:
                    generation_time = chat_end_time - http_start
                    performance_data["generation_ms"] = generation_time * 1000
                    performance_data["tokens_per_second"] = completion_tokens / generation_time if generation_time > 0 else 0

                # Log the chat session
                await self._log_chat_session(
                    thread_id=thread_id,
                    user_id=user_id,
                    user_profile=user_profile or {},
                    request_data=request_data,
                    response_data=response_data,
                    performance_data=performance_data,
                    system_prompt=system_prompt,
                    memory_context=memory_context,
                    request_start_time=request_start_time,
                    chat_end_time=chat_end_time
                )

                # Return content AS IS, including <thinking> tags
                return {
                    "response": content,
                    "memories_used": memory_context.get("memories_used", 0),
                    "token_usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens
                    },
                    "performance": performance_data
                }
            else:
                error_msg = f"LLM Error: {response.status_code} - {response.text}"
                print(error_msg)

                # Log error response
                response_data = {
                    "error": True,
                    "error_type": "llm_api_error",
                    "error_message": error_msg,
                    "status_code": response.status_code,
                    "response_text": response.text
                }

                await self._log_chat_session(
                    thread_id=thread_id,
                    user_id=user_id,
                    user_profile=user_profile or {},
                    request_data=request_data,
                    response_data=response_data,
                    performance_data=performance_data,
                    system_prompt=system_prompt,
                    memory_context=memory_context,
                    request_start_time=request_start_time,
                    chat_end_time=chat_end_time
                )

                return {
                    "response": "I'm having trouble thinking right now. Please try again later.",
                    "error": error_msg,
                    "error_type": "llm_api_error",
                    "memories_used": memory_context.get("memories_used", 0),
                    "performance": performance_data
                }

        except httpx.HTTPError as e:
            error_msg = f"HTTP error in LLM chat: {str(e)}"
            logger.error(error_msg)

            # Log error
            await self._log_error_session(
                thread_id=thread_id,
                user_id=user_id,
                user_profile=user_profile or {},
                error_type="http_error",
                error_message=str(e),
                request_start_time=request_start_time
            )

            return {
                "response": "I'm having trouble connecting to the language model. Please try again later.",
                "error": error_msg,
                "error_type": "http_error",
                "memories_used": memory_context.get("memories_used", 0)
            }

        except httpx.ConnectError as e:
            error_msg = f"Connection error to LLM service: {str(e)}"
            logger.error(error_msg)

            # Log error
            await self._log_error_session(
                thread_id=thread_id,
                user_id=user_id,
                user_profile=user_profile or {},
                error_type="connection_error",
                error_message=str(e),
                request_start_time=request_start_time
            )

            return {
                "response": "Unable to connect to the language model service. Please try again later.",
                "error": error_msg,
                "error_type": "connection_error",
                "memories_used": memory_context.get("memories_used", 0)
            }

        except Exception as e:
            error_msg = f"Error in LLM chat: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Log error
            await self._log_error_session(
                thread_id=thread_id,
                user_id=user_id,
                user_profile=user_profile or {},
                error_type="unknown_error",
                error_message=str(e),
                request_start_time=request_start_time
            )

            return {
                "response": "I encountered an error while processing your request.",
                "error": error_msg,
                "error_type": "unknown_error",
                "memories_used": memory_context.get("memories_used", 0)
            }

    async def _log_chat_session(self, thread_id: str, user_id: str, user_profile: Dict[str, Any],
                               request_data: Dict[str, Any], response_data: Dict[str, Any],
                               performance_data: Dict[str, Any], system_prompt: str,
                               memory_context: Dict[str, Any], request_start_time: float,
                               chat_end_time: float):
        """Log a successful chat session."""
        try:
            from api.services.chat_logger import get_chat_logger
            chat_logger = await get_chat_logger()

            await chat_logger.log_chat_session(
                thread_id=thread_id,
                user_id=user_id,
                user_profile=user_profile,
                request_data=request_data,
                response_data=response_data,
                performance_data=performance_data,
                system_prompt=system_prompt,
                memory_context=memory_context,
                start_time=request_start_time,
                end_time=chat_end_time
            )
        except Exception as e:
            logger.error(f"Failed to log chat session: {e}", exc_info=True)

    async def _log_error_session(self, thread_id: str, user_id: str, user_profile: Dict[str, Any],
                               error_type: str, error_message: str, request_start_time: float):
        """Log a failed chat session."""
        try:
            from api.services.chat_logger import get_chat_logger
            chat_logger = await get_chat_logger()

            response_data = {
                "error": True,
                "error_type": error_type,
                "error_message": error_message,
                "llm_response": "Error occurred during processing"
            }

            await chat_logger.log_chat_session(
                thread_id=thread_id,
                user_id=user_id,
                user_profile=user_profile,
                request_data={"error_context": error_type},
                response_data=response_data,
                performance_data={},
                system_prompt="",
                memory_context={},
                start_time=request_start_time,
                end_time=time.time()
            )
        except Exception as e:
            logger.error(f"Failed to log error session: {e}", exc_info=True)