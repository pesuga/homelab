"""Test script for the family assistant agent."""

import asyncio
import httpx


async def test_chat():
    """Test chat functionality."""
    base_url = "http://localhost:8001"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: First conversation
        print("\n🧪 Test 1: First conversation with memory storage")
        print("=" * 60)

        response = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Hi! My name is John and I love Python programming.",
                "user_id": "dad"
            }
        )

        result = response.json()
        print(f"User: Hi! My name is John and I love Python programming.")
        print(f"Assistant: {result['response']}")
        print(f"Thread ID: {result['thread_id']}")
        print(f"Memories used: {result['memories_used']}")

        thread_id = result['thread_id']

        # Wait for Mem0 to process
        print("\n⏳ Waiting 3 seconds for memory to be stored...")
        await asyncio.sleep(3)

        # Test 2: Second conversation should remember the first
        print("\n🧪 Test 2: Second conversation with memory retrieval")
        print("=" * 60)

        response = await client.post(
            f"{base_url}/chat",
            json={
                "message": "What's my name and what do I like?",
                "user_id": "dad",
                "thread_id": thread_id
            }
        )

        result = response.json()
        print(f"User: What's my name and what do I like?")
        print(f"Assistant: {result['response']}")
        print(f"Memories used: {result['memories_used']}")

        # Test 3: New conversation in new thread
        print("\n🧪 Test 3: New thread, agent should still remember from Mem0")
        print("=" * 60)

        response = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Do you remember me?",
                "user_id": "dad"
            }
        )

        result = response.json()
        print(f"User: Do you remember me?")
        print(f"Assistant: {result['response']}")
        print(f"Thread ID: {result['thread_id']} (new thread)")
        print(f"Memories used: {result['memories_used']}")

        # Test 4: Get conversation history
        print("\n🧪 Test 4: Retrieve conversation history")
        print("=" * 60)

        response = await client.get(
            f"{base_url}/conversations/{thread_id}",
            params={"user_id": "dad"}
        )

        history = response.json()
        print(f"Conversation history for thread {thread_id}:")
        for msg in history['messages']:
            print(f"  [{msg['role']}]: {msg['content'][:60]}...")

        print("\n✅ All tests completed successfully!")


async def test_health():
    """Test health check."""
    print("\n🏥 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/health")
        print(f"Health check: {response.json()}")


async def test_user_profile():
    """Test user profile retrieval."""
    print("\n👤 Testing user profile...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/users/dad")
        profile = response.json()
        print(f"User profile: {profile['name']} ({profile['role']})")
        print(f"Permissions: {profile['permissions']}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 Family Assistant Agent Test Suite")
    print("=" * 60)

    try:
        await test_health()
        await test_user_profile()
        await test_chat()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
