### Change Proposal: Replace Admin Frontend with Tailwind Admin Template (Next.js)  (revisited)

## Why
To accelerate UI iteration by leveraging a proven Tailwind admin template with Next.js, reduce initial frontend wiring, and align with current frontend tech choices.

## What Changes
- Replace the current admin frontend with a Next.js Tailwind-based template.
- Remove/disable the old admin frontend under production/family-assistant/family-assistant/frontend.
- Wire the new admin UI to existing backend endpoints for auth and dashboard data.

- Change ID: replace-admin-frontend-tailwind-nextjs
- Scope: Frontend only; backend APIs remain in production/family-assistant/family-assistant/
- Rationale: Accelerate UI by leveraging a battle-tested Tailwind admin template and Next.js template; improve consistency and iteration speed.
- Success criteria: (1) New Next.js Tailwind admin scaffold renders locally; (2) Authentication flows integrate with existing backend; (3) Admin routes (dashboard, settings) render and fetch data from backend endpoints.
- Risks: Template differences may require adapting types and API contracts; plan to migrate in small deltas.
