# Week 1: Foundation Hardening - Comprehensive Plan

**Duration:** 5 days  
**Goal:** Secure, scalable, testable, observable foundation  
**Status:** Ready to Execute

## Overview

Week 1 establishes the architectural foundation with **security, testing, and observability** as first-class concerns. This is not just about features - it's about building a production-ready platform.

---

## Core Pillars

### 1. Security First
- JWT authentication with role-based access control
- Rate limiting and abuse prevention
- Input validation and sanitization
- Security testing from day one

### 2. Testing Strategy
- Unit tests (pytest, vitest)
- Integration tests (API contracts)
- End-to-end tests (Playwright)
- Test coverage targets (>80%)

### 3. Observability
- OpenTelemetry distributed tracing
- Structured logging (JSON format)
- Prometheus metrics
- Real-time monitoring dashboards

### 4. Scalability
- Separate frontend/backend deployments
- Stateless API design
- Proper state management (Zustand)
- Database connection pooling

---

## Day 1: Security & Architecture Foundation

### Morning: Testing Strategy Design

**Task 1.1: Create Testing Framework Structure**
```bash
# Backend testing structure
production/family-assistant/family-assistant/
├── tests/
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_memory_manager.py
│   │   ├── test_prompt_builder.py
│   │   └── conftest.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_database.py
│   │   └── test_memory_layers.py
│   ├── e2e/
│   │   ├── test_user_flows.py
│   │   └── test_admin_workflows.py
│   └── fixtures/
│       ├── family_members.json
│       └── test_conversations.json
├── pytest.ini
└── .coveragerc

# Frontend testing structure
production/family-assistant/family-assistant/frontend/
├── src/
│   └── __tests__/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── stores/
├── e2e/
│   ├── auth.spec.ts
│   ├── family-management.spec.ts
│   └── playwright.config.ts
├── vitest.config.ts
└── .coverage/
```

**Task 1.2: Configure Testing Tools**

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=api
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

# .coveragerc
[run]
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/'],
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80
    }
  }
})
```

**Task 1.3: Create Test Fixtures**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.models.database import Base, get_db

SQLALCHEMY_TEST_DATABASE_URL = "postgresql://test:test@localhost/family_assistant_test"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def mock_family_member():
    return {
        "id": "test-user-123",
        "telegram_id": 12345678,
        "first_name": "Test",
        "last_name": "User",
        "role": "parent",
        "age_group": "adult",
        "language_preference": "en"
    }
```

### Afternoon: JWT Authentication Implementation

**Task 1.4: Install Authentication Dependencies**

```bash
cd production/family-assistant/family-assistant
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
pip install pytest pytest-cov pytest-asyncio httpx
```

**Task 1.5: Create Authentication Module**

```python
# api/auth/jwt.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.models.database import get_db, FamilyMember
from sqlalchemy.orm import Session

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> FamilyMember:
    token = credentials.credentials
    payload = AuthService.decode_token(token)
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    user = db.query(FamilyMember).filter(FamilyMember.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Role-based authorization decorator
def require_role(allowed_roles: list[str]):
    async def role_checker(user: FamilyMember = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return user
    return role_checker
```

**Task 1.6: Create Authentication Routes**

```python
# api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.auth.jwt import AuthService, get_current_user
from api.models.database import get_db, FamilyMember

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    telegram_id: int
    password: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Find user by telegram_id
    user = db.query(FamilyMember).filter(
        FamilyMember.telegram_id == request.telegram_id
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # For now, simple authentication (enhance with password later)
    token = AuthService.create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": f"{user.first_name} {user.last_name}",
            "role": user.role,
            "language": user.language_preference
        }
    }

@router.get("/me")
async def get_current_user_info(user: FamilyMember = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "telegram_id": user.telegram_id,
        "name": f"{user.first_name} {user.last_name}",
        "role": user.role,
        "language": user.language_preference,
        "permissions": {
            "manage_users": user.role == "parent",
            "view_all_conversations": user.role == "parent",
            "edit_prompts": user.role == "parent"
        }
    }
```

**Task 1.7: Write Authentication Tests**

