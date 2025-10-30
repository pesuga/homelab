# Known Issues & Workarounds

This document tracks known issues in the homelab platform and their temporary workarounds.

## 🔴 Critical Issues

### 1. Homelab Dashboard Authentication CSRF Failure

**Status**: Known Issue - Fix Deferred
**Discovered**: 2025-10-30
**Priority**: P2 (Medium)
**Impact**: Dashboard login non-functional, but all services accessible via direct URLs

**Symptoms**:
- Login page loads correctly at http://100.81.76.55:30800
- Credentials entry results in "400 Bad Request - The CSRF session token is missing"
- Pod experiencing continuous restarts (181+ as of 2025-10-30)

**Root Cause**:
- Flask sessions not persisting (using in-memory storage)
- Database init script not idempotent (trigger already exists error)
- Session cookies invalidated by pod restarts

**Workaround**:
Access services directly without dashboard:
- **Grafana**: https://grafana.homelab.pesulabs.net (admin/admin123)
- **N8n**: https://n8n.homelab.pesulabs.net (admin/admin123)
- **Prometheus**: https://prometheus.homelab.pesulabs.net
- **Open WebUI**: https://webui.homelab.pesulabs.net (admin/admin123)
- **Flowise**: https://flowise.homelab.pesulabs.net (admin/admin123)

**Correct Credentials** (for when fixed):
- Username: `admin`
- Password: `ChangeMe!2024#Secure` (from deployment secret)

**Fix Required**:
See `services/homelab-dashboard/TROUBLESHOOTING.md` for complete fix plan.

**Estimated Fix Time**: 1-2 hours

---

## 🟡 Medium Priority Issues

### 2. Sprint 3 Completion Status Ambiguous

**Status**: Documentation Inconsistency
**Discovered**: 2025-10-30
**Priority**: P3 (Low)
**Impact**: README shows "IN PROGRESS" but all objectives are actually complete

**Issue**:
- README.md shows Sprint 3 as "IN PROGRESS"
- All Sprint 3 objectives are actually complete (ROCm, Ollama, LiteLLM, Mem0)
- Misleading project status

**Workaround**:
Reference actual deployment status:
- ROCm 7.2.0 ✅ Installed
- Ollama 0.12.6 ✅ Running with GPU (81.54 t/s)
- LiteLLM ✅ Running on port 8000
- Tailscale ✅ Configured (100.72.98.106)
- Models ✅ Loaded (mistral, llama3.1, qwen2.5-coder, glm4, nomic-embed-text)

**Fix Required**: Update README.md Sprint 3 status to "✅ COMPLETED"

---

## 🟢 Low Priority Issues

### 3. Documentation Password Inconsistency

**Status**: Documentation Gap
**Discovered**: 2025-10-30
**Priority**: P3 (Low)
**Impact**: Confusion about correct credentials

**Issue**:
Various documentation references `admin123` as password, but actual deployment uses `ChangeMe!2024#Secure`

**Files Affected**:
- CLAUDE.md references "admin/admin123"
- Deployment secret uses "ChangeMe!2024#Secure"

**Workaround**:
Use correct passwords from deployment manifests:
- Homelab Dashboard: `ChangeMe!2024#Secure`
- Other services: `admin123` (Grafana, N8n, etc.)

**Fix Required**: Standardize passwords across documentation and deployments

---

## 📋 Tracked for Future Fixes

### 4. No Centralized Log Aggregation

**Status**: Feature Gap
**Priority**: P2 (Medium) - Sprint 4 item
**Impact**: Difficult to troubleshoot issues across services

**Current State**: Logs scattered across pods, accessed via `kubectl logs`

**Planned Solution**: Loki + Promtail deployment (Sprint 4)

---

### 5. No GitOps Automation

**Status**: Feature Gap
**Priority**: P2 (Medium) - Sprint 4 item
**Impact**: Manual kubectl apply for all deployments

**Current State**: All deployments via direct kubectl apply

**Planned Solution**: Flux CD bootstrap (Sprint 4 - in progress)

---

## 📊 Issue Summary

| Priority | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 1 | Workaround available |
| 🟡 Medium | 2 | Tracked for future |
| 🟢 Low | 1 | Non-blocking |
| Total | 4 | - |

---

## 🔄 Update History

- **2025-10-30**: Initial document created
  - Added dashboard auth CSRF issue
  - Added Sprint 3 status documentation issue
  - Added password inconsistency issue
  - Added log aggregation and GitOps tracking

---

## 📝 How to Report New Issues

1. Check this document first to avoid duplicates
2. Add new issue to appropriate priority section
3. Include: Status, Discovered date, Priority, Impact, Workaround
4. Update issue summary table
5. Commit changes to Git

---

**Last Updated**: 2025-10-30
**Maintained By**: Claude Code + User
