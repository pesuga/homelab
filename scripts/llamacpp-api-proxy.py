#!/usr/bin/env python3
"""
Simple proxy to convert OpenAI API format to llama.cpp completion API format
and provide concurrent inference capability.
"""

import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="llama.cpp API Proxy", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LLAMACPP_BASE_URL = "http://localhost:8080"

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

async def get_llamacpp_response(prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """Get response from llama.cpp server using completion endpoint."""

    # Try different endpoints that llama.cpp might support
    endpoints_to_try = [
        "/completion",
        "/api/completion",
        "/backend/completion",
        "/generate"
    ]

    for endpoint in endpoints_to_try:
        try:
            url = f"{LLAMACPP_BASE_URL}{endpoint}"

            payload = {
                "prompt": prompt,
                "n_predict": max_tokens,
                "temperature": temperature,
                "stop": ["<dummy32000>"]
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "").strip()
                    if content:
                        return content

        except Exception as e:
            logger.debug(f"Failed to use endpoint {endpoint}: {e}")
            continue

    raise HTTPException(status_code=500, detail="Could not connect to llama.cpp server")

def format_chat_to_prompt(messages: List[Message]) -> str:
    """Convert OpenAI chat format to llama.cpp prompt format."""
    prompt = ""
    for msg in messages:
        if msg.role == "system":
            prompt += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
        elif msg.role == "user":
            prompt += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
        elif msg.role == "assistant":
            prompt += f"<|im_start|>assistant\n{msg.content}<|im_end|>\n"

    prompt += "<|im_start|>assistant\n"
    return prompt

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """OpenAI-compatible chat completions endpoint."""

    # Convert chat messages to prompt
    prompt = format_chat_to_prompt(request.messages)

    try:
        # Get response from llama.cpp
        content = await get_llamacpp_response(
            prompt=prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        # Format response as OpenAI-compatible
        return ChatCompletionResponse(
            id="chatcmpl-" + str(asyncio.get_event_loop().time()),
            created=int(asyncio.get_event_loop().time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(prompt.split()) + len(content.split())
            }
        )

    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": "mistral-7b-openorca",
                "object": "model",
                "created": 1698729600,
                "owned_by": "local"
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)