#!/usr/bin/env python3
"""Test script for llama.cpp integration with Family Assistant."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from agents.llamacpp_client import ChatllamaCPP
from langchain_core.messages import HumanMessage, SystemMessage


async def test_llamacpp_connection():
    """Test connection to llama.cpp service."""
    print("Testing llama.cpp connection...")
    print(f"Base URL: {settings.llamacpp_base_url}")
    print(f"Model: {settings.llamacpp_model}")

    # Test basic health check
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.llamacpp_base_url}/health")
            if response.status_code == 200:
                print("✅ llama.cpp service is healthy")
                data = response.json()
                print(f"   Status: {data.get('status')}")
            else:
                print(f"❌ Service returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False

    return True


def test_llamacpp_client():
    """Test llama.cpp LangChain client."""
    print("\nTesting llama.cpp LangChain client...")

    try:
        # Initialize the client
        llm = ChatllamaCPP(
            base_url=settings.llamacpp_base_url,
            model=settings.llamacpp_model,
            temperature=settings.llamacpp_temperature,
            max_tokens=settings.llamacpp_max_tokens
        )

        print(f"✅ Client initialized successfully")
        print(f"   Base URL: {llm.base_url}")
        print(f"   Model: {llm.model}")
        print(f"   Temperature: {llm.temperature}")
        print(f"   Max Tokens: {llm.max_tokens}")

        # Test a simple completion
        print("\nTesting simple completion...")
        test_message = "Hello! Please say 'Integration test successful' in your response."
        response = llm.invoke([HumanMessage(content=test_message)])

        print(f"✅ Completion successful!")
        print(f"   Response: {response[:100]}..." if len(response) > 100 else f"   Response: {response}")

        return True

    except Exception as e:
        print(f"❌ Error with llama.cpp client: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that old ollama settings still work."""
    print("\nTesting backward compatibility...")

    try:
        # These should map to llama.cpp values
        assert settings.ollama_base_url == settings.llamacpp_base_url
        assert settings.ollama_model == settings.llamacpp_model
        assert settings.ollama_temperature == settings.llamacpp_temperature
        assert settings.ollama_max_tokens == settings.llamacpp_max_tokens

        print("✅ Backward compatibility working")
        print(f"   ollama_base_url -> {settings.ollama_base_url}")
        print(f"   ollama_model -> {settings.ollama_model}")
        return True

    except Exception as e:
        print(f"❌ Backward compatibility error: {e}")
        return False


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Family Assistant - llama.cpp Integration Test")
    print("=" * 60)

    # Test 1: Connection
    connection_ok = await test_llamacpp_connection()
    if not connection_ok:
        print("\n❌ Connection test failed. Please check:")
        print("   - llama.cpp service is running at http://localhost:8080")
        print("   - Model is fully loaded")
        return False

    # Test 2: Client
    client_ok = test_llamacpp_client()
    if not client_ok:
        print("\n❌ Client test failed.")
        return False

    # Test 3: Backward Compatibility
    compat_ok = test_backward_compatibility()
    if not compat_ok:
        print("\n❌ Backward compatibility test failed.")
        return False

    print("\n" + "=" * 60)
    print("🎉 All tests passed! llama.cpp integration is ready!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)