```python
# tests/unit/test_auth.py
import pytest
from api.auth.jwt import AuthService
from datetime import timedelta

def test_password_hashing():
    password = "test_password_123"
    hashed = AuthService.get_password_hash(password)
    
    assert hashed != password
    assert AuthService.verify_password(password, hashed)
    assert not AuthService.verify_password("wrong_password", hashed)

def test_create_access_token():
    data = {"sub": "user123", "role": "parent"}
    token = AuthService.create_access_token(data, timedelta(minutes=30))
    
    assert token is not None
    decoded = AuthService.decode_token(token)
    assert decoded["sub"] == "user123"
    assert decoded["role"] == "parent"

# tests/integration/test_auth_api.py
def test_login_success(client, mock_family_member, db_session):
    # Create test user
    from api.models.database import FamilyMember
    user = FamilyMember(**mock_family_member)
    db_session.add(user)
    db_session.commit()
    
    response = client.post("/api/v1/auth/login", json={
        "telegram_id": mock_family_member["telegram_id"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "parent"

def test_protected_route_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # No credentials

def test_protected_route_with_valid_token(client, mock_family_member, db_session):
    # Create user and get token
    from api.models.database import FamilyMember
    from api.auth.jwt import AuthService
    
    user = FamilyMember(**mock_family_member)
    db_session.add(user)
    db_session.commit()
    
    token = AuthService.create_access_token({"sub": str(user.id)})
    
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "parent"
```

**Deliverables Day 1:**
- ✅ Testing framework configured
- ✅ JWT authentication implemented
- ✅ Authentication tests passing
- ✅ Test coverage >80% for auth module

---

## Day 2: Monitoring & Observability

### Morning: OpenTelemetry Setup

**Task 2.1: Install Observability Dependencies**

```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-sqlalchemy
pip install opentelemetry-instrumentation-redis
pip install opentelemetry-exporter-otlp
```

**Task 2.2: Configure OpenTelemetry**

```python
# api/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource

def setup_tracing(app, service_name="family-assistant-api"):
    # Create resource with service name
    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": "2.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development")
    })
    
    # Set up tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter (to Grafana Tempo or Jaeger)
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True
    )
    
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    return trace.get_tracer(__name__)

# Custom span decorators
def traced_operation(operation_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(operation_name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("operation.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("operation.success", False)
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator
```

**Task 2.3: Add Structured Logging**

```python
# api/observability/logging.py
import logging
import json
from datetime import datetime
from typing import Any

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add trace context if available
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
            log_data["span_id"] = record.span_id
        
        # Add custom fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging():
    logger = logging.getLogger("family_assistant")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger

# Usage in code
logger = setup_logging()

# Example usage
logger.info("User authenticated", extra={
    "user_id": user.id,
    "role": user.role,
    "action": "login"
})
```

**Task 2.4: Add Prometheus Metrics**

```python
# api/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Define custom metrics
request_count = Counter(
    "family_assistant_requests_total",
    "Total request count",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "family_assistant_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

llm_generation_duration = Histogram(
    "family_assistant_llm_generation_seconds",
    "LLM generation duration",
    ["model"]
)

memory_layer_latency = Histogram(
    "family_assistant_memory_layer_latency_seconds",
    "Memory layer operation latency",
    ["layer", "operation"]
)

active_users = Gauge(
    "family_assistant_active_users",
    "Number of active users"
)

def setup_metrics(app):
    # Auto-instrument FastAPI
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    
    return {
        "request_count": request_count,
        "request_duration": request_duration,
        "llm_duration": llm_generation_duration,
        "memory_latency": memory_layer_latency,
        "active_users": active_users
    }
```

### Afternoon: Rate Limiting & Security Middleware

**Task 2.5: Implement Rate Limiting**

```bash
pip install slowapi
```

```python
# api/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exceeded handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail.split()[-1]
        }
    )

# Apply to specific routes
from fastapi import APIRouter
router = APIRouter()

@router.post("/api/v1/chat")
@limiter.limit("20/minute")  # 20 requests per minute per user
async def chat(request: Request, ...):
    pass

@router.post("/api/v1/memory/search")
@limiter.limit("30/minute")  # More generous for search
async def search_memory(request: Request, ...):
    pass
```

**Task 2.6: Add Security Headers Middleware**

```python
# api/middleware/security.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
```

**Deliverables Day 2:**
- ✅ OpenTelemetry tracing operational
- ✅ Structured JSON logging
- ✅ Prometheus metrics exposed
- ✅ Rate limiting implemented
- ✅ Security headers added

---

## Day 3: Frontend Architecture & Deployment

