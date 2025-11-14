"""Memory-enabled agent with LangGraph + Mem0 integration."""

import httpx
import json
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config.settings import settings


class AgentState(TypedDict):
    """State for the family assistant agent."""
    messages: List[Dict[str, str]]
    user_id: str
    user_profile: Optional[Dict[str, Any]]
    memories: List[Dict[str, Any]]
    context: str


class FamilyAssistantAgent:
    """Main family assistant agent with memory capabilities."""

    def __init__(self):
        """Initialize the agent with LLM and checkpointer."""
        # Initialize Ollama LLM
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=settings.ollama_temperature
        )

        # Initialize PostgreSQL checkpointer
        # Note: PostgresSaver.from_conn_string returns a context manager
        # We'll handle setup in the graph compilation
        self.checkpointer = None

        # Build agent graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve_memory", self._retrieve_memory)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("store_memory", self._store_memory)

        # Define edges
        workflow.set_entry_point("retrieve_memory")
        workflow.add_edge("retrieve_memory", "generate_response")
        workflow.add_edge("generate_response", "store_memory")
        workflow.add_edge("store_memory", END)

        # Compile without checkpointer for now (will add in Phase 2)
        # Memory is handled by Mem0 + PostgreSQL conversation_history
        return workflow.compile()

    async def _retrieve_memory(self, state: AgentState) -> AgentState:
        """Retrieve relevant memories from Mem0."""
        user_id = state["user_id"]
        last_message = state["messages"][-1]["content"]

        try:
            # Search Mem0 for relevant memories
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.mem0_api_url}/v1/memories/search/",
                    json={
                        "query": last_message,
                        "user_id": user_id,
                        "limit": 5
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    memories = response.json()
                    state["memories"] = memories if memories else []

                    # Format memories as context
                    if memories:
                        context = "Relevant information from previous conversations:\n"
                        context += "\n".join([f"- {m.get('memory', m)}" for m in memories])
                        state["context"] = context
                    else:
                        state["context"] = "No previous conversation history found."
                else:
                    state["memories"] = []
                    state["context"] = "No previous conversation history found."

        except Exception as e:
            print(f"Error retrieving memory: {e}")
            state["memories"] = []
            state["context"] = "No previous conversation history found."

        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate response using Ollama with memory context."""
        messages = state["messages"]
        context = state.get("context", "")
        user_profile = state.get("user_profile", {})

        # Build system prompt with context
        system_prompt = f"""You are a helpful family AI assistant with memory of previous conversations.

{context}

User Profile:
- Name: {user_profile.get('name', 'Unknown')}
- Role: {user_profile.get('role', 'Unknown')}
- Age: {user_profile.get('age', 'Unknown')}

Please respond naturally, using the context from previous conversations when relevant.
Be friendly, helpful, and respectful of the user's role and permissions."""

        # Convert messages to LangChain format
        lc_messages = [SystemMessage(content=system_prompt)]

        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))

        # Generate response
        try:
            response = await self.llm.ainvoke(lc_messages)
            assistant_message = {
                "role": "assistant",
                "content": response.content
            }
            state["messages"].append(assistant_message)
        except Exception as e:
            print(f"Error generating response: {e}")
            error_message = {
                "role": "assistant",
                "content": "I apologize, but I encountered an error processing your request. Please try again."
            }
            state["messages"].append(error_message)

        return state

    async def _store_memory(self, state: AgentState) -> AgentState:
        """Store conversation in Mem0."""
        user_id = state["user_id"]
        messages = state["messages"]

        try:
            # Store last 2 messages (user + assistant)
            recent_messages = messages[-2:] if len(messages) >= 2 else messages

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.mem0_api_url}/v1/memories/",
                    json={
                        "messages": [
                            {"role": msg["role"], "content": msg["content"]}
                            for msg in recent_messages
                        ],
                        "user_id": user_id
                    },
                    timeout=10.0
                )
        except Exception as e:
            print(f"Error storing memory: {e}")

        return state

    async def chat(
        self,
        message: str,
        user_id: str,
        thread_id: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chat with the agent.

        Args:
            message: User message
            user_id: User identifier
            thread_id: Conversation thread ID
            user_profile: User profile information

        Returns:
            Dict containing the response and metadata
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "user_profile": user_profile or {},
            "memories": [],
            "context": ""
        }

        # Configuration (checkpointing disabled for Phase 1)
        config = {}

        # Run the agent
        try:
            final_state = await self.graph.ainvoke(initial_state, config)

            # Extract response
            assistant_message = final_state["messages"][-1]

            return {
                "response": assistant_message["content"],
                "memories_used": len(final_state.get("memories", [])),
                "thread_id": thread_id,
                "user_id": user_id
            }

        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "error": str(e),
                "thread_id": thread_id,
                "user_id": user_id
            }


# Global agent instance
agent = FamilyAssistantAgent()
