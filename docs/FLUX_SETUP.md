# Flux Setup Guide

This document outlines the steps to set up Flux for GitOps on your K3s cluster.

## Prerequisites

- A running K3s cluster (see K3S_SETUP.md)
- Git repository for storing your Kubernetes manifests
- `kubectl` installed and configured on your workstation
- GitHub, GitLab, or other Git provider account

## 1. Install Flux CLI

Install the Flux CLI on your workstation:

```bash
# For macOS with Homebrew
brew install fluxcd/tap/flux

# For Linux
curl -s https://fluxcd.io/install.sh | sudo bash

# Verify the installation
flux --version
```

## 2. Export GitHub Personal Access Token

If using GitHub, create a personal access token with repo permissions and export it:

```bash
export GITHUB_TOKEN=<your-github-token>
export GITHUB_USER=<your-github-username>
```

## 3. Check Kubernetes Cluster Compatibility

```bash
flux check --pre
```

## 4. Bootstrap Flux onto your Cluster

```bash
# Replace with your repository details
flux bootstrap github \
  --owner=$GITHUB_USER \
  --repository=homelab \
  --branch=main \
  --path=./clusters/homelab \
  --personal
```

## 5. Verify Flux Installation

```bash
# Check that Flux components are running
k -n flux-system get pods

# Verify source controller is working
flux get sources git
```

## 6. Understanding Flux Components

- **GitRepository**: Defines where Flux should pull manifests from
- **Kustomization**: Defines which paths in the Git repository to deploy
- **HelmRepository/HelmRelease**: For Helm-based deployments (not used in our setup)
- **Receiver**: For triggering reconciliation via webhooks

## 7. Manual Reconciliation

```bash
# Trigger reconciliation manually if needed
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

## 8. Debugging Flux

```bash
# Check Flux logs
flux logs

# Check status of resources
flux get all -A
```
