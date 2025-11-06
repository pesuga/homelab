# Quick Start: LobeChat Voice + Whisper + Flowise

## Summary

You have all the pieces running! Here's what you need to do:

### ✅ Already Working
1. **Whisper STT**: `http://whisper.homelab.svc.cluster.local:9000` - Running and ready
2. **LobeChat**: `https://chat.homelab.pesulabs.net` - Already configured to use Whisper
3. **Flowise**: `https://flowise.homelab.pesulabs.net` - Ready for agent creation

### 🎯 What We Need to Do

#### Step 1: Fix LobeChat STT Configuration (10 min)
LobeChat is configured with `STT_SERVER_URL: http://whisper.homelab.svc.cluster.local:9000`, but we need to verify the API format compatibility.

**Potential Issue**: LobeChat might expect OpenAI's `/v1/audio/transcriptions` endpoint, but Whisper uses `/asr`.

**Quick Fix Options**:
1. **Use Browser STT** (already working): LobeChat has built-in Web Speech API
2. **Test if Whisper endpoint works**: Check if LobeChat can adapt to `/asr` format
3. **Create API adapter**: Small N8n workflow or proxy to translate formats

#### Step 2: Create Flowise Chat Agent (15 min)
1. Go to https://flowise.homelab.pesulabs.net
2. Create new chatflow:
   - Add "Chat Ollama" node (connect to `http://100.72.98.106:11434`)
   - Add "Conversation Chain" or "Agent" node
   - Optional: Add "Qdrant" for RAG/memory
   - Optional: Add tools/functions
3. Test chatflow in Flowise UI
4. Get API endpoint: `/api/v1/prediction/{chatflowId}`

#### Step 3: Connect LobeChat to Flowise (20 min)
**Option A - Direct**: Configure LobeChat to use Flowise as custom model provider
**Option B - Via N8n**: Create webhook workflow to proxy LobeChat → Flowise
**Option C - Via LiteLLM**: Use LiteLLM router to expose Flowise as OpenAI-compatible endpoint

#### Step 4: Test End-to-End (5 min)
1. Open LobeChat
2. Click microphone icon
3. Speak: "Hello, test message"
4. Verify:
   - Transcription appears
   - Message sent to agent
   - Response received

## Immediate Next Steps

### Test 1: Verify Whisper Works
```bash
# Download test audio (JFK speech)
wget https://github.com/openai/whisper/raw/main/tests/jfk.flac -O /tmp/test.flac

# Test Whisper API
curl -X POST http://100.72.98.106:30900/asr \
  -F "audio_file=@/tmp/test.flac" \
  -F "language=en" \
  -F "output=json"

# Should return: {"text": "And so my fellow Americans..."}
```

### Test 2: Try LobeChat Voice Input
1. Go to https://chat.homelab.pesulabs.net
2. Start new chat
3. Click microphone button
4. Say something in Spanish (default language is es-ES)
5. Check if transcription appears

**If it works**: Browser STT is active (no Whisper needed for basic function)
**If it doesn't work**: Need to configure Whisper integration properly

### Test 3: Create Simple Flowise Agent
1. Access Flowise: https://flowise.homelab.pesulabs.net (admin/flowise2025)
2. Click "Add New Chatflow"
3. Drag these nodes:
   - **Chat Models** → **ChatOllama**
     - Base URL: `http://100.72.98.106:11434`
     - Model: `llama3.1:8b`
   - **Chains** → **Conversation Chain**
     - Connect ChatOllama to it
4. Click "Save" and then "Deploy"
5. Test in Flowise chat window
6. Copy API endpoint from settings

## Current Architecture

```
LobeChat Frontend (Browser)
    ↓
[Built-in Web Speech API for STT]
    ↓
LobeChat Backend
    ↓
[Currently: Direct to Ollama]
Ollama LLM (http://100.72.98.106:11434)
```

**Goal Architecture**:
```
LobeChat Frontend (Browser)
    ↓
[Voice Recording]
    ↓
Whisper STT (http://whisper.homelab.svc.cluster.local:9000/asr)
    ↓
[Transcribed Text]
    ↓
Flowise Agent (https://flowise.homelab.pesulabs.net/api/v1/prediction/{id})
    ↓
[Agent processes with Ollama + tools/RAG]
    ↓
LobeChat (Display response)
```

## Troubleshooting

### LobeChat Not Using Whisper
**Check**:
```bash
# View LobeChat config
kubectl get configmap lobechat-config -n homelab -o yaml | grep STT

# View LobeChat logs for STT requests
kubectl logs -n homelab -l app=lobechat --tail=100 | grep -i "stt\|whisper\|transcrib"
```

**Possible Issues**:
1. LobeChat using browser STT instead of server STT
2. API format mismatch between LobeChat and Whisper
3. Network connectivity issue

### Whisper Not Responding
**Check**:
```bash
# Test Whisper health
curl http://100.72.98.106:30900/docs

# View Whisper logs
kubectl logs -n homelab -l app=whisper --tail=50

# Test from inside cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://whisper.homelab.svc.cluster.local:9000/
```

### Flowise Agent Not Responding
**Check**:
```bash
# View Flowise logs
kubectl logs -n homelab -l app=flowise --tail=50

# Test Flowise API
curl -I https://flowise.homelab.pesulabs.net

# Check if chatflow exists
# Go to Flowise UI → Chatflows → verify your flow is deployed
```

## Configuration Files to Update

### If Whisper Integration Needed
Update `infrastructure/kubernetes/services/lobechat/lobechat.yaml`:
```yaml
# In ConfigMap data section, verify/update:
STT_SERVER_URL: "http://whisper.homelab.svc.cluster.local:9000"
ENABLE_STT: "1"
# May need to add:
STT_API_ENDPOINT: "/asr"  # If LobeChat supports custom endpoint
```

### If Flowise Integration Needed
Option 1 - Add Flowise as model provider in LobeChat UI:
- Settings → Model Providers → Add Custom Provider
- API Endpoint: `https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId}`
- Format: Custom

Option 2 - Update ConfigMap with Flowise endpoint:
```yaml
# Add to lobechat-config:
CUSTOM_MODELS: "flowise-agent"
FLOWISE_API_URL: "https://flowise.homelab.pesulabs.net"
FLOWISE_CHATFLOW_ID: "{your-chatflow-id}"
```

## What To Do First

**I recommend**:
1. **Test Whisper first** with the curl command above
2. **Create a simple Flowise agent** - this is independent and you can test it separately
3. **Try LobeChat voice** - see if browser STT works (it might already!)
4. **Then connect the pieces** - based on what works

Do you want me to:
- A) Help you test Whisper transcription now?
- B) Guide you through creating a Flowise agent?
- C) Test the current LobeChat voice input?
- D) All of the above in sequence?
