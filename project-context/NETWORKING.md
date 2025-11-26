# Homelab Networking Standard ("The Golden Rules")

**Status:** ACTIVE / ENFORCED
**Last Updated:** 2025-11-26
**Source:** Migrated from project_context/NETWORKING_STANDARD.md

---

## The Problem
"Every new service or change we need to make we break what was done before."

## The Solution
A strict set of rules that ALL services and agents must follow. No exceptions without a documented RFC.

---

## Rule 1: The "Internal vs External" Separation

### 🛑 Internal Traffic (Service-to-Service)
**Services running inside the cluster MUST talk to each other using K3s Internal DNS.**

*   **Protocol:** `HTTP` (No TLS)
*   **Address Format:** `http://<service-name>.<namespace>.svc.cluster.local:<port>`
*   **Example:** N8n talking to Qdrant
    *   ✅ `http://qdrant.homelab.svc.cluster.local:6333`
    *   ❌ `https://qdrant.homelab.pesulabs.net` (BANNED for internal calls)
    *   ❌ `http://192.168.x.x` (BANNED - IPs change)

**Why?**
1.  **Speed:** No TLS overhead.
2.  **Reliability:** Bypasses Ingress, Hairpin NAT, and Certificate trust issues.
3.  **Simplicity:** It just works, always.

### 🌍 External Traffic (User-to-Service)
**Users (Browsers, Mobile Apps) talk to services via the Ingress Controller (Traefik).**

*   **Protocol:** `HTTPS` (TLS Terminated at Traefik)
*   **Address Format:** `https://<subdomain>.pesulabs.net`
*   **Mechanism:** Traefik `IngressRoute` with Cloudflare DNS-01 Challenge.

---

## Rule 2: TLS & DNS Strategy (Cloudflare)

**We use Cloudflare as the Single Source of Truth for DNS and TLS.**

### 1. DNS Management
*   **Zone:** `pesulabs.net` managed on Cloudflare.
*   **Agents:** Can configure DNS records using the Cloudflare API token.
*   **Token Location:** `~/.cloudflare/credentials` (on host) -> `cloudflare-api-token` (Secret in `homelab` namespace).

### 2. TLS Certificates (Wildcards)
*   **Provider:** Let's Encrypt via Traefik.
*   **Challenge:** DNS-01 (Cloudflare).
*   **Why?** Allows wildcard certificates (`*.pesulabs.net`) and works behind NAT/Firewalls without opening port 80.

### 3. Ingress Configuration
All external services MUST use this template:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: my-service
  namespace: homelab
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`my-service.pesulabs.net`)
      kind: Rule
      services:
        - name: my-service
          port: 80
  tls:
    certResolver: default # Configured for Cloudflare DNS-01
```

---

## Rule 3: Port Standardization

To avoid "What port was that again?" confusion:

| Service Type | Internal Port | Container Port |
| :--- | :--- | :--- |
| **Web UI** | `80` | `80` or `3000` |
| **API** | `8080` | `8080` |
| **Metrics** | `9090` | `9090` |
| **Database** | Standard (`5432`, `6379`) | Standard |

*   **Service Definition:** K8s Services should map `port: 80` to `targetPort: <container-port>` whenever possible for HTTP services, so internal URLs are clean (e.g., `http://n8n.homelab`).

---

## Network Topology [VERIFIED 2025-11-26]

### Tailscale Mesh
- **Service Node (asuna)**: 100.81.76.55
- **Compute Node (pesubuntu)**: 100.86.122.109
- **MagicDNS**: Enabled
- **Purpose**: Secure inter-node communication

### LAN Network
- **Subnet**: 192.168.8.0/24
- **Gateway**: 192.168.8.1 (GL-MT2500)
- **Compute Node**: 192.168.8.129
- **Service Node**: TBD (requires verification)

### K8s Networking
- **CNI**: Flannel (default K3s)
- **Service CIDR**: 10.43.0.0/16 (default K3s)
- **Pod CIDR**: TBD
- **Ingress**: Traefik (websecure entrypoint on port 443)

---

## Verified Service URLs [VERIFIED 2025-11-26]

### External (HTTPS via Traefik)
- **N8n**: https://n8n.fa.pesulabs.net
- **Authentik**: https://auth.pesulabs.net
- **Family App**: https://app.fa.pesulabs.net
- **Family Admin**: https://admin.fa.pesulabs.net
- **Family API**: https://api.fa.pesulabs.net

### Internal (K8s ClusterIP)
- **N8n**: `n8n.homelab.svc:80`
- **Authentik Server**: `authentik-server.authentik.svc:9000`
- **Family App**: `family-assistant.family-assistant-app.svc:80`
- **Family Admin**: `family-admin.homelab.svc:3000`
- **Family API**: `family-assistant-backend.homelab.svc:8001`
- **PostgreSQL**: `postgres.homelab.svc:5432`
- **Redis**: `redis.homelab.svc:6379`
- **Qdrant**: `qdrant.homelab.svc:6333`
- **Mem0**: `mem0.homelab.svc:8080`
- **LlamaCpp**: `llamacpp-service.default.svc:8081`

---

## Common Violations & Fixes

### ❌ Violation: Frontend calling backend via external HTTPS
```javascript
// WRONG
const API_URL = "https://api.fa.pesulabs.net";
```

### ✅ Fix: Use internal DNS
```javascript
// CORRECT (server-side)
const API_URL = "http://family-assistant-backend.homelab.svc:8001";

// CORRECT (client-side browser)
const API_URL = "https://api.fa.pesulabs.net"; // Browser must use external
```

### ❌ Violation: Using IP addresses
```yaml
# WRONG
env:
  - name: DATABASE_HOST
    value: "10.43.239.209"
```

### ✅ Fix: Use service DNS
```yaml
# CORRECT
env:
  - name: DATABASE_HOST
    value: "postgres.homelab.svc"
```

---

## Compliance Validation

**Last Audit**: 2025-11-20
**Compliance Status**: 100%

### Enforcement Checklist
- [x] All services use internal DNS for service-to-service calls
- [x] All external routes use Traefik IngressRoute
- [x] All web services expose port 80 (mapped to container ports)
- [x] All TLS certificates use Cloudflare DNS-01 via certResolver: default
- [x] No hardcoded IPs in service configurations
- [x] No mixed HTTP/HTTPS in single application context

---

## Related Documentation

- See `SERVICES.md` for complete service inventory with internal URLs
- See `ARCHITECTURE.md` for network topology diagrams
- See `AUTHENTIK_INTEGRATION.md` for SSO integration patterns

---

**Maintenance Notes**:
- Update this file when network architecture changes
- Run compliance audit after any networking changes
- Document exceptions with RFC in git commit messages
- Review quarterly for accuracy