### Morning: Separate Frontend Deployment

**Task 3.1: Create Frontend Nginx Configuration**

```nginx
# production/family-assistant/family-assistant/frontend/nginx.conf
server {
    listen 3000;
    server_name _;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Task 3.2: Create Frontend Dockerfile**

```dockerfile
# production/family-assistant/family-assistant/frontend/Dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build application
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**Task 3.3: Create Kubernetes Manifests**

```yaml
# production/family-assistant/kubernetes/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: family-assistant-frontend
  namespace: homelab
  labels:
    app: family-assistant-frontend
    component: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: family-assistant-frontend
  template:
    metadata:
      labels:
        app: family-assistant-frontend
        component: frontend
    spec:
      containers:
      - name: frontend
        image: 100.81.76.55:30500/family-assistant-frontend:latest
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: VITE_API_URL
          value: "http://family-assistant-api:8000"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: family-assistant-frontend
  namespace: homelab
spec:
  type: NodePort
  selector:
    app: family-assistant-frontend
  ports:
  - port: 3000
    targetPort: 3000
    nodePort: 30081
    name: http
```

### Afternoon: Zustand State Management

**Task 3.4: Install State Management Dependencies**

```bash
cd production/family-assistant/family-assistant/frontend
npm install zustand immer
npm install -D @types/node
```

**Task 3.5: Create Store Structure**

```typescript
// src/stores/familyStore.ts
import create from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { familyApi } from '../services/api/family'

interface FamilyMember {
  id: string
  telegram_id: number
  first_name: string
  last_name: string
  role: 'parent' | 'teenager' | 'child' | 'grandparent'
  age_group: 'child' | 'teen' | 'adult' | 'elder'
  language_preference: 'en' | 'es' | 'bilingual'
  active_skills: string[]
  created_at: string
}

interface FamilyState {
  members: FamilyMember[]
  loading: boolean
  error: string | null
  
  // Actions
  fetchMembers: () => Promise<void>
  addMember: (member: Omit<FamilyMember, 'id' | 'created_at'>) => Promise<void>
  updateMember: (id: string, data: Partial<FamilyMember>) => Promise<void>
  deleteMember: (id: string) => Promise<void>
  
  // Selectors
  getMemberById: (id: string) => FamilyMember | undefined
  getParents: () => FamilyMember[]
  getChildren: () => FamilyMember[]
}

export const useFamilyStore = create<FamilyState>()(
  devtools(
    immer((set, get) => ({
      members: [],
      loading: false,
      error: null,
      
      fetchMembers: async () => {
        set({ loading: true, error: null })
        try {
          const members = await familyApi.getMembers()
          set({ members, loading: false })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch members',
            loading: false 
          })
        }
      },
      
      addMember: async (memberData) => {
        set({ loading: true, error: null })
        try {
          const newMember = await familyApi.createMember(memberData)
          set((state) => {
            state.members.push(newMember)
            state.loading = false
          })
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to add member',
            loading: false 
          })
          throw error
        }
      },
      
      updateMember: async (id, data) => {
        // Optimistic update
        const previousMembers = get().members
        set((state) => {
          const index = state.members.findIndex(m => m.id === id)
          if (index !== -1) {
            state.members[index] = { ...state.members[index], ...data }
          }
        })
        
        try {
          const updated = await familyApi.updateMember(id, data)
          set((state) => {
            const index = state.members.findIndex(m => m.id === id)
            if (index !== -1) {
              state.members[index] = updated
            }
          })
        } catch (error) {
          // Rollback on failure
          set({ members: previousMembers })
          throw error
        }
      },
      
      deleteMember: async (id) => {
        set({ loading: true })
        try {
          await familyApi.deleteMember(id)
          set((state) => {
            state.members = state.members.filter(m => m.id !== id)
            state.loading = false
          })
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },
      
      // Selectors
      getMemberById: (id) => get().members.find(m => m.id === id),
      getParents: () => get().members.filter(m => m.role === 'parent'),
      getChildren: () => get().members.filter(m => 
        m.role === 'child' || m.role === 'teenager'
      ),
    }))
  )
)
```

**Task 3.6: Create API Client Layer**

