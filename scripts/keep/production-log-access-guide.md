# Production Log Access Guide

This guide shows how to run the chat log analyzer script against production logs once the Family Assistant API with chat logging is deployed.

## 📋 Prerequisites

1. **Chat Logging Feature** must be deployed (not yet deployed)
2. **SSH access** to service node (asuna: 100.81.76.55)
3. **kubectl access** to the Kubernetes cluster
4. **Required tools**: jq, bc (already in most systems)

## 🗂️ **Production Log Locations**

### Primary Location: Service Node
```
ssh pesu@100.75.194.1
/var/log/family-assistant/chat-sessions/
├── 2025-12-01/
│   ├── chat-sessions-2025-12-01.ndjson
│   ├── session-summary-2025-12-01.json
│   └── errors-2025-12-01.ndjson
└── 2025-12-02/
```

### Alternative: Pod Volume Mount
If logs are mounted in pods:
```
kubectl exec family-assistant-api-xxxxx -n fa-platform -- ls /var/log/family-assistant/chat-sessions/
```

## 🚀 **Running Production Analysis**

### Method 1: Direct SSH Access (Recommended)

```bash
# SSH to service node
ssh pesu@100.81.76.55

# Run analysis on service node
./scripts/keep/chat-log-analyzer.sh --date today --summary --tokens --performance

# User-specific analysis for last week
./scripts/keep/chat-log-analyzer.sh --user "user123" --last-week --cost

# Find slow requests
./scripts/keep/chat-log-analyzer.sh --date today --slow-requests --threshold 5000
```

### Method 2: Remote Script Execution

```bash
# Copy script to service node (one-time setup)
scp /home/pesu/Rakuflow/systems/homelab/scripts/keep/chat-log-analyzer.sh pesu@100.81.76.55:/tmp/

# Run analysis remotely
ssh pesu@100.81.76.55 "/tmp/chat-log-analyzer.sh --date today --summary"
```

### Method 3: Pod-Based Analysis

If logs are pod-mounted (alternative approach):

```bash
# Copy logs locally first
kubectl cp family-assistant-api-xxxxx:/var/log/family-assistant/chat-sessions/2025-12-01/*.ndjson ./tmp/

# Run analysis locally
./scripts/keep/chat-log-analyzer.sh --log-dir ./tmp --date 2025-12-01 --summary
```

### Method 4: Port-Forwarded Access

For direct access without SSH:

```bash
# Set up port forwarding to service node
ssh -L 9000:100.81.76.55:22 pesu@100.81.76.55

# In another terminal, access logs
curl http://localhost:9000/var/log/family-assistant/chat-sessions/2025-12-01/chat-sessions-2025-12-01.ndjson

# Or mount via SSHFS (advanced)
```

## 📊 **Common Production Analysis Commands**

### Daily Production Summary
```bash
ssh pesu@100.81.76.55 "./scripts/keep/chat-log-analyzer.sh --date $(date +%Y-%m-%d) --summary --tokens --performance --cost"
```

### Error Analysis (Production)
```bash
ssh pesu@100.81.76.55 "./scripts/keep/chat-log-analyzer.sh --date $(date +%Y-%m-%d) --errors --export-json production-errors-$(date +%Y-%m-%d).json"
```

### Performance Monitoring
```bash
ssh pesu@100.81.76.55 "./scripts/keep/chat-log-analyzer.sh --date $(date +%Y-%m-%d) --performance --slow-requests --threshold 5000"
```

### Cost Tracking
```bash
ssh pesu@100.81.76.55 "./scripts/keep/chat-log-analyzer.sh --last-week --cost --models"
```

### User Activity Analysis
```bash
ssh pesu@100.81.76.55 "./scripts/keep/chat-log-analyzer.sh --last-month --user 'user_id' --tokens"
```

## 🤖 **Automated Daily Reports**

### Cron Job on Service Node

Set up automated daily summary generation:

```bash
# SSH to service node
ssh pesu@100.81.76.55

# Edit crontab
crontab -e

# Add daily summary generation at 2 AM
0 2 * * * /home/pesu/Rakuflow/systems/homelab/scripts/keep/daily-summary-generator.py --date $(date +\%Y-\%m-\%d) --output-dir /var/log/family-assistant/reports

# Add weekly cleanup of old logs (keep 30 days)
0 3 * * 0 find /var/log/family-assistant/chat-sessions -type d -mtime +30 -exec rm -rf {} \;
```

