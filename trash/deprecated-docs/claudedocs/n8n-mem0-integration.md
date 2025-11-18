# N8n + Mem0 Integration Guide

## Overview

This guide shows how to integrate Mem0 (AI memory layer) with N8n workflows for persistent conversation memory.

## Quick Access

- **N8n**: https://n8n.homelab.pesulabs.net (admin/admin123)
- **Mem0 API**: `http://mem0.homelab.svc.cluster.local:8080`
- **External Mem0**: `http://100.81.76.55:30880` (for testing)

## Mem0 Configuration

**Status**: ✅ Healthy and running
- LLM Model: `mistral:7b-instruct-q4_K_M`
- Embedding Model: `nomic-embed-text`
- Vector Store: Qdrant at `qdrant.homelab.svc.cluster.local:6333`
- Collection: `mem0_memories`

## N8n Workflow: Store Memory

### Step 1: Create New Workflow

1. Go to https://n8n.homelab.pesulabs.net
2. Click **"+ Add workflow"**
3. Name it: **"Mem0 - Store Memory"**

### Step 2: Add HTTP Request Node

1. Click **"+"** to add node
2. Search for **"HTTP Request"**
3. Configure:

**Basic Settings**:
- **Method**: POST
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/`

**Headers** (click "Add Option" → "Headers"):
```json
{
  "Content-Type": "application/json"
}
```

**Body** (select "JSON"):
```json
{
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.message }}"
    }
  ],
  "user_id": "{{ $json.userId }}"
}
```

### Step 3: Add Manual Trigger (for testing)

1. Click **"+"** at the start
2. Select **"Manual Trigger"**
3. Add test data:
```json
{
  "message": "I love building AI agents with N8n",
  "userId": "testuser123"
}
```

### Step 4: Test the Workflow

1. Click **"Execute Workflow"**
2. Check output - should see memory stored successfully

## N8n Workflow: Retrieve Memory

### Step 1: Create Retrieval Workflow

1. New workflow: **"Mem0 - Retrieve Memory"**

### Step 2: Add HTTP Request Node

**Basic Settings**:
- **Method**: GET
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/?user_id={{ $json.userId }}`

**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

### Step 3: Test Retrieval

Input:
```json
{
  "userId": "testuser123"
}
```

Expected output: Array of stored memories for that user

## N8n Workflow: Search Memories

### HTTP Request Node for Search

**Basic Settings**:
- **Method**: POST
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/`

**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**Body**:
```json
{
  "query": "{{ $json.query }}",
  "user_id": "{{ $json.userId }}"
}
```

**Test Input**:
```json
{
  "query": "What does the user like to build?",
  "userId": "testuser123"
}
```

## Complete Agent Workflow with Memory

### Architecture

```
Webhook Trigger
  ↓
[1] Retrieve Memories (Search)
  ↓
[2] Format Context (Code Node)
  ↓
[3] Call Ollama with Context
  ↓
[4] Store New Memory
  ↓
Return Response
```

### Workflow Nodes

#### Node 1: Webhook Trigger
- **Type**: Webhook
- **Path**: `/chat`
- **Method**: POST
- **Expected Input**:
```json
{
  "message": "user message here",
  "userId": "unique_user_id"
}
```

#### Node 2: Search Memories
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/`
- **Body**:
```json
{
  "query": "{{ $json.body.message }}",
  "user_id": "{{ $json.body.userId }}"
}
```

#### Node 3: Format Context (Code Node)
- **Type**: Code
- **Language**: JavaScript

```javascript
// Get memories from previous node
const memories = $input.all();
const currentMessage = $('Webhook').first().json.body.message;
const userId = $('Webhook').first().json.body.userId;

// Format memories as context
let context = "Previous conversations:\n";
if (memories.length > 0 && memories[0].json.length > 0) {
  context += memories[0].json.map(m => `- ${m.memory}`).join('\n');
} else {
  context = "No previous conversation history.";
}

// Create prompt with context
const prompt = `${context}

Current user message: ${currentMessage}

