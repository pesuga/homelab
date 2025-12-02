# Chat Logging Deployment Guide

This guide shows how to deploy the comprehensive chat logging system for the Family Assistant API.

## 📋 Overview

The chat logging system captures all interactions with llama.cpp including:
- User prompts and AI responses
- System prompts and context
- Token economics and costs
- Performance metrics and latency
- Memory system interactions
- Session tracking and user analytics

## 🚀 **Deployment Steps**

### 1. Build Updated API Image

```bash
# Navigate to API directory
cd /home/pesu/Rakuflow/systems/homelab/services/family-api

# Build image with chat logging
docker build -t 100.81.76.55:30500/family-api:v2.4.0-chat-logging .

# Push to registry (when registry is available)
docker push 100.81.76.55:30500/family-api:v2.4.0-chat-logging
```

### 2. Update Deployment Configuration

Add volume mount for log directory:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: family-assistant-api
  namespace: fa-platform
spec:
  template:
    spec:
      containers:
      - name: family-assistant-api
        image: 100.81.76.55:30500/family-api:v2.4.0-chat-logging
        volumeMounts:
        - name: chat-logs
          mountPath: /var/log/family-assistant/chat-sessions
        env:
        # Add chat logging configuration
        - name: CHAT_LOG_ENABLED
          value: "true"
        - name: CHAT_LOG_DIR
          value: "/var/log/family-assistant/chat-sessions"
        - name: CHAT_LOG_RETENTION_DAYS
          value: "30"
        - name: CHAT_LOG_COMPRESSION_DAYS
          value: "7"
        # Existing environment variables...
      volumes:
      - name: chat-logs
        hostPath:
          path: /var/log/family-assistant/chat-sessions
          type: DirectoryOrCreate
```

### 3. Create Persistent Volume for Logs

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: chat-logs-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /var/log/family-assistant/chat-sessions
    type: DirectoryOrCreate
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: chat-logs-pvc
  namespace: fa-platform
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 4. Deploy Updated Service

```bash
# Apply the updated deployment
kubectl apply -f k8s/family-assistant-api-deployment.yaml

# Wait for rollout
kubectl rollout status deployment/family-assistant-api -n fa-platform

# Verify new pod is running
kubectl get pods -n fa-platform -l app=family-assistant-api
```

### 5. Verify Logging is Working

```bash
# Check if log directory is created
kubectl exec -n fa-platform deployment/family-assistant-api -- ls -la /var/log/family-assistant/chat-sessions/

# Generate test chat session to create logs
curl -X POST https://api.fa.pesulabs.net/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test logging", "user_id": "test-user"}'

# Check log files
kubectl exec -n fa-platform deployment/family-assistant-api -- find /var/log/family-assistant/chat-sessions -name "*.ndjson"
```

## 📊 **Testing the Analysis Tools**

### 1. Test CLI Analyzer

```bash
# SSH to service node
ssh pesu@100.75.194.1

# Run daily summary
./scripts/keep/chat-log-analyzer.sh --date today --summary --tokens --performance

# User-specific analysis
./scripts/keep/chat-log-analyzer.sh --user "test-user" --last-week --cost

# Export to JSON
./scripts/keep/chat-log-analyzer.sh --date today --export-json daily-report.json
```

### 2. Test Daily Summary Generator

```bash
# Generate automated daily report
./scripts/keep/daily-summary-generator.py --date today --output-dir /tmp/reports

# Generate weekly report
./scripts/keep/daily-summary-generator.py --last-week --output-dir /tmp/reports
```

## 🔧 **Configuration Options**

### Chat Logging Settings

```python
# In settings.py
CHAT_LOG_DIR = "/var/log/family-assistant/chat-sessions"
CHAT_LOG_RETENTION_DAYS = 30
CHAT_LOG_COMPRESSION_DAYS = 7
CHAT_LOG_BATCH_SIZE = 10
CHAT_LOG_FLUSH_INTERVAL_SECONDS = 5.0
CHAT_LOG_MAX_QUEUE_SIZE = 1000
CHAT_LOG_ENABLED = True
```

### Token Cost Configuration

```python
TOKEN_COSTS_PER_MILLION = {
    "Kimi-VL-A3B": 0.20,
    "Mistral-7B": 0.15,
    "Mixtral-8x7B": 0.35,
    "Llama-3.1-8B": 0.18,
    "default": 0.20
}
```

## 📈 **Production Log Access**

### Direct SSH Access

```bash
# Access logs on service node
ssh pesu@100.75.194.1
ls -la /var/log/family-assistant/chat-sessions/$(date +%Y-%m-%d)/
```

### Kubernetes Access

```bash
# Copy logs from pod
kubectl cp family-assistant-api-xxxx:/var/log/family-assistant/chat-sessions/2025-12-01/chat-sessions-2025-12-01.ndjson ./local-analysis/

