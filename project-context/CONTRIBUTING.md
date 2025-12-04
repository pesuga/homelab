# Contributing to Project Documentation

## Purpose
This document defines how to keep the documentation in **project-context** up‑to‑date and how to use the auxiliary folders (`/docs`, `scripts/keep`, `/tmp`).

## Updating `project-context`
- **When to edit**: Any change to architecture, network topology, services, or important decisions.
- **What to edit**: Update the relevant section in the existing `README.md` and the specific files (`ARCHITECTURE.md`, `SERVICES.md`, `KNOWLEDGE.md`, `SESSION-STATE.md`).
- **Preserve existing content**: Do not delete existing information; append new details and keep a changelog entry at the bottom of each file.
- **Review**: Open a PR and request a review from the documentation owner before merging.

## Using `/docs`
- Create docs here for **temporary** work‑in‑progress material (e.g., design drafts, investigation notes).
- Add a header `# Temporary Documentation` and a comment `<!-- TODO: migrate or delete -->`.
- Once the feature/fix is complete, either move the content to `project-context` or delete the file.

## Scripts
- Keep useful scripts in `scripts/keep/`.
- Add an entry to `scripts/keep/INDEX.md` describing each script’s purpose.

## `/tmp` SOP
- Store session‑specific artifacts (logs, intermediate outputs) in `/tmp`.
- After the session, run `/validate-session` and then move any valuable artifacts to a permanent location.

## Changelog
- Add a short entry at the end of this file for every documentation‑related change, following the format:
  - `YYYY‑MM‑DD: Brief description of change (author)`

---

*Last updated: 2025‑12‑04*
