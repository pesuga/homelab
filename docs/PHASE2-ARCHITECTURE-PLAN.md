# Phase 2: Deployment Infrastructure Architecture

**Status**: Phase 2.1 Complete - Manual GitOps Active
**Timeline**: 2-3 weeks (4 sub-phases)
**Risk Level**: Medium (mitigated)
**Agent**: system-architect

---

## Executive Summary

Phase 2 builds on the successful Phase 1 foundation to create a production-ready GitOps deployment system. The architecture prioritizes **pragmatism over perfection** - delivering automated, reliable deployments without enterprise complexity.

**⚠️ Current Status**: Phase 2.1 complete with manual GitOps workaround active due to network connectivity issue preventing Flux Git synchronization.

**Core Objectives**:
- ✅ Bootstrap Flux CD for declarative infrastructure (Installed, manual sync)
- ⏳ Implement semantic versioning with git traceability (In Progress)
- ⏳ Setup GitHub Actions CI/CD for automated builds (Planned)
- ⏳ Deploy OpenTelemetry Collector for observability (Planned)

**Expected Outcomes** (Modified for Manual GitOps):
- Deployment success rate: 95% → **99%+** (via manual validation)
- Mean time to deploy: 5 minutes → **< 3 minutes** (manual apply)
- Mean time to recovery: 10 minutes → **< 5 minutes** (git revert + apply)
- Manual kubectl operations: **1-2 per deployment** (until Flux sync resolved)

---

## Implementation Phases

### Phase 2.1: Foundation (Week 1, Days 1-2) ✅ COMPLETE

**Objective**: Bootstrap Flux CD and configure secret management

**Status**: Complete with manual GitOps workaround

**Completed Tasks**:
1. ✅ Install Sealed Secrets controller (v0.33.1)
2. ✅ Bootstrap Flux CD (v2.7.3, all 6 controllers running)
3. ⏳ Migrate secrets to Sealed Secrets (Deferred - using manual kubectl for now)
4. ✅ Create Flux GitRepository sources (Created, sync blocked by network)
5. ✅ Verify Flux controllers healthy (All healthy)

**Achieved**:
- ✅ Flux CD installed and operational
- ✅ Deploy key configured in GitHub
- ✅ Infrastructure ready for GitOps
- ⚠️ Git sync blocked by network timeout issue

**Workaround Implemented**:
- Manual GitOps workflow documented (`docs/MANUAL-GITOPS-WORKFLOW.md`)
- Helper scripts created (`scripts/manual-deploy.sh`, `scripts/verify-deployment.sh`)
- Git remains source of truth, deployments via `kubectl apply`

**Network Issue Investigation**: See `docs/FLUX-NETWORK-INVESTIGATION.md` for details

---

### Phase 2.2: GitOps Migration (Week 1, Days 3-5) 🔄

**Objective**: Migrate existing deployments to Flux control

**Tasks**:
1. Create Flux Kustomizations for infrastructure
2. Migrate databases (PostgreSQL, Redis, Qdrant)
3. Migrate monitoring (Prometheus, Loki)
4. Migrate Family Assistant (backend, frontend)
5. Migrate Dashboard and N8n

**Success Criteria**:
- ✓ All services under Flux control
- ✓ Drift detection working
- ✓ Auto-healing operational

**Rollback Plan**: Delete Flux Kustomizations, services remain running

---

### Phase 2.3: CI/CD Pipeline (Week 2, Days 1-3) 🚀

**Objective**: Automate builds and deployments via GitHub Actions

**Tasks**:
1. Create semantic versioning scripts
2. Setup Family Assistant CI/CD workflow
3. Setup Dashboard CI/CD workflow
4. Configure monorepo service detection
5. Add image scanning and security checks

**Success Criteria**:
- ✓ Git push triggers automated build
- ✓ Tests run before deployment
- ✓ Images tagged with semantic versions
- ✓ Vulnerabilities scanned and reported

**Rollback Plan**: Manual builds continue working via scripts

---

### Phase 2.4: Observability (Week 2-3) 📊