### Kubernetes CronJob (Alternative)

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
            image: your-log-analyzer-image
            volumeMounts:
            - name: log-volume
              mountPath: /var/log/family-assistant
            command: ["/scripts/keep/daily-summary-generator.py", "--date", "$(date +\%Y-\%m-\%d)"]
          volumes:
          - name: log-volume
            hostPath:
              path: /var/log/family-assistant
              type: Directory
          restartPolicy: OnFailure
```

## 🔧 **Log Volume Configuration**

### Kubernetes PersistentVolume for Logs

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
      path: /var/log/family-assistant
      type: DirectoryOrCreate
```

### Pod Volume Mount Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: family-assistant-api
spec:
  template:
    spec:
      containers:
      - name: family-assistant-api
        volumeMounts:
        - name: chat-logs
          mountPath: /var/log/family-assistant/chat-sessions
      volumes:
      - name: chat-logs
        persistentVolumeClaim:
          claimName: chat-logs-pvc
```

## 📈 **Monitoring Log Health**

### Check Log Generation Status
```bash
# Check if logs are being generated
ssh pesu@100.81.76.55 "find /var/log/family-assistant/chat-sessions -name '*.ndjson' -mtime -1 | wc -l"

# Check disk usage
ssh pesu@100.81.76.55 "du -sh /var/log/family-assistant/"

# Check for errors in recent logs
ssh pesu@100.81.76.55 "find /var/log/family-assistant/chat-sessions -name 'errors-*.ndjson' -mtime -7 | head -5"
```

### Log Retention Enforcement
```bash
# Manual cleanup (run periodically)
ssh pesu@100.81.76.55 "
# Delete logs older than 30 days
find /var/log/family-assistant/chat-sessions -type d -mtime +30 -exec rm -rf {} \;

# Compress logs older than 7 days
find /var/log/family-assistant/chat-sessions -name '*.ndjson' -mtime +7 -exec gzip {} \;

# List current status
echo '=== Current Log Status ==='
du -sh /var/log/family-assistant/chat-sessions
find /var/log/family-assistant/chat-sessions -name '*.ndjson' | wc -l
find /var/log/family-assistant/chat-sessions -name '*.gz' | wc -l
"
```

## 🆘 **Troubleshooting**

### Common Issues

1. **Logs Not Generated Yet**
   - Solution: The chat logging feature needs to be deployed first
   - Check: `kubectl logs family-assistant-api-xxxxx -n fa-platform | grep -i "chat logger"`

2. **Permission Denied**
   - Solution: Ensure proper file permissions
   - Fix: `ssh pesu@100.81.76.55 "sudo mkdir -p /var/log/family-assistant/chat-sessions && sudo chown -R pesu:pesu /var/log/family-assistant"`

3. **Missing Dependencies**
   - Solution: Install required tools
   - Fix: `sudo apt-get update && sudo apt-get install -y jq bc`

4. **Disk Space Issues**
   - Solution: Implement log rotation and cleanup
   - Fix: Add the cleanup cronjob shown above

### Debug Commands
```bash
# Check API pod logs for chat logging status
kubectl logs family-assistant-api-xxxxx -n fa-platform | grep -i "chat"

# Verify log directory structure
ssh pesu@100.81.76.55 "ls -la /var/log/family-assistant/chat-sessions/"

# Test script with dry run
ssh pesu@100.81.76.55 "echo 'Testing script access...' && /home/pesu/Rakuflow/systems/homelab/scripts/keep/chat-log-analyzer.sh --help"
```

## 📞 **Support**

If you encounter issues with production log access:

1. **Check API Deployment Status**: Ensure the chat logging feature is deployed
2. **Verify Directory Permissions**: Confirm write access to log directory
3. **Test Script Functionality**: Run with `--help` to verify script is accessible
4. **Monitor Resource Usage**: Check disk space and memory on service node

The chat logging system will automatically create logs once the updated API is deployed, making these analysis commands fully functional! 🚀