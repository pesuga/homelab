### Design Considerations

- Approach: Replace the admin frontend with a Tailwind Admin Next.js template; keep backend integration points intact.
- Architecture: Next.js App Router with a global AuthContext; Tailwind CSS for styling; data fetches align with existing backend APIs under production/family-assistant/family-assistant/api.
- Data Flow: User logs in via backend auth, token stored in client context; dashboard components fetch health/metrics from backend endpoints.
- Security: Reuse existing auth scheme; ensure protected routes render login when unauthenticated.
