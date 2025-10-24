# Quick Start: LiteLLM in N8n

**Goal**: Add local LLM to N8n workflows in 2 minutes

---

## Step 1: Add Credential (30 seconds)

1. Open N8n: http://100.81.76.55:30678
2. Login: `admin` / `admin123`
3. Profile icon → **Settings** → **Credentials**
4. **+ Add Credential** → Search **OpenAI**
5. Fill in:
   ```
   Name: LiteLLM Local
   API Key: sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0

   [Advanced Options]:
   Base URL: http://100.72.98.106:8000/v1
   ```
6. **Save**

---

## Step 2: Create Test Workflow (1 minute)

1. **Workflows** → **Add Workflow**
2. Name: "LLM Test"
3. Add **Manual Trigger** node
4. Add **OpenAI Chat Model** node
5. Configure:
   ```
   Credential: LiteLLM Local
   Model: gpt-3.5-turbo
   Prompt: Say hello in a creative way
   ```
6. Connect nodes
7. **Test workflow** → Execute
8. Should see creative greeting response!

---

## Available Models

```
gpt-3.5-turbo  → Llama 3.1 8B (best for general use)
mistral        → Mistral 7B (fast)
qwen-coder     → Qwen 14B (code generation)
```

---

## That's It!

You now have local AI in N8n workflows.

**Full Guide**: `docs/N8N-LITELLM-INTEGRATION.md`

---

## Quick Troubleshooting

**Connection error?**
```bash
# Check LiteLLM is running
systemctl status litellm
```

**Auth error?**
- Double-check API key in N8n credentials
- Make sure Base URL is set: `http://100.72.98.106:8000/v1`

**Slow?**
- Use `mistral` model for faster responses
- Reduce max_tokens to 100-200
