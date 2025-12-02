"""
Content Filtering Service - Phase 3

Provides multi-level content filtering with keyword blocking, domain filtering,
and severity classification for parental controls.
"""

import re
from datetime import datetime
from typing import List, Optional, Set, Dict, Any, Tuple
from uuid import UUID
from urllib.parse import urlparse
import asyncpg

from ..models.user_management import (
    ContentFilterLevel,
    FilterSeverity,
    FilterAction,
    ContentFilterLog,
    ContentFilterLogCreate,
    ContentFilterCheck,
    ContentFilterResult,
)


class ContentFilter:
    """Content filtering service with multi-level protection"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

        # Default keyword lists by severity
        self.default_blocked_keywords = {
            FilterSeverity.CRITICAL: [
                # Violence and harm
                "kill", "murder", "suicide", "self-harm", "weapon", "gun", "knife",
                # Adult content
                "porn", "sex", "nude", "xxx", "adult",
                # Drugs and substances
                "drug", "cocaine", "heroin", "meth",
                # Hate speech
                "hate", "racist", "nazi",
            ],
            FilterSeverity.HIGH: [
                # Inappropriate behavior
                "bully", "threat", "violence", "abuse",
                # Gambling
                "casino", "gamble", "bet",
                # Scams
                "scam", "phishing", "hack",
            ],
            FilterSeverity.MEDIUM: [
                # Mild language
                "damn", "hell", "crap",
                # Risky activities
                "party", "alcohol", "beer", "wine",
            ],
            FilterSeverity.LOW: [
                # Dating and relationships
                "dating", "girlfriend", "boyfriend",
                # Social media concerns
                "meet strangers", "share location",
            ],
        }

        # Default blocked domains
        self.default_blocked_domains = {
            # Adult content
            "pornhub.com",
            "xvideos.com",
            "xnxx.com",
            # Gambling
            "bet365.com",
            "888casino.com",
            # Dangerous content
            "4chan.org",
            "8chan.net",
        }

        # Safe domains (always allowed)
        self.safe_domains = {
            "wikipedia.org",
            "khanacademy.org",
            "google.com",
            "youtube.com",  # Note: Content still filtered
            "github.com",
            "stackoverflow.com",
        }

    # ==============================================================================
    # Content Checking
    # ==============================================================================

    async def check_content(
        self, user_id: UUID, content_type: str, content: str
    ) -> ContentFilterResult:
        """
        Check content against filtering rules

        Args:
            user_id: User ID to check parental controls for
            content_type: Type of content (message, search, url, image)
            content: Content to check

        Returns:
            ContentFilterResult with allowed status, action, reason, severity
        """
        # Get user's parental controls
        async with self.db.acquire() as conn:
            controls_row = await conn.fetchrow(
                """
                SELECT pc.content_filter_level, pc.blocked_keywords,
                       pc.allowed_domains, pc.blocked_domains,
                       pc.notify_parent_on_flagged_content, pc.parent_id
                FROM parental_controls pc
                WHERE pc.child_id = $1
                ORDER BY pc.created_at DESC
                LIMIT 1
                """,
                user_id,
            )

            # No parental controls - allow all
            if not controls_row:
                return ContentFilterResult(
                    allowed=True,
                    action=FilterAction.ALLOWED_WITH_WARNING,
                    reason=None,
                    severity=None,
                    filtered_content=None,
                )

            filter_level = ContentFilterLevel(controls_row["content_filter_level"])
            custom_blocked = set(controls_row["blocked_keywords"] or [])
            allowed_domains = set(controls_row["allowed_domains"] or [])
            blocked_domains = set(controls_row["blocked_domains"] or [])
            notify_parent = controls_row["notify_parent_on_flagged_content"]
            parent_id = controls_row["parent_id"]

        # Check if filtering is off
        if filter_level == ContentFilterLevel.OFF:
            return ContentFilterResult(
                allowed=True,
                action=FilterAction.ALLOWED_WITH_WARNING,
                reason="Filtering disabled",
                severity=None,
                filtered_content=None,
            )

        # Perform checks based on content type
        if content_type == "url":
            result = await self._check_url(
                content, filter_level, allowed_domains, blocked_domains
            )
        else:
            result = await self._check_text(
                content, filter_level, custom_blocked
            )

        # Log if content was filtered
        if result.action in [FilterAction.BLOCKED, FilterAction.WARNED, FilterAction.FLAGGED]:
            await self._log_filtered_content(
                user_id,
                content_type,
                content,
                result.reason or "Content filtered",
                result.severity or FilterSeverity.LOW,
                result.action,
                notify_parent,
            )

        return result

    async def _check_text(
        self,
        content: str,
        filter_level: ContentFilterLevel,
        custom_blocked: Set[str],
    ) -> ContentFilterResult:
        """Check text content for blocked keywords"""
        content_lower = content.lower()

        # Combine default and custom blocked keywords
        blocked_keywords = custom_blocked.copy()

        # Add default keywords based on filter level
        if filter_level == ContentFilterLevel.STRICT:
            for severity in [FilterSeverity.CRITICAL, FilterSeverity.HIGH, FilterSeverity.MEDIUM, FilterSeverity.LOW]:
                blocked_keywords.update(self.default_blocked_keywords[severity])
        elif filter_level == ContentFilterLevel.MODERATE:
            for severity in [FilterSeverity.CRITICAL, FilterSeverity.HIGH]:
                blocked_keywords.update(self.default_blocked_keywords[severity])

        # Check for keyword matches
        for severity in [FilterSeverity.CRITICAL, FilterSeverity.HIGH, FilterSeverity.MEDIUM, FilterSeverity.LOW]:
            for keyword in self.default_blocked_keywords[severity]:
                if keyword in blocked_keywords and self._contains_keyword(content_lower, keyword):
                    # Determine action based on severity
                    if severity == FilterSeverity.CRITICAL:
                        action = FilterAction.BLOCKED
                    elif severity == FilterSeverity.HIGH:
                        action = FilterAction.WARNED if filter_level == ContentFilterLevel.MODERATE else FilterAction.BLOCKED
                    else:
                        action = FilterAction.FLAGGED if filter_level == ContentFilterLevel.MODERATE else FilterAction.WARNED

                    return ContentFilterResult(
                        allowed=action != FilterAction.BLOCKED,
                        action=action,
                        reason=f"Contains blocked keyword: '{keyword}'",
                        severity=severity,
                        filtered_content=self._redact_keyword(content, keyword) if action == FilterAction.BLOCKED else None,
                    )

        # No issues found
        return ContentFilterResult(
            allowed=True,
            action=FilterAction.ALLOWED_WITH_WARNING,
            reason=None,
            severity=None,
            filtered_content=None,
        )

    async def _check_url(
        self,
        url: str,
        filter_level: ContentFilterLevel,
        allowed_domains: Set[str],
        blocked_domains: Set[str],
    ) -> ContentFilterResult:
        """Check URL against domain filtering rules"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]

            # Check if domain is in allowed list
            if domain in allowed_domains or domain in self.safe_domains:
                return ContentFilterResult(
                    allowed=True,
                    action=FilterAction.ALLOWED_WITH_WARNING,
                    reason="Domain in allowed list",
                    severity=None,
                    filtered_content=None,
                )

            # Check if domain is in blocked list
            combined_blocked = blocked_domains.copy()
            if filter_level == ContentFilterLevel.STRICT:
                combined_blocked.update(self.default_blocked_domains)

            if domain in combined_blocked:
                return ContentFilterResult(
                    allowed=False,
                    action=FilterAction.BLOCKED,
                    reason=f"Blocked domain: {domain}",
                    severity=FilterSeverity.HIGH,
                    filtered_content="[URL BLOCKED]",
                )

            # Check for suspicious TLDs
            suspicious_tlds = [".xxx", ".adult", ".sex", ".porn"]
            for tld in suspicious_tlds:
                if domain.endswith(tld):
                    return ContentFilterResult(
                        allowed=False,
                        action=FilterAction.BLOCKED,
                        reason=f"Suspicious TLD: {tld}",
                        severity=FilterSeverity.CRITICAL,
                        filtered_content="[URL BLOCKED]",
                    )

            # URL appears safe
            return ContentFilterResult(
                allowed=True,
                action=FilterAction.ALLOWED_WITH_WARNING,
                reason=None,
                severity=None,
                filtered_content=None,
            )

        except Exception as e:
            # Invalid URL
            return ContentFilterResult(
                allowed=False,
                action=FilterAction.BLOCKED,
                reason=f"Invalid URL: {str(e)}",
                severity=FilterSeverity.MEDIUM,
                filtered_content="[INVALID URL]",
            )

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        """Check if text contains keyword (word boundary aware)"""
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _redact_keyword(self, text: str, keyword: str) -> str:
        """Redact keyword from text"""
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)

    # ==============================================================================
    # Content Filter Logging
    # ==============================================================================

    async def _log_filtered_content(
        self,
        user_id: UUID,
        content_type: str,
        content: str,
        reason: str,
        severity: FilterSeverity,
        action: FilterAction,
        notify_parent: bool,
    ) -> UUID:
        """Log filtered content and optionally notify parent"""
        async with self.db.acquire() as conn:
            # Truncate content snippet
            content_snippet = content[:500] if len(content) > 500 else content

            # Insert log
            row = await conn.fetchrow(
                """
                INSERT INTO content_filter_logs (
                    user_id, content_type, content_snippet,
                    filter_reason, severity, action_taken, parent_notified
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                user_id,
                content_type,
                content_snippet,
                reason,
                severity.value,
                action.value,
                notify_parent,
            )

            log_id = row["id"]

            # TODO: Send notification to parent if enabled
            # This would integrate with notification service

            return log_id

    async def get_content_filter_logs(
        self,
        user_id: Optional[UUID] = None,
        severity: Optional[FilterSeverity] = None,
        action: Optional[FilterAction] = None,
        limit: int = 100,
    ) -> List[ContentFilterLog]:
        """Retrieve content filter logs with optional filtering"""
        async with self.db.acquire() as conn:
            conditions = []
            values = []
            param_count = 1

            if user_id:
                conditions.append(f"user_id = ${param_count}")
                values.append(user_id)
                param_count += 1

            if severity:
                conditions.append(f"severity = ${param_count}")
                values.append(severity.value)
                param_count += 1

            if action:
                conditions.append(f"action_taken = ${param_count}")
                values.append(action.value)
                param_count += 1

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            values.append(limit)

            query = f"""
                SELECT * FROM content_filter_logs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count}
            """

            rows = await conn.fetch(query, *values)
            return [ContentFilterLog(**dict(row)) for row in rows]

    # ==============================================================================
    # Filtering Statistics
    # ==============================================================================

    async def get_filter_stats(
        self, user_id: UUID, days: int = 7
    ) -> Dict[str, Any]:
        """Get content filtering statistics for user"""
        async with self.db.acquire() as conn:
            # Get total filtered count
            total_filtered = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM content_filter_logs
                WHERE user_id = $1
                  AND created_at >= NOW() - INTERVAL '1 day' * $2
                """,
                user_id,
                days,
            )

            # Get counts by severity
            severity_counts = await conn.fetch(
                """
                SELECT severity, COUNT(*) as count
                FROM content_filter_logs
                WHERE user_id = $1
                  AND created_at >= NOW() - INTERVAL '1 day' * $2
                GROUP BY severity
                """,
                user_id,
                days,
            )

            # Get counts by action
            action_counts = await conn.fetch(
                """
                SELECT action_taken, COUNT(*) as count
                FROM content_filter_logs
                WHERE user_id = $1
                  AND created_at >= NOW() - INTERVAL '1 day' * $2
                GROUP BY action_taken
                """,
                user_id,
                days,
            )

            # Get most common filter reasons
            common_reasons = await conn.fetch(
                """
                SELECT filter_reason, COUNT(*) as count
                FROM content_filter_logs
                WHERE user_id = $1
                  AND created_at >= NOW() - INTERVAL '1 day' * $2
                GROUP BY filter_reason
                ORDER BY count DESC
                LIMIT 10
                """,
                user_id,
                days,
            )

            return {
                "user_id": str(user_id),
                "days": days,
                "total_filtered": total_filtered,
                "by_severity": {row["severity"]: row["count"] for row in severity_counts},
                "by_action": {row["action_taken"]: row["count"] for row in action_counts},
                "common_reasons": [
                    {"reason": row["filter_reason"], "count": row["count"]}
                    for row in common_reasons
                ],
            }

    # ==============================================================================
    # Custom Filtering Rules
    # ==============================================================================

    async def add_blocked_keyword(
        self, child_id: UUID, parent_id: UUID, keyword: str
    ) -> bool:
        """Add custom blocked keyword to parental controls"""
        async with self.db.acquire() as conn:
            # Get current blocked keywords
            row = await conn.fetchrow(
                """
                SELECT blocked_keywords
                FROM parental_controls
                WHERE child_id = $1 AND parent_id = $2
                """,
                child_id,
                parent_id,
            )

            if not row:
                raise ValueError("Parental controls not found")

            blocked_keywords = set(row["blocked_keywords"] or [])
            blocked_keywords.add(keyword.lower())

            # Update parental controls
            await conn.execute(
                """
                UPDATE parental_controls
                SET blocked_keywords = $1, updated_at = NOW()
                WHERE child_id = $2 AND parent_id = $3
                """,
                list(blocked_keywords),
                child_id,
                parent_id,
            )

            return True

    async def remove_blocked_keyword(
        self, child_id: UUID, parent_id: UUID, keyword: str
    ) -> bool:
        """Remove custom blocked keyword from parental controls"""
        async with self.db.acquire() as conn:
            # Get current blocked keywords
            row = await conn.fetchrow(
                """
                SELECT blocked_keywords
                FROM parental_controls
                WHERE child_id = $1 AND parent_id = $2
                """,
                child_id,
                parent_id,
            )

            if not row:
                raise ValueError("Parental controls not found")

            blocked_keywords = set(row["blocked_keywords"] or [])
            blocked_keywords.discard(keyword.lower())

            # Update parental controls
            await conn.execute(
                """
                UPDATE parental_controls
                SET blocked_keywords = $1, updated_at = NOW()
                WHERE child_id = $2 AND parent_id = $3
                """,
                list(blocked_keywords),
                child_id,
                parent_id,
            )

            return True

    async def add_blocked_domain(
        self, child_id: UUID, parent_id: UUID, domain: str
    ) -> bool:
        """Add blocked domain to parental controls"""
        async with self.db.acquire() as conn:
            # Normalize domain
            domain = domain.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            # Get current blocked domains
            row = await conn.fetchrow(
                """
                SELECT blocked_domains
                FROM parental_controls
                WHERE child_id = $1 AND parent_id = $2
                """,
                child_id,
                parent_id,
            )

            if not row:
                raise ValueError("Parental controls not found")

            blocked_domains = set(row["blocked_domains"] or [])
            blocked_domains.add(domain)

            # Update parental controls
            await conn.execute(
                """
                UPDATE parental_controls
                SET blocked_domains = $1, updated_at = NOW()
                WHERE child_id = $2 AND parent_id = $3
                """,
                list(blocked_domains),
                child_id,
                parent_id,
            )

            return True

    async def add_allowed_domain(
        self, child_id: UUID, parent_id: UUID, domain: str
    ) -> bool:
        """Add allowed domain to parental controls (whitelist)"""
        async with self.db.acquire() as conn:
            # Normalize domain
            domain = domain.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            # Get current allowed domains
            row = await conn.fetchrow(
                """
                SELECT allowed_domains
                FROM parental_controls
                WHERE child_id = $1 AND parent_id = $2
                """,
                child_id,
                parent_id,
            )

            if not row:
                raise ValueError("Parental controls not found")

            allowed_domains = set(row["allowed_domains"] or [])
            allowed_domains.add(domain)

            # Update parental controls
            await conn.execute(
                """
                UPDATE parental_controls
                SET allowed_domains = $1, updated_at = NOW()
                WHERE child_id = $2 AND parent_id = $3
                """,
                list(allowed_domains),
                child_id,
                parent_id,
            )

            return True
