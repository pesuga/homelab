# Backend Connectivity Requirements for Family Admin Panel

## Issue Summary
The Family Admin Panel frontend cannot connect to the backend API from within the Kubernetes cluster. The frontend is running as a deployment in the `homelab` namespace and attempting to reach `family-assistant-backend:8001` but receiving `ERR_CONNECTION_REFUSED`.

## Current Frontend Configuration
- **Frontend Deployment**: `family-admin` in `homelab` namespace
- **Backend Target**: `family-assistant-backend:8001` (ClusterIP service)
- **API Base URL**: `http://family-assistant-backend:8001` (configured in `.env.local`)
- **Authentication**: Development bypass active (no auth required)

## Connectivity Test Results
```bash
# Command that fails from admin pod:
kubectl exec deploy/family-admin -n homelab -- curl "http://family-assistant-backend:8001/api/v1/family/members"

# Result: connection refused
```

## Required Backend Service Configuration

### 1. Backend Service Verification
**Required**: Ensure backend service is properly exposed and accessible

**Current Services**:
```bash
# Expected backend service:
kubectl get svc -n homelab | grep backend
# Should show: family-assistant-backend ClusterIP <IP> 8001/TCP,8123/TCP,8008/TCP

# Current admin service:
kubectl get svc -n homelab | grep family-admin
# Shows: family-admin ClusterIP <IP> 80/TCP,3000/TCP
```

### 2. Network Policies
**Required**: Allow traffic from `family-admin` pods to `family-assistant-backend` service

**Network Policy Needed**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-admin-to-backend
  namespace: homelab
spec:
  podSelector:
    matchLabels:
      app: family-admin
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: family-assistant-backend
    ports:
    - protocol: TCP
      port: 8001
```

### 3. Service Discovery
**Required**: Verify DNS resolution within cluster

**Test Commands**:
```bash
# Test DNS resolution from admin pod:
kubectl exec deploy/family-admin -n homelab -- nslookup family-assistant-backend.homelab.svc.cluster.local

# Test direct IP access:
kubectl exec deploy/family-admin -n homelab -- curl -v "http://<backend-service-ip>:8001/health"
```

### 4. Backend Health Checks
**Required**: Ensure backend is ready to accept connections

**Health Endpoints to Test**:
- `GET /` - Basic API status
- `GET /health` - Application health
- `GET /api/v1/family/members` - Family API endpoint

## Frontend Error Handling Status
✅ **Graceful Degradation**: Frontend shows mock data when backend unavailable
✅ **Error Messaging**: Clear "Backend not accessible, using mock data" message
✅ **UI Continuity**: Family management interface remains functional with sample data
✅ **Retry Logic**: Will attempt real backend connection on each page load

## Expected Backend Response Format

### Family Members Endpoint
**URL**: `GET /api/v1/family/members`
**Expected Response**:
```json
[
  {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "parent|teenager|child|grandparent",
    "avatar": "url_or_base64",
    "language_preference": "en|es",
    "parental_controls": {
      "safe_search": true,
      "content_filter": "strict|moderate|off",
      "screen_time_daily": 120,
      "screen_time_weekend": 180,
      "allowed_apps": ["app1", "app2"],
      "blocked_keywords": ["keyword1", "keyword2"]
    },
    "created_at": "2025-01-01T00:00:00Z",
    "last_active": "2025-01-01T12:00:00Z"
  }
]
```

## Priority
🔴 **CRITICAL** - This is blocking core family management functionality

## Success Criteria
1. ✅ Frontend can successfully connect to `http://family-assistant-backend:8001`
2. ✅ `GET /api/v1/family/members` returns family member data
3. ✅ Authentication headers work correctly
4. ✅ CORS is properly configured for cross-origin requests
5. ✅ Family management UI loads real data instead of mock data

## Troubleshooting Steps for Backend Team

### 1. Verify Backend Service
```bash
kubectl get svc -n homelab family-assistant-backend
kubectl describe svc -n homelab family-assistant-backend
```

### 2. Check Backend Pods
```bash
kubectl get pods -n homelab -l app=backend
kubectl logs -n homelab <backend-pod-name>
```

### 3. Test Internal Connectivity
```bash
# From any pod in homelab namespace:
kubectl exec -it <any-pod> -n homelab -- curl "http://family-assistant-backend:8001/"
```

### 4. Verify Network Policies
```bash
kubectl get networkpolicies -n homelab
kubectl describe networkpolicy <policy-name> -n homelab
```

### 5. Check Service Endpoints
```bash
kubectl get endpoints -n homelab family-assistant-backend
```

## Frontend Files Updated for Backend Integration
- `src/lib/api-client.ts` - Aligned with OpenAPI spec endpoints
- `src/hooks/useFamilyData.ts` - Graceful fallback to mock data
- `.env.local` - Backend URL configuration
- `BACKEND_REQUIREMENTS_FAMILY_MANAGEMENT.md` - Full API specifications

---

**Status**: Frontend ready for backend integration
**Blocker**: Network connectivity between admin frontend and backend service
**Contact**: Backend team to resolve service accessibility issues