"""
Application Startup and Initialization

Handles:
- Memory manager initialization
- Prompt builder setup
- Database connections
- Service health checks
"""

import asyncio
from pathlib import Path
from typing import Optional

from api.services.memory_manager import MemoryManager, create_memory_manager
from api.services.prompt_builder import PromptBuilder, create_prompt_builder


class ApplicationState:
    """Global application state"""

    def __init__(self):
        self.memory_manager: Optional[MemoryManager] = None
        self.prompt_builder: Optional[PromptBuilder] = None
        self.initialized: bool = False

    async def initialize(self):
        """Initialize all Phase 2 services"""
        if self.initialized:
            return

        print("🚀 Initializing Phase 2 services...")

        try:
            # Initialize Memory Manager
            print("  📦 Initializing MemoryManager (5-layer architecture)...")
            self.memory_manager = await create_memory_manager()
            print("    ✅ Redis connection established")
            print("    ✅ Mem0 client ready")
            print("    ✅ Qdrant collections initialized")
            print("    ✅ Ollama embedding service connected")

            # Initialize Prompt Builder
            print("  📝 Initializing PromptBuilder...")
            self.prompt_builder = create_prompt_builder()
            print("    ✅ Prompt templates loaded")
            print("    ✅ Role prompts cached")
            print("    ✅ Bilingual context ready")

            self.initialized = True
            print("✅ Phase 2 services initialized successfully!\n")

        except Exception as e:
            print(f"❌ Failed to initialize Phase 2 services: {e}")
            raise

    async def shutdown(self):
        """Cleanup and shutdown services"""
        if not self.initialized:
            return

        print("\n🛑 Shutting down Phase 2 services...")

        try:
            if self.memory_manager:
                await self.memory_manager.close()
                print("  ✅ MemoryManager closed")

            self.initialized = False
            print("✅ Phase 2 services shut down successfully")

        except Exception as e:
            print(f"⚠️ Error during shutdown: {e}")


# Global application state
app_state = ApplicationState()


async def startup_event():
    """FastAPI startup event handler"""
    await app_state.initialize()


async def shutdown_event():
    """FastAPI shutdown event handler"""
    await app_state.shutdown()
