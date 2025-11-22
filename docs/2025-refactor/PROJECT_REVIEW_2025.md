# Project Deep Dive & Review: Family AI Platform (Revised)

**Date:** 2025-11-19
**Reviewer:** Antigravity Agent
**Status:** Updated with User Corrections

## 1. Executive Summary

This project is an ambitious attempt to build a private, family-centric AI platform. The vision is to provide a "Family OS" that is private, trustworthy, and capable of handling family data (photos, schedules, memories) locally.

**Core Philosophy:**
- **Privacy First:** Local processing is non-negotiable.
- **Spanish Native:** Spanish language support is a hard requirement.
- **Business Model:** Future revenue via Cloud Backups and Support services.

**Current Status:**
- **Transitioning Stack:** Moving away from "hobbyist" tools (Flowise, WebUI) to a more robust, custom stack.
- **Infrastructure:** K3s cluster split between a **Compute Node** (GPU/Inference) and a **Service Node** (Apps).
- **Pain Points:** Networking stability is the primary blocker. "Agent Churn" has caused configuration drift.

---

## 2. Stack Analysis (Corrected)

### AI Engine
- **Inference:** **llama.cpp** (Replaced Ollama).
    - *Reason:* Likely for better control, performance, or specific model support on the AMD GPU.
- **Speech:** **Whisper** (Batch processing).
    - *Use Case:* Processing audio files (STT) for indexing/memory, NOT real-time conversation.
    - *Requirement:* High accuracy in Spanish.
- **Memory/Vector:** **Qdrant** + **Mem0**.
    - *Status:* Core to the "Family Context" value proposition.

### Application Layer
- **Orchestration:** **N8n**.
    - *Role:* The "glue" for all logic and workflows.
- **Frontend:** Custom Family App (React/Next.js?).
    - *Issue:* Confusion between "Admin Frontend" and "User UI".
- **Database:** PostgreSQL + Redis.

### Deprecated / Dismissed Tools
The following are **OUT** and should be removed/archived:
- ❌ **Flowise** (Replaced by N8n/Code)
- ❌ **Open WebUI** (Not needed, building custom UI)
- ❌ **LobeChat** (Dismissed)
- ❌ **Grafana** (Too complex/overkill? Replaced by simpler dashboard?)

---

## 3. Critical Issues & Solutions

### 3.1 Networking "The Knot"
**Problem:** Every new feature or agent changes the networking setup, breaking previous configurations. No consistent standard for Internal vs External traffic.
**Root Cause:** Lack of a "Golden Rule" for networking.
**Solution:** Create `docs/NETWORKING_STANDARD.md`.
- **Rule 1:** Internal services MUST talk via K3s DNS (`svc.cluster.local`).
- **Rule 2:** Ingress is ONLY for user-facing traffic (browser/mobile).
- **Rule 3:** TLS is terminated at the Ingress (Traefik), internal traffic is HTTP.

### 3.2 Repository Confusion
**Problem:** Agents confuse Admin UIs with User UIs.
**Solution:** Rename directories to be explicit.
- `apps/family-portal` (The User UI)
- `apps/system-admin` (The Admin UI)
- `services/` (Backend APIs)

### 3.3 Authentication
**Problem:** Need centralized auth for the platform.
**Requirement:** Compare Authelia vs Authentik.
- *Goal:* Single Sign-On (SSO) for all services.

---

## 4. Strategic Roadmap

1.  **Stabilize Networking:** Define and enforce the Networking Standard. Fix the "broken" state.
2.  **Clean Up:** Remove deprecated tools (Flowise, Grafana, etc.) from the repo to stop confusing agents.
3.  **Implement Auth:** Select and deploy Authelia or Authentik.
4.  **Build Core UI:** Focus on the custom Family App frontend without the distraction of other UI tools.
