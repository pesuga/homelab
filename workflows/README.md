# N8n Workflow Templates

This directory contains ready-to-use N8n workflow templates for your homelab.

---

## Available Workflows

### litellm-test-workflow.json

**Purpose**: Test your LiteLLM API integration with N8n

**What it does**:
1. Accepts a question
2. Sends it to your local LLM (via LiteLLM)
3. Returns the answer with token usage stats

**Nodes**:
- Manual Trigger
- Set (define question)
- HTTP Request (call LiteLLM API)
- Set (format response)

**How to import**:
1. Open N8n: http://100.81.76.55:30678
2. Go to **Workflows** → **⋮** → **Import from File**
3. Select `litellm-test-workflow.json`
4. Click **Import**
5. Click **Execute Workflow** to test

**Models available**:
- `gpt-3.5-turbo` - Llama 3.1 8B (general purpose)
- `mistral` - Mistral 7B (fast)
- `qwen-coder` - Qwen 14B (code generation)

---

## How to Use These Workflows

### Method 1: Import via UI

1. Download or copy the workflow JSON file
2. In N8n: **Workflows** → **⋮** → **Import from File**
3. Paste JSON or upload file
4. Click **Import**

### Method 2: Import via curl

```bash
# Copy workflow file to N8n pod
kubectl cp workflows/litellm-test-workflow.json homelab/n8n-xxxxx:/tmp/

# Access N8n pod
kubectl exec -it -n homelab n8n-xxxxx -- /bin/sh

# Import via N8n CLI (if available)
# Or import manually via UI
```

### Method 3: Direct Copy-Paste

1. Open the JSON file
2. Copy all contents
3. In N8n: **Workflows** → **⋮** → **Import from File**
4. Paste JSON
5. Click **Import**

---

## Customizing Workflows

### Change the Model

Edit the HTTP Request body:
```json
{
  "model": "mistral",  // Change to: gpt-3.5-turbo, mistral, or qwen-coder
  "messages": [...]
}
```

### Change the Prompt

Edit the message content:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Your new prompt here"
    }
  ]
}
```

### Add System Prompt

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant specializing in DevOps."
    },
    {
      "role": "user",
      "content": "{{ $json.question }}"
    }
  ]
}
```

### Adjust Response Length

```json
{
  "max_tokens": 100   // Short: 100-200
                      // Medium: 500-1000
                      // Long: 2000-4000
}
```

### Control Creativity

```json
{
  "temperature": 0.2  // Focused, deterministic
                      // Default: 0.7
                      // Creative: 1.0+
}
```

---

## Creating Your Own Workflows

### Basic Structure

```
Trigger Node (Manual, Webhook, Schedule, etc.)
  ↓
Data Preparation (Set, Code, etc.)
  ↓
HTTP Request to LiteLLM
  ↓
Process Response
  ↓
Output (Email, Slack, Database, etc.)
```

### LiteLLM HTTP Request Template

Use this in any workflow:

```json
{
  "method": "POST",
  "url": "http://100.72.98.106:8000/v1/chat/completions",
  "headers": {
    "Authorization": "Bearer {{ $json.litellm_api_key }}",
    "Content-Type": "application/json"
  },
  "body": {
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "{{ $json.your_input }}"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

---

## Common Workflow Patterns

### Pattern 1: Question → Answer

```
Manual Trigger → Set Question → LiteLLM → Display
```

### Pattern 2: Scheduled Analysis

```
Schedule (daily) → Get Data → LiteLLM Analysis → Email Report
```

### Pattern 3: Event-Driven Processing

```
Webhook → Extract Data → LiteLLM Processing → Take Action
```

### Pattern 4: Multi-Step AI

```
Trigger → LiteLLM (plan) → Execute Plan → LiteLLM (review) → Output
```

---

## Example Ideas

### Email Summarizer
Summarize incoming emails and send to Slack

### Code Reviewer
Review GitHub PRs automatically

### Alert Analyzer
Analyze Prometheus alerts and suggest fixes

### Daily Report
Generate daily homelab status report

### Smart Home
Process sensor data and make decisions

### Content Generator
Generate blog posts, documentation, etc.

### Data Analyzer
Analyze CSV/JSON data and provide insights

### Chatbot
Create a custom chatbot for your team

---

## Workflow Best Practices

### 1. Error Handling

Add **IF** nodes to check for errors:
```
HTTP Request
  ↓
IF (check if response is valid)
  ├─ Success → Continue
  └─ Error → Send Alert
```

### 2. Logging

Log LLM calls to database:
```
After LiteLLM Response
  ↓
Insert to PostgreSQL (track usage, cost, etc.)
```

### 3. Caching

Cache frequent responses:
```
Check Redis Cache
  ├─ Hit → Return cached
  └─ Miss → Call LiteLLM → Store in Redis
```

### 4. Rate Limiting

Control how often workflows run:
```
Check last run time
  ├─ Too soon → Skip
  └─ OK → Continue
```

### 5. Token Management

Monitor token usage:
```
After LiteLLM
  ↓
Extract usage.total_tokens
  ↓
If > 1000 → Send alert
```

---

## Testing Workflows

### Test in N8n UI

1. Open workflow
2. Click **Execute Workflow**
3. View results in each node
4. Check **Execution History** for logs

### Test via API

```bash
# Trigger via webhook (if workflow has webhook trigger)
curl -X POST http://100.81.76.55:30678/webhook/your-webhook-id \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'
```

### Test with Manual Trigger

Use the **Manual Trigger** node during development, then switch to:
- **Webhook Trigger** for API access
- **Schedule Trigger** for automated runs
- **Email Trigger** for email-based workflows

---

## Workflow Credentials

### LiteLLM API

Already configured in `litellm-test-workflow.json`:
```
API Key: Set via N8n credentials (variable: litellm_api_key)
Base URL: http://100.72.98.106:8000/v1
```

### Adding Other Services

**PostgreSQL**:
```
Host: postgres.homelab.svc.cluster.local
Port: 5432
Database: homelab
User: homelab
Password: Set via N8n credentials (variable: postgres_password)
```

**Redis**:
```
Host: redis.homelab.svc.cluster.local
Port: 6379
```

---

## Contributing Workflows

If you create useful workflows:

1. Export from N8n (Workflows → ⋮ → Export)
2. Save to this directory: `workflows/your-workflow-name.json`
3. Add description to this README
4. Commit and push

---

## Resources

- **N8n Docs**: https://docs.n8n.io
- **LiteLLM API**: http://100.72.98.106:8000/docs
- **Integration Guide**: `../docs/N8N-LITELLM-INTEGRATION.md`
- **Visual Guide**: `../docs/N8N-LITELLM-VISUAL-GUIDE.md`
- **Quick Reference**: `../docs/N8N-NODES-FOR-LITELLM.md`

---

## Support

Having issues?

1. Check workflow execution logs in N8n
2. Test LiteLLM API directly:
   ```bash
   curl http://100.72.98.106:8000/health
   ```
3. Check compute node:
   ```bash
   systemctl status litellm
   systemctl status ollama
   ```
4. Review documentation in `docs/`

---

**Last Updated**: 2025-10-24
**Workflows**: 1
**Status**: Production Ready ✅