**Objective**: Deploy OTEL Collector and enable tracing

**Tasks**:
1. Deploy OTEL Collector
2. Configure Loki integration
3. Configure Prometheus integration
4. Enable OTEL in Family Assistant
5. Enable OTEL in Dashboard
6. Create OTEL dashboards in Grafana (future)

**Success Criteria**:
- ✓ OTEL Collector healthy and receiving data
- ✓ Logs flowing to Loki via OTEL
- ✓ Metrics flowing to Prometheus
- ✓ Traces captured (foundation for Jaeger)

**Rollback Plan**: Disable OTEL_SDK in services, collector removed

---

## Key Architecture Decisions

### 1. Semantic Versioning Strategy

**Tag Format**: `v{MAJOR}.{MINOR}.{PATCH}-{GIT_SHA}-{ENVIRONMENT}`

**Examples**:
- Production: `v2.1.0-a3f5c2b-prod`
- Development: `v2.1.0-a3f5c2b-dev`
- Latest stable: `v2.1.0` (alias)

**Versioning Rules**:
- **MAJOR**: Breaking API changes, schema migrations
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, security patches
- **GIT_SHA**: First 7 chars of commit hash (traceability)

### 2. Flux CD Repository Structure

```
homelab/
├── clusters/
│   └── homelab/                    # Cluster configs
│       ├── flux-system/            # Auto-generated
│       ├── infrastructure.yaml     # Infrastructure Kustomization
│       ├── apps.yaml               # Application Kustomization
│       └── secrets/                # Sealed Secrets
├── infrastructure/
│   ├── databases/                  # PostgreSQL, Redis, Qdrant
│   ├── observability/              # Prometheus, Loki, OTEL
│   └── networking/                 # Traefik (future)
├── apps/
│   ├── family-assistant/           # Backend, frontend
│   ├── homelab-dashboard/
│   └── n8n/
└── services/                       # Source code
```

### 3. Secret Management

**Solution**: Sealed Secrets (Bitnami)

**Why**:
- Simple, no external dependencies
- Works with GitOps (encrypted in Git)
- Free and open source

**Usage**:
```bash
kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_PASSWORD=secret \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > postgres-credentials.yaml
```

### 4. CI/CD Pipeline Stages

```
Stage 1: Build & Test
  ├─ Unit tests
  ├─ Linting (ruff)
  └─ Code coverage

Stage 2: Build & Scan
  ├─ Docker build
  ├─ Trivy security scan
  └─ SARIF upload to GitHub

Stage 3: Push to Registry
  ├─ Tag with semantic version
  ├─ Tag with git SHA
  └─ Push to local registry

Stage 4: Update Manifests
  ├─ Update Kustomization
  ├─ Git commit
  └─ Trigger Flux reconciliation

Stage 5: Automatic Deploy
  └─ Flux watches Git, auto-deploys
```

### 5. OpenTelemetry Collector

**Deployment**: Gateway mode (single collector for all services)

**Integrations**:
- **Logs** → Loki
- **Metrics** → Prometheus
- **Traces** → Jaeger (future)

**Resource Limits**:
- CPU: 200m request, 1 CPU limit
- Memory: 256Mi request, 512Mi limit
- Memory limiter at 512Mi to prevent OOM

---

## Risk Mitigation

### High Risks

| Risk | Mitigation |
|------|-----------|
| Flux bootstrap fails | Manual install fallback, test network first |
| Secret migration breaks services | Test in non-prod namespace, keep manual backup |
| Registry auth fails in CI | Use insecure registry config, document workaround |

### Medium Risks

| Risk | Mitigation |
|------|-----------|
| OTEL collector resource exhaustion | Memory limiter processor, conservative limits |
| Flux drift detection conflicts | `flux suspend` during maintenance |

---

## Success Metrics

### Deployment Metrics
- Deployment success rate: **99%+** (from 95%)
- Mean time to deploy: **< 2 minutes** (from 5 minutes)
- Mean time to recovery: **< 5 minutes** (automated rollback)

