# Flowise Chat Agent Creation Guide

**Date**: 2025-11-04
**Goal**: Create a chat agent in Flowise connected to Ollama

## Access Information

### Flowise UI
- **URL**: https://flowise.homelab.pesulabs.net
- **Username**: `admin`
- **Password**: `flowise2025`
- **Status**: ✅ Running (pod healthy, HTTPS working)

## Step-by-Step Agent Creation

### Step 1: Login to Flowise

1. Open browser to: **https://flowise.homelab.pesulabs.net**
2. Login with credentials:
   - Username: `admin`
   - Password: `flowise2025`

### Step 2: Create New Chatflow

1. Click **"+ Add New Chatflow"** button (top right)
2. Give it a name: **"Homelab Assistant"** (or your preferred name)
3. You'll see a blank canvas with a toolbar on the left

### Step 3: Add Chat Model Node (Ollama)

1. In the left toolbar, click **"Chat Models"**
2. Find and drag **"ChatOllama"** to the canvas
3. Click on the ChatOllama node to configure:
   - **Base URL**: `http://100.72.98.106:11434`
   - **Model Name**: Choose one:
     - `llama3.1:8b` (recommended - good balance)
     - `gpt-oss:20b` (powerful but slower)
     - `mistral:7b-instruct-q4_K_M` (fast, good for instructions)
   - **Temperature**: `0.7` (creative but focused)
   - Leave other settings as default

### Step 4: Add Conversation Memory (Optional but Recommended)

1. In the left toolbar, click **"Memory"**
2. Drag **"Buffer Memory"** to the canvas
3. Click on it to configure:
   - **Memory Key**: `chat_history`
   - **Session ID**: Leave empty (will be set by API calls)
4. Connect the Buffer Memory node to ChatOllama:
   - Drag from the memory output to the "Memory" input of ChatOllama

### Step 5: Add Conversation Chain

1. In the left toolbar, click **"Chains"**
2. Drag **"Conversation Chain"** to the canvas
3. Connect the nodes:
   - **ChatOllama** output → **Language Model** input of Conversation Chain
   - **Buffer Memory** output → **Memory** input of Conversation Chain (if using memory)

**Your chatflow should look like**:
```
[Buffer Memory] ──→ [ChatOllama] ──→ [Conversation Chain]
                          ↓
                    (also connects to Conversation Chain Memory input)
```

### Step 6: Configure System Prompt (Optional)

If you want to customize the agent's personality:

1. Click on the **Conversation Chain** node
2. Find the **"System Message"** field
3. Add your custom prompt, for example:

```
You are a helpful AI assistant for a homelab environment. You help with:
- Technical troubleshooting
- System administration tasks
- Explaining complex concepts simply
- Providing code examples when asked

Be concise, friendly, and technical when appropriate.
```

### Step 7: Test the Chatflow

1. Click the **"Test"** button in the top right
2. A chat window will appear on the right side
3. Try sending a message: "Hello, can you help me?"
4. Verify you get a response from Ollama
5. Send a follow-up message to test memory: "What did I just ask you?"

### Step 8: Save and Deploy

1. Click the **"Save"** button (top right, floppy disk icon)
2. Your chatflow is now saved
3. Click the **"Deploy"** button or toggle to make it active

### Step 9: Get API Endpoint

1. After deploying, click the **"API"** button (top right)
2. You'll see the API endpoint URL:
   ```
   POST https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId}
   ```
3. Copy the **Chatflow ID** (the UUID in the URL)
4. Note the example API request shown

## API Usage

### Endpoint Format

```
POST https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId}
```

### Request Format

```json
{
  "question": "Your question here",
  "overrideConfig": {
    "sessionId": "unique-session-id-for-user"
  }
}
```

### Example cURL Request

```bash
# Replace {chatflowId} with your actual chatflow ID
curl -X POST https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId} \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Hello, how are you?",
    "overrideConfig": {
      "sessionId": "user123"
    }
  }'
```

### Example Response

```json
{
  "text": "Hello! I'm doing well, thank you for asking. How can I assist you today?",
  "chatflowId": "abc-123-def",
  "sessionId": "user123",
  "chatId": "xyz-789"
}
```

## Advanced Configurations

### Option 1: Add RAG with Qdrant (Knowledge Base)

If you want the agent to access a knowledge base:

1. **Add Document Loader**:
   - Toolbar → "Document Loaders" → Choose type (PDF, Text, etc.)

2. **Add Text Splitter**:
   - Toolbar → "Text Splitters" → "Recursive Character Text Splitter"
   - Connect Document Loader → Text Splitter

3. **Add Embeddings**:
   - Toolbar → "Embeddings" → "Ollama Embeddings"
   - Base URL: `http://100.72.98.106:11434`
   - Model: `nomic-embed-text`

