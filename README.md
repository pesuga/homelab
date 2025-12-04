# Homelab Project

**A two‑node Kubernetes homelab** that provides self‑hosted AI services, automation, and family‑focused applications. This repository is the single source of truth for infrastructure, services, and documentation.

---

## Quick Overview

- **Architecture**: K3s cluster spanning a **service node** (`asuna`, Tailscale IP `100.81.76.55`) and a **compute node** (`pesubuntu`, Tailscale IP `100.72.98.106`).
- **Core Services**: Dashboard, N8n workflow automation, Family Assistant (FastAPI), LlamaCpp GPU‑accelerated LLM inference.
- **Networking**: Secure Tailscale mesh, Traefik ingress with automatic Let's Encrypt TLS.
- **Observability**: Prometheus, Grafana, Loki.
- **GitOps**: Flux CD continuously reconciles manifests from this repository.
- **CI/CD**: GitHub Actions builds the Family Portal UI and pushes images to GitHub Container Registry.

---

## Repository Structure

```
homelab/
├── infrastructure/          # IaC – K8s manifests, Flux config, legacy Docker compose
├── services/               # Application source code (family‑api, dashboard, n8n, …)
├── project‑context/        # Authoritative documentation (architecture, ADRs, …)
├── docs/                   # Temporary, work‑in‑progress docs (to be cleaned up)
├── scripts/keep/           # Permanent utility scripts (indexed in INDEX.md)
├── tmp/                    # Ephemeral, git‑ignored artifacts (session files)
└── README.md               # **This file** – high‑level project overview
```

- **`project‑context/`** is the single source of truth for architecture, decisions, and detailed documentation. All other docs should reference or link to files here.
- **`docs/`** holds drafts; move finished content to `project‑context/` or delete it.
- **`scripts/keep/`** contains useful scripts; see `scripts/keep/INDEX.md` for an index.
- **`tmp/`** is for session‑specific files and is ignored by Git.

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/pesuga/homelab.git && cd homelab
   ```
2. **Review the architecture** – see `project‑context/ARCHITECTURE.md` for a full diagram and component breakdown.
3. **Deploy the cluster** (requires access to the two nodes):
   ```bash
   # On the service node (asuna)
   curl -sfL https://get.k3s.io | sh -
   # Install Flux CD
   flux install
   # Apply the GitOps configuration
   flux reconcile source git flux-system
   flux reconcile kustomization homelab
   ```
   *Flux will automatically pull manifests from the `infrastructure/` directory and keep the cluster in sync.*
4. **Access services** via the Traefik ingress (HTTPS) or directly through Tailscale IPs. The dashboard is available at `https://dashboard.homelab.local` (replace with your domain).

---

## Documentation

- **Architecture** – `project‑context/ARCHITECTURE.md`
- **Decision Records** – `project‑context/ADR-*.md`
- **Service Inventory** – `project‑context/SERVICES.md`
- **Operational Guides** – this `README.md` and the various `*.md` files under `project‑context/`.

All documentation follows the conventions described in `project‑context/CONTRIBUTING.md`.

---

## Contributing

Please read `project‑context/CONTRIBUTING.md` for guidelines on:
- Adding or updating documentation.
- Introducing new services or infrastructure components.
- Keeping the GitOps workflow clean (commit, push, let Flux apply).

When adding new scripts, place them under `scripts/keep/` and update `scripts/keep/INDEX.md`.

---

## License

This project is licensed under the **Apache License 2.0**. See the `LICENSE` file for details.

---

*Last updated: 2025‑12‑04*
