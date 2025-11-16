# Pre-Deployment Testing Checklist

**Purpose**: Ensure systematic testing before deploying Python services to production
**Target**: Family Assistant and future Python services
**Updated**: 2025-11-15

---

## 📋 Phase 1: Local Development Testing

### Code Quality Checks
- [ ] **Static Analysis**: Run `ruff check .` and fix all errors
- [ ] **Type Checking**: Run `mypy api/` and fix all type errors
- [ ] **Code Formatting**: Run `black .` and `ruff format .`
- [ ] **Import Validation**: Test all imports in isolated Python environment
- [ ] **Dependency Check**: Verify `requirements.txt` has all required dependencies

### Unit Testing
- [ ] **Core API Tests**: `pytest tests/unit/ -v`
- [ ] **Database Models Tests**: `pytest tests/unit/test_models.py -v`
- [ ] **Authentication Tests**: `pytest tests/unit/test_auth.py -v`
- [ ] **Multimodal Processing Tests**: `pytest tests/unit/test_multimodal.py -v`
- [ ] **Test Coverage**: `pytest --cov=api tests/` (minimum 80% coverage)

### Integration Testing
- [ ] **Database Connection**: Test PostgreSQL connection with real credentials
- [ ] **Redis Connection**: Test Redis connectivity
- [ ] **External Service APIs**: Test Ollama, Mem0, Qdrant connections
- [ ] **Multimodal Processing**: Test image, audio, document processing
- [ ] **WebSocket Functionality**: Test real-time dashboard updates

---

## 📋 Phase 2: Container Build Testing

### Docker Build Validation
- [ ] **Multi-stage Build**: `docker build --no-cache -t family-assistant:test .`
- [ ] **Base Image Security**: Run `docker scan family-assistant:test`
- [ ] **Layer Analysis**: `docker history family-assistant:test`
- [ ] **Size Optimization**: Image size under 2GB preferred
- [ ] **Security Scan**: `trivy image family-assistant:test`

### Container Runtime Testing
- [ ] **Container Startup**: `docker run --rm -p 8001:8001 family-assistant:test`
- [ ] **Health Check**: Wait for health check to pass
- [ ] **Basic API Tests**: Test `/health` and `/` endpoints
- [ ] **Resource Limits**: Test with `docker run --memory=1g --cpus=0.5`
- [ ] **Volume Mounts**: Test with mounted volumes if applicable

### Python Environment Validation
- [ ] **Import Testing**: Test all imports inside container
- [ ] **Dependency Versions**: Verify critical dependency versions
- [ ] **PATH Configuration**: Verify `PYTHONPATH` is correct
- [ ] **Module Discovery**: Test dynamic module loading
- [ ] **Error Handling**: Test graceful failure on missing dependencies

---

## 📋 Phase 3: Staging Environment Testing

### Environment Configuration
- [ ] **Environment Variables**: All required vars present and valid
- [ ] **Database Connections**: Test all database connections
- [ ] **External Services**: Test all external service integrations
- [ ] **Network Connectivity**: Test all required network endpoints
- [ ] **File System Access**: Test file/directory permissions

### API Functionality Testing
- [ ] **All Endpoints**: Test every documented API endpoint
- [ ] **Error Handling**: Test error responses and status codes
- [ ] **Request/Response Validation**: Test Pydantic model validation
- [ ] **Rate Limiting**: Test rate limiting functionality
- [ ] **Authentication/Authorization**: Test all auth flows

### Performance Testing
- [ ] **Load Testing**: `ab -n 1000 -c 10 http://localhost:8001/health`
- [ ] **Memory Usage**: Monitor memory under load
- [ ] **Response Times**: All endpoints respond under 200ms
- [ ] **Concurrent Requests**: Test with concurrent API calls
- [ ] **Database Query Performance**: Analyze slow queries

---

## 📋 Phase 4: Production Readiness

### Deployment Preparation
- [ ] **Image Versioning**: Tag image with semantic version
- [ ] **Configuration Management**: Verify production config
- [ ] **Secrets Management**: Verify secrets are properly secured
- [ ] **Backup Strategy**: Confirm database backup procedures
- [ ] **Rollback Plan**: Have rollback procedure documented

### Monitoring & Observability
- [ ] **Health Endpoints**: `/health` endpoint functional
- [ ] **Metrics Export**: Prometheus metrics accessible
- [ ] **Logging**: Structured logging to stdout
- [ ] **Error Tracking**: Error reporting configured
- [ ] **Performance Monitoring**: Response time tracking

### Security Validation
- [ ] **Container Security**: Non-root user, minimal attack surface
- [ ] **API Security**: Authentication, rate limiting, input validation
- [ ] **Dependency Security**: No known vulnerabilities
- [ ] **Network Security**: Proper firewall rules
- [ ] **Data Protection**: Sensitive data encrypted

---

## 📋 Phase 5: Post-Deployment Verification

