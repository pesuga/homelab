"""
Chat Session Logger for llama.cpp interactions.

Provides comprehensive logging of chat sessions including prompts, responses,
system prompts, token economics, and performance metrics with async queue
for non-blocking operation.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import aiofiles
import gzip
import shutil
from dataclasses import dataclass, asdict
import psutil

logger = logging.getLogger(__name__)

@dataclass
class ChatSessionEntry:
    """Complete chat session log entry."""
    timestamp: str
    session_id: str
    thread_id: str
    user_id: str
    user_profile: Dict[str, Any]
    request: Dict[str, Any]
    response: Dict[str, Any]
    performance: Dict[str, Any]
    token_economics: Dict[str, Any]
    system_info: Dict[str, Any]

@dataclass
class TokenEconomics:
    """Token usage and cost tracking."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    tokens_per_second: float
    model_used: str

@dataclass
class PerformanceMetrics:
    """Performance timing information."""
    total_latency_ms: float
    prompt_processing_ms: float
    generation_ms: float
    http_request_ms: float
    memory_retrieval_ms: float

class ChatLogger:
    """Async chat session logger with queue-based non-blocking operation."""

    # Model cost per million tokens (adjust based on actual costs)
    MODEL_COSTS = {
        "Kimi-VL-A3B": 0.20,
        "Mistral-7B": 0.15,
        "Mixtral-8x7B": 0.35,
        "Llama-3.1-8B": 0.18,
        "default": 0.20
    }

    def __init__(self, log_dir: str = "/var/log/family-assistant/chat-sessions"):
        self.log_dir = Path(log_dir)
        self.log_queue = asyncio.Queue(maxsize=1000)
        self.batch_size = 10
        self.flush_interval = 5.0  # seconds
        self.retention_days = 30
        self.compression_days = 7

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Task for processing log entries
        self._processor_task = None
        self._shutdown_event = asyncio.Event()

        logger.info(f"ChatLogger initialized with log_dir: {self.log_dir}")

    async def start(self):
        """Start the log processor."""
        if self._processor_task is None:
            self._processor_task = asyncio.create_task(self._process_logs())
            logger.info("ChatLogger started")

    async def stop(self):
        """Stop the log processor and flush remaining logs."""
        if self._processor_task:
            self._shutdown_event.set()

            # Process any remaining logs
            await self._flush_logs()

            # Wait for processor to finish
            await self._processor_task

            logger.info("ChatLogger stopped")

    async def log_chat_session(
        self,
        thread_id: str,
        user_id: str,
        user_profile: Dict[str, Any],
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        performance_data: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        memory_context: Optional[Dict[str, Any]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ):
        """Log a complete chat session with full context."""
        try:
            # Generate session ID if not present
            session_id = getattr(self, '_current_session_id', None) or f"sess_{uuid.uuid4().hex[:12]}"

            # Calculate token economics
            token_econ = self._calculate_token_economics(request_data, response_data, start_time, end_time)

            # Build performance metrics
            performance = self._build_performance_metrics(performance_data, start_time, end_time)

            # Enhance request data with system prompt and memory context
            enhanced_request = request_data.copy()
            if system_prompt:
                enhanced_request["system_prompt"] = system_prompt
            if memory_context:
                enhanced_request["memory_context"] = memory_context

            # Create session entry
            session_entry = ChatSessionEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                session_id=session_id,
                thread_id=thread_id,
                user_id=user_id,
                user_profile=user_profile,
                request=enhanced_request,
                response=response_data,
                performance=performance,
                token_economics=asdict(token_econ),
                system_info=self._get_system_info()
            )

            # Add to queue for async processing
            await self.log_queue.put(asdict(session_entry))

            logger.debug(f"Chat session logged: session_id={session_id}, user_id={user_id}")

        except Exception as e:
            logger.error(f"Failed to log chat session: {e}", exc_info=True)

    def _calculate_token_economics(
        self,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> TokenEconomics:
        """Calculate token usage and cost information."""

        # Extract token counts (fallback to estimations if not provided)
        prompt_tokens = request_data.get("prompt_tokens", 0)
        completion_tokens = response_data.get("completion_tokens", 0)

        # If no explicit tokens, estimate from text (rough approximation: 1 token ≈ 4 characters)
        if prompt_tokens == 0:
            user_message = request_data.get("user_message", "")
            system_prompt = request_data.get("system_prompt", "")
            prompt_tokens = (len(user_message) + len(system_prompt)) // 4

        if completion_tokens == 0:
            llm_response = response_data.get("llm_response", "")
            completion_tokens = len(llm_response) // 4

        total_tokens = prompt_tokens + completion_tokens

        # Determine model type and cost
        model_used = request_data.get("model", "default")
        if "/" in model_used:  # Extract model name from path
            model_parts = model_used.split("/")
            model_name = next((part for part in model_parts if part in self.MODEL_COSTS), "default")
        else:
            model_name = model_used

        cost_per_million = self.MODEL_COSTS.get(model_name, self.MODEL_COSTS["default"])
        estimated_cost_usd = (total_tokens / 1_000_000) * cost_per_million

        # Calculate tokens per second
        tokens_per_second = 0.0
        if start_time and end_time and completion_tokens > 0:
            duration_seconds = end_time - start_time
            if duration_seconds > 0:
                tokens_per_second = completion_tokens / duration_seconds

        return TokenEconomics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            tokens_per_second=tokens_per_second,
            model_used=model_used
        )

    def _build_performance_metrics(
        self,
        performance_data: Optional[Dict[str, Any]],
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """Build comprehensive performance metrics."""

        performance = {
            "total_latency_ms": 0.0,
            "prompt_processing_ms": 0.0,
            "generation_ms": 0.0,
            "http_request_ms": 0.0,
            "memory_retrieval_ms": 0.0
        }

        # Add provided performance data
        if performance_data:
            performance.update(performance_data)

        # Calculate total latency if start/end times provided
        if start_time and end_time:
            total_latency_ms = (end_time - start_time) * 1000
            performance["total_latency_ms"] = total_latency_ms

        return performance

    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information."""
        try:
            # Get pod name from environment variable
            pod_name = os.getenv("POD_NAME", "unknown")

            # Get basic system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            return {
                "api_pod": pod_name,
                "compute_node": "pesubuntu",  # Based on architecture
                "cpu_usage_percent": cpu_percent,
                "memory_usage_mb": memory.used // (1024 * 1024),
                "memory_percent": memory.percent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to get system info: {e}")
            return {
                "api_pod": os.getenv("POD_NAME", "unknown"),
                "compute_node": "pesubuntu",
                "error": str(e)
            }

    async def _process_logs(self):
        """Process log entries from queue and write to files."""
        logger.info("Log processor started")

        batch = []

        while not self._shutdown_event.is_set():
            try:
                # Wait for log entries or shutdown
                try:
                    timeout = self.flush_interval
                    entry = await asyncio.wait_for(self.log_queue.get(), timeout=timeout)
                    batch.append(entry)
                except asyncio.TimeoutError:
                    # Flush batch on timeout
                    if batch:
                        await self._flush_logs()
                        batch = []
                    continue

                # Flush if batch is full
                if len(batch) >= self.batch_size:
                    await self._flush_logs()
                    batch = []

            except Exception as e:
                logger.error(f"Error in log processor: {e}", exc_info=True)

        # Final flush on shutdown
        if batch:
            await self._flush_logs()

    async def _flush_logs(self):
        """Flush current batch of logs to files."""
        if not self.log_queue.empty() or hasattr(self, '_current_batch'):
            # Get all current entries
            entries = []

            # Get entries from queue
            while not self.log_queue.empty():
                try:
                    entry = self.log_queue.get_nowait()
                    entries.append(entry)
                except asyncio.QueueEmpty:
                    break

            if entries:
                await self._write_log_entries(entries)

    async def _write_log_entries(self, entries: List[Dict[str, Any]]):
        """Write log entries to daily log file."""
        try:
            # Group entries by date
            entries_by_date = {}
            for entry in entries:
                date = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).date()
                if date not in entries_by_date:
                    entries_by_date[date] = []
                entries_by_date[date].append(entry)

            # Write entries for each date
            for date, date_entries in entries_by_date.items():
                await self._write_daily_log(date, date_entries)

        except Exception as e:
            logger.error(f"Failed to write log entries: {e}", exc_info=True)

    async def _write_daily_log(self, date, entries: List[Dict[str, Any]]):
        """Write entries to a daily log file."""
        try:
            date_str = date.strftime("%Y-%m-%d")
            date_dir = self.log_dir / date_str
            date_dir.mkdir(exist_ok=True)

            log_file = date_dir / f"chat-sessions-{date_str}.ndjson"

            # Append entries to file
            async with aiofiles.open(log_file, mode='a', encoding='utf-8') as f:
                for entry in entries:
                    log_line = json.dumps(entry, ensure_ascii=False, default=str) + '\n'
                    await f.write(log_line)

            logger.debug(f"Wrote {len(entries)} entries to {log_file}")

        except Exception as e:
            logger.error(f"Failed to write daily log for {date}: {e}", exc_info=True)

    async def cleanup_old_logs(self):
        """Clean up and compress old log files."""
        try:
            cutoff_date = datetime.now().date() - timedelta(days=self.retention_days)
            compression_date = datetime.now().date() - timedelta(days=self.compression_days)

            # Remove old logs
            for date_dir in self.log_dir.iterdir():
                if date_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").date()

                        # Delete very old logs
                        if dir_date < cutoff_date:
                            shutil.rmtree(date_dir)
                            logger.info(f"Deleted old log directory: {date_dir}")

                        # Compress old but not too old logs
                        elif dir_date < compression_date:
                            await self._compress_log_directory(date_dir)

                    except ValueError:
                        # Skip directories that don't match date format
                        continue

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}", exc_info=True)

    async def _compress_log_directory(self, date_dir: Path):
        """Compress log files in a date directory."""
        try:
            for log_file in date_dir.glob("*.ndjson"):
                compressed_file = log_file.with_suffix(log_file.suffix + ".gz")

                if not compressed_file.exists():
                    # Compress the file
                    async with aiofiles.open(log_file, 'rb') as f_in:
                        content = await f_in.read()

                    # Write compressed version
                    with gzip.open(compressed_file, 'wt', encoding='utf-8') as f_out:
                        f_out.write(content.decode('utf-8'))

                    # Remove original file
                    log_file.unlink()
                    logger.debug(f"Compressed log file: {log_file} -> {compressed_file}")

        except Exception as e:
            logger.error(f"Failed to compress log directory {date_dir}: {e}", exc_info=True)

# Global instance
chat_logger = ChatLogger()

async def get_chat_logger() -> ChatLogger:
    """Get the global chat logger instance."""
    return chat_logger