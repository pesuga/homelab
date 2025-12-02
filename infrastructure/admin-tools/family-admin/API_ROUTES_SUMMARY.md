# Family Admin API Routes - Quick Summary

## ✅ Implementation Complete

API routes have been set up to proxy requests from the browser to internal Kubernetes services.

## 📁 Files Created

### API Routes
```
src/app/api/
├── README.md                           # Overview of API architecture
├── health/route.ts                     # Health check endpoint
├── ready/route.ts                      # Readiness probe endpoint
├── family/
│   ├── chat/route.ts                  # Chat proxy
│   ├── members/route.ts               # Family member CRUD
│   └── [...path]/route.ts             # Catch-all proxy
└── llm/
    └── chat/route.ts                   # Direct LLM access
```

### Supporting Files
```
src/lib/api-helpers.ts                  # Shared utilities
.env.example                            # Environment template
API_IMPLEMENTATION_GUIDE.md             # Comprehensive docs
```

### Configuration
```
infrastructure/kubernetes/family-assistant-admin/deployment.yaml
  ✓ Updated environment variables
  ✓ Changed NEXT_PUBLIC_API_URL → FAMILY_API_URL (server-side)
  ✓ Added LLAMACPP_API_URL and MEM0_API_URL
```

## 🚀 How It Works

**Old Architecture (Broken):**
```
Browser → http://family-assistant-backend.homelab:8001 ❌
(Cannot resolve cluster DNS)
```

**New Architecture (Working):**
```
Browser → /api/family/chat
         ↓
Next.js API Route (server-side)
         ↓
http://family-assistant-backend.homelab:8001 ✅
```

## 📝 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check (for K8s liveness) |
| `/api/ready` | GET | Readiness check (for K8s readiness) |
| `/api/family/chat` | POST | Chat with family assistant |
| `/api/family/members` | GET/POST/PUT/DELETE | Manage family members |
| `/api/family/*` | ALL | Catch-all proxy to backend |
| `/api/llm/chat` | POST | Direct LLM access (llama.cpp) |

## 🔧 Environment Variables

### Server-Side (API Routes)
```bash
FAMILY_API_URL=http://family-assistant-backend.homelab:8001
LLAMACPP_API_URL=http://llamacpp-kimi-vl-service.llamacpp:8080
MEM0_API_URL=http://mem0.homelab:8080
```

### Client-Side (Browser)
```bash
NEXT_PUBLIC_APP_URL=https://app.fa.pesulabs.net
```

## 🧪 Testing

### Health Check
```bash
curl https://admin.fa.pesulabs.net/api/health
```

### Chat Endpoint
```bash
curl -X POST https://admin.fa.pesulabs.net/api/family/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## 🤖 Agent-Friendly Features

1. **Comprehensive inline documentation** in every route file
2. **Consistent patterns** across all endpoints
3. **Reusable helpers** in `api-helpers.ts`
4. **Clear error messages** with debugging context
5. **Type-safe** with TypeScript
6. **Well-structured** following Next.js conventions

## 📚 Documentation

- **Quick Start:** This file
- **Detailed Guide:** `API_IMPLEMENTATION_GUIDE.md`
- **API Overview:** `src/app/api/README.md`
- **Environment Setup:** `.env.example`

## 🔄 Next Steps

1. **Build and deploy** the updated admin panel:
   ```bash
   cd infrastructure/admin-tools/family-admin
   npm install  # Install dependencies
   npm run build  # Build for production
   # Build Docker image and push to registry
   ```

2. **Update Kubernetes deployment:**
   ```bash
   kubectl apply -f infrastructure/kubernetes/family-assistant-admin/deployment.yaml
   ```

3. **Verify deployment:**
   ```bash
   kubectl get pods -n homelab -l app.kubernetes.io/name=family-admin
   curl https://admin.fa.pesulabs.net/api/health
   ```

4. **Update frontend components** to use new API routes:
   ```typescript
   // Change from:
   fetch('http://backend:8001/api/endpoint')

   // To:
   fetch('/api/family/endpoint')
   ```

## ⚠️ Breaking Changes

The deployment now uses different environment variable names:

**Removed:**
- `NEXT_PUBLIC_API_URL` (was exposed to browser)

**Added:**
- `FAMILY_API_URL` (server-side only)
- `LLAMACPP_API_URL` (server-side only)
- `MEM0_API_URL` (server-side only)

Any frontend code using `process.env.NEXT_PUBLIC_API_URL` must be updated to use API routes instead.

## 🎯 Benefits

✅ **Security:** Backend URLs not exposed to browser
✅ **No CORS issues:** Same-origin requests
✅ **Better error handling:** Centralized error transformation
✅ **Easier debugging:** Server-side logging
✅ **Flexibility:** Can transform requests/responses
✅ **Caching:** Server-side response caching possible
✅ **Authentication:** Server-side token handling

## 📞 Support

For questions or issues:
1. Check `API_IMPLEMENTATION_GUIDE.md` for detailed examples
2. Review inline code comments in route files
3. Check Kubernetes logs: `kubectl logs -n homelab -l app.kubernetes.io/name=family-admin`
