# Homelab Project – Family‑First AI Platform

> **"Privacy‑first, local‑first AI for families."**

![GitHub Stars](https://img.shields.io/github/stars/pesuga/homelab?style=flat&logo=github) ![License](https://img.shields.io/github/license/pesuga/homelab?style=flat) ![Last Commit](https://img.shields.io/github/last-commit/pesuga/homelab/main?style=flat)

---

## 🚀 Executive Summary (from PRD)

Family Assistant is a **privacy‑first, self‑hosted AI platform** built for multi‑generational families. It delivers **local‑first processing** – no recurring cloud API costs – while offering a **unified knowledge base** and **robust parental controls**. Powered by a two‑node Kubernetes homelab, it combines **GPU‑accelerated LLM inference** with a modern web UI.

### 🌟 Key Differentiators

- **Local‑First Processing** – All AI runs on‑premises, guaranteeing zero ongoing API fees.
- **Privacy by Design** – Data never leaves your home network; end‑to‑end encryption protects everything.
- **Family‑Centric UX** – Role‑based access (Parent, Teen, Child) with age‑appropriate content filters.
- **Extensible MCP Framework** – Plug‑in custom tools, integrate Home Assistant, and build community‑driven extensions.
- **Open‑Source Core** – Community‑driven development with optional paid support.

---

## 📂 Repository Structure

```
homelab/
├── infrastructure/          # IaC – K8s manifests, Flux config, legacy Docker compose
├── services/               # Application source (family‑api, dashboard, n8n, …)
├── project‑context/        # Authoritative docs (architecture, PRD, ADRs, …)
├── docs/                   # Draft docs – move finished files to project‑context
├── scripts/keep/           # Permanent utility scripts (see INDEX.md)
├── tmp/                    # Ephemeral, git‑ignored session artifacts
└── README.md               # **This file** – high‑level project overview
```

- **`project‑context/`** is the single source of truth for architecture, product requirements, and design decisions.
- **`docs/`** holds work‑in‑progress documentation; clean up or migrate when stable.
- **`scripts/keep/`** contains useful scripts; see `scripts/keep/INDEX.md`.
- **`tmp/`** is for temporary session files and is ignored by Git.

---

## 🛠️ Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/pesuga/homelab.git && cd homelab
   ```
2. **Read the architecture** – `project‑context/ARCHITECTURE.md` provides a full diagram and component breakdown.
3. **Deploy the cluster** (requires access to the two nodes):
   ```bash
   # On the service node (asuna)
   curl -sfL https://get.k3s.io | sh -
   # Install Flux CD
   flux install
   # Sync manifests from this repo
   flux reconcile source git flux-system
   flux reconcile kustomization homelab
   ```
   Flux will continuously apply the manifests under `infrastructure/`.
4. **Access services** via the Traefik ingress (HTTPS) or directly through Tailscale IPs. The dashboard is reachable at `https://dashboard.homelab.local` (or your custom domain).

---

## 📚 Documentation Hub

- **Product Requirements** – `project‑context/PRD.md` (executive summary, personas, functional & non‑functional specs).
- **Architecture** – `project‑context/ARCHITECTURE.md` (system diagram, network, Kubernetes layout).
- **Decision Records** – `project‑context/ADR-*.md` (rationale for key choices).
- **Contribution Guide** – `project‑context/CONTRIBUTING.md` (how to add docs, scripts, code).

All documentation follows the conventions described in `project‑context/CONTRIBUTING.md`.

---

## 🤝 Contributing

We welcome contributions! Please read the **Contribution Guide** for:
- Adding or updating documentation.
- Introducing new services or infrastructure components.
- Keeping the GitOps workflow clean (commit → push → let Flux apply).

When you add scripts, place them under `scripts/keep/` and update `scripts/keep/INDEX.md`.

---

## 📜 License

This project is licensed under the **Apache License 2.0**. See the `LICENSE` file for details.

---

*Last updated: 2025‑12‑04*
