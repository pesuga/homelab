# Authentik Integration Guide

**Status:** ACTIVE
**Last Updated:** 2025-11-19

## Overview

All external access to services should be protected by Authentik. This provides Single Sign-On (SSO) and centralized user management.

## Integration Methods

### 1. Proxy Provider (The Standard)

For services that don't support OIDC natively (or where we want to enforce auth at the ingress level), we use the **Proxy Provider**.

**How it works:**
Traefik forwards requests to Authentik -> Authentik checks session -> Authentik forwards to Service.

**Steps:**
1.  **Create Provider in Authentik:**
    *   Type: Proxy Provider
    *   Name: `Provider for <Service>`
    *   Authentication Flow: `default-authentication-flow`
    *   Authorization Flow: `default-provider-authorization-implicit-consent`
    *   Forward Auth (Single Application): Selected
    *   External Host: `https://<service>.pesulabs.net`

2.  **Create Application in Authentik:**
    *   Name: `<Service>`
    *   Slug: `<service>`
    *   Provider: Select the provider created above.

3.  **Configure Ingress (Kubernetes):**
    Add the `authentik` middleware to your IngressRoute.

    ```yaml
    apiVersion: traefik.containo.us/v1alpha1
    kind: IngressRoute
    metadata:
      name: my-service
      namespace: homelab
    spec:
      routes:
        - match: Host(`my-service.pesulabs.net`)
          kind: Rule
          services:
            - name: my-service
              port: 80
          middlewares:
            - name: authentik  # <--- THIS IS KEY
            - namespace: authentik
    ```

### 2. OIDC Provider (Native Auth)

For services that support OIDC (e.g., Grafana, Portainer), use the **OIDC Provider**.

**Steps:**
1.  **Create Provider in Authentik:**
    *   Type: OAuth2/OpenID Provider
    *   Redirect URIs: `https://<service>.pesulabs.net/login/generic_oauth` (check service docs)
    *   Client ID: (Copy this)
    *   Client Secret: (Copy this)

2.  **Configure Service:**
    *   Update the service configuration (env vars or config file) with the Client ID, Secret, and Authentik URLs.

## Middleware Definition

The `authentik` middleware is defined in the `authentik` namespace. It points to the Authentik Outpost.

```yaml
# Already deployed in cluster
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: authentik
  namespace: authentik
spec:
  forwardAuth:
    address: http://authentik-server.authentik.svc.cluster.local:9000/outpost.goauthentik.io/auth/traefik
    trustForwardHeader: true
    authResponseHeaders:
      - X-authentik-username
      - X-authentik-groups
      - X-authentik-email
      - X-authentik-name
      - X-authentik-uid
      - X-authentik-jwt
      - X-authentik-meta-jwks
      - X-authentik-meta-outpost
      - X-authentik-meta-provider
      - X-authentik-meta-app
      - X-authentik-meta-version

## Service Integration Checklist

| Service | Integration Method | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Portainer** | OIDC Provider | [ ] Pending | Native OIDC support. |
| **N8n** | Proxy Provider | [ ] Pending | Use `X-authentik-username` header. |
| **Family Admin** | Proxy Provider | [ ] Pending | See `FRONTEND_ARCHITECTURE_REVIEW_GEMINI.md`. |
| **Family API** | Proxy Provider | [ ] Pending | Protects Swagger/OpenAPI docs. |
| **Chat UI** | Proxy Provider | [ ] Pending | Protects the chat interface. |

```
