# Skill-Based Sub-Agent Architecture for Token-Efficient Family Assistant

## Executive Summary

This document outlines a comprehensive solution for implementing specialized sub-agents within the existing family assistant system to achieve 80-85% token reduction while maintaining full functionality through MCP tool integration. The architecture leverages the existing robust infrastructure (MCP system, five-layer memory, FastAPI routing) and introduces skill-based specialized agents with just-in-time context injection.

## Problem Statement

The current family assistant system loads full context (20K+ tokens) for every request, including all skill prompts, tool descriptions, and memory layers. This results in:
- High token costs for every interaction
- Slow response times due to large context processing
- Inefficient resource utilization
- Limited scalability for complex multi-user family scenarios

## Proposed Solution: Skill-Based Sub-Agent Architecture

### Core Architecture

```
Main Family Assistant (Core Agent)
├── Intent Classification Router (100 tokens)
├── Calendar Sub-Agent + Calendar MCP Tools
├── Reminders Sub-Agent + Reminders MCP Tools
├── Homework Sub-Agent + Educational MCP Tools
├── Health Sub-Agent + Medical MCP Tools
└── General Conversation (no tools)
```

### Token Efficiency Gains

- **Current System**: 20K+ tokens per request
- **Sub-Agent System**: 3K tokens per request (85% reduction)
- **Skill Context**: Pre-loaded once per agent session
- **Tool Descriptions**: 60% smaller (domain-specific)

## Technology Stack

### Core Framework
- **Orchestration**: LangGraph (stateful multi-agent workflows)
- **API**: FastAPI (existing infrastructure)
- **Containerization**: Docker + Kubernetes (existing)
- **Database**: PostgreSQL + Redis + Qdrant (existing five-layer memory)

### Agent Management
- **Agent Lifecycle**: Custom SubAgentManager service
- **Communication**: Agent Communication Protocol (ACP) 2.0 compliant
- **State Management**: LangGraph state graphs with checkpointing
- **Token Budgeting**: Dynamic allocation based on task priority

### Memory & Context
- **Skill Context**: Pre-loaded skill prompts (5-10K tokens each)
- **Working Memory**: Mem0 integration per agent
- **Context Injection**: Vector-based retrieval with semantic compression
- **Memory Sharing**: Hierarchical memory architecture

### Security & Monitoring
- **Authentication**: JWT + RBAC (existing system)
- **Agent Sandboxing**: Resource limits + process isolation
- **Monitoring**: Prometheus + OpenTelemetry + custom dashboards
- **Security**: Input validation + encrypted inter-agent communication

## Detailed Architecture

### 1. Agent Orchestration Layer

**SubAgentManager Service**
```python
class SubAgentManager:
    def __init__(self):
        self.agents = {
            'calendar': CalendarSubAgent(),
            'reminders': RemindersSubAgent(),
            'homework': HomeworkSubAgent(),
            'health': HealthSubAgent()
        }
        self.intent_classifier = IntentClassifier()
        self.token_budget = TokenBudgetManager(total_budget=8000)

    async def route_request(self, user_input: str, user_context: dict):
        intent = await self.intent_classifier.classify(user_input, 100)
        agent = self.agents.get(intent.agent_type)
        budget = self.token_budget.allocate(intent.priority)

        return await agent.handle(user_input, user_context, budget)
```

**Intent Classification**
```python
class IntentClassifier:
    INTENTS = {
        'calendar': ['schedule', 'appointment', 'meeting', 'calendar'],
        'reminders': ['remind', 'reminder', 'notify', 'alert'],
        'homework': ['homework', 'assignment', 'study', 'school'],
        'health': ['medicine', 'health', 'doctor', 'medication'],
        'general': []  # fallback
    }

    async def classify(self, text: str, max_tokens: int = 100):
        # Fast classification using small model
        # Returns agent_type, confidence, priority
```

### 2. Sub-Agent Implementation

**Calendar Sub-Agent Example**
```python
class CalendarSubAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            agent_id="calendar_agent",
            skill_prompt=self.load_calendar_skill(),  # 5.7K tokens
            tools=[MCPCalendarTools()],  # Domain-specific tools
            max_context=3000,  # Reduced from 20K
            memory_layers=["working", "family"]  # Selective memory
        )

    async def handle(self, user_input: str, user_context: dict, budget: int):
        # 1. Inject skill context (pre-loaded)
        # 2. Retrieve relevant memory (Layer 2 + Layer 3)
        # 3. Execute MCP tools if needed
        # 4. Generate response using minimal context

        context = await self.build_context(user_context, budget)
        tools_result = await self.execute_tools(user_input, context)
        return await self.generate_response(context, tools_result)
```

