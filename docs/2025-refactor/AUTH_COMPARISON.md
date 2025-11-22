# Authentication Solution Comparison: Authelia vs Authentik

**Date:** 2025-11-19
**Context:** Homelab environment with K3s, Traefik Ingress, and a need for centralized SSO.

## Overview

Both **Authelia** and **Authentik** are excellent open-source authentication providers. They both support:
- Single Sign-On (SSO)
- Multi-Factor Authentication (MFA/2FA)
- Integration with Traefik (Forward Auth)
- LDAP/OIDC Provider capabilities

---

## 1. Authelia

**"The Lightweight Shield"**

Authelia is a focused, lightweight authentication server. It doesn't try to be a full Identity Provider (IdP) with a complex management UI; it focuses on protecting routes.

### ✅ Pros
- **Lightweight:** Uses significantly fewer resources (RAM/CPU) than Authentik.
- **Simple Configuration:** Configured via a single YAML file. "Infrastructure as Code" friendly by default.
- **Traefik Native:** Extremely common pairing with Traefik. Thousands of tutorials and examples exist.
- **Stateless(ish):** Can run with just a Redis/Postgres backend, very easy to redeploy.
- **Security First:** Very strict security defaults.

### ❌ Cons
- **No Admin UI:** User management is often done via a separate file or an external LDAP. No "Click to add user" interface out of the box (though recent versions are improving this).
- **Limited Features:** It does Auth well, but doesn't have the vast feature set of Authentik (flows, stages, policies).

### 🎯 Best For...
- Users who prefer **YAML configuration** over UI clicking.
- Environments with limited resources.
- When you just want to "protect these URLs" without complex logic.

---

## 2. Authentik

**"The Enterprise Identity Platform"**

Authentik is a full-featured Identity Provider, comparable to Keycloak or Okta. It is powerful, flexible, and complex.

### ✅ Pros
- **Powerful Admin UI:** Full web interface for managing users, groups, applications, and providers.
- **Flows & Stages:** Extremely customizable authentication flows (e.g., "If user is in group X, skip 2FA, otherwise require Yubikey").
- **Application Dashboard:** Provides a user-facing "Launchpad" of all their apps (great for family members).
- **Versatile:** Can act as an LDAP server, OIDC provider, SAML provider, and Proxy provider all in one.

### ❌ Cons
- **Heavy:** Requires more resources (Python/Django based). Can be slow to start.
- **Complexity:** The "Flows" concept has a steep learning curve. Setting up a simple proxy can take 10+ clicks.
- **Overkill:** Might be too much engine for a simple family homelab.

### 🎯 Best For...
- Users who want a **Web UI** for management.
- When you need complex auth logic or specific user flows.
- If you want a built-in "App Dashboard" for the family.

---

## 3. Recommendation for Family AI Platform

**Winner: Authentik**

**Why?**
1.  **Family Management:** The **Admin UI** is crucial. You don't want to edit a YAML file and restart a service just to reset your partner's password or add a child's account.
2.  **App Dashboard:** The built-in dashboard is a huge "Quality of Life" win for family members. They log in once and see icons for "Photos", "Chat", "Files", etc.
3.  **Future Proofing:** As you add more services (Nextcloud, etc.), Authentik's OIDC support makes integration easier than Authelia's stricter setup.

**Caveat:** It will use ~500MB-1GB more RAM than Authelia, but on your hardware, this is acceptable for the usability gains.
