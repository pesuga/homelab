# Flowise + Mem0 Integration Guide

## Overview

This guide shows how to connect Flowise to your Mem0 instance for persistent conversation memory across sessions.

## Mem0 Instance Details

**✅ Status**: Healthy and accessible from Flowise pod

**Connection Details**:
- **Base URL**: `http://mem0.homelab.svc.cluster.local:8080`
- **Cluster IP**: `10.43.144.87:8080`
- **External Access** (for testing): `http://100.81.76.55:30880`
- **API Version**: v1.0.0
- **Health Endpoint**: `/health`

**Configuration**:
- LLM Model: `mistral:7b-instruct-q4_K_M`
- Embedding Model: `nomic-embed-text`
- Vector Store: Qdrant at `qdrant.homelab.svc.cluster.local:6333`
- Collection: `mem0_memories`

## Mem0 API Endpoints

### 1. Add Memory
```bash
POST http://mem0.homelab.svc.cluster.local:8080/v1/memories/

# Example:
curl -X POST http://mem0.homelab.svc.cluster.local:8080/v1/memories/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "My name is Alice and I love Python programming"}
    ],
    "user_id": "alice123"
  }'
```

### 2. Get All Memories
```bash
GET http://mem0.homelab.svc.cluster.local:8080/v1/memories/?user_id=alice123
```

### 3. Search Memories
```bash
POST http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/

# Example:
curl -X POST http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What programming languages does Alice like?",
    "user_id": "alice123"
  }'
```

### 4. Delete Memory
```bash
DELETE http://mem0.homelab.svc.cluster.local:8080/v1/memories/{memory_id}
```

## Option 1: Using Custom Function Node in Flowise

Since Flowise doesn't have a native Mem0 node, you'll use the **Custom Function** node to interact with Mem0's API.

### Step 1: Create Custom Function Node for Memory Storage

1. In Flowise, add a **Custom Function** node
2. Name it: `Store Memory`
3. Paste this code:

```javascript
async function storeMemory(input) {
    const userId = input.userId || 'default_user';
    const message = input.message;

    try {
        const response = await fetch('http://mem0.homelab.svc.cluster.local:8080/v1/memories/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                messages: [
                    { role: 'user', content: message }
                ],
                user_id: userId
            })
        });

        const result = await response.json();
        return { success: true, memory: result };
    } catch (error) {
        console.error('Memory storage error:', error);
        return { success: false, error: error.message };
    }
}

// Main execution
return await storeMemory($input);
```

### Step 2: Create Custom Function Node for Memory Retrieval

1. Add another **Custom Function** node
2. Name it: `Retrieve Memory`
3. Paste this code:

```javascript
async function retrieveMemories(input) {
    const userId = input.userId || 'default_user';
    const query = input.query;

    try {
        // Search for relevant memories
        const response = await fetch('http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                user_id: userId
            })
        });

        const memories = await response.json();

        // Format memories for context
        if (memories && memories.length > 0) {
            const context = memories.map(m => m.memory).join('\n');
            return {
                success: true,
                context: context,
                count: memories.length
            };
        } else {
            return {
                success: true,
                context: 'No previous memories found.',
                count: 0
            };
        }
    } catch (error) {
        console.error('Memory retrieval error:', error);
        return {
            success: false,
            error: error.message,
            context: ''
        };
    }
}

// Main execution
return await retrieveMemories($input);
```

### Step 3: Integrate into Your Chatflow

**Architecture**:
```
User Input → Retrieve Memory → Add to Prompt → ChatOllama → Store Memory → Response
```

**Flow Diagram**:
1. **Input Node**: Capture user message and userId
2. **Retrieve Memory**: Search Mem0 for relevant context
3. **Prompt Template**: Combine memories with current message
4. **ChatOllama**: Generate response with memory context
5. **Store Memory**: Save conversation to Mem0
6. **Output**: Return response to user

### Step 4: Prompt Template with Memory

