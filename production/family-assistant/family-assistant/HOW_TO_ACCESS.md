# How to Access and Experience Family Assistant

Complete guide to accessing, testing, and exploring the Family Assistant platform deployed in Week 1.

---

## 🌐 Live Application Access

### 1. Frontend Dashboard (HTTPS - Recommended)
```bash
https://family.homelab.pesulabs.net
```

**Features**:
- Beautiful cappuccino moka dark theme
- Real-time system monitoring
- Architecture visualization
- Family member management interface
- Zustand state management with DevTools

### 2. Backend API (HTTPS)
```bash
# Base API endpoint
https://family-api.homelab.pesulabs.net/api/v1/

# Health check
curl -k https://family-api.homelab.pesulabs.net/api/v1/health

# API documentation
https://family-api.homelab.pesulabs.net/docs

# Metrics
curl -k https://family-api.homelab.pesulabs.net/metrics
```

### 3. Direct NodePort Access (Development)
```bash
# Frontend
http://100.81.76.55:30300

# Backend
http://100.81.76.55:30080

# Test health
curl http://100.81.76.55:30300/health
curl http://100.81.76.55:30080/api/v1/health
```

---

## 🔍 Explore What Was Built

### Day 1: Authentication System
```bash
# Test login endpoint
curl -X POST https://family-api.homelab.pesulabs.net/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"

# Get current user profile (with token)
curl -k https://family-api.homelab.pesulabs.net/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify token
curl -k -X POST https://family-api.homelab.pesulabs.net/api/v1/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Day 2: Observability Stack
```bash
# Prometheus metrics
curl -k https://family-api.homelab.pesulabs.net/metrics | grep http_requests_total

# Check distributed tracing headers
curl -k -I https://family-api.homelab.pesulabs.net/api/v1/

# View structured JSON logs
kubectl logs -n homelab -l app=family-assistant --tail=20
```

### Day 3: Frontend Features

**Open in Browser** and explore:
- **Zustand State Management**: Browser DevTools → Redux DevTools extension
- **Optimistic Updates**: Edit family members, watch instant UI updates
- **API Integration**: Network tab shows JWT tokens in Authorization headers
- **Error Handling**: Disconnect backend, see graceful error recovery

**Browser DevTools Checklist**:
- F12 → Console: Structured logging
- F12 → Network: API calls with JWT tokens
- F12 → Redux DevTools: Zustand store inspection
- F12 → Application → Local Storage: Token storage

### Day 4: E2E Tests
```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant/frontend

# Interactive UI mode (BEST for exploring)
npm run test:e2e:ui

# Run with browser visible
npm run test:e2e:headed

# Run specific test
npx playwright test auth.spec.ts --headed

# Generate new tests
npm run test:e2e:codegen https://family.homelab.pesulabs.net

# View test report
npm run test:e2e:report
```

### Day 5: Production Deployment
```bash
# Check Kubernetes resources
kubectl get pods,svc,ingressroute -n homelab | grep family-assistant

# View logs
kubectl logs -n homelab -l app=family-assistant-frontend --tail=50
kubectl logs -n homelab -l app=family-assistant --tail=50

# Check resource usage
kubectl top pods -n homelab | grep family-assistant