**Base Sub-Agent Class**
```python
class BaseSubAgent:
    def __init__(self, agent_id: str, skill_prompt: str, tools: list, max_context: int):
        self.agent_id = agent_id
        self.skill_prompt = skill_prompt  # Pre-loaded once
        self.tools = tools
        self.max_context = max_context
        self.memory_manager = MemoryManager(agent_id)

    async def build_context(self, user_context: dict, budget: int):
        # Dynamic context assembly within budget
        # Priority: Skill prompt > User context > Working memory > Recent history
        pass
```

### 3. Memory Integration

**Hierarchical Memory Architecture**
```
Global Memory (5 Layers)
├── Layer 1: Redis (Hot Cache) - Immediate context
├── Layer 2: Mem0 (Working Memory) - Agent-specific working memory
├── Layer 3: PostgreSQL (Structured Data) - Family data + Agent profiles
├── Layer 4: Qdrant (Vector Search) - Semantic memory
└── Layer 5: Archive (Long-term) - Historical data

Agent-Specific Memory
├── Skill Context (Pre-loaded) - Domain knowledge (5-10K tokens)
├── Session Memory (Mem0) - Conversation context per agent
├── Tool Results (Cache) - Recent tool execution results
└── Agent State (PostgreSQL) - Persistent agent configuration
```

**Memory Management**
```python
class AgentMemoryManager:
    async def get_relevant_memory(self, agent_id: str, query: str, budget: int):
        # 1. Agent skill context (pre-loaded, no budget cost)
        # 2. Recent agent sessions (Mem0, semantic search)
        # 3. Global family context (selective, based on budget)
        # 4. Tool execution cache (if relevant)

        return {
            'skill_context': self.skill_contexts[agent_id],  # Pre-loaded
            'working_memory': await self.search_mem0(agent_id, query),
            'family_context': await self.get_family_context(budget),
            'tool_cache': await self.get_tool_cache(agent_id, query)
        }
```

### 4. MCP Integration

**Enhanced MCP Architecture**
```python
class SkillSpecificMCPManager:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.tools = self.load_agent_tools(agent_type)  # Domain-specific
        self.tool_descriptions = self.compress_descriptions()  # 60% smaller

    async def execute_tool(self, tool_name: str, parameters: dict):
        # Execute domain-specific tool
        # Log usage for agent metrics
        # Return result with minimal overhead
        pass

class CalendarMCPTools:
    TOOLS = [
        "calendar_create_event",      # Creates real calendar events
        "calendar_search_events",     # Searches existing events
        "calendar_check_conflicts",   # Detects scheduling conflicts
        "calendar_get_availability"   # Finds free time slots
    ]

    def compress_descriptions(self):
        # Focused descriptions for calendar domain only
        # Reduces from 2K tokens to 800 tokens per tool set
```

### 5. API Integration

**New API Endpoints**
```python
# Agent Management
GET    /api/v1/agents                           # List available agents
POST   /api/v1/agents/{agent_id}/activate        # Activate specific agent
GET    /api/v1/agents/{agent_id}/status          # Agent status and metrics

# Agent Communication
POST   /api/v1/agents/{agent_id}/chat             # Direct agent chat
POST   /api/v1/agents/{agent_id}/delegate         # Delegate task to agent

# Agent Configuration
PUT    /api/v1/agents/{agent_id}/config           # Update agent settings
GET    /api/v1/agents/{agent_id}/memory            # Agent memory context
POST   /api/v1/agents/{agent_id}/tools             # Execute agent tools

# Monitoring
GET    /api/v1/agents/metrics                    # System-wide agent metrics
GET    /api/v1/agents/{agent_id}/performance      # Individual agent performance
```