### Automation Metrics
- Manual kubectl operations: **0 per week** (from daily)
- Git commits to production: **< 10 minutes** (via Flux)
- Failed builds caught by CI: **100%** (before production)

### Observability Metrics
- OTEL data ingestion: **99% uptime**
- Log retention: **7 days** (via Loki)
- Trace sampling: **10%** (performance balance)

### Quality Metrics
- Critical vulnerabilities: **0** (caught by Trivy)
- Test coverage: **> 80%** (enforced in CI)
- Image size reduction: **20%** (multi-stage builds)

---

## Execution Principles ⚠️ IMPORTANT

### Step-by-Step Testing Protocol

**Every step must follow this pattern**:
1. **Plan** - Document what we're about to do
2. **Execute** - Implement the change
3. **Test** - Verify it works as intended
4. **Validate** - Check no regressions introduced
5. **Document** - Update all relevant docs
6. **Commit** - Save verified working state

**No moving forward until current step is fully verified and documented.**

### Documentation Hygiene

**Before each phase**:
- Audit existing documentation for accuracy
- Mark deprecated docs with `[DEPRECATED]` prefix
- Move outdated docs to `trash/deprecated-docs-{date}/`
- Update all cross-references to new locations

**During each phase**:
- Update documentation in real-time as changes are made
- Keep docs synchronized with actual cluster state
- Remove contradictory or outdated information immediately

**After each phase**:
- Review all documentation for consistency
- Ensure newcomers can follow the docs without confusion
- Test documentation by following it step-by-step

### Verification Checklist (Every Step)

- [ ] Services remain healthy (no disruption)
- [ ] Tests pass (automated + manual)
- [ ] Documentation updated
- [ ] Git commit with clear message
- [ ] Rollback plan tested

---

## Next Steps

### Immediate Actions (Week 1)

**Day 1: Preparation** 🔍
- [x] Review architecture document
- [x] Audit current documentation (already clean, no deprecated files found)
- [x] Install kubeseal CLI (v0.27.2)
- [x] Install Sealed Secrets controller (v0.33.1)
- [x] Test Sealed Secrets in test namespace (✅ working)
- [x] Backup current cluster state (/tmp/homelab-backup-20251117.yaml)
- [ ] Generate GitHub Personal Access Token (pending - needed for Flux bootstrap)
- **Verification**: ✅ Documentation clean, ✅ Sealed Secrets working, ✅ Backup successful, ⏳ GitHub token pending

**Day 2: Flux Bootstrap** 🏗️
- [ ] Bootstrap Flux CD (read-only mode)
- [ ] Verify all 6 Flux controllers healthy
- [ ] Test reconciliation loop (no-op changes)
- [ ] Update documentation with Flux endpoints
- **Verification**: `flux check` passes, no service disruption, docs updated

**Day 3-4: Secret Migration** 🔐
- [ ] Install Sealed Secrets controller
- [ ] Test seal/unseal in test namespace
- [ ] Migrate PostgreSQL credentials
- [ ] Migrate Redis credentials
- [ ] Verify services still functional
- [ ] Update documentation with secret management process
- **Verification**: All services running, secrets working, process documented

**Day 5: First Migration** 🚀
- [ ] Migrate Family Assistant to Flux (one service only)
- [ ] Test drift detection (manual change, verify auto-revert)
- [ ] Test auto-healing (delete pod, verify recreation)
- [ ] Update deployment documentation
- **Verification**: Flux managing service, drift detection working, docs current

---

## Documentation References

- **Full Architecture**: See complete system-architect analysis above
- **Phase 1 Fixes**: `/docs/PHASE1-FIXES-COMPLETE.md`
- **Deployment Problems**: `/docs/DEPLOYMENT-PROBLEMS-ANALYSIS.md`
- **Scripts**: `/scripts/README.md`

---

**Ready to proceed with Phase 2.1 (Flux Bootstrap)?**

**Estimated Completion**: 2-3 weeks
**Total ROI**: 10x improvement in deployment reliability and developer velocity
