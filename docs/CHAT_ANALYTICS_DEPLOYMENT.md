# Chat Analytics Deployment Guide

**Date**: 2025-12-03
**Commit**: ba6e461

## Changes Summary

### Backend (family-api)
- Modified: `services/family-api/src/api/services/chat_logger.py`
- Created: `services/family-api/src/api/services/loki_service.py`
- Modified: `services/family-api/src/api/routes/analytics.py`

### Frontend (family-admin)
- Modified: `infrastructure/admin-tools/family-admin/src/types/analytics.ts`
- Modified: `infrastructure/admin-tools/family-admin/src/lib/api-client.ts`
- Modified: `infrastructure/admin-tools/family-admin/src/hooks/useAnalytics.ts`
- Modified: `infrastructure/admin-tools/family-admin/src/app/(admin)/analytics/sub-agents/page.tsx`

## Deployment Steps

### Option 1: Automated (Recommended - via GitHub Actions)

**Status**: ⚠️ Not Available Yet
- Family API: No automated build configured
- Family Admin: No automated build configured

**Future Enhancement**: Create GitHub Actions workflows similar to `build-family-portal.yaml`

### Option 2: Manual Build & Deploy

#### Step 1: Build Family API Image
```bash
cd services/family-api

# Build Docker image
docker build -t ghcr.io/pesuga/homelab/family-api:latest .

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u pesuga --password-stdin

# Push image
docker push ghcr.io/pesuga/homelab/family-api:latest
```

#### Step 2: Build Family Admin Image
```bash
cd infrastructure/admin-tools/family-admin

# Build Docker image
docker build -t ghcr.io/pesuga/homelab/family-admin:latest .

# Push image
docker push ghcr.io/pesuga/homelab/family-admin:latest
```

#### Step 3: Restart Kubernetes Deployments
```bash
# Restart family-api pod to pull new image
kubectl rollout restart deployment/family-assistant-backend -n homelab

# Restart family-admin pod to pull new image
kubectl rollout restart deployment/family-admin -n homelab

# Monitor rollout status
kubectl rollout status deployment/family-assistant-backend -n homelab
kubectl rollout status deployment/family-admin -n homelab
```

#### Step 4: Verify Deployment
```bash
# Check pod logs for errors
kubectl logs -f deployment/family-assistant-backend -n homelab --tail=50
kubectl logs -f deployment/family-admin -n homelab --tail=50

# Test API endpoints
curl -H "Authorization: Bearer <token>" \
  https://api.fa.pesulabs.net/api/v1/analytics/chat/overview?range=24h

# Test admin UI
curl https://admin.fa.pesulabs.net/
```

## Verification Steps

### 1. Check Chat Logs in Loki
```bash
# Port-forward Loki
kubectl port-forward -n homelab svc/loki 3100:3100 &

# Query for chat logs
curl -G 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={app="family-api"} | json | type="chat_session_log"' \
  --data-urlencode "start=$(date -u -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date -u +%s)000000000"
```

### 2. Test API Endpoints
```bash
# Get chat overview
curl -H "Authorization: Bearer <token>" \
  https://api.fa.pesulabs.net/api/v1/analytics/chat/overview?range=24h

# Get chat logs
curl -H "Authorization: Bearer <token>" \
  https://api.fa.pesulabs.net/api/v1/analytics/chat/logs?limit=10&range=24h

# Get token stats
curl -H "Authorization: Bearer <token>" \
  https://api.fa.pesulabs.net/api/v1/analytics/chat/tokens?range=7d
```

### 3. Verify Frontend
1. Navigate to https://admin.fa.pesulabs.net/analytics/sub-agents
2. Click "Chat Logs" tab
3. Verify:
   - Overview metrics display
   - Token usage chart renders
   - Chat sessions table populates
   - Time range selector works

## Troubleshooting

### No Logs Appearing in Loki
1. Check pod logs: `kubectl logs -n homelab <family-api-pod>`
2. Verify JSON format with `"type": "chat_session_log"`
3. Check Promtail is running: `kubectl get pods -n homelab -l app=promtail`
4. Query Loki directly (port-forward test)

### API Endpoint Errors
1. Check Loki connectivity: `http://loki.homelab.svc.cluster.local:3100`
2. Verify authentication headers
3. Check LogQL query syntax in Loki service
4. Review API pod logs for errors

### Frontend Not Loading Data
1. Verify API endpoints return data (curl test)
2. Check browser console for errors
3. Verify authentication/authorization
4. Test with different time ranges

## Next Actions

1. **Create GitHub Actions Workflows** (recommended):
   - `.github/workflows/build-family-api.yaml`
   - `.github/workflows/build-family-admin.yaml`
   - Follow pattern from `build-family-portal.yaml`

2. **Update ARCHITECTURE.md**:
   - Mark Family API as automated CI/CD once workflow created
   - Mark Family Admin as automated CI/CD once workflow created

3. **Generate Test Data**:
   - Use main chat interface to generate chat sessions
   - Wait ~1 minute for logs to appear in Loki
   - Verify Chat Logs tab updates
