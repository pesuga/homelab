# GitHub Personal Access Token Setup for Flux CD

**Purpose**: Create a GitHub Personal Access Token (PAT) for Flux CD to manage GitOps automation
**Required Permissions**: `repo` (Full control of private repositories)
**Token Type**: Fine-grained or Classic (both work)

---

## Quick Steps

### Option 1: Fine-Grained Token (Recommended)

1. **Navigate to GitHub Settings**:
   - Go to: https://github.com/settings/tokens?type=beta
   - Click **"Generate new token"** → **"Generate new token (fine-grained)"**

2. **Configure Token**:
   - **Token name**: `flux-homelab` (or any descriptive name)
   - **Expiration**: 90 days (or custom - you can always regenerate)
   - **Description**: "Flux CD GitOps automation for homelab cluster"
   - **Resource owner**: `pesuga` (your account)

3. **Repository Access**:
   - Select **"Only select repositories"**
   - Choose: `pesuga/homelab`

4. **Permissions** (Repository permissions):
   - **Contents**: ✅ Read and write
   - **Metadata**: ✅ Read-only (automatically selected)
   - **Workflows**: ✅ Read and write (optional, for GitHub Actions)

5. **Generate Token**:
   - Click **"Generate token"**
   - **⚠️ COPY THE TOKEN IMMEDIATELY** - you won't see it again!

### Option 2: Classic Token (Alternative)

1. **Navigate to Classic Tokens**:
   - Go to: https://github.com/settings/tokens
   - Click **"Generate new token"** → **"Generate new token (classic)"**

2. **Configure Token**:
   - **Note**: `flux-homelab`
   - **Expiration**: 90 days (recommended)
   - **Select scopes**:
     - ✅ `repo` (Full control of private repositories)
       - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events

3. **Generate Token**:
   - Click **"Generate token"** at the bottom
   - **⚠️ COPY THE TOKEN IMMEDIATELY**

---

## Token Security

### ✅ Do's
- Store token in password manager (1Password, Bitwarden, etc.)
- Use environment variable for bootstrap: `export GITHUB_TOKEN=ghp_...`
- Regenerate if compromised
- Set reasonable expiration (30-90 days)

### ❌ Don'ts
- Don't commit token to Git repository
- Don't share token in Slack/Discord/chat
- Don't store in plain text files
- Don't use same token for multiple purposes

---

## Using the Token

### Set Environment Variable
```bash
# Copy your token and run:
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Verify it's set:
echo "Token length: ${#GITHUB_TOKEN}"
# Should show: Token length: 40 (classic) or 93+ (fine-grained)
```

### Bootstrap Flux
```bash
# With token in environment, run:
flux bootstrap github \
  --owner=pesuga \
  --repository=homelab \
  --branch=main \
  --path=./clusters/homelab \
  --personal
```

---

## Token Permissions Explained

### `repo` (Full control of private repositories)
**Why needed**: Flux needs to:
1. **Read** repository contents to sync manifests
2. **Write** to commit Flux system manifests during bootstrap
3. **Create deploy keys** for automated sync (optional)
4. **Access repository metadata** for validation

**What Flux will do**:
- Create/update files in `clusters/homelab/flux-system/`
- Commit Flux component manifests
- Read Kubernetes manifests for reconciliation
- Optional: Create webhook for instant notifications

---

## Token Lifecycle

### Initial Bootstrap (One-time)
1. Generate token with `repo` permissions
2. Export as `GITHUB_TOKEN` environment variable
3. Run `flux bootstrap github ...`
4. Flux commits its manifests to Git
5. **Token can be deleted after bootstrap** (if using deploy key method)

### Ongoing Operation
**Option A - Deploy Key** (Recommended):
- Flux creates a read-only deploy key during bootstrap
- Stored as Kubernetes secret `flux-system/flux-system`
- Token not needed after bootstrap
- More secure (no write access needed)

**Option B - Personal Access Token**:
- Keep token active for write operations
- Store in Kubernetes secret
- Required for automated manifest commits
- Needed for webhook setup

---

## Troubleshooting

### "Bad credentials" Error
```
✗ failed to create repository deploy key: POST https://api.github.com/repos/pesuga/homelab/keys: 401 Bad credentials
```
**Solution**:
- Token expired or invalid
- Regenerate token with correct permissions
- Re-export `GITHUB_TOKEN`

### "Resource not accessible by integration" Error
```
✗ Resource not accessible by integration
```
**Solution**:
- Fine-grained token missing `Contents: Write` permission
- Switch to classic token with `repo` scope
- Or add write permission to fine-grained token

### "Token does not have required scopes" Error
```
✗ token does not have required scopes
```
**Solution**:
- Missing `repo` scope on classic token
- Add `repo` scope and regenerate

---

## Quick Reference

### Generate Token URLs
- **Fine-grained**: https://github.com/settings/tokens?type=beta
- **Classic**: https://github.com/settings/tokens

### Required Permissions
| Token Type | Permission | Access Level |
|------------|-----------|--------------|
| Fine-grained | Contents | Read and write |
| Fine-grained | Metadata | Read-only |
| Classic | repo | Full control |

### Token Format
- **Classic**: `ghp_` followed by 36-40 characters
- **Fine-grained**: `github_pat_` followed by ~60+ characters

### Test Token
```bash
# Test token validity:
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/pesuga/homelab

# Should return JSON with repository info (not 401/403)
```

---

## After Bootstrap

Once bootstrap completes successfully:

1. **Verify Flux is using deploy key**:
   ```bash
   kubectl get secret flux-system -n flux-system -o yaml
   # Should contain: identity, identity.pub, known_hosts
   ```

2. **Check deploy key on GitHub**:
   - Visit: https://github.com/pesuga/homelab/settings/keys
   - Should see: "flux-system-main-flux-system-./clusters/homelab"

3. **Optional: Delete token**:
   - If using deploy key method (default)
   - Token only needed for bootstrap
   - Can regenerate if needed for future operations

4. **Save token securely**:
   - Store in password manager
   - Label with creation date
   - Note expiration date for renewal

---

**Created**: 2025-12-01
**Author**: Claude Code
**Purpose**: Flux CD GitOps automation setup
