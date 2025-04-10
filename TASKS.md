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
-   [x] **Nginx Ingress:**
    -   [x] Create Kustomize base for Nginx Ingress manifests in `infrastructure/nginx-ingress/`.
    -   [x] Reference Nginx base in `clusters/homelab/infrastructure.yaml`.
    -   [x] Verify Nginx Ingress controller deployment and service.
    -   [x] Configure Nginx Ingress with LoadBalancer service type to work with MetalLB.
-   [x] **~~Tailscale~~ MetalLB:** _(Tailscale replaced with MetalLB for local network access)_
    -   [x] Create namespace for MetalLB in `infrastructure/metallb/namespace.yaml`.
    -   [x] Install MetalLB using HelmRelease in `infrastructure/metallb/installation.yaml`.
    -   [x] Configure IP address pool in `infrastructure/metallb/config.yaml`.
    -   [x] Verify MetalLB deployment and IP address assignment.
-   [x] **Monitoring Stack (Grafana, Prometheus, Loki):**
    -   [x] Create Kustomize base for Prometheus manifests in `infrastructure/monitoring/prometheus/`.
    -   [x] Create Kustomize base for Loki manifests in `infrastructure/monitoring/loki/`.
    -   [x] Create Kustomize base for Grafana manifests in `infrastructure/monitoring/grafana/`.
    -   [x] Configure data sources in Grafana (Prometheus, Loki).
    -   [x] Reference monitoring bases in `clusters/homelab/infrastructure.yaml`.
    -   [x] Verify monitoring components deployment and basic functionality.
    -   [x] Create ingress resources for monitoring stack in `infrastructure/ingress/monitoring-stack.yaml`.
-   [x] **TLS Certificates:**
    -   [x] Create self-signed wildcard certificate for `*.homelab.local` using script in `infrastructure/certificates/`.
    -   [x] Store TLS certificate in `homelab-tls` secret in `cert-storage` namespace.
    -   [x] Configure ingress resources to use TLS certificate.
    -   [x] Verify HTTPS access to services via ingress.
-   [ ] **(Future) Cert-Manager:**
    -   [ ] Create Kustomize base for Cert-Manager manifests in `infrastructure/cert-manager/`.
    -   [ ] Configure ClusterIssuer(s) (e.g., Let's Encrypt).
    -   [ ] Reference Cert-Manager base in `clusters/homelab/infrastructure.yaml`.
    -   [ ] Verify Cert-Manager deployment.

## Phase 3: Application Deployment (Kustomize/Manifests Only)

-   [ ] Define `GitRepository` source in `apps/sources/` (if different from infrastructure).
-   [x] **Databases (PostgreSQL, Qdrant):**
    -   [x] Create Kustomize base for PostgreSQL manifests in `apps/databases/postgresql/` (including PVC).
    -   [x] Create Kustomize base for Qdrant manifests in `apps/databases/qdrant/` (including PVC).
    -   [x] Reference database bases in `clusters/homelab/apps.yaml`.
    -   [x] Verify database deployments and persistent volumes.
    -   [x] Create ingress resources for database stack in `infrastructure/ingress/database-stack.yaml`.
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

## Phase 5: Local Network Access

-   [x] Setup local domain access:
    -   [x] Configure MetalLB for IP allocation.
    -   [x] Configure NGINX Ingress controller with LoadBalancer service type.
    -   [x] Create ingress resources for all services with TLS support.
    -   [x] Generate and apply self-signed certificates for HTTPS access.
    -   [x] Document required `/etc/hosts` entries in `infrastructure/hosts-entry.txt`.

## Phase 6: Ongoing Maintenance & Refinement

-   [ ] Regularly review Flux reconciliation status.
-   [ ] Update component manifests as new versions are released.
-   [ ] Refine Kustomize overlays for environment-specific configurations if needed.
-   [x] Add documentation to `infrastructure/README.md`.