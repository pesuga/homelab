"""llama.cpp client compatible with LangChain ChatOllama interface."""

import httpx
from typing import Dict, Any, List, Optional
from langchain_core.language_models.llms import BaseLLM
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from pydantic import Field
import json


class ChatllamaCPP(BaseLLM):
    """llama.cpp client compatible with LangChain ChatOllama interface."""

    base_url: str = "http://localhost:8080"
    model: str = "Kimi-VL-A3B-Thinking-2506-Q4_K_M"
    temperature: float = 0.7
    max_tokens: int = 2048
    streaming: bool = False

    def __init__(self, **kwargs):
        """Initialize the llama.cpp client."""
        super().__init__(**kwargs)

    @property
    def _llm_type(self) -> str:
        """Return type identifier."""
        return "llamacpp"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """Generate response using llama.cpp completion API."""
        # Convert LangChain messages to llama.cpp format
        prompt = self._convert_messages_to_prompt(messages)

        # Prepare request payload
        payload = {
            "prompt": prompt,
            "n_predict": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "stop": stop or [],
            "stream": False,
        }

        # Make API request
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/completion", json=payload)
                response.raise_for_status()
                result = response.json()

                # Extract content from llama.cpp response
                if "content" in result:
                    return result["content"]
                else:
                    return ""

        except httpx.RequestError as e:
            raise Exception(f"Error calling llama.cpp API: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> str:
        """Async version of generate."""
        # Convert LangChain messages to llama.cpp format
        prompt = self._convert_messages_to_prompt(messages)

        # Prepare request payload
        payload = {
            "prompt": prompt,
            "n_predict": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "stop": stop or [],
            "stream": False,
        }

        # Make API request
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.base_url}/completion", json=payload)
                response.raise_for_status()
                result = response.json()

                # Extract content from llama.cpp response
                if "content" in result:
                    return result["content"]
                else:
                    return ""

        except httpx.RequestError as e:
            raise Exception(f"Error calling llama.cpp API: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert LangChain messages to llama.cpp prompt format."""
        prompt_parts = []

        for message in messages:
            if isinstance(message, SystemMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            else:
                # Default handling for other message types
                prompt_parts.append(str(message.content))

        return "\n".join(prompt_parts)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters for caching."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _get_parameters(self) -> Dict[str, Any]:
        """Get model parameters."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "model": self.model,
            "base_url": self.base_url,
        }