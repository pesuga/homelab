# Homelab Networking Standard ("The Golden Rules")

**Status:** ACTIVE / ENFORCED
**Last Updated:** 2025-11-20

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