```
You are a helpful AI assistant. You have access to previous conversations with this user.

Previous Context:
{memoryContext}

Current User Message:
{userInput}

Please respond naturally, using the context from previous conversations when relevant.
```

## Option 2: HTTP Request Node (Simpler)

If you prefer a simpler approach, use Flowise's **HTTP Request** node:

### Store Memory with HTTP Request

**Node Configuration**:
- **Method**: POST
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/`
- **Headers**:
  ```json
  {
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "{{input}}"
      }
    ],
    "user_id": "{{userId}}"
  }
  ```

### Retrieve Memory with HTTP Request

**Node Configuration**:
- **Method**: POST
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/`
- **Headers**:
  ```json
  {
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "query": "{{query}}",
    "user_id": "{{userId}}"
  }
  ```

## Complete Example Flow

### Recommended Chatflow Structure:

```
┌─────────────┐
│  User Input │
│  (message + │
│   userId)   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Retrieve Memory │ ← Custom Function or HTTP Request
│   from Mem0     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Prompt Template │ ← Inject memory context
│  with Context   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ChatOllama     │ ← llama3.1:8b or mistral
│  (with memory)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Store Memory   │ ← Custom Function or HTTP Request
│    to Mem0      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Response to    │
│     User        │
└─────────────────┘
```

## Testing Mem0 Integration

### Test 1: Store a Memory

```bash
curl -X POST http://100.81.76.55:30880/v1/memories/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I am building a homelab with K3s and Ollama"}
    ],
    "user_id": "testuser"
  }'
```

### Test 2: Retrieve Memories

```bash
curl http://100.81.76.55:30880/v1/memories/?user_id=testuser
```

### Test 3: Search Memories

```bash
curl -X POST http://100.81.76.55:30880/v1/memories/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the user building?",
    "user_id": "testuser"
  }'
```

## Key Benefits

1. **Persistent Memory**: Conversations persist across sessions
2. **Semantic Search**: Mem0 uses embeddings to find relevant context
3. **User-Specific**: Each user has isolated memory space
4. **Vector-Backed**: Powered by Qdrant for fast similarity search
5. **LLM Integration**: Uses Ollama models for memory processing

## Best Practices

1. **User ID Management**: Always include a unique `userId` to keep memories separate
2. **Memory Pruning**: Periodically clean old or irrelevant memories
3. **Context Length**: Limit retrieved memories to avoid token limits (top 3-5 most relevant)
4. **Error Handling**: Handle Mem0 API failures gracefully
5. **Privacy**: Don't store sensitive information in memories

## Troubleshooting

### Connection Issues

```bash
# Test from Flowise pod
kubectl exec -n homelab $(kubectl get pod -n homelab -l app=flowise -o jsonpath='{.items[0].metadata.name}') -- \
  curl http://mem0.homelab.svc.cluster.local:8080/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "mem0-api",
  "version": "1.0.0",
  "config": {
    "llm_model": "mistral:7b-instruct-q4_K_M",
    "embedding_model": "nomic-embed-text",
    "vector_store": "qdrant://qdrant.homelab.svc.cluster.local:6333",
    "collection": "mem0_memories"
  }
}
```

### Check Mem0 Logs

```bash
kubectl logs -n homelab -l app=mem0 -f
```

### Verify Qdrant Connection

Mem0 stores memories in Qdrant. Check if the collection exists:

```bash
curl http://100.81.76.55:30633/collections/mem0_memories
```

## Next Steps

1. Create a test chatflow in Flowise with Mem0 integration
2. Test memory storage and retrieval
3. Add error handling and fallbacks
4. Integrate with your LobeChat → Whisper → Flowise flow
5. Monitor Mem0 usage and performance

## Related Documentation

- `flowise-quick-start.md` - Creating basic chatflows
- `flowise-agent-creation-guide.md` - Detailed Flowise setup
- `whisper-test-results.md` - Whisper STT integration
- `lobechat-audio-agent-integration.md` - Complete audio pipeline
