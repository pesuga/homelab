# System Architecture

**Status:** ACTIVE
**Last Updated:** 2025-11-19

## Overview

The Homelab is a private, family-centric AI platform designed for privacy, multilingual support (Spanish/English), and modularity. It runs on a two-node Kubernetes (K3s) cluster with a separate network gateway.

## Hardware Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / WAN                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────▼────────────┐
          │   GL-MT2500 Firewall   │
          │   • OpenWRT            │
          │   • Tailscale Exit     │
          │   • DHCP/DNS           │
          └───────────┬────────────┘
                      │
          ┌───────────▼────────────┐
          │   Local Network        │
          │   192.168.8.0/24       │
          └───────────┬────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐          ┌──────▼─────────┐
│  Compute Node  │          │  Service Node  │
│  (pesubuntu)   │          │  (asuna)       │
│  192.168.8.129 │          │  192.168.8.20  │
└────────────────┘          └────────────────┘
```

### Nodes

1.  **Service Node (`asuna`)**
    *   **Role:** Orchestration & General Services
    *   **OS:** Ubuntu Server 22.04 LTS
    *   **Software:** K3s, PostgreSQL, Redis, N8n, Qdrant, Mem0, Authentik
    *   **IP:** `192.168.8.20` (Tailscale: `100.81.76.55`)

2.  **Compute Node (`pesubuntu`)**
    *   **Role:** Heavy AI Inference (GPU)
    *   **OS:** Ubuntu 25.10
    *   **Hardware:** Intel i5, 32GB RAM, AMD Radeon RX 7800 XT
    *   **Software:** LlamaCpp (Host Network), ROCm
    *   **IP:** `192.168.8.129` (Tailscale: `100.86.122.109`)

## Software Stack

### Core Infrastructure
*   **Orchestrator:** K3s (Lightweight Kubernetes)
*   **Networking:** Flannel (CNI), Traefik (Ingress), Tailscale (VPN/Mesh)
*   **GitOps:** Flux CD (Planned/Partial), Manual `kubectl apply` (Current)

### Data Layer
*   **Database:** PostgreSQL (HA)
*   **Cache:** Redis
*   **Vector DB:** Qdrant

### AI Stack
*   **LLM Engine:** LlamaCpp (running on Compute Node)
*   **Memory:** Mem0 (Long-term memory for agents)
*   **Orchestration:** N8n (Workflows), AgentStack

### Authentication
*   **Provider:** Authentik
*   **Protocol:** OAuth2 / OIDC / Proxy Provider

## Deployment Strategy (GitOps)

We follow a "Pragmatic GitOps" approach.

1.  **Source of Truth:** The Git repository (`homelab/`) is the single source of truth.
2.  **Manifests:** All resources are defined in `infrastructure/kubernetes/`.
3.  **Secrets:** Managed via Sealed Secrets (encrypted in Git).
4.  **Workflow:**
    *   **Dev:** Edit manifests -> Commit -> `kubectl apply` (Current)
    *   **Prod (Future):** Edit manifests -> Commit -> Flux Auto-Sync

## Networking Strategy

See `NETWORKING_STANDARD.md` for the "Golden Rules".

*   **Internal:** `http://<service>.<namespace>.svc.cluster.local:<port>`
*   **External:** `https://<subdomain>.pesulabs.net` (via Traefik)