# Describe deployment
kubectl describe deployment -n homelab family-assistant-frontend
```

---

## 🎯 Quick Demo Scenarios

### Scenario 1: Complete Auth Flow
```bash
# 1. Login and get token
TOKEN=$(curl -sk -X POST https://family-api.homelab.pesulabs.net/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Get user profile
curl -k https://family-api.homelab.pesulabs.net/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Verify token
curl -k -X POST https://family-api.homelab.pesulabs.net/api/v1/auth/verify \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Scenario 2: Monitor System Health
```bash
# Watch pods in real-time
watch -n 2 'kubectl get pods -n homelab | grep family-assistant'

# Stream frontend logs
kubectl logs -f -n homelab -l app=family-assistant-frontend

# Stream backend logs
kubectl logs -f -n homelab -l app=family-assistant

# Check metrics
watch -n 5 'curl -sk https://family-api.homelab.pesulabs.net/metrics | grep http_requests_total | head -10'
```

### Scenario 3: Test High Availability
```bash
# Get current frontend pods
kubectl get pods -n homelab -l app=family-assistant-frontend

# Delete one pod (should auto-recover)
kubectl delete pod -n homelab $(kubectl get pods -n homelab -l app=family-assistant-frontend -o jsonpath='{.items[0].metadata.name}')

# Watch recreation
kubectl get pods -n homelab -l app=family-assistant-frontend -w

# Frontend should still work (2 replicas)
curl -k https://family.homelab.pesulabs.net/health
```

---

## 🧪 Run Test Suites

### Backend Unit Tests
```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant

# Activate virtual environment
source venv/bin/activate

# Run all unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=api --cov-report=html --cov-report=term

# Open coverage report
firefox htmlcov/index.html
```

### Frontend E2E Tests
```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant/frontend

# Run all E2E tests
npm run test:e2e

# Interactive mode (best for learning)
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug

# Specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
```

### Complete Test Suite
```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant

# Run everything (backend + frontend + linting)
./scripts/run-all-tests.sh

# Skip E2E for faster run
./scripts/run-all-tests.sh --skip-e2e

# Skip services check
./scripts/run-all-tests.sh --skip-services

# View test summary
cat test-summary.md
```

---

## 📖 Review Documentation

```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant

# Week 1 completion reports
less WEEK1_FOUNDATION_COMPLETE.md      # Days 1-3 summary
less WEEK1_DAY4_TESTING_COMPLETE.md    # E2E testing details
less WEEK1_DAY5_DEPLOYMENT_COMPLETE.md # Production deployment

# E2E testing guide
less frontend/e2e/README.md

# Main documentation
less README.md
less INSTALL.md
```

---

## 🐳 Docker Image Exploration

### View Images
```bash
# List all Family Assistant images
docker images | grep family-assistant

# Check image sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep family-assistant
```

### Inspect Images
```bash
# Frontend image details
docker inspect 100.81.76.55:30500/family-assistant-frontend:week1 | jq '.[0].Config'

# Backend image details
docker inspect 100.81.76.55:30500/family-assistant-backend:week1 | jq '.[0].Config'

# Check image layers
docker history 100.81.76.55:30500/family-assistant-frontend:week1
```

### Run Locally (Development)
```bash
# Frontend (standalone)
docker run -p 3000:3000 family-assistant-frontend:week1
# Access: http://localhost:3000

# Backend (with SQLite for testing)
docker run -p 8000:8001 \
  -e DATABASE_URL=sqlite:///./test.db \
  -e ENVIRONMENT=development \
  family-assistant-backend:week1
# Access: http://localhost:8000/docs
```

---

## 🎨 Browser-Based Exploration

### Recommended Browser Setup

1. **Install Extensions**:
   - Redux DevTools (for Zustand state inspection)
   - React Developer Tools
   - JSON Viewer

2. **Open Application**:
   ```bash
   firefox https://family.homelab.pesulabs.net
   ```

3. **Open DevTools** (F12):
   - **Console**: Structured logging, errors
   - **Network**: API calls, JWT tokens, timing
   - **Redux**: Zustand state management
   - **Application**: LocalStorage (auth tokens)
   - **Performance**: Page load metrics

### What to Look For

**Network Tab**:
- Authorization headers with JWT tokens
- API response times
- WebSocket connections (if any)
- Cached static assets (1 year expiry)

**Console**:
- Structured logging output
- Error handling messages
- State change notifications

**Redux DevTools**:
- AuthStore state (user, isAuthenticated, tokens)
- FamilyStore state (members, selectedMember)
- Action history and state diffs

---

## 📊 Kubernetes Exploration

### Pod Management
```bash
# Get all Family Assistant pods
kubectl get pods -n homelab -l app=family-assistant-frontend
kubectl get pods -n homelab -l app=family-assistant

# Pod details
kubectl describe pod -n homelab <pod-name>

# Get pod YAML
kubectl get pod -n homelab <pod-name> -o yaml

# Execute commands in pod
kubectl exec -it -n homelab <frontend-pod> -- /bin/sh
kubectl exec -it -n homelab <backend-pod> -- /bin/bash
```

### Service & Networking
```bash
# Get services
kubectl get svc -n homelab | grep family-assistant

# Service details
kubectl describe svc -n homelab family-assistant-frontend

# Check endpoints
kubectl get endpoints -n homelab family-assistant-frontend

# Test internal connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -n homelab -- \
  wget -O- http://family-assistant-frontend.homelab.svc.cluster.local:3000/health
```

### Ingress & Traffic
```bash
# Get ingress routes
kubectl get ingressroute -n homelab | grep family-assistant

# Ingress details
kubectl describe ingressroute -n homelab family-assistant-frontend

# Check Traefik routing
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik --tail=100
```

---

## 🚀 Recommended Exploration Path

**For first-time experience, follow this sequence**:

### Step 1: Quick Health Check (2 minutes)
```bash
# Check all services are running
curl -k https://family.homelab.pesulabs.net/health
curl -k https://family-api.homelab.pesulabs.net/api/v1/

# Check Kubernetes status
kubectl get pods -n homelab | grep family-assistant
```

### Step 2: Open Frontend in Browser (5 minutes)
```bash
firefox https://family.homelab.pesulabs.net
```
- Open DevTools (F12)
- Explore the UI
- Watch Network tab for API calls
- Check Redux DevTools for state

### Step 3: Test Authentication (3 minutes)
```bash
# Get token via API
TOKEN=$(curl -sk -X POST https://family-api.homelab.pesulabs.net/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')

# Use token
curl -k https://family-api.homelab.pesulabs.net/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Step 4: Run E2E Tests in UI Mode (10 minutes)
```bash
cd /home/pesu/Rakuflow/systems/homelab/production/family-assistant/family-assistant/frontend
npm run test:e2e:ui
```
- Watch tests run interactively
- See authentication flow automation
- Observe optimistic updates

### Step 5: Monitor Live System (5 minutes)
```bash
# Terminal 1: Watch pods
watch -n 2 'kubectl get pods -n homelab | grep family-assistant'

# Terminal 2: Stream logs
kubectl logs -f -n homelab -l app=family-assistant-frontend

# Terminal 3: Monitor metrics
watch -n 5 'curl -sk https://family-api.homelab.pesulabs.net/metrics | grep http_requests'
```

### Step 6: Review Documentation (10 minutes)
```bash
# Read week summaries
cat WEEK1_FOUNDATION_COMPLETE.md
cat WEEK1_DAY4_TESTING_COMPLETE.md
cat WEEK1_DAY5_DEPLOYMENT_COMPLETE.md
```

---

## 🔧 Troubleshooting

### Frontend Not Loading
```bash
# Check pods
kubectl get pods -n homelab -l app=family-assistant-frontend

# Check logs
kubectl logs -n homelab -l app=family-assistant-frontend --tail=100

# Check service
kubectl get svc -n homelab family-assistant-frontend

# Test NodePort directly
curl http://100.81.76.55:30300/health
```

### Backend API Errors
```bash
# Check backend pod
kubectl get pods -n homelab -l app=family-assistant

# Check logs
kubectl logs -n homelab -l app=family-assistant --tail=100

# Check database connection
kubectl logs -n homelab -l app=family-assistant | grep -i postgres

# Test directly
curl http://100.81.76.55:30080/api/v1/
```

### HTTPS/Traefik Issues
```bash
# Check Traefik
kubectl get pods -n kube-system | grep traefik

# Check ingress routes
kubectl get ingressroute -n homelab | grep family-assistant

# Check TLS certificate
kubectl get secret -n homelab homelab-tls

# Check Traefik logs
kubectl logs -n kube-system -l app.kubernetes.io/name=traefik --tail=100
```

---

## 📝 Quick Reference

### Important URLs
- Frontend HTTPS: https://family.homelab.pesulabs.net
- Backend HTTPS: https://family-api.homelab.pesulabs.net
- Frontend NodePort: http://100.81.76.55:30300
- Backend NodePort: http://100.81.76.55:30080

### Important Commands
```bash
# Check everything
kubectl get all -n homelab | grep family-assistant

# Restart frontend
kubectl rollout restart deployment -n homelab family-assistant-frontend

# Restart backend
kubectl rollout restart deployment -n homelab family-assistant

# View all logs
kubectl logs -n homelab --all-containers=true -l app=family-assistant-frontend
```

### Test Credentials
- Username: `testuser`
- Password: `testpass123`
- Role: `parent`

---

## 🎓 Learning Resources

### Documentation Files
- `WEEK1_FOUNDATION_COMPLETE.md` - Days 1-3 overview
- `WEEK1_DAY4_TESTING_COMPLETE.md` - Testing infrastructure
- `WEEK1_DAY5_DEPLOYMENT_COMPLETE.md` - Production deployment
- `frontend/e2e/README.md` - E2E testing guide
- `README.md` - Main project documentation

### Code Exploration
- `api/auth/` - Authentication implementation
- `api/observability/` - Tracing, logging, metrics
- `frontend/src/stores/` - Zustand state management
- `frontend/e2e/` - Playwright E2E tests
- `infrastructure/kubernetes/` - K8s manifests

---

**Last Updated**: November 12, 2025
**Week 1 Status**: ✅ Complete - All 5 days delivered
**Production Status**: ✨ LIVE at https://family.homelab.pesulabs.net
