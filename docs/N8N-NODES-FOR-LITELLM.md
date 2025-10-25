# Using LiteLLM in N8n - Which Nodes to Use

**TL;DR**: Use the **OpenAI** nodes in N8n with a custom base URL pointing to your LiteLLM server.

---

## Method 1: OpenAI Node (Recommended)

### Step 1: Add Credential

1. **Open N8n**: http://100.81.76.55:30678
2. **Settings** → **Credentials** → **+ Add Credential**
3. Search for: **OpenAI**
4. Select: **OpenAI API**
5. Configure:
   ```
   Credential Name: LiteLLM Local
   API Key: sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0

   [Advanced Options - Click to expand]:
   Base URL: http://100.72.98.106:8000/v1
   ```
6. **Save**

### Step 2: Find the Right Node

In N8n workflow editor, search for these nodes:

**Option A: "OpenAI" node** (older N8n versions)
- Search: `OpenAI`
- Node name: `OpenAI`
- This is a general OpenAI node

**Option B: "OpenAI Chat" or "Chat OpenAI"** (newer N8n versions)
- Search: `Chat` or `OpenAI`
- Node name might be: `Chat OpenAI`, `OpenAI Chat Model`, or similar
- This is specifically for chat completions

**Option C: Look in AI category**
- Click the `+` button in workflow
- Look for **AI** or **Language Models** section
- Find any OpenAI-related node

### Step 3: Configure the Node

Once you add the OpenAI node:

```
Credential: LiteLLM Local
Resource: Chat (or Message, depending on version)
Operation: Create / Complete

Model: gpt-3.5-turbo
Message/Prompt: Your prompt here

[Optional]:
Temperature: 0.7
Max Tokens: 500
```

### Example Configuration:

**If using "OpenAI" node**:
```
Resource: Chat
Operation: Message
Model: gpt-3.5-turbo
Prompt: {{ $json.question }}
```

**If using newer Chat node**:
```
Model: gpt-3.5-turbo
Messages:
  - Role: system
    Content: You are a helpful assistant
  - Role: user
    Content: {{ $json.question }}
```

---

## Method 2: HTTP Request Node (Always Works)

If you can't find the OpenAI node, use the **HTTP Request** node directly:

### Step 1: Add HTTP Request Node

1. Search: `HTTP Request`
2. Add to workflow

### Step 2: Configure

