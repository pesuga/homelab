# LobeChat mem0 Middleware

Transparent proxy that adds persistent memory to LobeChat conversations.

## Architecture

```
LobeChat → Middleware (port 11435) → Ollama (port 11434)
              ↓
            mem0 API (memory storage)
```

## How It Works

1. **Intercepts** chat requests from LobeChat
2. **Fetches** relevant memories from mem0 based on conversation context
3. **Injects** memories into system prompt for personalization
4. **Forwards** enhanced request to Ollama
5. **Returns** Ollama response to LobeChat
6. **Stores** new memories asynchronously to mem0

## Configuration

### Environment Variables

```bash
PORT=11435  # Middleware listen port
OLLAMA_URL=http://100.72.98.106:11434  # Ollama backend
MEM0_URL=http://mem0.homelab.svc.cluster.local:8080  # mem0 API
```

### LobeChat Configuration

Point LobeChat to middleware instead of Ollama directly:

```bash
# In lobechat ConfigMap
OLLAMA_PROXY_URL=http://lobechat-mem0-middleware.homelab.svc.cluster.local:11435
```

## User Identification

Middleware uses `X-User-ID` header to identify users. If not provided, uses `default_user`.

To set user ID from LobeChat, you can:
1. Use browser localStorage to set user ID
2. Configure via environment variable
3. Implement authentication layer

## API Endpoints

### Health Check
```bash
GET /health
```

### Chat (with memory)
```bash
POST /api/chat
{
  "model": "gpt-oss:20b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}
```

### Generate (passthrough)
```bash
POST /api/generate
```

## Development

### Local Testing
```bash
npm install
npm start
```

### Docker Build
```bash
docker build -t lobechat-mem0-middleware:latest .
```

### Kubernetes Deployment
```bash
kubectl apply -f infrastructure/kubernetes/services/lobechat/mem0-middleware.yaml
```

## Monitoring

### Logs
```bash
kubectl logs -n homelab -l app=lobechat-mem0-middleware -f
```

### Memory Statistics
```bash
# Check mem0 memory count
curl http://mem0.homelab.svc.cluster.local:8080/v1/memories/?user_id=default_user
```

## Example Conversation Flow

### First Conversation
```
User: "Hola, me llamo Pedro y me gusta el ciclismo"
↓ Middleware → mem0: No existing memories
↓ Ollama: Responds without memory context
↓ mem0 stores: {"name": "Pedro", "interest": "cycling"}
```

### Second Conversation (Next Day)
```
User: "¿Qué tal?"
↓ Middleware → mem0: Retrieves "Pedro likes cycling"
↓ Enhanced prompt: "User's name is Pedro, interested in cycling"
↓ Ollama: "¡Hola Pedro! ¿Cómo va el ciclismo?"
```

## Troubleshooting

### mem0 Connection Failed
- Check mem0 service is running: `kubectl get pods -l app=mem0`
- Verify mem0 endpoint: `curl http://mem0.homelab.svc.cluster.local:8080/health`

### Ollama Not Responding
- Verify Ollama is accessible from middleware pod
- Check Tailscale connectivity to compute node

### No Memories Being Stored
- Check middleware logs for mem0 API errors
- Verify mem0 has Qdrant connection
- Test mem0 API directly

## Performance

- **Memory Fetch**: ~50-200ms (from Qdrant)
- **Memory Injection**: <10ms (string manipulation)
- **Total Overhead**: ~60-250ms per request

Minimal impact on response time, massive improvement in conversation quality!
