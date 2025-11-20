# Service Inventory

**Status:** ACTIVE
**Last Updated:** 2025-11-20 (Evening)

## Active Services

| Service | Internal URL (Cluster DNS) | External URL (Ingress) | Notes |
| :--- | :--- | :--- | :--- |
| **N8n** | `http://n8n.homelab.svc.cluster.local:80` | `https://n8n.fa.pesulabs.net` | Workflow automation |
| **Qdrant** | `http://qdrant.homelab.svc.cluster.local:6333` | - | Vector Database |
| **Mem0** | `http://mem0.homelab.svc.cluster.local:8000` | - | Memory Service |
| **LlamaCpp** | `http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080` | - | LLM Inference (Service points to LAN IP) |
| **PostgreSQL** | `postgres.homelab.svc.cluster.local:5432` | - | Main Database |
| **Redis** | `redis.homelab.svc.cluster.local:6379` | - | Cache |
| **Authentik** | `http://authentik-server.authentik.svc.cluster.local:80` | `https://auth.pesulabs.net` | Identity Provider |
| **Family API** | `http://family-assistant-backend.homelab.svc.cluster.local:8001` | `https://api.fa.pesulabs.net` | Backend API |
| **Family App** | `http://family-assistant.family-assistant-app.svc.cluster.local:80` | `https://app.fa.pesulabs.net` | User Interface |
| **Family Admin** | `http://family-admin.homelab.svc.cluster.local:80` | `https://admin.fa.pesulabs.net` | Admin Dashboard |

## Alternative Access (NodePort)

| Service | NodePort Access | URL |
| :--- | :--- | :--- |
| **Family API** | `http://100.81.76.55:30801` | Direct backend access |
| **Family Portal** | `http://100.81.76.55:32748` | Direct frontend access |

## Node IP Addresses

| Node | Hostname | LAN IP | Tailscale IP |
| :--- | :--- | :--- | :--- |
| **Service Node** | `asuna` | `192.168.8.20` | `100.81.76.55` |
| **Compute Node** | `pesubuntu` | `192.168.8.129` | `100.86.122.109` |
| **Gateway** | `GL-MT2500` | `192.168.8.1` | `100.64.0.1` |

## Service Health Status

All critical services operational as of 2025-11-20 evening:
- ✅ **Authentik:** Server & Worker running (0 restarts after fixing command→args issue)
- ✅ **Family Admin:** 2/2 pods running (fixed image pull and nginx config)
- ✅ **Family App:** 2/2 pods running with internal DNS
- ✅ **Family API:** Backend running, accessible via internal DNS
- ✅ **N8N:** Running stable
- ✅ **PostgreSQL:** Healthy
- ✅ **Redis:** Healthy

## Critical Notes

1.  **LlamaCpp:** Runs on `pesubuntu` with `hostNetwork: true`. Accessed via a K8s Service (`llamacpp-kimi-vl-service`) that points to the LAN IP `192.168.8.129`.
2.  **Golden Rules Compliance:** All services now use internal DNS (`http://<service>.<namespace>.svc.cluster.local:<port>`) for service-to-service communication.
3.  **Port Standardization:** Web services expose port 80, mapping to container ports (80→9000 Authentik, 80→3000 admin, 80→5678 N8N).
4.  **External Access:** All external routes use Traefik IngressRoute with TLS via Cloudflare DNS-01 (certResolver: default).
5.  **Recent Fixes:** Authentik CrashLoopBackOff (command→args), Family Admin ImagePullBackOff (image reference + nginx config).