```typescript
// src/services/api/client.ts
import axios, { AxiosError, AxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    
    // Format error for consistent handling
    const errorMessage = error.response?.data?.message || error.message
    return Promise.reject(new Error(errorMessage))
  }
)

export default apiClient

// src/services/api/family.ts
import apiClient from './client'

export const familyApi = {
  getMembers: async () => {
    const response = await apiClient.get('/api/v1/family/members')
    return response.data
  },
  
  createMember: async (data: any) => {
    const response = await apiClient.post('/api/v1/family/members', data)
    return response.data
  },
  
  updateMember: async (id: string, data: any) => {
    const response = await apiClient.put(`/api/v1/family/members/${id}`, data)
    return response.data
  },
  
  deleteMember: async (id: string) => {
    await apiClient.delete(`/api/v1/family/members/${id}`)
  }
}
```

**Task 3.7: Write Frontend Tests**

```typescript
// src/__tests__/stores/familyStore.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useFamilyStore } from '../../stores/familyStore'
import { familyApi } from '../../services/api/family'

vi.mock('../../services/api/family')

describe('FamilyStore', () => {
  beforeEach(() => {
    useFamilyStore.setState({ members: [], loading: false, error: null })
  })
  
  it('should fetch members successfully', async () => {
    const mockMembers = [
      { id: '1', first_name: 'John', role: 'parent' },
      { id: '2', first_name: 'Jane', role: 'parent' }
    ]
    
    vi.mocked(familyApi.getMembers).mockResolvedValue(mockMembers)
    
    await useFamilyStore.getState().fetchMembers()
    
    expect(useFamilyStore.getState().members).toEqual(mockMembers)
    expect(useFamilyStore.getState().loading).toBe(false)
  })
  
  it('should handle optimistic updates', async () => {
    const member = { id: '1', first_name: 'John', role: 'parent' }
    useFamilyStore.setState({ members: [member] })
    
    const updatePromise = useFamilyStore.getState().updateMember('1', {
      first_name: 'Johnny'
    })
    
    // Check optimistic update
    expect(useFamilyStore.getState().members[0].first_name).toBe('Johnny')
    
    await updatePromise
  })
})
```

**Deliverables Day 3:**
- ✅ Frontend deployed separately
- ✅ Zustand state management working
- ✅ API client layer with error handling
- ✅ Frontend tests passing

---

## Day 4: Integration & E2E Testing

### Morning: Backend API Tests

**Task 4.1: Protect Existing Routes**

```python
# Update api/routes/phase2_routes.py
from api.auth.jwt import get_current_user, require_role

@router.get("/api/phase2/users/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    current_user: FamilyMember = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Users can only access their own profile unless they're parents
    if current_user.id != user_id and current_user.role != "parent":
        raise HTTPException(403, "Cannot access other user profiles")
    
    profile = db.query(FamilyMember).filter(FamilyMember.id == user_id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    
    return profile

@router.get("/api/v1/family/members")
async def get_family_members(
    current_user: FamilyMember = Depends(require_role(["parent"]))
):
    # Only parents can view all family members
    return await family_service.get_all_members()
```

**Task 4.2: Integration Tests**

```python
# tests/integration/test_protected_endpoints.py
def test_family_members_requires_auth(client):
    response = client.get("/api/v1/family/members")
    assert response.status_code == 403

def test_family_members_requires_parent_role(client, db_session):
    # Create teenager user
    teen = FamilyMember(
        telegram_id=99999,
        first_name="Teen",
        role="teenager"
    )
    db_session.add(teen)
    db_session.commit()
    
    token = AuthService.create_access_token({"sub": str(teen.id)})
    
    response = client.get(
        "/api/v1/family/members",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]

def test_family_members_allows_parent(client, db_session, mock_family_member):
    user = FamilyMember(**mock_family_member)
    db_session.add(user)
    db_session.commit()
    
    token = AuthService.create_access_token({"sub": str(user.id)})
    
    response = client.get(
        "/api/v1/family/members",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### Afternoon: End-to-End Tests

**Task 4.3: Setup Playwright**

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

```typescript
// e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

**Task 4.4: Write E2E Tests**

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should show login page for unauthenticated users', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL('/login')
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible()
  })
  
  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login')
    
    await page.fill('input[name="telegram_id"]', '12345678')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Welcome')).toBeVisible()
  })
  
  test('should redirect to login when token expires', async ({ page, context }) => {
    // Set expired token
    await context.addCookies([{
      name: 'auth_token',
      value: 'expired_token',
      domain: 'localhost',
      path: '/',
    }])
    
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/login')
  })
})

