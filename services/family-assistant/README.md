# Family AI Assistant

Privacy-focused, self-hosted AI assistant for family use with persistent memory, proactive capabilities, and tool integration.

## Architecture

```
LobeChat (UI) → FastAPI → LangGraph Agent → Ollama (LLM)
                     ↓
              Tool Layer (N8n)
                     ↓
         Memory Layer (Mem0 + Qdrant + PostgreSQL)
```

## Features

- **Persistent Memory**: Remembers everything about family members via Mem0 + Qdrant
- **Multi-User**: Separate contexts and permissions for parents and kids
- **Tool Integration**: Calendar (Google), notes (Joplin), tasks (future)
- **Proactive**: Morning briefings, reminders, alerts via Celery scheduling
- **Educational**: Homework help for kids with age-appropriate guidance
- **Privacy-First**: All data stays on-premises, local LLM inference

## Project Structure

```
services/family-assistant/
├── api/                    # FastAPI REST API
│   ├── main.py            # API entrypoint
│   ├── routes/            # API endpoints
│   └── middleware/        # Auth, logging
├── agents/                 # LangGraph agents
│   ├── orchestrator.py    # Main routing agent
│   ├── education.py       # Homework help agent
│   └── base.py            # Base agent class
├── tools/                  # LangGraph tools
│   ├── calendar.py        # Google Calendar integration
│   ├── notes.py           # Joplin notes
│   └── base.py            # Base tool class
├── config/                 # Configuration
│   ├── settings.py        # Environment variables
│   └── permissions.py     # User permissions
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
└── Dockerfile             # Container image
```

## Installation

### Prerequisites

- Ollama running on compute node (http://100.72.98.106:11434)
- PostgreSQL (postgres.homelab.svc.cluster.local:5432)
- Redis (redis.homelab.svc.cluster.local:6379)
- Mem0 + Qdrant (already deployed)
- N8n for tool integration (already deployed)

### Setup

```bash
# Install dependencies
cd /home/pesu/Rakuflow/systems/homelab/services/family-assistant
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Create PostgreSQL schema
python -m api.setup_db

# Run API
uvicorn api.main:app --host 0.0.0.0 --port 8001
```

## Configuration

### Environment Variables (.env)

```bash
# LLM
OLLAMA_BASE_URL=http://100.72.98.106:11434
OLLAMA_MODEL=llama3.1:8b

# Databases
POSTGRES_HOST=postgres.homelab.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_USER=homelab
POSTGRES_PASSWORD=your_password
POSTGRES_DB=homelab

REDIS_HOST=redis.homelab.svc.cluster.local
REDIS_PORT=6379

# Memory
MEM0_API_URL=http://mem0.homelab.svc.cluster.local:8080
QDRANT_URL=http://qdrant.homelab.svc.cluster.local:6333

# N8n Tools
N8N_BASE_URL=http://100.81.76.55:30678
N8N_WEBHOOK_PATH=/webhook

# Authentication
AUTHENTIK_URL=https://auth.homelab.pesulabs.net
AUTHENTIK_CLIENT_ID=your_client_id
AUTHENTIK_CLIENT_SECRET=your_secret

# API
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
```

## Development

### Running Locally

```bash
# Start API in development mode
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Run tests
pytest tests/

# Type checking
mypy api/ agents/ tools/
```

### Testing Agent

```bash
# Test basic conversation
curl -X POST http://localhost:8001/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is on my calendar tomorrow?",
    "user_id": "dad"
  }'
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t family-assistant:latest .

# Run container
docker run -d \
  --name family-assistant \
  -p 8001:8001 \
  --env-file .env \
  family-assistant:latest
```

### Kubernetes Deployment

```bash
kubectl apply -f infrastructure/kubernetes/services/family-assistant/
```

## Usage Examples

### Adding Calendar Event

```python
POST /agent/chat
{
  "message": "Add dentist appointment tomorrow at 3pm",
  "user_id": "dad"
}
```

### Saving Note

```python
POST /agent/chat
{
  "message": "Save a note: Remember to buy milk and eggs",
  "user_id": "dad"
}
```

### Homework Help

```python
POST /agent/chat
{
  "message": "Help me understand photosynthesis",
  "user_id": "kid1"
}
```

## Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: `journalctl -u family-assistant -f`

## Security

- **Authentication**: Authentik SSO integration
- **Permissions**: Role-based access control (parent vs child)
- **Audit Logging**: All tool actions logged to PostgreSQL
- **Network**: Internal cluster communication only
- **TLS**: HTTPS via Traefik + Let's Encrypt

## Roadmap

### Phase 1: Core Memory System ✅
- LangGraph agent with Mem0 integration
- PostgreSQL checkpoint persistence
- Basic conversation API

### Phase 2: Multi-User (In Progress)
- Authentik SSO
- User profiles and permissions
- Context switching

### Phase 3: Tool Integration
- Google Calendar
- Joplin notes
- N8n workflow tools

### Phase 4: Proactive Capabilities
- Celery scheduling
- Morning briefings
- Event reminders
- Notifications

### Phase 5: Educational Support
- Homework help agent
- Age-appropriate filtering
- Learning resources RAG

## License

Private family project - not for public distribution.

## Support

For issues or questions, create a ticket in the homelab repository.
