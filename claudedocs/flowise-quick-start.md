# Flowise Chat Agent - Quick Start

## 🚀 Access Flowise

**URL**: https://flowise.homelab.pesulabs.net
**Login**: `admin` / `flowise2025`

## 📝 Create Your First Agent (5 Minutes)

### Step 1: Add Nodes

Click "+ Add New Chatflow", then drag these nodes from the left toolbar:

1. **Chat Models** → **ChatOllama**
   ```
   Base URL: http://100.72.98.106:11434
   Model: llama3.1:8b
   Temperature: 0.7
   ```

2. **Memory** → **Buffer Memory**
   ```
   Memory Key: chat_history
   ```

3. **Chains** → **Conversation Chain**

### Step 2: Connect Nodes

```
[Buffer Memory] ─┬─→ [ChatOllama] ──→ [Conversation Chain]
                 └─────────────────────────┘
```

Connect:
- Buffer Memory output → ChatOllama Memory input
- ChatOllama output → Conversation Chain Language Model input
- Buffer Memory output → Conversation Chain Memory input

### Step 3: Test & Deploy

1. Click **"Test"** button (top right)
2. Send: "Hello, how are you?"
3. Verify response
4. Click **"Save"**
5. Click **"Deploy"**

### Step 4: Get API Endpoint

1. Click **"API"** button
2. Copy the URL:
   ```
   POST https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId}
   ```
3. Save the chatflow ID

## 🧪 Test Your Agent

```bash
# Replace {chatflowId} with your actual ID
curl -X POST https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId} \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Hello, introduce yourself",
    "overrideConfig": {
      "sessionId": "test123"
    }
  }'
```

## 📊 Agent Configurations

### Basic Chat Agent (Recommended to Start)
```
ChatOllama (llama3.1:8b) + Buffer Memory + Conversation Chain
```
**Use case**: General conversation, simple Q&A

### Advanced: RAG Agent (Knowledge Base)
```
ChatOllama + Ollama Embeddings + Qdrant + Conversational Retrieval QA
```
**Use case**: Document Q&A, knowledge retrieval

### Advanced: Tool-Using Agent
```
ChatOllama + Custom Tools + Conversational Agent
```
**Use case**: API calls, task automation

## 🔧 Available Ollama Models

Your available models (from LobeChat config):
- `llama3.1:8b` ⭐ Recommended - Fast, good quality
- `gpt-oss:20b` - Powerful but slower
- `mistral:7b-instruct-q4_K_M` - Fast, instruction-following
- `qwen2.5-coder:14b` - Coding tasks
- `glm4:9b` - Multilingual

## 🎯 What's Next?

After creating your agent:
1. Test it in Flowise UI ✅
2. Test API with curl ✅
3. Configure LobeChat to use it
4. Test voice → Whisper → Flowise flow

---

**Full Guide**: `claudedocs/flowise-agent-creation-guide.md`