// e2e/family-management.spec.ts
test.describe('Family Management', () => {
  test.beforeEach(async ({ page, context }) => {
    // Login as parent
    await context.addCookies([{
      name: 'auth_token',
      value: 'valid_parent_token',
      domain: 'localhost',
      path: '/',
    }])
  })
  
  test('should display family members list', async ({ page }) => {
    await page.goto('/family-members')
    
    await expect(page.getByRole('heading', { name: 'Family Members' })).toBeVisible()
    await expect(page.getByText('Total Members')).toBeVisible()
  })
  
  test('should add new family member', async ({ page }) => {
    await page.goto('/family-members')
    
    await page.click('button:has-text("Add Member")')
    await page.fill('input[name="first_name"]', 'Test')
    await page.fill('input[name="telegram_id"]', '99999999')
    await page.selectOption('select[name="role"]', 'child')
    await page.click('button:has-text("Save")')
    
    await expect(page.getByText('Test')).toBeVisible()
  })
})
```

**Deliverables Day 4:**
- ✅ All Phase 2 routes protected
- ✅ Integration tests passing
- ✅ E2E tests with Playwright
- ✅ Test coverage >80%

---

## Day 5: Deployment & Verification

### Morning: Build & Deploy

**Task 5.1: Build Production Images**

```bash
# Backend
cd production/family-assistant/family-assistant
docker build -t family-assistant-api:v2.1 .
docker tag family-assistant-api:v2.1 100.81.76.55:30500/family-assistant-api:v2.1
docker push 100.81.76.55:30500/family-assistant-api:v2.1

# Frontend
cd frontend
docker build -t family-assistant-frontend:v2.1 -f Dockerfile .
docker tag family-assistant-frontend:v2.1 100.81.76.55:30500/family-assistant-frontend:v2.1
docker push 100.81.76.55:30500/family-assistant-frontend:v2.1
```

**Task 5.2: Deploy to Kubernetes**

```bash
# Update backend deployment
kubectl set image deployment/family-assistant -n homelab \
  family-assistant=100.81.76.55:30500/family-assistant-api:v2.1

# Deploy frontend
kubectl apply -f production/family-assistant/kubernetes/frontend-deployment.yaml

# Verify deployments
kubectl rollout status deployment/family-assistant -n homelab
kubectl rollout status deployment/family-assistant-frontend -n homelab

# Check pods
kubectl get pods -n homelab -l app=family-assistant
kubectl get pods -n homelab -l app=family-assistant-frontend
```

### Afternoon: Verification & Monitoring

**Task 5.3: Smoke Tests**

```bash
# Test authentication
curl -X POST http://100.81.76.55:30080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"telegram_id": 12345678}'

# Test protected endpoint (should fail without token)
curl http://100.81.76.55:30080/api/v1/family/members

# Test with token
TOKEN="<token_from_login>"
curl http://100.81.76.55:30080/api/v1/family/members \
  -H "Authorization: Bearer $TOKEN"

# Test frontend health
curl http://100.81.76.55:30081/health

