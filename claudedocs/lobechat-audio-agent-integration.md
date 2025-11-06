# LobeChat Audio + Whisper STT + Flowise Agent Integration

**Date**: 2025-11-04
**Goal**: Enable voice input in LobeChat using Whisper STT, connected to Flowise chat agent

## Current Status

### ✅ Services Running
- **LobeChat**: Running at `https://chat.homelab.pesulabs.net` (2 pods, 1 healthy)
- **Whisper**: Running at `http://whisper.homelab.svc.cluster.local:9000` (2 pods healthy)
- **Flowise**: Running at `https://flowise.homelab.pesulabs.net` (1 pod healthy)

### ✅ Existing Configuration
- LobeChat already has `STT_SERVER_URL: http://whisper.homelab.svc.cluster.local:9000` configured
- Whisper API available with `/asr` and `/detect-language` endpoints
- LobeChat connected to Ollama LLM at `http://100.72.98.106:11434`

## Architecture Flow

```
User (Browser)
    ↓ [Voice Recording]
LobeChat Frontend
    ↓ [Audio File]
LobeChat Backend (STT_SERVER_URL)
    ↓ [POST /asr]
Whisper Service
    ↓ [Transcribed Text]
LobeChat (Text Processing)
    ↓ [Text Prompt]
Flowise Agent (OpenAI-compatible API)
    ↓ [Agent Response]
User (Text/TTS Response)
```

## Implementation Plan

### Phase 1: Test Whisper STT Integration
1. ✅ Verify Whisper API endpoints
2. ⏳ Test Whisper transcription with sample audio
3. ⏳ Verify LobeChat can call Whisper API
4. ⏳ Test voice recording in LobeChat UI

### Phase 2: Configure LobeChat for Whisper
1. ⏳ Update LobeChat config with correct STT settings
2. ⏳ Verify OpenAI-compatible STT format
3. ⏳ Test audio upload and transcription flow
4. ⏳ Debug any API format mismatches

### Phase 3: Create Flowise Chat Agent
1. ⏳ Access Flowise at https://flowise.homelab.pesulabs.net
2. ⏳ Create new chatflow with:
   - Chat model node (Ollama)
   - Conversation memory
   - Optional: RAG with Qdrant
   - Optional: Tools/functions
3. ⏳ Configure agent personality and behavior
4. ⏳ Test chatflow and get API endpoint

### Phase 4: Connect LobeChat to Flowise
1. ⏳ Configure LobeChat to use Flowise API
2. ⏳ Map Flowise chatflow to OpenAI-compatible format
3. ⏳ Test text chat flow first
4. ⏳ Test voice → STT → agent → response

### Phase 5: End-to-End Testing
1. ⏳ Record voice message in LobeChat
2. ⏳ Verify transcription appears
3. ⏳ Verify agent processes request
4. ⏳ Verify response is delivered
5. ⏳ Test TTS output (optional)

## Technical Details

### Whisper API Endpoints

**Transcription Endpoint**:
```bash
POST /asr
Content-Type: multipart/form-data

Parameters:
- audio_file: Audio file (WAV, MP3, FLAC, etc.)
- task: "transcribe" (default) or "translate"
- language: ISO language code (optional, auto-detect if not specified)
- initial_prompt: Optional prompt to guide transcription
- word_timestamps: Boolean (default: false)
- output: "json" (default), "txt", "srt", "vtt"
```

**Example Request**:
```bash
curl -X POST http://whisper.homelab.svc.cluster.local:9000/asr \
  -F "audio_file=@recording.wav" \
  -F "language=en" \
  -F "output=json"
```

**Example Response**:
```json
{
  "text": "This is the transcribed text",
  "language": "en",
  "segments": [...],
  "words": [...]
}
```

### LobeChat STT Configuration

**Current Config** (from ConfigMap):
```yaml
STT_SERVER_URL: http://whisper.homelab.svc.cluster.local:9000
ENABLE_STT: "1"
```

**What LobeChat Expects**:
- OpenAI-compatible STT API format
- Endpoint: `/v1/audio/transcriptions` (OpenAI format)
- OR custom endpoint mapping

**Potential Issue**: LobeChat might expect OpenAI `/v1/audio/transcriptions` format, but Whisper uses `/asr`

**Solutions**:
1. **Option A**: Add proxy/adapter layer to convert Whisper → OpenAI format
2. **Option B**: Configure LobeChat to use Whisper's native `/asr` endpoint
3. **Option C**: Use LobeChat's browser-based STT (Web Speech API) - already working

