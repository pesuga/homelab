# Repository Restructuring Proposal

**Goal:** Eliminate confusion between "Admin Frontends" (system management) and "User Frontends" (family interface), and clean up the nested `family-assistant` mess.

## Current State (The "Mess")

The `production/family-assistant/family-assistant` directory is currently a mix of everything:
- **User UI:** `family-app/`
- **Admin UI:** `admin-nextjs/`
- **Backend:** `api/`, `agents/`, `config/`, `services/`
- **Root Clutter:** `Dockerfile`, `requirements.txt`, `start.sh`, `Makefile`

## Proposed Structure

```
homelab/
├── apps/                      # 📱 User-Facing Applications (The "Product")
│   ├── family-portal/         # [MIGRATED] from family-assistant/family-app
│   └── mobile-app/            # Future React Native app
│
├── services/                  # ⚙️ Backend Services (The "Engine")
│   ├── family-api/            # [MIGRATED] from family-assistant (root + api/)
│   │   ├── src/               # Python source code
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── memory-engine/         # Mem0 / Vector DB Logic
│   └── workflow-engine/       # N8n configurations
│
├── infrastructure/            # 🏗️ Platform Infrastructure
│   ├── k8s/                   # Kubernetes Manifests
│   │   ├── apps/              # Manifests for apps/
│   │   ├── services/          # Manifests for services/
│   │   └── base/
│   └── admin-tools/           # 🛠️ Admin UIs (Not for Family)
│       ├── family-admin/      # [MIGRATED] from family-assistant/admin-nextjs
│       ├── monitoring/        # Grafana, Prometheus
│       └── auth/              # Authentik/Authelia
│
└── docs/                      # 📚 Documentation
```

## 📋 Migration Map

| Current Path | New Path | Notes |
| :--- | :--- | :--- |
| `production/family-assistant/family-assistant/family-app` | `apps/family-portal` | The main interface for the family. |
| `production/family-assistant/family-assistant/admin-nextjs` | `infrastructure/admin-tools/family-admin` | For YOU (Admin) to manage the system. |
| `production/family-assistant/family-assistant/api` | `services/family-api/src` | The core backend logic. |
| `production/family-assistant/family-assistant/*.py` | `services/family-api/src` | Move root python files to src. |
| `production/family-assistant/family-assistant/requirements.txt` | `services/family-api/requirements.txt` | Backend dependencies. |
| `production/family-assistant/family-assistant/Dockerfile` | `services/family-api/Dockerfile` | Backend container definition. |
| `production/family-assistant/*.yaml` | `infrastructure/k8s/services/family-api/` | Deployment manifests. |

## Execution Plan

1.  **Create Directories:** Set up the new `apps/`, `services/`, and `infrastructure/admin-tools/` skeleton.
2.  **Move & Rename:** Execute the moves defined in the Migration Map.
3.  **Fix Imports:** Update Dockerfiles and CI/CD scripts to point to new paths.
4.  **Clean Up:** Remove the empty `production/family-assistant` directory.
