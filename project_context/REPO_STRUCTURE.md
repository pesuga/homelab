# Repository Structure

**Status:** ACTIVE
**Last Updated:** 2025-11-19

## Overview

The repository is organized to clearly separate user-facing applications, backend services, and infrastructure configuration.

```
homelab/
├── apps/                      # 📱 User-Facing Applications (The "Product")
│   ├── family-portal/         # The main interface for the family (Next.js)
│   └── mobile-app/            # (Future) React Native app
│
├── services/                  # ⚙️ Backend Services (The "Engine")
│   ├── family-api/            # Core backend logic (Python/FastAPI)
│   │   ├── src/               # Source code
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── memory-engine/         # Mem0 / Vector DB Logic
│   └── workflow-engine/       # N8n configurations
│
├── infrastructure/            # 🏗️ Platform Infrastructure
│   ├── kubernetes/            # Kubernetes Manifests
│   │   ├── apps/              # Manifests for apps/
│   │   ├── services/          # Manifests for services/
│   │   ├── auth/              # Authentik
│   │   ├── monitoring/        # Prometheus, Grafana (Custom)
│   │   └── base/
│   └── admin-tools/           # 🛠️ Admin UIs (Not for Family)
│       ├── family-admin/      # Admin interface for system management
│
├── project_context/           # 🧠 Source of Truth for Agents & Developers
│   ├── ARCHITECTURE.md
│   ├── NETWORKING_STANDARD.md
│   ├── SERVICE_INVENTORY.md
│   └── ...
│
└── docs/                      # 📚 Historical Documentation & Archives
```

## Key Locations

| Component | Path | Description |
| :--- | :--- | :--- |
| **Family Portal** | `apps/family-portal` | The frontend UI for family members. |
| **Family API** | `services/family-api` | The backend API service. |
| **Admin UI** | `infrastructure/admin-tools/family-admin` | The admin dashboard. |
| **K8s Manifests** | `infrastructure/kubernetes` | Deployment configurations. |
| **Context** | `project_context` | **READ THIS FIRST.** |

## Migration Notes (Nov 2025)

The old `production/family-assistant` directory has been deprecated and split into the structure above.
- `family-app` -> `apps/family-portal`
- `admin-nextjs` -> `infrastructure/admin-tools/family-admin`
- `api` -> `services/family-api`
