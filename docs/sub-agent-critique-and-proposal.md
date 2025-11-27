# Critique & Revised Proposal: Skill-Based Sub-Agent Architecture

## Part 1: Critique of Original Specification

### 1. Architectural Mismatch: Router vs. Orchestrator
*   **Original Spec**: Proposed a **Router-based** architecture (`IntentClassifier` -> `SubAgent`). In this model, the user is handed off entirely to a specialized agent (e.g., the "Calendar Agent").
*   **User Goal**: You stated: *"The main agent (orchestrator) should only focus on its personality... When it needs something external... it could ask a sub-agent."*
*   **The Problem**: The Router model bypasses the Main Agent. If the user says "Hey Jarvis, check my calendar and tell me a joke about it," the Router sends this to the Calendar Agent. The Calendar Agent (optimized for efficiency) likely lacks the "Jarvis" personality and the "joke" skill. The Main Agent is cut out of the loop.

### 2. Local LLM Efficiency & Latency
*   **Original Spec**: Suggests "Pre-loaded skill prompts (5-10K tokens each)" for multiple agents.
*   **The Problem**: In a local environment (e.g., single GPU), "pre-loading" multiple distinct system prompts into the KV Cache is memory-intensive.
    *   If you have 1 active slot: Switching from Main Agent -> Calendar Agent requires re-processing the entire Calendar system prompt (latency spike).
    *   If you have multiple slots: It consumes significant VRAM (e.g., 4 agents * 5k tokens = 20k tokens of KV cache), reducing space for the actual conversation.

### 3. Complexity Overhead
*   **Original Spec**: Proposes a complex `SubAgentManager`, `IntentClassifier` (100 tokens), and `TokenBudgetManager`.
*   **The Problem**: This adds significant engineering complexity. Managing state handoffs between agents (e.g., if the user switches topics mid-chat) is notoriously difficult in Router architectures.

---

## Part 2: Revised Proposal - "Main Agent as Orchestrator"

### Core Concept
Instead of *routing* the user away, the **Main Agent remains the single point of contact**. Sub-agents are treated exactly like **MCP Tools**. The Main Agent "calls" a sub-agent just like it calls a calculator.

### Architecture Diagram

```mermaid
graph TD
    User[User] --> Main[Main Agent (Orchestrator)]
    Main -->|Maintains Personality & Context| Main
    
    subgraph "MCP Tool Layer"
        Main -- "call_tool(query_calendar)" --> CalAgent[Calendar Sub-Agent]
        Main -- "call_tool(query_health)" --> HealthAgent[Health Sub-Agent]
        Main -- "call_tool(query_homework)" --> EduAgent[Homework Sub-Agent]
    end
    
    subgraph "Execution"
        CalAgent -->|Executes| CalTools[Calendar MCP Tools]
        HealthAgent -->|Executes| MedTools[Medical MCP Tools]
    end
    
    CalAgent -->|Returns Summary| Main
    Main -->|Synthesizes Response| User
```

### Key Changes & Benefits

#### 1. Token Efficiency via "Just-in-Time" Context
*   **Main Agent**: Has a lightweight system prompt (Personality + General Instructions). It does *not* know how to *manage* a calendar, only that it *can* ask the Calendar Agent.
*   **Sub-Agents**: Their heavy prompts (5k+ tokens) are only loaded **ephemerally** when called.
    *   *Optimization*: For local LLMs, you can run sub-agents as simple "chains" that execute and die, or keep them warm if VRAM permits.
    *   *Result*: The Main Agent's context window remains clean. It only sees the *result* from the sub-agent (e.g., "Meeting created for 2 PM"), not the 50 steps and tool definitions it took to get there.

#### 2. "Sub-Agents as Tools" Pattern
The Main Agent sees a tool definition like this:

```json
{
  "name": "consult_calendar_expert",
  "description": "Ask the calendar specialist to view, create, or manage events. Use this for complex scheduling queries.",
  "input_schema": {
    "type": "object",
    "properties": {
      "request": { "type": "string", "description": "Natural language request for the calendar agent" }
    }
  }
}
```

When the Main Agent calls this tool, the system (middleware):
1.  Instantiates the **Calendar Sub-Agent** (with its specific prompt and tools).
2.  Passes the `request`.
3.  The Sub-Agent thinks, calls its own granular tools (`add_event`, `check_availability`), and formulates a final answer.
4.  The system returns that answer to the Main Agent as the "tool output".

#### 3. Simplified State Management
*   The Main Agent holds the conversation history.
*   Sub-agents don't need to know about the user's life story, only the specific request passed to them. This drastically reduces the context they need to process.

### Technology Stack Adjustments

*   **Orchestration**: **LangGraph** is perfect for this. The Main Agent is the root node. Sub-agents are subgraph nodes.
*   **Interface**: The Main Agent is the only one exposing an API to the frontend.
*   **Memory**:
    *   **Main Agent**: Access to "User Profile" and "Conversation History".
    *   **Sub-Agents**: Access to "Domain Knowledge" (e.g., homework docs) and "Task-Specific Memory" (e.g., current scheduling constraints).

### Comparison

| Feature | Original (Router) | Revised (Orchestrator) |
| :--- | :--- | :--- |
| **User Experience** | Fragmented (talks to different bots) | Unified (talks to one persona) |
| **Personality** | Hard to maintain across agents | Centralized in Main Agent |
| **Token Cost** | Low (if routed correctly) | **Lowest** (Main Agent context is minimal; Sub-agent context is ephemeral) |
| **Latency** | High (context switching) | Medium (sub-agent execution time) |
| **Complexity** | High (handoffs, state sync) | Medium (standard tool calling pattern) |

### Recommendation
Adopt the **Orchestrator Pattern**. It aligns perfectly with your request for a "Main Agent" that focuses on personality while offloading heavy lifting to specialized, token-efficient sub-agents via the MCP protocol.
