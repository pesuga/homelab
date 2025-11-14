# LobeChat Integration with Family Assistant

## Overview

Family Assistant now provides OpenAI-compatible API endpoints, allowing seamless integration with LobeChat and other OpenAI-compatible clients.

## API Endpoints

### Base URL
- **NodePort**: `http://100.81.76.55:30801`
- **Ingress (HTTPS)**: `https://assistant.homelab.pesulabs.net`

### OpenAI-Compatible Endpoints

#### 1. List Models
```bash
GET /v1/models
```

Returns available models for selection in LobeChat.

**Response**:
```json
{
  "object": "list",
  "data": [{
    "id": "family-assistant",
    "object": "model",
    "owned_by": "homelab"
  }]
}
```

#### 2. Chat Completions
```bash
POST /v1/chat/completions
Content-Type: application/json
```

**Request Body**:
```json
{
  "model": "family-assistant",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "user": "dad"  // user_id for memory/permissions
}
```

**Response**:
```json
{
  "id": "chatcmpl-xyz",
  "object": "chat.completion",
  "created": 1762365260,
  "model": "family-assistant",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Good morning, Dad! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 1,
    "completion_tokens": 10,
    "total_tokens": 11
  }
}
```

## LobeChat Configuration

### Option 1: Add as Custom Model Provider

1. Open LobeChat: http://100.81.76.55:30910
2. Go to Settings → Language Model
3. Add Custom Provider:
   - **Name**: Family Assistant
   - **Base URL**: `http://family-assistant.homelab.svc.cluster.local:8001`
   - **API Key**: (leave empty, not required)
   - **Model**: `family-assistant`

### Option 2: Update LobeChat ConfigMap

Add Family Assistant to the LobeChat configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: lobechat-config
  namespace: homelab
data:
  # Add custom model provider
  CUSTOM_MODELS: |
    [
      {
        "name": "Family Assistant",
        "baseURL": "http://family-assistant.homelab.svc.cluster.local:8001/v1",
        "apiKey": "",
        "models": ["family-assistant"]
      }
    ]
```

Then restart LobeChat:
```bash
kubectl rollout restart deployment/lobechat -n homelab
```

## Features

### Memory & Context Awareness
- **User Profiles**: Each user has permissions and preferences
- **Conversation History**: All conversations stored in PostgreSQL
- **Semantic Memory**: Mem0 + Qdrant for cross-conversation recall
- **Role-Based Access**: Parents vs children have different capabilities

### Family-Specific Capabilities
- **Multi-user Support**: Use the `user` field to specify family member
- **Permission Checking**: Finance, calendar, admin features per role
- **Educational Filtering**: Age-appropriate responses for children
- **Proactive Features**: (Coming in Phase 4) Morning briefings, reminders

## Testing

### Test OpenAI Endpoint
```bash
curl -X POST http://100.81.76.55:30801/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "family-assistant",
    "messages": [{"role": "user", "content": "Hello!"}],
    "user": "dad"
  }' | jq
```

### Test with Different Users
```bash
# As parent (full permissions)
curl -X POST http://100.81.76.55:30801/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "family-assistant",
    "messages": [{"role": "user", "content": "What are my permissions?"}],
    "user": "dad"
  }' | jq

# As child (homework help enabled)
curl -X POST http://100.81.76.55:30801/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "family-assistant",
    "messages": [{"role": "user", "content": "Can you help with my math homework?"}],
    "user": "kid1"
  }' | jq
```

## Architecture

```
LobeChat (UI) 
    ↓ HTTP POST /v1/chat/completions
Family Assistant API (FastAPI)
    ↓ Uses
LangGraph Agent (State Machine)
    ↓ Retrieves from
Mem0 (Semantic Memory) + Qdrant (Vector DB)
    ↓ Calls
Ollama (llama3.1:8b on Compute Node)
    ↓ Stores in
PostgreSQL (Conversation History, User Profiles)
```

## Next Steps

1. **Phase 2**: Add Authentik SSO for web-based authentication
2. **Phase 3**: Integrate Google Calendar, Joplin notes, task management
3. **Phase 4**: Proactive capabilities (morning briefings, reminders via Celery)
4. **Phase 5**: Educational agent with age-appropriate content filtering

## Troubleshooting

### Check API Health
```bash
curl http://100.81.76.55:30801/health | jq
```

### View Logs
```bash
kubectl logs -n homelab -l app=family-assistant -f
```

### Test Native Endpoint (Bypass OpenAI format)
```bash
curl -X POST http://100.81.76.55:30801/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "dad"}' | jq
```