Please respond naturally, using the context from previous conversations when relevant.`;

return {
  json: {
    prompt: prompt,
    message: currentMessage,
    userId: userId,
    memoryContext: context
  }
};
```

#### Node 4: Call Ollama
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://100.72.98.106:11434/api/chat`
- **Body**:
```json
{
  "model": "llama3.1:8b",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant with memory of previous conversations."
    },
    {
      "role": "user",
      "content": "{{ $json.prompt }}"
    }
  ],
  "stream": false
}
```

#### Node 5: Store Memory
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://mem0.homelab.svc.cluster.local:8080/v1/memories/`
- **Body**:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "{{ $('Code').first().json.message }}"
    },
    {
      "role": "assistant",
      "content": "{{ $json.message.content }}"
    }
  ],
  "user_id": "{{ $('Code').first().json.userId }}"
}
```

#### Node 6: Respond to Webhook
- **Type**: Respond to Webhook
- **Response Body**:
```json
{
  "response": "{{ $('Call Ollama').first().json.message.content }}",
  "userId": "{{ $('Code').first().json.userId }}",
  "memoryStored": true
}
```

## Audio Integration: Whisper → Ollama + Mem0

### Complete Flow

```
Audio File Upload (Webhook)
  ↓
[1] Call Whisper STT
  ↓
[2] Search Memories
  ↓
[3] Format Context
  ↓
[4] Call Ollama
  ↓
[5] Store Conversation
  ↓
Return Text Response
```

### Whisper STT Node
- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://whisper.homelab.svc.cluster.local:9000/asr`
- **Body Type**: Multipart Form Data
- **Fields**:
  - `audio_file`: `{{ $binary.data }}`
  - `task`: `transcribe`
  - `language`: `en`
  - `output`: `json`

**Note**: Audio file must be in the binary data from webhook

## Testing Mem0 from N8n

### Test 1: Store a Memory

Create workflow with HTTP Request:
```
POST http://mem0.homelab.svc.cluster.local:8080/v1/memories/
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "I am testing N8n integration"}
  ],
  "user_id": "n8n_test"
}
```

### Test 2: Get All Memories

```
GET http://mem0.homelab.svc.cluster.local:8080/v1/memories/?user_id=n8n_test
```

### Test 3: Search Memories

```
POST http://mem0.homelab.svc.cluster.local:8080/v1/memories/search/
Content-Type: application/json

{
  "query": "What is the user testing?",
  "user_id": "n8n_test"
}
```

## Available Ollama Models

From N8n, you can use these models at `http://100.72.98.106:11434`:
- `llama3.1:8b` ⭐ Recommended
- `gpt-oss:20b` (slower, more powerful)
- `mistral:7b-instruct-q4_K_M`
- `qwen2.5-coder:14b` (best for code)
- `glm4:9b` (multilingual)

## Best Practices

1. **User ID**: Always use unique user IDs to keep memories separate
2. **Memory Limit**: Retrieve only top 3-5 most relevant memories
3. **Error Handling**: Add N8n error handling nodes for API failures
4. **Rate Limiting**: Add delays if making many requests
5. **Privacy**: Don't store sensitive personal information

## Troubleshooting

### Check Mem0 Health
Add HTTP Request node:
```
GET http://mem0.homelab.svc.cluster.local:8080/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "mem0-api",
  "version": "1.0.0"
}
```

### Check from Command Line

```bash
# Test Mem0 API
curl http://100.81.76.55:30880/health

# Store a test memory
curl -X POST http://100.81.76.55:30880/v1/memories/ \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "test"}],
    "user_id": "test123"
  }'

# Retrieve memories
curl http://100.81.76.55:30880/v1/memories/?user_id=test123
```

## Next Steps

1. ✅ Create basic "Store Memory" workflow in N8n
2. ✅ Test memory storage and retrieval
3. Create complete agent workflow with memory
4. Add Whisper STT for audio input
5. Test end-to-end: Audio → Text → Memory → Response

## Related Documentation

- `whisper-test-results.md` - Whisper STT setup
- `lobechat-audio-agent-integration.md` - Complete audio pipeline
- `flowise-mem0-integration.md` - Alternative Flowise approach