# Access logs in real-time
kubectl exec -it deployment/family-assistant-api -n fa-platform -- tail -f /var/log/family-assistant/chat-sessions/$(date +%Y-%m-%d)/chat-sessions-$(date +%Y-%m-%d).ndjson
```

### Remote Analysis

```bash
# Run analysis remotely via SSH
ssh pesu@100.75.194.1 "/home/pesu/Rakuflow/systems/homelab/scripts/keep/chat-log-analyzer.sh --date today --summary --tokens"
```

## 🗂️ **Log File Format**

### NDJSON Structure

```json
{
  "timestamp": "2025-12-01T15:30:00.123Z",
  "session_id": "sess_abc123",
  "thread_id": "thread_xyz789",
  "user_id": "user_456",
  "request": {
    "message": "Hello, how can you help me?",
    "timestamp": "2025-12-01T15:30:00.123Z",
    "metadata": {}
  },
  "response": {
    "message": "I'm here to help! What do you need?",
    "timestamp": "2025-12-01T15:30:02.456Z",
    "model": "Kimi-VL-A3B-Thinking-2506-Q4_K_M",
    "metadata": {}
  },
  "token_economics": {
    "prompt_tokens": 15,
    "completion_tokens": 22,
    "total_tokens": 37,
    "model_used": "Kimi-VL-A3B-Thinking-2506-Q4_K_M",
    "estimated_cost_usd": 0.000008
  },
  "performance": {
    "http_request_ms": 2456,
    "generation_ms": 2100,
    "memory_retrieval_ms": 156,
    "prompt_assembly_ms": 89,
    "total_latency_ms": 2456
  },
  "system_prompt": "You are a helpful AI assistant...",
  "memory_context": {
    "redis_hits": 2,
    "mem0_retrieved": 1,
    "qdrant_searches": 1
  }
}
```

### Directory Structure

```
/var/log/family-assistant/chat-sessions/
├── 2025-12-01/
│   ├── chat-sessions-2025-12-01.ndjson
│   ├── session-summary-2025-12-01.json
│   └── errors-2025-12-01.ndjson
├── 2025-12-02/
│   ├── chat-sessions-2025-12-02.ndjson
│   ├── session-summary-2025-12-02.json
│   └── errors-2025-12-02.ndjson
└── compressed/
    ├── chat-sessions-2025-11-24.ndjson.gz
    └── session-summary-2025-11-24.json.gz
```

## 🤖 **Automation Setup**

### Cron Job for Daily Analysis

```bash
# Edit crontab
crontab -e

# Add daily summary generation at 2 AM
0 2 * * * /home/pesu/Rakuflow/systems/homelab/scripts/keep/daily-summary-generator.py --date $(date +\%Y-\%m-\%d) --output-dir /var/log/family-assistant/reports

# Add weekly cleanup of old logs (keep 30 days)
0 3 * * 0 find /var/log/family-assistant/chat-sessions -type d -mtime +30 -exec rm -rf {} \;

# Add compression of old logs (older than 7 days)
0 4 * * * find /var/log/family-assistant/chat-sessions -name '*.ndjson' -mtime +7 -exec gzip {} \;
```

### Kubernetes CronJob Alternative

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: chat-log-daily-summary
  namespace: fa-platform
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: log-analyzer
            image: 100.81.76.55:30500/family-api:v2.4.0-chat-logging
            volumeMounts:
            - name: chat-logs
              mountPath: /var/log/family-assistant/chat-sessions
            command: ["/scripts/keep/daily-summary-generator.py", "--date", "$(date +%Y-%m-%d)"]
          volumes:
          - name: chat-logs
            persistentVolumeClaim:
              claimName: chat-logs-pvc
          restartPolicy: OnFailure
```

## 🆘 **Troubleshooting**

### Common Issues

1. **Log Directory Not Created**
   - Check if volume mount is correctly configured
   - Verify pod has write permissions to log directory
   - Check if CHAT_LOG_ENABLED=true is set

2. **No Log Files Generated**
   - Verify chat endpoints are being called
   - Check application logs for errors
   - Ensure chat logger service is initialized

3. **Analysis Script Errors**
   - Check if jq and bc are installed: `which jq bc`
   - Verify log file permissions
   - Check JSON format validity

### Debug Commands

```bash
# Check pod logs for chat logger issues
kubectl logs -f deployment/family-assistant-api -n fa-platform | grep -i "chat"

# Verify log directory exists and is writable
kubectl exec deployment/family-assistant-api -n fa-platform -- test -w /var/log/family-assistant/chat-sessions

# Check if chat logger is running
kubectl exec deployment/family-assistant-api -n fa-platform -- ps aux | grep -i chat

# Test JSON parsing
kubectl exec deployment/family-assistant-api -n fa-platform -- cat /var/log/family-assistant/chat-sessions/$(date +%Y-%m-%d)/chat-sessions-$(date +%Y-%m-%d).ndjson | jq . | head -1
```

## 📞 **Support**

If you encounter issues with the chat logging deployment:

1. **Check this guide** for common solutions
2. **Review the production log access guide** at `/scripts/keep/production-log-access-guide.md`
3. **Test with demo data** using the scripts in `/scripts/keep/`
4. **Check application logs** for chat logger initialization messages
5. **Verify volume mounts** and permissions

The chat logging system will provide comprehensive insights into your AI assistant usage patterns, performance, and costs once deployed! 🚀