### Immediate Health Checks (First 5 minutes)
- [ ] **Container Status**: Pod Running and Ready
- [ ] **Health Endpoint**: `/health` responding correctly
- [ ] **Basic Functionality**: Core API calls working
- [ ] **Database Connectivity**: All database connections healthy
- [ ] **External Services**: All external integrations working

### Extended Monitoring (First 30 minutes)
- [ ] **Error Rates**: No increasing error trends
- [ ] **Response Times**: Consistent performance
- [ ] **Resource Usage**: CPU/memory within expected ranges
- [ ] **Database Performance**: No slow queries or connection issues
- [ ] **User Experience**: Dashboard and UI functioning correctly

### Functionality Verification (First hour)
- [ ] **Complete API Testing**: All endpoints tested in production
- [ ] **End-to-End Workflows**: Test complete user journeys
- [ ] **Data Integrity**: Verify data consistency
- [ ] **Backup Verification**: Confirm backup processes working
- [ ] **Documentation Updates**: Update API docs if needed

---

## 🚨 Critical Stop Conditions

**DO NOT DEPLOY** if any of these conditions exist:

### Showstoppers
- ❌ Unit tests failing
- ❌ Container build failures
- ❌ Health endpoint not responding
- ❌ Database connection failures
- ❌ Critical security vulnerabilities

### High Risk
- ⚠️ Performance degradation (>2x slower than baseline)
- ⚠️ Memory leaks detected
- ⚠️ Increasing error rates
- ⚠️ Missing monitoring/observability

### Medium Risk
- ⚠️ Minor security issues (document and create plan)
- ⚠️ Non-critical functionality issues
- ⚠️ Performance below optimal but acceptable

---

## 🔧 Automated Testing Scripts

### Quick Test Script
```bash
#!/bin/bash
# quick-test.sh - Essential pre-deployment tests

echo "🧪 Running quick pre-deployment tests..."

# 1. Code quality
echo "Checking code quality..."
ruff check . || exit 1
black --check . || exit 1

# 2. Unit tests
echo "Running unit tests..."
pytest tests/unit/ -x || exit 1

# 3. Container build
echo "Building container..."
docker build -t family-assistant:test . || exit 1

# 4. Container health check
echo "Testing container health..."
docker run --rm -d --name test-container -p 8001:8001 family-assistant:test
sleep 30
curl -f http://localhost:8001/health || exit 1
docker stop test-container

echo "✅ All quick tests passed!"
```

### Comprehensive Test Script
```bash
#!/bin/bash
# comprehensive-test.sh - Full pre-deployment validation

echo "🔍 Running comprehensive pre-deployment tests..."

# Source environment variables
source .env.test || exit 1

# Phase 1: Code Quality
echo "=== Code Quality Checks ==="
ruff check . || exit 1
mypy api/ || exit 1
black --check . || exit 1
pytest --cov=api tests/ --cov-fail-under=80 || exit 1

# Phase 2: Container Testing
echo "=== Container Testing ==="
docker build --no-cache -t family-assistant:comprehensive . || exit 1
docker run --rm --name test-container -p 8001:8001 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e REDIS_URL="$REDIS_URL" \
  family-assistant:comprehensive &
CONTAINER_PID=$!

# Wait for container to start
sleep 60

# Test API endpoints
echo "Testing API endpoints..."
curl -f http://localhost:8001/health || exit 1
curl -f http://localhost:8001/dashboard/system-health || exit 1

# Performance test
echo "Running performance test..."
ab -n 100 -c 5 http://localhost:8001/health || exit 1

# Cleanup
docker stop test-container
echo "✅ All comprehensive tests passed!"
```

---

## 📝 Test Results Template

```markdown
## Deployment Test Results

**Date**: [Date]
**Version**: [Version Tag]
**Environment**: [Staging/Production]

### Test Summary
- Code Quality: ✅ PASS / ❌ FAIL
- Unit Tests: ✅ PASS / ❌ FAIL ([X]/[Y] tests)
- Integration Tests: ✅ PASS / ❌ FAIL
- Container Build: ✅ PASS / ❌ FAIL
- Performance: ✅ PASS / ❌ FAIL ([avg_response_time]ms)
- Security Scan: ✅ PASS / ❌ FAIL ([X] vulnerabilities)

### Issues Found
1. [Issue description]
   - Severity: [High/Medium/Low]
   - Resolution: [Fix description]

### Deployment Decision
[ ] APPROVED for deployment
[ ] REJECTED - critical issues must be resolved
[ ] APPROVED WITH CAVEATS - monitor closely
```

---

## 🔄 Continuous Improvement

### Regular Review Points
- Monthly: Review and update test scripts
- Quarterly: Update security scanning procedures
- Each release: Update checklist based on lessons learned

### Metrics to Track
- Test execution time
- Defect detection rate
- Deployment success rate
- Mean time to recovery (MTTR)
- Test coverage percentage

---

**Remember**: A skipped test today is a production incident tomorrow. 🛡️