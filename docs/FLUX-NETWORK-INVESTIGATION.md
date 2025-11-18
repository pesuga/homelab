# Flux CD Network Connectivity Investigation

**Date**: 2025-11-17 to 2025-11-18
**Status**: ⚠️ UNRESOLVED - Git clone operations timing out
**Issue**: GitRepository cannot sync from GitHub despite network connectivity

## Investigation Summary

### ✅ What Works
1. **Pod-to-GitHub Connectivity**: Regular pods CAN reach GitHub
   - HTTPS (443): ✅ Working (`curl -I https://github.com`)
   - SSH (22): ✅ Working (`nc -zv github.com 22`)
   - Tested with: `nicolaka/netshoot` pod

2. **Flux CD Installation**: Fully operational
   - All 6 controllers healthy and running
   - Bootstrap completed successfully
   - Deploy key installed in GitHub (read-only)
   - SSH secret exists in `flux-system` namespace

3. **Source Controller Connectivity**:
   - Can reach GitHub on port 22
   - Deploy key properly configured
   - Known hosts configured correctly

### ❌ What Fails
**Git Clone Operations from source-controller**:
```
Error: "error decoding upload-pack response: context deadline exceeded"
```

**Symptoms**:
- Connection establishes (no "permission denied" or "connection refused")
- Clone operation starts but times out during data transfer
- Happens with both HTTPS and SSH protocols
- Timeout increased from 180s to 600s - still fails

## Network Test Results

### Test 1: Basic HTTPS Connectivity
```bash
kubectl exec nettest -- curl -I -m 10 https://github.com
# Result: ✅ SUCCESS - HTTP/2 200
```

### Test 2: SSH Port Check
```bash
kubectl exec nettest -- nc -zv github.com 22
# Result: ✅ SUCCESS - Connection succeeded
```

### Test 3: Source Controller to GitHub
```bash
kubectl exec -n flux-system deployment/source-controller -- sh -c 'nc -zv github.com 22'
# Result: ✅ SUCCESS - Port 22 open
```

### Test 4: Git Clone from Regular Pod
```bash
kubectl run git-test --image=alpine/git -- git clone ssh://git@github.com/pesuga/homelab.git
# Result: ❌ FAILED - Permission denied (expected - no deploy key)
```

### Test 5: Git Clone from Source Controller
```
Automatic reconciliation every 1 minute
# Result: ❌ FAILED - "context deadline exceeded"
```

## Configuration Details

### GitRepository Configuration
```yaml
spec:
  url: ssh://git@github.com/pesuga/homelab.git
  ref:
    branch: main
  interval: 1m0s
  timeout: 600s  # Increased from 180s
  secretRef:
    name: flux-system
```

### SSH Secret
- **Name**: `flux-system` in `flux-system` namespace
- **Type**: Opaque
- **Contents**:
  - `identity`: ECDSA P-384 private key
  - `identity.pub`: Public key (deployed to GitHub)
  - `known_hosts`: GitHub host key

### GitHub Deploy Key
- **ID**: 135054121
- **Title**: flux-system-main-flux-system-./clusters/homelab
- **Access**: read-only
- **Created**: 2025-10-31T13:35:49Z
- **Status**: ✅ Active in repository

## Error Analysis

### Error Pattern
```json
{
  "error": "failed to checkout and determine revision: unable to clone 'ssh://git@github.com/pesuga/homelab.git': error decoding upload-pack response: context deadline exceeded",
  "timestamp": "2025-11-18T00:29:56.340Z"
}
```

### Root Cause Hypothesis

**Most Likely**: Network bandwidth/latency issue specific to git protocol
- Connection establishes successfully (SSH handshake works)
- upload-pack response decoding times out
- Suggests slow/unstable data transfer during clone operation
- Not a general network connectivity issue (other protocols work)

**Possible Causes**:
1. **ISP/Network Throttling**: Git protocol traffic being rate-limited or shaped
2. **MTU Issues**: Packet fragmentation causing slow transfers
3. **Proxy/Firewall Deep Packet Inspection**: Interfering with git protocol
4. **Repository Size**: Large repository taking too long to clone
5. **GitHub API Rate Limiting**: Though unlikely for git clone operations

## Mitigation Attempts

### Attempt 1: Switch from HTTPS to SSH
- **Action**: Bootstrap with SSH URL instead of HTTPS
- **Result**: ❌ FAILED - Same timeout error with SSH

### Attempt 2: Increase Timeout
- **Action**: Increased timeout from 180s to 600s
- **Result**: ❌ FAILED - Still times out

### Attempt 3: Manual Reconciliation
- **Action**: Force reconciliation with `flux reconcile`
- **Result**: ❌ FAILED - Timeout persists

## Next Steps (Prioritized)

### Option 1: Workaround - Manual GitOps (Recommended for now)
**Pros**: Unblocks Phase 2 development, maintains Git as source of truth
**Cons**: No automatic sync, manual `kubectl apply` required
**Implementation**:
1. Continue using Git repository as source
2. Apply manifests manually via `kubectl apply -k`
3. Defer full GitOps until network issue resolved
4. Document manual deployment process

### Option 2: Network Diagnostics
**Actions**:
1. Test git clone from compute node (pesubuntu)
2. Check MTU settings on both nodes
3. Test with different DNS servers
4. Verify no transparent proxy interfering
5. Contact ISP about potential throttling

### Option 3: Alternative Git Source
**Implementation**:
1. Deploy local Gitea instance
2. Mirror repository to local Gitea
3. Configure Flux to sync from local source
4. Pros: Full GitOps functionality, no external dependency
5. Cons: Additional infrastructure, mirror sync needed

### Option 4: Repository Optimization
**Actions**:
1. Check repository size: `git count-objects -vH`
2. Reduce repository size if needed (LFS, history rewrite)
3. Create shallow clone support
4. Split large repository if necessary

## Temporary Solution (Active)

**Status**: Phase 2.1 complete with caveat

**What's Working**:
- ✅ Flux CD installed and operational
- ✅ Sealed Secrets controller ready
- ✅ Repository structure prepared for GitOps
- ✅ Deploy key configured

**What's Blocked**:
- ❌ Automatic Git sync from GitHub
- ❌ Full GitOps automation
- ❌ Phase 2.2 implementation

**Workaround**:
- Manual deployments via `kubectl apply`
- Git as source of truth for manifests
- Defer automatic sync until resolution

## Documentation
- [x] Phase 2.1 Day 1 completion documented
- [x] Network investigation documented
- [x] Workaround strategy documented
- [ ] Manual deployment process documented
- [ ] Network fix procedure documented (when found)

## References
- Flux Documentation: https://fluxcd.io/flux/faq/
- GitHub Deploy Keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys
- K3s Networking: https://docs.k3s.io/networking

---

**Investigation Date**: 2025-11-17 to 2025-11-18
**Investigator**: Claude Code
**Status**: Investigation complete, awaiting resolution strategy decision