4. **Add Qdrant Vector Store**:
   - Toolbar → "Vector Stores" → "Qdrant"
   - URL: `http://qdrant.homelab.svc.cluster.local:6333`
   - Collection Name: `homelab-knowledge`
   - Connect: Text Splitter → Documents, Ollama Embeddings → Embeddings

5. **Use as Retriever**:
   - Replace Conversation Chain with "Conversational Retrieval QA Chain"
   - Connect Qdrant → Vector Store input
   - Connect ChatOllama → Language Model input

### Option 2: Add Tools/Functions

If you want the agent to perform actions:

1. **Add Tools**:
   - Toolbar → "Tools" → Choose from available tools
   - Examples: Calculator, Web Browser, Custom API, etc.

2. **Use Agent Executor**:
   - Toolbar → "Agents" → "Conversational Agent"
   - Connect ChatOllama → Chat Model
   - Connect Tools → Tools input

### Option 3: Add Custom API Tool

If you want the agent to call specific APIs:

1. **Add Custom Tool**:
   - Toolbar → "Tools" → "Custom Tool"
   - Configure API endpoint, method, parameters
   - Add description for when agent should use it

## Troubleshooting

### Ollama Connection Issues

**Problem**: "Failed to connect to Ollama"

**Solution**:
```bash
# Test Ollama from Flowise pod
kubectl exec -it -n homelab $(kubectl get pod -n homelab -l app=flowise -o name) -- \
  curl http://100.72.98.106:11434/api/tags

# Should return list of models
```

### No Response from Agent

**Problem**: Agent doesn't respond or times out

**Possible Causes**:
1. Model not loaded in Ollama
2. Ollama too slow (try smaller model)
3. Network connectivity issue

**Solution**:
```bash
# Check available models
curl http://100.72.98.106:11434/api/tags

# Test model directly
curl http://100.72.98.106:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello",
  "stream": false
}'
```

### Memory Not Working

**Problem**: Agent doesn't remember previous messages

**Possible Causes**:
1. Session ID not being passed
2. Memory not connected properly
3. Memory cleared between requests

**Solution**:
- Always pass same `sessionId` in API requests for same conversation
- Verify memory node is connected to chat model
- Check memory configuration in chatflow

## Integration with LobeChat

### Method 1: Custom Model Provider (Recommended)

Configure LobeChat to use Flowise as a custom model:

1. In LobeChat Settings → Model Providers
2. Add Custom Provider:
   - **Name**: Flowise Agent
   - **Endpoint**: `https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId}`
   - **API Key**: (leave empty if no auth)
   - **Model ID**: Your chatflow ID

### Method 2: OpenAI-Compatible Wrapper

Create a small proxy that translates OpenAI format → Flowise format:

```python
# Simple Flask/FastAPI proxy
@app.post("/v1/chat/completions")
async def openai_to_flowise(request: ChatRequest):
    # Map OpenAI format to Flowise format
    flowise_request = {
        "question": request.messages[-1].content,
        "overrideConfig": {
            "sessionId": request.user or "default"
        }
    }

    # Call Flowise API
    response = requests.post(
        f"https://flowise.homelab.pesulabs.net/api/v1/prediction/{CHATFLOW_ID}",
        json=flowise_request
    )

    # Map back to OpenAI format
    return {
        "choices": [{
            "message": {
                "content": response.json()["text"]
            }
        }]
    }
```

### Method 3: N8n Middleware

Create N8n workflow:
1. Webhook receives from LobeChat
2. Transform to Flowise format
3. Call Flowise API
4. Transform response
5. Return to LobeChat

## Recommended Starter Configuration

### Simple Conversational Agent
```
Components:
- ChatOllama (llama3.1:8b)
- Buffer Memory
- Conversation Chain

Best for: General chat, Q&A
```

### RAG Agent with Knowledge Base
```
Components:
- ChatOllama (llama3.1:8b)
- Ollama Embeddings (nomic-embed-text)
- Qdrant Vector Store
- Conversational Retrieval QA Chain

Best for: Document Q&A, knowledge retrieval
```

### Tool-Using Agent
```
Components:
- ChatOllama (llama3.1:8b)
- Custom Tools (APIs, calculators, etc.)
- Conversational Agent

Best for: Task automation, API integration
```

## Testing Checklist

- [ ] Chatflow created and saved
- [ ] Ollama connection working
- [ ] Test message receives response
- [ ] Memory working (follow-up questions)
- [ ] Chatflow deployed
- [ ] API endpoint copied
- [ ] API tested via curl
- [ ] Session ID persistence tested

## Next Steps After Creation

1. ✅ Create basic chatflow
2. ✅ Test in Flowise UI
3. ✅ Get API endpoint
4. ⏳ Test API with curl
5. ⏳ Configure LobeChat to use Flowise
6. ⏳ Test voice → Whisper → Flowise flow

---

**Status**: Ready to create chatflow
**URL**: https://flowise.homelab.pesulabs.net
**Credentials**: admin / flowise2025