```
Method: POST
URL: http://100.72.98.106:8000/v1/chat/completions

Authentication: Header Auth
  Header Name: Authorization
  Header Value: Bearer sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0

Body Content Type: JSON
Body:
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.question }}"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

### Step 3: Parse Response

Add a **Set** node after HTTP Request:

```
response: {{ $json.choices[0].message.content }}
```

---

## Complete Workflow Examples

### Example 1: Using HTTP Request Node (Ready to Import)

Copy this JSON and import it into N8n:

```json
{
  "name": "LiteLLM Test - HTTP Request",
  "nodes": [
    {
      "parameters": {},
      "id": "manual-trigger",
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "question",
              "value": "What are the benefits of running a homelab?"
            }
          ]
        }
      },
      "id": "set-question",
      "name": "Set Question",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://100.72.98.106:8000/v1/chat/completions",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "Bearer sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "model",
              "value": "gpt-3.5-turbo"
            },
            {
              "name": "messages",
              "value": "={{ [{\"role\": \"user\", \"content\": $json.question}] }}"
            },
            {
              "name": "temperature",
              "value": "0.7"
            },
            {
              "name": "max_tokens",
              "value": "500"
            }
          ]
        },
        "options": {}
      },
      "id": "http-request",
      "name": "Call LiteLLM",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [650, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "question",
              "value": "={{ $('Set Question').item.json.question }}"
            },
            {
              "name": "answer",
              "value": "={{ $json.choices[0].message.content }}"
            },
            {
              "name": "model",
              "value": "={{ $json.model }}"
            },
            {
              "name": "tokens_used",
              "value": "={{ $json.usage.total_tokens }}"
            }
          ]
        }
      },
      "id": "format-response",
      "name": "Format Response",
      "type": "n8n-nodes-base.set",
      "typeVersion": 1,
      "position": [850, 300]
    }
  ],
  "connections": {
    "Manual Trigger": {
      "main": [
        [
          {
            "node": "Set Question",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Set Question": {
      "main": [
        [
          {
            "node": "Call LiteLLM",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Call LiteLLM": {
      "main": [
        [
          {
            "node": "Format Response",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {}
}
```

### How to Import:

1. In N8n, click **Workflows** → **Import from File**
2. Paste the JSON above
3. Click **Import**
4. Click **Execute Workflow**

---

## Example 2: Simpler Version

```json
{
  "name": "Simple LiteLLM Test",
  "nodes": [
    {
      "parameters": {},
      "name": "When clicking 'Test workflow'",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://100.72.98.106:8000/v1/chat/completions",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "Bearer sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0"
            }
          ]
        },
        "sendBody": true,
        "contentType": "json",
        "body": "={\n  \"model\": \"gpt-3.5-turbo\",\n  \"messages\": [\n    {\n      \"role\": \"user\",\n      \"content\": \"Write a haiku about homelab servers\"\n    }\n  ]\n}",
        "options": {}
      },
      "name": "LiteLLM API Call",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [460, 300]
    }
  ],
  "connections": {
    "When clicking 'Test workflow'": {
      "main": [
        [
          {
            "node": "LiteLLM API Call",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

---

## Troubleshooting

### "Node not found" or "Can't find OpenAI node"

**Solution**: Use the HTTP Request node method above. It always works in any N8n version.

### "Connection refused"

**Check**:
```bash
# Is LiteLLM running?
systemctl status litellm

# Can you reach it?
curl http://100.72.98.106:8000/health

# Are you on Tailscale network?
tailscale status
```

### "Authentication failed"

**Check**:
- API key is correct: `sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0`
- Authorization header format: `Bearer <key>` (note the space)
- Base URL in credential: `http://100.72.98.106:8000/v1` (with /v1)

### "Empty response"

**Check**:
- Model name is correct: `gpt-3.5-turbo`, `mistral`, or `qwen-coder`
- Messages format is correct (array of objects with role/content)
- Max tokens isn't too low (try 500+)

---

## Available Models

Use these model names in your requests:

```json
"model": "gpt-3.5-turbo"  // Llama 3.1 8B - General purpose
"model": "mistral"         // Mistral 7B - Fast
"model": "qwen-coder"      // Qwen 14B - Code generation
```

---

## Testing with curl (Outside N8n)

Before testing in N8n, verify the API works:

```bash
# Test without auth (should fail)
curl -X POST http://100.72.98.106:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}]}'

# Should return: {"error": {"message": "Authentication Error, No api key passed in."}}

# Test with auth (should work)
curl -X POST http://100.72.98.106:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-zwcYHyyR9rx7stuFhocu3_gErZShHqCxsnPDpcDr4m0" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Say hi"}],
    "max_tokens": 20
  }'

# Should return: {"id": "...", "choices": [{"message": {"content": "Hello! ..."}}]}
```

---

## Next Steps

1. ✅ Import one of the workflow JSONs above
2. ✅ Test it
3. ✅ Modify the prompt to your needs
4. ✅ Build more complex workflows

---

## Pro Tips

### Use Variables for Model Selection

```json
{
  "model": "={{ $('Set Config').item.json.model_choice }}",
  "messages": [...]
}
```

### Stream Responses (for long outputs)

Add to request body:
```json
{
  "stream": false  // Keep false for N8n (easier to parse)
}
```

### Add System Prompts

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful DevOps assistant specializing in Kubernetes."
    },
    {
      "role": "user",
      "content": "{{ $json.question }}"
    }
  ]
}
```

---

**Summary**:
- ✅ Use **HTTP Request** node (always works)
- ✅ Or use **OpenAI** node if available in your N8n version
- ✅ Import the workflow JSON above to get started quickly
