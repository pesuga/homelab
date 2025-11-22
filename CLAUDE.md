<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

<!-- PROJECT-CONTEXT:START -->

When starting a clean session always read `@project-context/README.md` to learn about the project.

After the work has been done we need to very carefully validate the work done and update the project context files.

<!-- PROJECT-CONTEXT:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rules
- Always use Tailscale IPs for inter-node communication
- Before claiming "all services working" run `/verify-claim claim:"all services working perfectly"`
- Before session completion run `/validate-session` to verify completion claims
- Before deploying new services run `/homelab-health section:infrastructure`
- When troubleshooting use `/homelab-health` for comprehensive status
- When running commands in the compute node, verify where you are, most likely you are already there.
- For any kubectl command you need to run, there is no need to ssh.
- After working on any of the apps (dashboard, family assistant or any other) remember to commit and push.

#### Validation Integration Rules
1. Never claim service completion without verification
2. Always use `/verify-claim` before stating services are working
3. Run `/validate-session` at the end of each development session
4. Document actual validation results, not assumptions
5. Use `/homelab-context` for architecture reference when needed

#### Available Validation Commands
- `/validate-session` - Comprehensive session validation against SESSION-STATE.md
- `/verify-claim` - Real-time verification of service status claims
- `/homelab-health` - Complete system health dashboard
- `/homelab-context` - Architecture and system knowledge reference

### Documentation Structure

This project follows a structured documentation approach for Claude Code sessions:

#### Core Documentation Sections
- **`session-state`**: Track what happened during each session (commands, files, outcomes, decisions)
- **`sprint-updates`**: Progress on current sprint objectives and里程碑 (milestones)
- **`architecture-changes`**: Design decisions, new patterns, structural modifications
- **`services-inventory`**: New/modified/deleted services and their current status
- **`knowledge-capture`**: Reusable patterns, code snippets, lessons learned, best practices
- **`blocking-issues`**: Current impediments, blockers, and their resolution status
- **`next-steps`**: Immediate action items and priorities for the next session

#### Documentation Locations
- **Primary**: `project-context/SESSION-STATE.md` - Main session tracking
- **Archive**: `project-context/archive/` - Historical session documentation (date-stamped)
- **Temporary**: Session-specific docs in project root (to be cleaned up by end-of-session hook)

#### "Where We Left Off" Section
Located at the end of this file, this section provides context continuity between sessions:
- Current working directory and branch
- Active tasks and their completion status
- Tools and services being used
- Continuation instructions for next session



## 📍 Where We Left Off

**Last Session**: 2025-11-15 - End-of-session documentation and cleanup
**Working Directory**: /home/pesu/Rakuflow/systems/homelab
**Current Branch**: main

### Active Tasks
- **Completed**: End-of-session hook execution with documentation updates
- **Files Processed**: Session documentation archived, temporary files cleaned up
- **Next**: Review updated documentation and continue with next development tasks

### Tools & Services Being Used
- Claude Code with end-of-session hook automation
- Project documentation and session management system
- Git workflow with 89 uncommitted files

### Session Summary
- **Documentation**: Session state archived to claudedocs/archive/
- **Cleanup**: Temporary files and one-time scripts removed
- **Continuity**: "Where We Left Off" section updated for next session

### Continuation Instructions
1. Check git status and commit any important changes
2. Review docs/SESSION-STATE.md for detailed session history
3. Continue with next development tasks based on current sprint objectives
4. Verify service health if working on infrastructure

### Quick Status Check
- [x] Session documentation processed and archived
- [x] Temporary files cleaned up
- [x] "Where We Left Off" section updated
