#!/usr/bin/env python3
"""
Daily Summary Generator for Chat Session Logs

Automated daily statistics generation for chat sessions including:
- Token usage and cost tracking
- Performance analytics and trends
- User activity and engagement metrics
- Error tracking and system health
"""

import json
import os
import sys
import argparse
import gzip
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailySummaryGenerator:
    """Generates comprehensive daily summaries from chat session logs."""

    def __init__(self, log_dir: str = "/var/log/family-assistant/chat-sessions"):
        self.log_dir = Path(log_dir)
        self.model_costs = {
            "Kimi-VL-A3B": 0.20,
            "Mistral-7B": 0.15,
            "Mixtral-8x7B": 0.35,
            "Llama-3.1-8B": 0.18,
            "default": 0.20
        }

    def generate_daily_summary(self, date: datetime) -> Dict[str, Any]:
        """Generate comprehensive daily summary for a specific date."""
        date_str = date.strftime("%Y-%m-%d")
        date_dir = self.log_dir / date_str

        if not date_dir.exists():
            logger.warning(f"No log directory found for date: {date_str}")
            return self._empty_summary(date_str)

        # Load log entries
        entries = self._load_log_entries(date_dir)

        if not entries:
            logger.warning(f"No log entries found for date: {date_str}")
            return self._empty_summary(date_str)

        logger.info(f"Processing {len(entries)} entries for {date_str}")

        # Generate summary components
        summary = {
            "date": date_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_sessions": self._count_unique_sessions(entries),
            "total_messages": len(entries),
            "unique_users": self._count_unique_users(entries),
            "token_economics": self._generate_token_summary(entries),
            "performance": self._generate_performance_summary(entries),
            "user_activity": self._generate_user_activity_summary(entries),
            "model_usage": self._generate_model_usage_summary(entries),
            "error_analysis": self._generate_error_summary(entries),
            "hourly_breakdown": self._generate_hourly_breakdown(entries),
            "top_conversations": self._generate_top_conversations(entries),
            "system_health": self._generate_system_health_summary(entries),
            "trends": self._calculate_trends(entries, date)
        }

        return summary

    def _load_log_entries(self, date_dir: Path) -> List[Dict[str, Any]]:
        """Load and parse log entries from date directory."""
        entries = []

        # Try main log file
        log_file = date_dir / f"chat-sessions-{date_dir.name}.ndjson"
        if log_file.exists():
            entries.extend(self._parse_log_file(log_file))

        # Try compressed log file
        gz_file = log_file.with_suffix('.ndjson.gz')
        if gz_file.exists():
            entries.extend(self._parse_gzipped_log_file(gz_file))

        return entries

    def _parse_log_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse NDJSON log file."""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            entries.append(entry)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON line in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")

        return entries

    def _parse_gzipped_log_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse gzipped NDJSON log file."""
        entries = []
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            entries.append(entry)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON line in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading gzipped log file {file_path}: {e}")

        return entries

    def _empty_summary(self, date_str: str) -> Dict[str, Any]:
        """Return empty summary structure for days with no data."""
        return {
            "date": date_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_sessions": 0,
            "total_messages": 0,
            "unique_users": 0,
            "token_economics": {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "estimated_cost_usd": 0.0,
                "average_tokens_per_message": 0.0
            },
            "performance": {
                "average_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "error_rate": 0.0
            },
            "user_activity": {},
            "model_usage": {},
            "error_analysis": {
                "total_errors": 0,
                "error_types": {},
                "errors_by_hour": {}
            },
            "hourly_breakdown": {},
            "top_conversations": [],
            "system_health": {
                "status": "no_data",
                "issues": []
            },
            "trends": {}
        }

    def _count_unique_sessions(self, entries: List[Dict[str, Any]]) -> int:
        """Count unique session IDs."""
        session_ids = {entry.get("session_id") for entry in entries if entry.get("session_id")}
        return len(session_ids)

    def _count_unique_users(self, entries: List[Dict[str, Any]]) -> int:
        """Count unique user IDs."""
        user_ids = {entry.get("user_id") for entry in entries if entry.get("user_id")}
        return len(user_ids)

    def _generate_token_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate token economics summary."""
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        total_cost = 0.0

        for entry in entries:
            token_econ = entry.get("token_economics", {})
            total_tokens += token_econ.get("total_tokens", 0)
            prompt_tokens += token_econ.get("prompt_tokens", 0)
            completion_tokens += token_econ.get("completion_tokens", 0)
            total_cost += token_econ.get("estimated_cost_usd", 0.0)

        avg_tokens_per_message = total_tokens / len(entries) if entries else 0.0

        return {
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "average_tokens_per_message": round(avg_tokens_per_message, 2)
        }

    def _generate_performance_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance metrics summary."""
        latencies = []
        error_count = 0

        for entry in entries:
            perf = entry.get("performance", {})
            latency = perf.get("total_latency_ms", 0)
            if latency > 0:
                latencies.append(latency)

            if entry.get("response", {}).get("error"):
                error_count += 1

        if not latencies:
            return {
                "average_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "error_rate": 0.0
            }

        latencies.sort()
        n = len(latencies)
        error_rate = (error_count / len(entries)) * 100 if entries else 0.0

        return {
            "average_latency_ms": round(sum(latencies) / n, 2),
            "min_latency_ms": round(latencies[0], 2),
            "max_latency_ms": round(latencies[-1], 2),
            "p95_latency_ms": round(latencies[int(n * 0.95)], 2),
            "error_rate": round(error_rate, 2)
        }

    def _generate_user_activity_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate user activity summary."""
        user_stats = defaultdict(lambda: {
            "sessions": set(),
            "messages": 0,
            "tokens": 0,
            "cost": 0.0,
            "total_latency": 0.0
        })

        for entry in entries:
            user_id = entry.get("user_id", "unknown")
            token_econ = entry.get("token_economics", {})
            perf = entry.get("performance", {})

            user_stats[user_id]["sessions"].add(entry.get("session_id", ""))
            user_stats[user_id]["messages"] += 1
            user_stats[user_id]["tokens"] += token_econ.get("total_tokens", 0)
            user_stats[user_id]["cost"] += token_econ.get("estimated_cost_usd", 0.0)
            user_stats[user_id]["total_latency"] += perf.get("total_latency_ms", 0)

        # Convert to serializable format and calculate averages
        user_summary = {}
        for user_id, stats in user_stats.items():
            user_summary[user_id] = {
                "sessions": len(stats["sessions"]),
                "messages": stats["messages"],
                "tokens": stats["tokens"],
                "cost_usd": round(stats["cost"], 6),
                "average_latency_ms": round(stats["total_latency"] / stats["messages"], 2) if stats["messages"] > 0 else 0.0
            }

        return user_summary

    def _generate_model_usage_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate model usage statistics."""
        model_stats = defaultdict(lambda: {
            "requests": 0,
            "tokens": 0,
            "cost": 0.0,
            "avg_latency": 0.0,
            "total_latency": 0.0
        })

        for entry in entries:
            token_econ = entry.get("token_economics", {})
            perf = entry.get("performance", {})
            model = token_econ.get("model_used", "unknown")

            model_stats[model]["requests"] += 1
            model_stats[model]["tokens"] += token_econ.get("total_tokens", 0)
            model_stats[model]["cost"] += token_econ.get("estimated_cost_usd", 0.0)
            model_stats[model]["total_latency"] += perf.get("total_latency_ms", 0)

        # Calculate averages and convert to serializable format
        model_summary = {}
        for model, stats in model_stats.items():
            avg_latency = stats["total_latency"] / stats["requests"] if stats["requests"] > 0 else 0.0
            model_summary[model] = {
                "requests": stats["requests"],
                "tokens": stats["tokens"],
                "cost_usd": round(stats["cost"], 6),
                "average_latency_ms": round(avg_latency, 2)
            }

        return model_summary

    def _generate_error_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate error analysis summary."""
        error_types = defaultdict(int)
        errors_by_hour = defaultdict(int)
        total_errors = 0

        for entry in entries:
            response = entry.get("response", {})
            if response.get("error"):
                total_errors += 1
                error_type = response.get("error_type", "unknown")
                error_types[error_type] += 1

                # Extract hour from timestamp
                timestamp = entry.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    hour = dt.hour
                    errors_by_hour[hour] += 1
                except:
                    pass

        return {
            "total_errors": total_errors,
            "error_types": dict(error_types),
            "errors_by_hour": dict(errors_by_hour)
        }

    def _generate_hourly_breakdown(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate hourly activity breakdown."""
        hourly_stats = defaultdict(lambda: {
            "messages": 0,
            "tokens": 0,
            "errors": 0,
            "unique_users": set()
        })

        for entry in entries:
            timestamp = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                hour = dt.hour
            except:
                hour = 0

            hourly_stats[hour]["messages"] += 1
            hourly_stats[hour]["tokens"] += entry.get("token_economics", {}).get("total_tokens", 0)
            if entry.get("response", {}).get("error"):
                hourly_stats[hour]["errors"] += 1
            hourly_stats[hour]["unique_users"].add(entry.get("user_id", ""))

        # Convert to serializable format
        hourly_summary = {}
        for hour, stats in hourly_stats.items():
            hourly_summary[str(hour)] = {
                "messages": stats["messages"],
                "tokens": stats["tokens"],
                "errors": stats["errors"],
                "unique_users": len(stats["unique_users"])
            }

        return hourly_summary

    def _generate_top_conversations(self, entries: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Generate top conversations by various metrics."""
        # Group by thread_id
        thread_stats = defaultdict(lambda: {
            "messages": 0,
            "tokens": 0,
            "cost": 0.0,
            "duration": 0.0,
            "start_time": None,
            "end_time": None,
            "user_id": None
        })

        for entry in entries:
            thread_id = entry.get("thread_id", "")
            token_econ = entry.get("token_economics", {})
            timestamp = entry.get("timestamp", "")

            if thread_id:
                thread_stats[thread_id]["messages"] += 1
                thread_stats[thread_id]["tokens"] += token_econ.get("total_tokens", 0)
                thread_stats[thread_id]["cost"] += token_econ.get("estimated_cost_usd", 0.0)
                thread_stats[thread_id]["user_id"] = entry.get("user_id", "")

                # Track time span
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if thread_stats[thread_id]["start_time"] is None or dt < thread_stats[thread_id]["start_time"]:
                        thread_stats[thread_id]["start_time"] = dt
                    if thread_stats[thread_id]["end_time"] is None or dt > thread_stats[thread_id]["end_time"]:
                        thread_stats[thread_id]["end_time"] = dt
                except:
                    pass

        # Sort by messages and convert to serializable format
        sorted_threads = sorted(thread_stats.items(), key=lambda x: x[1]["messages"], reverse=True)[:limit]

        top_conversations = []
        for thread_id, stats in sorted_threads.items():
            duration = 0.0
            if stats["start_time"] and stats["end_time"]:
                duration = (stats["end_time"] - stats["start_time"]).total_seconds()

            top_conversations.append({
                "thread_id": thread_id,
                "user_id": stats["user_id"],
                "messages": stats["messages"],
                "tokens": stats["tokens"],
                "cost_usd": round(stats["cost"], 6),
                "duration_seconds": round(duration, 2)
            })

        return top_conversations

    def _generate_system_health_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate system health summary."""
        total_messages = len(entries)
        error_count = sum(1 for entry in entries if entry.get("response", {}).get("error"))
        error_rate = (error_count / total_messages * 100) if total_messages > 0 else 0

        # Average latency
        latencies = [entry.get("performance", {}).get("total_latency_ms", 0) for entry in entries]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Determine health status
        status = "healthy"
        issues = []

        if error_rate > 5:
            status = "degraded"
            issues.append(f"High error rate: {error_rate:.1f}%")

        if avg_latency > 5000:
            if status == "healthy":
                status = "degraded"
            issues.append(f"High average latency: {avg_latency:.0f}ms")

        if error_rate > 15 or avg_latency > 10000:
            status = "unhealthy"

        return {
            "status": status,
            "error_rate_percent": round(error_rate, 2),
            "average_latency_ms": round(avg_latency, 2),
            "issues": issues
        }

    def _calculate_trends(self, entries: List[Dict[str, Any]], date: datetime) -> Dict[str, Any]:
        """Calculate trends by comparing with previous days."""
        trends = {}

        # Get previous day's data for comparison
        prev_date = date - timedelta(days=1)
        prev_date_str = prev_date.strftime("%Y-%m-%d")
        prev_date_dir = self.log_dir / prev_date_str

        if prev_date_dir.exists():
            prev_entries = self._load_log_entries(prev_date_dir)
            if prev_entries:
                # Calculate percentage changes
                current_sessions = self._count_unique_sessions(entries)
                prev_sessions = self._count_unique_sessions(prev_entries)

                current_messages = len(entries)
                prev_messages = len(prev_entries)

                current_tokens = sum(entry.get("token_economics", {}).get("total_tokens", 0) for entry in entries)
                prev_tokens = sum(entry.get("token_economics", {}).get("total_tokens", 0) for entry in prev_entries)

                trends = {
                    "sessions_change_pct": self._calculate_pct_change(prev_sessions, current_sessions),
                    "messages_change_pct": self._calculate_pct_change(prev_messages, current_messages),
                    "tokens_change_pct": self._calculate_pct_change(prev_tokens, current_tokens)
                }

        return trends

    def _calculate_pct_change(self, prev: float, current: float) -> float:
        """Calculate percentage change."""
        if prev == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - prev) / prev) * 100, 2)

    def save_summary(self, summary: Dict[str, Any], output_dir: Optional[str] = None) -> str:
        """Save summary to file."""
        if output_dir is None:
            output_dir = self.log_dir / summary["date"]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        summary_file = output_path / f"session-summary-{summary['date']}.json"

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Daily summary saved to: {summary_file}")
        return str(summary_file)

    def generate_and_save_summary(self, date: Optional[datetime] = None, output_dir: Optional[str] = None) -> str:
        """Generate and save daily summary."""
        if date is None:
            date = datetime.now(timezone.utc)

        summary = self.generate_daily_summary(date)
        return self.save_summary(summary, output_dir)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate daily summary from chat session logs"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to generate summary for (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="/var/log/family-assistant/chat-sessions",
        help="Log directory path"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for summary file"
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print summary to stdout"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress logging output"
    )

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Parse date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = datetime.now(timezone.utc)

    # Generate summary
    generator = DailySummaryGenerator(args.log_dir)

    try:
        summary_file = generator.generate_and_save_summary(target_date, args.output_dir)

        if not args.quiet:
            print(f"Daily summary generated: {summary_file}")

        if args.print:
            with open(summary_file, 'r') as f:
                print(f.read())

    except Exception as e:
        print(f"Error generating daily summary: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()