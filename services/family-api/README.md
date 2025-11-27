# Family Assistant API

Privacy-focused AI Assistant for Families with multimodal support and extensible sub-agent architecture.

## Features

- **Persistent Memory**: Multi-layer memory system with family context
- **Multimodal Support**: Text, image, audio, and document processing
- **Family Management**: Role-based access control and parental oversight
- **MCP Integration**: Extensible tool system via Model Context Protocol
- **Sub-Agent Architecture**: Specialized agents for calendar, homework, health, and more
- **Real-time Dashboard**: WebSocket-based system monitoring

## Architecture

### Orchestrator-Worker Pattern

The Family Assistant uses an orchestrator-worker pattern where the main agent retains personality and delegates specialized tasks to sub-agents:

```
Main Agent (Orchestrator)
    ↓
Intent Classification
    ↓
Sub-Agent Manager → Calendar Sub-Agent → Calendar Tools
                 → Homework Sub-Agent → Homework Tools (future)
                 → Health Sub-Agent → Health Tools (future)
```

**Key Benefits**:
- **Token Efficiency**: Sub-agents load specialized prompts (5-10K tokens) only when needed
- **Unified UX**: Main agent maintains personality and conversation context
- **Scalability**: Easy to add new specialized capabilities
- **Isolation**: Each sub-agent is self-contained and independently testable

See [Sub-Agent Catalog](../../docs/sub-agent-catalog.md) for available agents.

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis (optional, for caching)
- LlamaCpp server (for LLM inference)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd services/family-api
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
# Database migrations are applied automatically on startup
```

6. Run the server:
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

## Usage

### API Endpoints

**Base URL**: `http://localhost:8001`

#### Core Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /chat` - Main chat endpoint
- `POST /v1/chat/completions` - OpenAI-compatible chat endpoint

#### Sub-Agent Endpoints

Sub-agents are invoked automatically via intent classification, but can also be called directly:

```bash
# Let the system route automatically (recommended)
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Schedule a dentist appointment tomorrow at 2pm",
    "user_id": "user123",
    "thread_id": "conv456"
  }'

# Force a specific sub-agent
curl -X POST http://localhost:8001/api/v1/sub-agents/calendar/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Schedule a meeting",
    "user_context": {"user_id": "user123"}
  }'
```

### Authentication

JWT-based authentication for family members:

```bash
# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "parent", "password": "secure_password"}'

# Use token in requests
curl -X POST http://localhost:8001/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Development

### Project Structure

```
services/family-api/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   ├── routes/              # API routes
│   │   ├── services/            # Business logic
│   │   └── middleware/          # Middleware components
│   ├── sub_agents/              # Sub-agent architecture
│   │   ├── base/                # Base classes
│   │   │   ├── base_agent.py   # BaseSubAgent
│   │   │   └── mcp_base.py     # MCPToolBase
│   │   ├── calendar/            # Calendar sub-agent
│   │   │   ├── agent.py
│   │   │   ├── tools.py
│   │   │   └── skill_prompt.md
│   │   └── manager.py           # SubAgentManager & IntentClassifier
│   ├── config/                  # Configuration
│   └── database/                # Database models
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── sub_agents/              # Sub-agent tests
└── requirements.txt
```

### Adding a New Sub-Agent

Follow the [Sub-Agent Addition Guide](../../docs/sub-agent-addition-guide.md):

1. Create package: `src/sub_agents/<skill>/`
2. Add `skill_prompt.md` with specialized prompt
3. Implement `agent.py` (inherits `BaseSubAgent`)
4. Implement `tools.py` (inherits `MCPToolBase`)
5. Register in `manager.py`
6. Add unit tests
7. Update documentation

### Running Tests

```bash
# All tests
pytest tests/ -v

# Sub-agent tests only
pytest tests/sub_agents/ -v

# Specific test file
pytest tests/sub_agents/test_calendar.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Format code
black src/ tests/
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/family_assistant

# LLM Service
LLAMACPP_BASE_URL=http://localhost:8081
LLAMACPP_MODEL=kimi-vl-8k

# Authentication
JWT_SECRET_KEY=<your-secret-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Feature Flags
ENABLE_SUB_AGENTS=true
ENABLE_MULTIMODAL=true
```

### Sub-Agent Configuration

Sub-agents can be configured in `src/sub_agents/manager.py`:

```python
def get_sub_agent_manager() -> SubAgentManager:
    manager = SubAgentManager()

    # Register sub-agents
    manager.register_agent(CalendarSubAgent())
    # manager.register_agent(HomeworkSubAgent())  # Future

    return manager
```

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8001/health

# Detailed health (includes sub-agents)
curl http://localhost:8001/api/v1/health/detailed
```

### Metrics

Prometheus-compatible metrics available at `/metrics`:

- Request count and latency
- Sub-agent execution time
- Tool usage statistics
- Error rates

### Logging

Structured logging with different levels:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

## Deployment

### Docker

```bash
# Build image
docker build -t family-api:latest .

# Run container
docker run -d \
  -p 8001:8001 \
  -e DATABASE_URL=<url> \
  -e LLAMACPP_BASE_URL=<url> \
  --name family-api \
  family-api:latest
```

### Kubernetes

See `../../infrastructure/kubernetes/apps/family-assistant/` for deployment manifests.

## Troubleshooting

### Sub-Agent Not Found

If a sub-agent is not being invoked:

1. Check intent keywords in `IntentClassifier.INTENT_PATTERNS`
2. Verify agent is registered in `get_sub_agent_manager()`
3. Check logs for classification confidence scores
4. Try forcing the agent with `force_agent` parameter

### Tool Execution Errors

If MCP tools fail:

1. Check tool method signatures match definitions
2. Verify all tools are async methods
3. Check tool validation in `MCPToolBase._validate_tools()`
4. Review tool execution logs

### Performance Issues

If sub-agent execution is slow:

1. Check `max_context` setting (should be ≤3000 for local LLMs)
2. Monitor LLM inference time
3. Consider caching tool results
4. Profile with `cProfile` or `py-spy`

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for contribution guidelines.

## License

See [LICENSE](../../LICENSE) for license information.

## Documentation

- [Sub-Agent Catalog](../../docs/sub-agent-catalog.md) - Available sub-agents
- [Sub-Agent Addition Guide](../../docs/sub-agent-addition-guide.md) - How to add new agents
- [Architecture Proposal](../../docs/sub-agent-critique-and-proposal.md) - Design decisions
- [API Documentation](../../docs/api-documentation.md) - Full API reference

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: <docs-url>