**Integration with Existing Routes**
```python
# Extend existing /api/v1/family-chat
@router.post("/family-chat")
async def family_chat(request: ChatRequest):
    # 1. Route to appropriate sub-agent
    # 2. Execute with token budget
    # 3. Return response with agent metadata

    agent_result = await sub_agent_manager.route_request(
        request.message,
        request.user_context
    )

    return ChatResponse(
        message=agent_result.response,
        agent_used=agent_result.agent_id,
        tokens_used=agent_result.tokens_consumed,
        tools_executed=agent_result.tools_used
    )
```

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. **SubAgentManager Service**
   - Implement agent registry and lifecycle management
   - Create base sub-agent class with skill context loading
   - Build intent classification with 100-token budget

2. **Memory Integration**
   - Extend existing MemoryManager for agent-specific contexts
   - Implement agent session management in Mem0
   - Create agent profile storage in PostgreSQL

3. **API Endpoints**
   - Add agent management endpoints to existing FastAPI structure
   - Implement agent routing in family-chat endpoint
   - Create monitoring and metrics collection

### Phase 2: Skill Agents (Week 3-4)
1. **Calendar Sub-Agent**
   - Load calendar.md skill prompt (5.7K tokens)
   - Implement calendar-specific MCP tools integration
   - Create calendar-specific memory patterns

2. **Reminders Sub-Agent**
   - Load reminders.md skill prompt (7.8K tokens)
   - Integrate with existing reminder MCP tools
   - Implement reminder-specific context patterns

3. **Homework Sub-Agent**
   - Load homework_help.md skill prompt (10.7K tokens)
   - Create educational MCP tools integration
   - Build age-appropriate response patterns

### Phase 3: Advanced Features (Week 5-6)
1. **Health Sub-Agent**
   - Create medical/health domain agent
   - Implement medication reminder integration
   - Add health-specific safety protocols

2. **Token Optimization**
   - Implement context compression algorithms
   - Add dynamic token budget management
   - Create context pruning based on importance scores

3. **Performance Monitoring**
   - Set up Prometheus metrics for agent performance
   - Create OpenTelemetry tracing for agent workflows
   - Build custom dashboards for token efficiency

### Phase 4: Security & Testing (Week 7-8)
1. **Security Implementation**
   - Agent sandboxing with resource limits
   - Input validation across agent boundaries
   - Encrypted inter-agent communication

2. **Comprehensive Testing**
   - Unit tests for individual agents
   - Integration tests for agent communication
   - Load testing for token efficiency validation
   - Security testing for agent isolation

## Expected Outcomes

### Token Efficiency
- **85% reduction** in token usage per request (20K → 3K)
- **60% reduction** in tool description overhead
- **40% faster** response times due to smaller context

### Performance Improvements
- **3x better** concurrent user handling
- **50% reduction** in API response times
- **80% improvement** in memory utilization

### System Benefits
- **Scalability**: Support for 10x more concurrent family members
- **Maintainability**: Clear separation of concerns per domain
- **Extensibility**: Easy addition of new skill agents
- **Cost**: 70% reduction in LLM operational costs

## Risk Mitigation

### Technical Risks
- **Agent Coordination**: Implement comprehensive testing and fallback mechanisms
- **Memory Consistency**: Use transaction-based memory updates
- **Performance**: Implement caching and monitoring at all levels

### Operational Risks
- **Complexity**: Provide comprehensive documentation and admin dashboards
- **Migration**: Implement gradual rollout with feature flags
- **Monitoring**: Set up alerting for agent failures and token budget overruns

### Security Risks
- **Agent Isolation**: Implement process-level sandboxing
- **Data Privacy**: Extend existing RBAC to agent-level permissions
- **Input Validation**: Multi-layer validation across all agent boundaries

## Success Metrics

### Token Efficiency Metrics
- Tokens per request: Target < 3K (current > 20K)
- Token cost per interaction: Target 15% of current cost
- Context building time: Target < 200ms

### Performance Metrics
- Response time: Target < 2 seconds (current > 5 seconds)
- Concurrent users: Target 100+ (current ~10)
- Memory usage: Target 50% reduction per user

### Quality Metrics
- Task completion rate: Maintain > 95%
- User satisfaction: Target > 4.5/5.0
- Error rate: Target < 1% of interactions

## Conclusion

The skill-based sub-agent architecture provides a comprehensive solution to the token efficiency problem while maintaining full functionality through MCP integration. By leveraging the existing robust infrastructure and implementing modern multi-agent patterns, we can achieve significant cost savings, improved performance, and better scalability for the family assistant system.

The phased implementation approach ensures minimal disruption to existing functionality while providing clear measurable improvements at each stage.