# Test metrics endpoint
curl http://100.81.76.55:30080/metrics
```

**Task 5.4: Monitor Dashboards**

Create Grafana dashboard for Family Assistant:

```yaml
# infrastructure/kubernetes/monitoring/dashboards/family-assistant.json
{
  "dashboard": {
    "title": "Family Assistant - Week 1 Foundation",
    "panels": [
      {
        "title": "API Request Rate",
        "targets": [{
          "expr": "rate(family_assistant_requests_total[5m])"
        }]
      },
      {
        "title": "Request Duration (P95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(family_assistant_request_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Authentication Success Rate",
        "targets": [{
          "expr": "rate(family_assistant_requests_total{endpoint=\"/api/v1/auth/login\", status=\"200\"}[5m]) / rate(family_assistant_requests_total{endpoint=\"/api/v1/auth/login\"}[5m])"
        }]
      },
      {
        "title": "Memory Layer Latency",
        "targets": [{
          "expr": "family_assistant_memory_layer_latency_seconds"
        }]
      },
      {
        "title": "Active Users",
        "targets": [{
          "expr": "family_assistant_active_users"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(family_assistant_requests_total{status=~\"5..\"}[5m])"
        }]
      }
    ]
  }
}
```

**Task 5.5: Load Testing**

```bash
# Install k6 for load testing
sudo apt install k6

# Create load test script
cat > load_test.js << 'SCRIPT'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp up to 10 users
    { duration: '3m', target: 10 },  // Stay at 10 users
    { duration: '1m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% failures
  },
};

const BASE_URL = 'http://100.81.76.55:30080';

export default function () {
  // Login
  let loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    telegram_id: 12345678
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(loginRes, {
    'login successful': (r) => r.status === 200,
    'has token': (r) => r.json('access_token') !== undefined,
  });
  
  let token = loginRes.json('access_token');
  
  // Get family members
  let membersRes = http.get(`${BASE_URL}/api/v1/family/members`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  
  check(membersRes, {
    'members retrieved': (r) => r.status === 200,
  });
  
  sleep(1);
}
SCRIPT

# Run load test
k6 run load_test.js
```

**Deliverables Day 5:**
- ✅ Production deployments successful
- ✅ All smoke tests passing
- ✅ Monitoring dashboards operational
- ✅ Load testing completed
- ✅ Performance baselines established

---

## Success Criteria

### Functional Requirements
- ✅ JWT authentication working with role-based access
- ✅ Frontend and backend deployed separately
- ✅ FamilyMembers page connected to real API
- ✅ Zustand state management operational
- ✅ Rate limiting protecting endpoints

### Testing Requirements
- ✅ Unit test coverage >80%
- ✅ Integration tests for all auth flows
- ✅ E2E tests for critical user journeys
- ✅ Load testing passed (P95 < 500ms)

### Observability Requirements
- ✅ OpenTelemetry tracing active
- ✅ Structured JSON logging
- ✅ Prometheus metrics exposed
- ✅ Grafana dashboard created
- ✅ Error tracking functional

### Security Requirements
- ✅ All endpoints protected by authentication
- ✅ RBAC enforced (parent vs child roles)
- ✅ Rate limiting preventing abuse
- ✅ Security headers configured
- ✅ Input validation on all routes

---

## Monitoring Dashboard

After Week 1, you'll have real-time visibility:

```
📊 Family Assistant Foundation Dashboard

Authentication
├─ Login Success Rate: 99.8%
├─ Active Sessions: 5
└─ Failed Auth Attempts: 2 (last 5min)

API Performance
├─ Request Rate: 45 req/sec
├─ P95 Latency: 187ms
├─ P99 Latency: 342ms
└─ Error Rate: 0.1%

Memory Layers
├─ Redis: 0.8ms avg
├─ Mem0: 12ms avg
├─ PostgreSQL: 15ms avg
└─ Qdrant: 98ms avg

Resources
├─ CPU Usage: 35%
├─ Memory Usage: 62%
├─ Active Connections: 12
└─ Database Pool: 8/20
```

---

## Risk Management

### High Priority Risks
1. **Database Connection Pool Exhaustion**
   - Mitigation: Connection pooling with max 20 connections
   - Monitoring: Alert when pool usage >80%

2. **JWT Secret Key Exposure**
   - Mitigation: Store in Kubernetes secret, rotate monthly
   - Monitoring: Audit log access

3. **Rate Limit Too Restrictive**
   - Mitigation: Start generous (20/min), adjust based on usage
   - Monitoring: Track rate limit hits

### Medium Priority Risks
1. **Frontend/Backend Version Mismatch**
   - Mitigation: Coordinated deployments, API versioning
   - Monitoring: Version mismatch errors

2. **Test Database Cleanup**
   - Mitigation: Automatic cleanup in conftest.py
   - Monitoring: Test database size

---

## Next Week Preview

**Week 2: Admin Features**
- Memory browser with semantic search
- Conversation history viewer
- Prompt management interface
- Analytics dashboard
- Advanced observability (distributed tracing UI)

**Prerequisites from Week 1:**
- ✅ Secure foundation
- ✅ Comprehensive testing
- ✅ Observability infrastructure
- ✅ Scalable architecture

---

## Conclusion

Week 1 is not just about features - it's about building a **production-ready foundation** with:
- 🔒 Security built-in from day one
- 🧪 Comprehensive testing at all levels
- 📊 Full observability and monitoring
- ⚡ Performance tested and validated
- 🏗️ Scalable architecture patterns

**Ready to execute?** Let's start with Day 1: Testing Strategy & JWT Authentication!
