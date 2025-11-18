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


**Build / Lint / Test**
- Build: `make build` (or `make install` to start services locally)
- Lint: `make lint` (also run `pip install -r core/requirements-dev.txt` first)
- Test: `make test`; for a single test, run `pytest <path> -k <test_name>` or `pytest <path>::<Class>::<method>`

**Code Style Guidelines**
- Imports: standard library, then third-party, then local; explicit imports; avoid `from x import *`
- Formatting: format with Black (88 line-length) and sort imports with isort; run `make format`
- Types: annotate with type hints; prefer explicit returns; use Pydantic models for APIs when applicable
- Naming: functions snake_case; classes CamelCase; constants ALL_CAPS
- Errors: avoid bare except; raise meaningful exceptions; API layers use HTTPException with status codes
- Testing: write unit tests for pure logic; use fixtures; keep tests fast and deterministic
- Documentation: include docstrings for modules/functions; reference behavior clearly

**Cursor / Copilot**
- Cursor rules: none detected in this workspace; Copilot rules: none present in this repo's Copilot guidance
