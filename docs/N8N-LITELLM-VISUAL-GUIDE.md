# Visual Guide: Using LiteLLM in N8n

**Problem**: There's no "LiteLLM" node in N8n
**Solution**: Use the **HTTP Request** node (works in ALL N8n versions)

---

## Quick Setup (5 Minutes)

### Step 1: Open N8n
```
URL: http://100.81.76.55:30678
Login: admin / admin123
```

### Step 2: Import Ready-Made Workflow

1. Click **Workflows** (left sidebar)
2. Click the **⋮** menu → **Import from File**
3. Choose: `workflows/litellm-test-workflow.json`
   - Or copy/paste the JSON from this file
4. Click **Import**
5. Click **Execute Workflow** button

**Done!** You should see a response about homelab benefits.

---

## What's in the Workflow?

```
┌─────────────────┐
│ Manual Trigger  │  ← Click "Execute Workflow"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Set Question   │  ← Define your question
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Call LiteLLM    │  ← HTTP POST to your LLM API
│  (HTTP Request) │     with API key authentication
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Response │  ← Parse and display result
└─────────────────┘
```

---

## Step-by-Step: Build It Yourself

### 1. Create New Workflow

Click **+ Add Workflow** → Name it: "My LLM Test"

### 2. Add Manual Trigger

1. Click the **+** button in canvas
2. Search: `manual`
3. Select: **Manual Trigger**
4. Place on canvas

### 3. Add HTTP Request Node

1. Click **+** button again
2. Search: `http request`
3. Select: **HTTP Request**
4. Connect to Manual Trigger

### 4. Configure HTTP Request

Click the HTTP Request node and fill in:

**Basic Settings**:
```
Method: POST
URL: http://100.72.98.106:8000/v1/chat/completions
```

**Headers Section**:
Click "Add Option" → "Header"

Add two headers:

Header 1:
```
Name: Authorization
Value: Bearer sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0
```

Header 2:
```
Name: Content-Type
Value: application/json
```

**Body Section**:
```
Send Body: ON (toggle it)
Content Type: JSON
Body (click "JSON" tab):
```

Paste this JSON:
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "Write a haiku about servers"
    }
  ],
  "max_tokens": 100
}
```

### 5. Test It!

1. Click **Execute Workflow** (top right)
2. Wait 2-5 seconds
3. Click the HTTP Request node
4. View **Output** tab

You should see:
```json
{
  "id": "chatcmpl-...",
  "choices": [
    {
      "message": {
        "content": "Silicon boxes hum,\nData flows through...",
        "role": "assistant"
      }
    }
  ]
}
```

---

## Making it Dynamic (Advanced)

### Add Variable Input

**Before HTTP Request**, add a **Set** node:

```
Node: Set
Values:
  - Name: question
    Value: What is Kubernetes?
```

**In HTTP Request**, change the body to:

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.question }}"
    }
  ]
}
```

Now the question comes from the previous node!

---

## Alternative: If OpenAI Node Exists

Some N8n versions have an **OpenAI** node. If you see it:

### Add OpenAI Credential

1. **Settings** → **Credentials** → **+ Add**
2. Search: **OpenAI**
3. Configure:
   ```
   Name: LiteLLM Local
   API Key: sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0

   [Advanced Options]:
   Base URL: http://100.72.98.106:8000/v1
   ```

### Use OpenAI Node

1. Add **OpenAI** node (search for it)
2. Select credential: **LiteLLM Local**
3. Configure:
   ```
   Resource: Chat
   Operation: Message / Complete
   Model: gpt-3.5-turbo
   Prompt: Your question here
   ```

---

## Changing the Model

Edit the request body to use different models:

**Fast responses** (Mistral 7B):
```json
{
  "model": "mistral",
  "messages": [...]
}
```

**Code generation** (Qwen 14B):
```json
{
  "model": "qwen-coder",
  "messages": [
    {
      "role": "user",
      "content": "Write a Python function to sort a list"
    }
  ]
}
```

**General purpose** (Llama 3.1 8B):
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [...]
}
```

---

## Accessing the Response

In nodes AFTER the HTTP Request, use these expressions:

**Get the answer**:
```
{{ $json.choices[0].message.content }}
```

**Get model name**:
```
{{ $json.model }}
```

**Get token usage**:
```
{{ $json.usage.total_tokens }}
```

**Example in Set node**:
```
Values:
  - Name: answer
    Value: {{ $json.choices[0].message.content }}
  - Name: tokens
    Value: {{ $json.usage.total_tokens }}
```

---

## Common Issues

### ❌ "Cannot connect"

**Check**:
```bash
# On compute node, verify LiteLLM is running:
systemctl status litellm

# Test the endpoint:
curl http://100.72.98.106:8000/health
```

### ❌ "401 Unauthorized"

**Fix**:
- Double-check the Authorization header
- Format must be: `Bearer sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0`
- Note the space after "Bearer"

### ❌ "Empty response"

**Fix**:
- Check model name is correct: `gpt-3.5-turbo`, `mistral`, or `qwen-coder`
- Increase max_tokens to 500+
- Check N8n execution logs for errors

### ❌ "Timeout"

**Fix**:
- Use faster model: `mistral` instead of `qwen-coder`
- Reduce max_tokens
- Check GPU usage on compute node: `rocm-smi`

---

## Example Workflows to Build

### 1. Email Summarizer
```
Email Trigger
  ↓
Extract Email Body
  ↓
HTTP Request (LiteLLM: "Summarize in 3 points")
  ↓
Send to Slack
```

### 2. Code Reviewer
```
GitHub Webhook (PR opened)
  ↓
Get PR Diff
  ↓
HTTP Request (LiteLLM with qwen-coder: "Review this code")
  ↓
Post Comment on PR
```

### 3. Smart Alerts
```
Prometheus Alert Webhook
  ↓
Get Alert Details
  ↓
HTTP Request (LiteLLM: "Suggest fix for this alert")
  ↓
Send Email with AI Recommendation
```

---

## Pro Tips

### 1. Use System Prompts for Better Results

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a DevOps expert. Be concise and technical."
    },
    {
      "role": "user",
      "content": "{{ $json.question }}"
    }
  ]
}
```

### 2. Control Creativity with Temperature

```json
{
  "temperature": 0.2,  // More focused, deterministic
  "temperature": 0.7,  // Balanced (default)
  "temperature": 1.0   // More creative
}
```

### 3. Save Cost with Token Limits

```json
{
  "max_tokens": 100   // Short answer
  "max_tokens": 500   // Medium
  "max_tokens": 2000  // Long
}
```

---

## Ready-Made Workflow Location

Import this file into N8n:
```
workflows/litellm-test-workflow.json
```

**How to import**:
1. In N8n: **Workflows** → **⋮** → **Import from File**
2. Select the JSON file
3. Click **Import**
4. Test it!

---

## Summary

✅ **Use HTTP Request node** - Works in all N8n versions
✅ **Import the ready workflow** - Get started in 30 seconds
✅ **Three models available** - gpt-3.5-turbo, mistral, qwen-coder
✅ **Fully local** - No data leaves your homelab
✅ **Unlimited usage** - No API costs

---

**Next**: Build your first real workflow (email summarizer, alert analyzer, etc.)!
