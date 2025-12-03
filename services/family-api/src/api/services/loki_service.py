"""
Loki Service for querying chat session logs.

Provides methods to query Loki using LogQL for chat analytics including
token usage, latency statistics, cost estimates, and error rates.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LokiQueryResult(BaseModel):
    """Result from a Loki query."""
    status: str
    data: Dict[str, Any]


class ChatLogEntry(BaseModel):
    """Individual chat log entry."""
    timestamp: str
    user_id: str
    thread_id: str
    session_id: str
    tokens: int
    latency_ms: float
    cost_usd: float
    model_used: str
    error: bool = False


class ChatOverviewMetrics(BaseModel):
    """Overview metrics for chat analytics."""
    total_requests: int
    total_tokens: int
    estimated_cost_usd: float
    error_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    time_range: str


class TokenStats(BaseModel):
    """Token usage statistics by model."""
    by_model: Dict[str, int]
    total: int
    time_range: str


class LokiService:
    """Service for querying Loki logs."""

    def __init__(self, loki_url: str = "http://loki.homelab.svc.cluster.local:3100"):
        self.loki_url = loki_url
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"LokiService initialized with URL: {self.loki_url}")

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def _get_time_range(self, time_range: str = "24h") -> tuple[int, int]:
        """Convert time range string to nanosecond timestamps.

        Args:
            time_range: Time range string (e.g., "24h", "7d", "30d")

        Returns:
            Tuple of (start_ns, end_ns) in nanoseconds
        """
        end = datetime.now(timezone.utc)

        # Parse time range
        if time_range.endswith("h"):
            hours = int(time_range[:-1])
            start = end - timedelta(hours=hours)
        elif time_range.endswith("d"):
            days = int(time_range[:-1])
            start = end - timedelta(days=days)
        else:
            # Default to 24h
            start = end - timedelta(hours=24)

        # Convert to nanoseconds
        start_ns = int(start.timestamp() * 1_000_000_000)
        end_ns = int(end.timestamp() * 1_000_000_000)

        return start_ns, end_ns

    async def query_range(
        self,
        query: str,
        start: int,
        end: int,
        step: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a LogQL range query.

        Args:
            query: LogQL query string
            start: Start time in nanoseconds
            end: End time in nanoseconds
            step: Query resolution step (optional)

        Returns:
            Query result data
        """
        try:
            params = {
                "query": query,
                "start": start,
                "end": end
            }
            if step:
                params["step"] = step

            response = await self.client.get(
                f"{self.loki_url}/loki/api/v1/query_range",
                params=params
            )
            response.raise_for_status()

            result = response.json()
            return result.get("data", {})

        except Exception as e:
            logger.error(f"Loki query_range failed: {e}", exc_info=True)
            raise

    async def get_chat_logs(
        self,
        limit: int = 100,
        time_range: str = "24h"
    ) -> List[ChatLogEntry]:
        """Fetch raw chat session logs.

        Args:
            limit: Maximum number of logs to return
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            List of chat log entries
        """
        try:
            start_ns, end_ns = self._get_time_range(time_range)

            query = f'''{{app="family-api"}} | json | type="chat_session_log" | limit {limit}'''

            response = await self.client.get(
                f"{self.loki_url}/loki/api/v1/query_range",
                params={
                    "query": query,
                    "start": start_ns,
                    "end": end_ns
                }
            )
            response.raise_for_status()

            result = response.json()

            # Parse log entries
            logs = []
            for stream in result.get("data", {}).get("result", []):
                for value in stream.get("values", []):
                    # value[0] is timestamp (ns), value[1] is log line
                    try:
                        import json
                        log_data = json.loads(value[1])

                        logs.append(ChatLogEntry(
                            timestamp=log_data.get("timestamp", ""),
                            user_id=log_data.get("user_id", ""),
                            thread_id=log_data.get("thread_id", ""),
                            session_id=log_data.get("session_id", ""),
                            tokens=log_data.get("token_economics", {}).get("total_tokens", 0),
                            latency_ms=log_data.get("performance", {}).get("total_latency_ms", 0.0),
                            cost_usd=log_data.get("token_economics", {}).get("estimated_cost_usd", 0.0),
                            model_used=log_data.get("token_economics", {}).get("model_used", "unknown"),
                            error=log_data.get("response", {}).get("error", False)
                        ))
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse log entry: {e}")
                        continue

            return logs[:limit]

        except Exception as e:
            logger.error(f"Failed to get chat logs: {e}", exc_info=True)
            return []

    async def get_token_stats(self, time_range: str = "24h") -> TokenStats:
        """Get token usage statistics by model.

        Args:
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            Token statistics by model
        """
        try:
            start_ns, end_ns = self._get_time_range(time_range)

            # Query for token usage by model
            query = f'''sum by (token_economics_model_used) (
                sum_over_time(
                    {{app="family-api"}}
                    | json
                    | type="chat_session_log"
                    | unwrap token_economics_total_tokens [{time_range}]
                )
            )'''

            data = await self.query_range(query, start_ns, end_ns)

            # Parse results
            by_model = {}
            total = 0

            for result in data.get("result", []):
                model = result.get("metric", {}).get("token_economics_model_used", "unknown")
                # Get the latest value
                values = result.get("values", [])
                if values:
                    token_count = int(float(values[-1][1]))
                    by_model[model] = token_count
                    total += token_count

            return TokenStats(
                by_model=by_model,
                total=total,
                time_range=time_range
            )

        except Exception as e:
            logger.error(f"Failed to get token stats: {e}", exc_info=True)
            return TokenStats(by_model={}, total=0, time_range=time_range)

    async def get_cost_estimate(self, time_range: str = "24h") -> float:
        """Calculate total estimated cost.

        Args:
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            Total estimated cost in USD
        """
        try:
            start_ns, end_ns = self._get_time_range(time_range)

            query = f'''sum(
                sum_over_time(
                    {{app="family-api"}}
                    | json
                    | type="chat_session_log"
                    | unwrap token_economics_estimated_cost_usd [{time_range}]
                )
            )'''

            data = await self.query_range(query, start_ns, end_ns)

            # Extract total cost
            for result in data.get("result", []):
                values = result.get("values", [])
                if values:
                    return float(values[-1][1])

            return 0.0

        except Exception as e:
            logger.error(f"Failed to get cost estimate: {e}", exc_info=True)
            return 0.0

    async def get_latency_stats(self, time_range: str = "24h") -> Dict[str, float]:
        """Get latency percentiles (P50, P95, P99).

        Args:
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            Dictionary with p50, p95, p99, and avg latency in ms
        """
        try:
            start_ns, end_ns = self._get_time_range(time_range)

            # Query for different percentiles
            percentiles = {}
            for p in [0.50, 0.95, 0.99]:
                query = f'''quantile_over_time({p},
                    {{app="family-api"}}
                    | json
                    | type="chat_session_log"
                    | unwrap performance_total_latency_ms [{time_range}]
                )'''

                data = await self.query_range(query, start_ns, end_ns)

                for result in data.get("result", []):
                    values = result.get("values", [])
                    if values:
                        key = f"p{int(p*100)}"
                        percentiles[key] = float(values[-1][1])

            # Also get average
            avg_query = f'''avg_over_time(
                {{app="family-api"}}
                | json
                | type="chat_session_log"
                | unwrap performance_total_latency_ms [{time_range}]
            )'''

            data = await self.query_range(avg_query, start_ns, end_ns)
            for result in data.get("result", []):
                values = result.get("values", [])
                if values:
                    percentiles["avg"] = float(values[-1][1])

            return percentiles

        except Exception as e:
            logger.error(f"Failed to get latency stats: {e}", exc_info=True)
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}

    async def get_request_count(self, time_range: str = "24h") -> int:
        """Count total chat requests.

        Args:
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            Total number of chat requests
        """
        try:
            start_ns, end_ns = self._get_time_range(time_range)

            query = f'''sum(
                count_over_time(
                    {{app="family-api"}}
                    | json
                    | type="chat_session_log" [{time_range}]
                )
            )'''

            data = await self.query_range(query, start_ns, end_ns)

            for result in data.get("result", []):
                values = result.get("values", [])
                if values:
                    return int(float(values[-1][1]))

            return 0

        except Exception as e:
            logger.error(f"Failed to get request count: {e}", exc_info=True)
            return 0

    async def get_error_rate(self, time_range: str = "24h") -> float:
        """Calculate error rate.

        Args:
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            Error rate as a decimal (0.0 to 1.0)
        """
        try:
            start_ns, end_ns = self._get_time_range(time_range)

            # Total errors
            error_query = f'''sum(
                count_over_time(
                    {{app="family-api"}}
                    | json
                    | type="chat_session_log"
                    | response_error="true" [{time_range}]
                )
            )'''

            error_data = await self.query_range(error_query, start_ns, end_ns)
            error_count = 0
            for result in error_data.get("result", []):
                values = result.get("values", [])
                if values:
                    error_count = int(float(values[-1][1]))

            # Total requests
            total_count = await self.get_request_count(time_range)

            if total_count > 0:
                return error_count / total_count

            return 0.0

        except Exception as e:
            logger.error(f"Failed to get error rate: {e}", exc_info=True)
            return 0.0

    async def get_chat_overview(self, time_range: str = "24h") -> ChatOverviewMetrics:
        """Get comprehensive chat analytics overview.

        Args:
            time_range: Time range string (e.g., "24h", "7d")

        Returns:
            Overview metrics including requests, tokens, cost, latency, error rate
        """
        try:
            # Run all queries in parallel
            total_requests = await self.get_request_count(time_range)
            token_stats = await self.get_token_stats(time_range)
            cost = await self.get_cost_estimate(time_range)
            latency_stats = await self.get_latency_stats(time_range)
            error_rate = await self.get_error_rate(time_range)

            return ChatOverviewMetrics(
                total_requests=total_requests,
                total_tokens=token_stats.total,
                estimated_cost_usd=cost,
                error_rate=error_rate,
                avg_latency_ms=latency_stats.get("avg", 0.0),
                p95_latency_ms=latency_stats.get("p95", 0.0),
                time_range=time_range
            )

        except Exception as e:
            logger.error(f"Failed to get chat overview: {e}", exc_info=True)
            # Return empty metrics on error
            return ChatOverviewMetrics(
                total_requests=0,
                total_tokens=0,
                estimated_cost_usd=0.0,
                error_rate=0.0,
                avg_latency_ms=0.0,
                p95_latency_ms=0.0,
                time_range=time_range
            )


# Global instance
loki_service = LokiService()


async def get_loki_service() -> LokiService:
    """Get the global Loki service instance."""
    return loki_service
