Family Admin Analytics Fix & Chat Log Integration Plan
Goal
Fix the broken "Family Admin" analytics page and integrate comprehensive chat log analysis (from 
chat-log-analyzer.sh
) into the dashboard.

Problem Analysis
Broken Analytics Page: The current "Sub-Agent Analytics" page in family-admin is failing because of a type mismatch between the Frontend (
AnalyticsOverview
 expecting 
metrics
 object) and the Backend (
OverviewResponse
 returning flat fields).
Missing Chat Logs: The current analytics only cover "Sub-Agents" (specialized tasks). General chat sessions are logged to /var/log/family-assistant/chat-sessions but not visible in the admin dashboard.
Script Logic: The chat-log-analyzer.sh script provides valuable insights (Token Economics, Latency, Cost) that need to be ported to the web UI.
User Review Required
IMPORTANT

Data Source Decision: We will implement a real-time log reader in the Python backend to serve chat analytics. This avoids duplicating data into the database but relies on file system access. Ensure the API container has read access to /var/log/family-assistant/chat-sessions.

Proposed Changes
1. Backend: Family API (services/family-api)
[MODIFY] src/api/services/chat_logger.py
Update: Modify log_chat_session to also log the structured JSON entry to stdout.
Format: Ensure the output is a single line JSON string per event, with a distinctive field (e.g., type="chat_session_log") to make LogQL filtering easy.
Rationale: This allows Promtail to scrape the logs and ship them to Loki without needing special volume mounts.
[NEW] src/api/services/loki_service.py
Create a service to interact with the Loki API.

Configuration: Read Loki URL from settings (default: http://loki.homelab.svc.cluster.local:3100).
Functionality:
query_range(query, start, end, step): Execute LogQL queries over a time range.
get_chat_logs(limit, start, end): Fetch raw chat logs using {app="family-api"} | json | type="chat_session_log".
get_aggregates(time_range): Execute aggregation queries for:
Token Usage: sum by (model) (sum_over_time({app="family-api"} | json | type="chat_session_log" | unwrap total_tokens [$RANGE]))
Request Count: sum(count_over_time({app="family-api"} | json | type="chat_session_log" [$RANGE]))
Latency: quantile_over_time(0.95, {app="family-api"} | json | type="chat_session_log" | unwrap performance_total_latency_ms [$RANGE])
[MODIFY] src/api/routes/analytics.py
Integrate: Inject LokiService.
Endpoints: Implement the chat analytics endpoints using data fetched from Loki.
GET /api/v1/analytics/chat/overview
GET /api/v1/analytics/chat/logs
2. Frontend: Family Admin (infrastructure/admin-tools/family-admin)
[MODIFY] src/types/analytics.ts
Update AnalyticsOverview to match the actual backend response structure.
Add new types for ChatLogAnalytics (matching the new backend endpoints).
[MODIFY] src/lib/api-client.ts
Add methods to fetch chat log analytics:
getChatLogOverview(timeRange: string)
getChatLogTokenEconomics(timeRange: string)
getChatLogPerformance(timeRange: string)
[MODIFY] src/hooks/useAnalytics.ts
Update to handle the corrected AnalyticsOverview type.
Add state and fetchers for the new chat log data.
[MODIFY] src/components/analytics/AnalyticsDashboard.tsx (or similar)
Fix: Update data accessors to match the corrected types.
Enhance: Add a new tab/section "Chat Logs".
Visualize:
Token Usage: Bar chart of tokens per model.
Cost: KPI card for estimated cost.
Latency: Line chart or distribution of response times.
Error Rate: Status indicator.
Verification Plan
Automated Tests
Backend: Unit tests for LogAnalyzerService using sample ndjson logs.
Frontend: Verify types build correctly.
Manual Verification
Fix Verification: Load the "Sub-Agent Analytics" page and verify it no longer errors and displays data.
Log Integration:
Generate some chat traffic (using the main chat interface).
Verify the "Chat Logs" section in Admin updates with new data.
Compare values with the output of chat-log-analyzer.sh to ensure accuracy.