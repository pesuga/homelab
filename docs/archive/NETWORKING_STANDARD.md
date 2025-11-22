# Homelab Networking Standard ("The Golden Rules")

**Date:** 2025-11-19
**Status:** DRAFT (To be ratified)

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
*   **Mechanism:** Traefik `IngressRoute` or K8s `Ingress`.

---

## Rule 2: Port Standardization

To avoid "What port was that again?" confusion:

| Service Type | Internal Port | Container Port |
| :--- | :--- | :--- |
| **Web UI** | `80` | `80` or `3000` |
| **API** | `8080` | `8080` |
| **Metrics** | `9090` | `9090` |
| **Database** | Standard (`5432`, `6379`) | Standard |

*   **Service Definition:** K8s Services should map `port: 80` to `targetPort: <container-port>` whenever possible for HTTP services, so internal URLs are clean (e.g., `http://n8n.homelab`).

---

## Rule 3: Ingress Configuration

All Ingress resources MUST:
1.  Use the `websecure` entrypoint.
2.  Enable TLS.
3.  (Future) Use the `auth` middleware (Authentik/Authelia).

```yaml
apiVersion: traefik.containo.us/v1alpha1
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
    certResolver: myresolver # or secretName
```

---

## Rule 4: DNS Strategy

*   **Public DNS (Cloudflare):** `*.pesulabs.net` -> `A` record to your WAN IP (or Tunnel).
*   **Local DNS (AdGuard/PiHole):** `*.pesulabs.net` -> `A` record to `192.168.8.20` (Service Node IP / Traefik LoadBalancer IP).
    *   *Crucial:* This ensures that when you are at home, traffic goes directly to the server, not out to the internet and back.

---

## Implementation Checklist

- [ ] **Audit:** Scan all N8n workflows and Environment Variables. Replace `https://...` with `http://...svc.cluster.local`.
- [ ] **Dashboard:** Update Homelab Dashboard to use Internal URLs for health checks (backend) and External URLs for links (frontend).
- [ ] **Documentation:** Add this file to the "Context" of every future Agent session.