### Flowise Integration

**Flowise API Pattern**:
```
https://flowise.homelab.pesulabs.net/api/v1/prediction/{chatflowId}

POST /api/v1/prediction/{chatflowId}
{
  "question": "User's question here",
  "overrideConfig": {
    "sessionId": "unique-session-id"
  }
}
```

**LobeChat → Flowise Mapping**:
- Configure Flowise chatflow as OpenAI-compatible endpoint
- Use N8n or custom middleware to adapt API formats
- Or configure LobeChat to use Flowise's native API

## Testing Strategy

### Test 1: Whisper Transcription
```bash
# Download test audio
wget https://github.com/openai/whisper/raw/main/tests/jfk.flac -O /tmp/test.flac

# Test Whisper API
curl -X POST http://100.72.98.106:30900/asr \
  -F "audio_file=@/tmp/test.flac" \
  -F "language=en" \
  -F "output=json"

# Expected: {"text": "And so my fellow Americans..."}
```

### Test 2: LobeChat STT
1. Access LobeChat at https://chat.homelab.pesulabs.net
2. Click microphone icon
3. Record voice message
4. Verify transcription appears in chat
5. Check browser console for API calls
6. Check LobeChat logs for STT requests

### Test 3: Flowise Agent
1. Access Flowise at https://flowise.homelab.pesulabs.net
2. Create simple chatflow:
   - ChatOllama node
   - Simple conversation chain
3. Test via Flowise UI
4. Get API endpoint URL
5. Test via curl

### Test 4: End-to-End
1. Configure LobeChat to use Flowise agent
2. Send text message via LobeChat
3. Verify Flowise processes request
4. Send voice message via LobeChat
5. Verify STT → Flowise → response flow

## Known Issues & Solutions

### Issue 1: LobeChat STT Format Mismatch
**Problem**: LobeChat expects OpenAI `/v1/audio/transcriptions`, Whisper uses `/asr`

**Solution**:
- Check if LobeChat supports custom STT endpoints
- Or create N8n webhook to proxy requests
- Or use LobeChat's built-in browser STT (Web Speech API)

### Issue 2: Multiple LobeChat Pods (1 Crashing)
**Problem**: `lobechat-d67bd45d9-4nlfm` has 692 restarts

**Solution**:
```bash
# Delete the failing pod
kubectl delete pod lobechat-d67bd45d9-4nlfm -n homelab

# Or scale down to 1 replica
kubectl scale deployment lobechat -n homelab --replicas=1
```

### Issue 3: Flowise → LobeChat Integration
**Problem**: Flowise and LobeChat use different API formats

**Solutions**:
1. **OpenAI Proxy**: Use litellm or similar to create OpenAI-compatible wrapper for Flowise
2. **N8n Middleware**: Create N8n workflow to translate between APIs
3. **Direct Integration**: Configure LobeChat with custom model endpoint

## Quick Start Commands

```bash
# Check service status
kubectl get pods -n homelab -l app=lobechat
kubectl get pods -n homelab -l app=whisper
kubectl get pods -n homelab -l app=flowise

# Test Whisper
curl -X POST http://100.72.98.106:30900/asr \
  -F "audio_file=@test.wav" \
  -F "language=en"

# View LobeChat logs
kubectl logs -n homelab -l app=lobechat --tail=50

# View Whisper logs
kubectl logs -n homelab -l app=whisper --tail=50

# View Flowise logs
kubectl logs -n homelab -l app=flowise --tail=50

# Access services
# LobeChat: https://chat.homelab.pesulabs.net
# Flowise: https://flowise.homelab.pesulabs.net
# Whisper: http://100.72.98.106:30900/docs
```

## Next Steps

1. ✅ Document current architecture
2. ⏳ Test Whisper transcription with audio file
3. ⏳ Check LobeChat STT configuration format
4. ⏳ Create simple Flowise chatflow
5. ⏳ Test LobeChat → Flowise integration
6. ⏳ Test voice → STT → agent flow
7. ⏳ Document final configuration

## Success Criteria

- ✅ User can record voice in LobeChat
- ✅ Voice is transcribed via Whisper STT
- ✅ Transcribed text sent to Flowise agent
- ✅ Agent processes request and responds
- ✅ Response displayed in LobeChat
- ✅ Optional: TTS reads response aloud

---

**Status**: Ready to implement
**Next Action**: Test Whisper transcription and verify LobeChat STT integration
