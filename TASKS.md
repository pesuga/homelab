# Homelab GitOps Project Tasks

This file tracks the setup and configuration tasks for the homelab cluster using FluxCD and Kustomize.

## Phase 1: Initial Setup & Flux Bootstrap

-   [ ] Create base directory structure (`clusters/homelab`, `infrastructure`, `apps`, `scripts`, `docs`).
-   [ ] Define Flux Kustomization entrypoints in `clusters/homelab/` (`infrastructure.yaml`, `apps.yaml`).
-   [ ] Prepare Flux bootstrap manifests (or script) in `clusters/homelab/flux-system/`.
-   [ ] Bootstrap FluxCD onto the k3s cluster, pointing it to `clusters/homelab/`.
-   [ ] Verify Flux components are running (`flux get all -n flux-system`).
-   [ ] Verify Flux is reconciling the `clusters/homelab/` path.

## Phase 2: Infrastructure Deployment (Kustomize/Manifests Only)

-   [ ] Define `GitRepository` source in `infrastructure/sources/` for this repository.
-   [ ] **Nginx Ingress:**
    -   [ ] Create Kustomize base for Nginx Ingress manifests in `infrastructure/nginx-ingress/`.
    -   [ ] Reference Nginx base in `clusters/homelab/infrastructure.yaml`.
    -   [ ] Verify Nginx Ingress controller deployment and service.
-   [ ] **Tailscale:**
    -   [ ] Create Kustomize base for Tailscale operator manifests in `infrastructure/tailscale/`.
    -   [ ] Reference Tailscale base in `clusters/homelab/infrastructure.yaml`.
    -   [ ] Verify Tailscale operator deployment.
-   [ ] **Monitoring Stack (Grafana, Prometheus, Loki):**
    -   [ ] Create Kustomize base for Prometheus manifests in `infrastructure/monitoring/prometheus/`.
    -   [ ] Create Kustomize base for Loki manifests in `infrastructure/monitoring/loki/`.
    -   [ ] Create Kustomize base for Grafana manifests in `infrastructure/monitoring/grafana/`.
    -   [ ] Configure data sources in Grafana (Prometheus, Loki).
    -   [ ] Reference monitoring bases in `clusters/homelab/infrastructure.yaml`.
    -   [ ] Verify monitoring components deployment and basic functionality.
-   [ ] **(Recommended) Cert-Manager:**
    -   [ ] Create Kustomize base for Cert-Manager manifests in `infrastructure/cert-manager/`.
    -   [ ] Configure ClusterIssuer(s) (e.g., Let's Encrypt).
    -   [ ] Reference Cert-Manager base in `clusters/homelab/infrastructure.yaml`.
    -   [ ] Verify Cert-Manager deployment.

## Phase 3: Application Deployment (Kustomize/Manifests Only)

-   [ ] Define `GitRepository` source in `apps/sources/` (if different from infrastructure).
-   [ ] **Databases (PostgreSQL, Qdrant):**
    -   [ ] Create Kustomize base for PostgreSQL manifests in `apps/databases/postgresql/` (including PVC).
    -   [ ] Create Kustomize base for Qdrant manifests in `apps/databases/qdrant/` (including PVC).
    -   [ ] Reference database bases in `clusters/homelab/apps.yaml`.
    -   [ ] Verify database deployments and persistent volumes.
-   [ ] **N8n:**
    -   [ ] Create Kustomize base for N8n manifests in `apps/n8n/` (including PVC, Ingress).
    -   [ ] Reference N8n base in `clusters/homelab/apps.yaml`.
    -   [ ] Verify N8n deployment and accessibility via Ingress.
-   [ ] **Leantime:**
    -   [ ] Create Kustomize base for Leantime manifests in `apps/leantime/` (including PVC, Ingress, DB connection).
    -   [ ] Reference Leantime base in `clusters/homelab/apps.yaml`.
    -   [ ] Verify Leantime deployment and accessibility via Ingress.

## Phase 4: Secrets Management

-   [ ] Integrate Sealed Secrets controller (if not already part of bootstrap).
-   [ ] Document process for encrypting secrets using `pub-sealed-secrets.pem`.
-   [ ] Encrypt initial required secrets (e.g., database passwords, API keys) and commit `SealedSecret` resources.

## Phase 5: Ongoing Maintenance & Refinement

-   [ ] Regularly review Flux reconciliation status.
-   [ ] Update component manifests as new versions are released.
-   [ ] Refine Kustomize overlays for environment-specific configurations if needed.
-   [ ] Add documentation to `docs/`.