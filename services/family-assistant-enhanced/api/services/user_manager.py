"""
User Management Service Layer - Phase 3

Provides business logic for family member management, RBAC, and permissions.
"""

import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncpg

from ..models.user_management import (
    FamilyMember,
    FamilyMemberCreate,
    FamilyMemberUpdate,
    UserRole,
    Permission,
    UserPermission,
    UserPermissionCreate,
    PermissionCheck,
    ParentalControls,
    ParentalControlsCreate,
    ParentalControlsUpdate,
    ScreenTimeLog,
    ScreenTimeUpdate,
    ScreenTimeStatus,
    AuditLog,
    AuditLogCreate,
)
from settings import settings


class UserManager:
    """User management service with RBAC and parental controls"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    # ==============================================================================
    # Family Member Management
    # ==============================================================================

    async def create_family_member(
        self, member_data: FamilyMemberCreate, created_by: Optional[UUID] = None
    ) -> FamilyMember:
        """Create new family member with role-based defaults"""
        async with self.db.acquire() as conn:
            # Check for duplicate telegram_id or email
            if member_data.telegram_id:
                existing = await conn.fetchrow(
                    "SELECT id FROM family_members WHERE telegram_id = $1",
                    member_data.telegram_id,
                )
                if existing:
                    raise ValueError(f"Family member with telegram_id {member_data.telegram_id} already exists")

            if member_data.email:
                existing = await conn.fetchrow(
                    "SELECT id FROM family_members WHERE email = $1",
                    member_data.email,
                )
                if existing:
                    raise ValueError(f"Family member with email {member_data.email} already exists")

            # Insert family member
            row = await conn.fetchrow(
                """
                INSERT INTO family_members (
                    telegram_id, email, username,
                    first_name, last_name, display_name, avatar_url, date_of_birth,
                    role, age_group, is_admin,
                    language_preference, timezone, theme_preference,
                    privacy_level, safety_level, content_filtering_enabled,
                    active_skills, preferences
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                RETURNING *
                """,
                member_data.telegram_id,
                member_data.email,
                member_data.username,
                member_data.first_name,
                member_data.last_name,
                member_data.display_name,
                member_data.avatar_url,
                member_data.date_of_birth,
                member_data.role.value,
                member_data.age_group.value if member_data.age_group else None,
                member_data.is_admin,
                member_data.language_preference.value,
                member_data.timezone,
                member_data.theme_preference,
                member_data.privacy_level.value,
                member_data.safety_level.value,
                member_data.content_filtering_enabled,
                member_data.active_skills,
                member_data.preferences,
            )

            # Audit log
            await self._create_audit_log(
                conn,
                user_id=created_by,
                action="create_family_member",
                resource_type="family_member",
                resource_id=row["id"],
                details={"role": member_data.role.value, "name": member_data.first_name},
            )

            return FamilyMember(**dict(row))

    async def get_family_member(self, member_id: UUID) -> Optional[FamilyMember]:
        """Retrieve family member by ID"""
        async with self.db.acquire() as conn:
            # Try family_members table first
            row = await conn.fetchrow(
                "SELECT * FROM family_members WHERE id = $1 AND is_active = TRUE",
                str(member_id),
            )
            if row:
                return FamilyMember(
                    id=str(row["id"]),
                    telegram_id=row["telegram_id"],
                    username=row["username"],
                    first_name=row["first_name"] or "",
                    last_name=row["last_name"] or "",
                    email=row["username"],  # Use username as email fallback
                    role=row["role"],
                    age_group=row["age_group"],
                    language_preference=row["language_preference"],
                    hashed_password=row.get("hashed_password"),
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            # Try users table (for admin accounts)
            # Since users table uses integer IDs, we need to match by email
            # First get the email from the JWT token or search by deterministic UUID pattern
            import uuid
            # Try to find user by checking if the UUID matches our deterministic pattern
            # This is a limitation of our mixed user ID system
            # For now, let's get the first admin user as fallback
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE is_admin = true AND is_active = true LIMIT 1",
            )
            if row:
                # Generate the same deterministic UUID to check if it matches
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{row['id']}")
                if str(user_uuid) == str(member_id):
                    # Get password hash for authentication
                    password_row = await conn.fetchrow(
                        "SELECT password_hash FROM users WHERE id = $1",
                        row["id"],
                    )
                    return FamilyMember(
                        id=str(user_uuid),
                        telegram_id=None,
                        username=row["username"],
                        first_name="Admin",
                        last_name="User",
                        email=row["email"],
                        role="parent" if row["is_admin"] else "member",
                        age_group="adult",
                        language_preference="en",
                        hashed_password=password_row["password_hash"] if password_row else None,
                        is_active=row["is_active"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )

            return None

    async def get_family_member_by_telegram_id(self, telegram_id: int) -> Optional[FamilyMember]:
        """Retrieve family member by Telegram ID"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM family_members WHERE telegram_id = $1 AND is_active = TRUE",
                telegram_id,
            )
            return FamilyMember(**dict(row)) if row else None

    async def update_family_member(
        self, member_id: UUID, update_data: FamilyMemberUpdate, updated_by: Optional[UUID] = None
    ) -> Optional[FamilyMember]:
        """Update family member profile"""
        async with self.db.acquire() as conn:
            # Build dynamic update query
            update_fields = []
            values = []
            param_count = 1

            for field, value in update_data.dict(exclude_unset=True).items():
                if value is not None:
                    # Handle enum values
                    if hasattr(value, "value"):
                        value = value.value
                    update_fields.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1

            if not update_fields:
                return await self.get_family_member(member_id)

            # Add updated_at
            update_fields.append(f"updated_at = ${param_count}")
            values.append(datetime.now())
            param_count += 1

            # Add member_id for WHERE clause
            values.append(member_id)

            query = f"""
                UPDATE family_members
                SET {', '.join(update_fields)}
                WHERE id = ${param_count}
                RETURNING *
            """

            row = await conn.fetchrow(query, *values)

            if row:
                # Audit log
                await self._create_audit_log(
                    conn,
                    user_id=updated_by,
                    action="update_family_member",
                    resource_type="family_member",
                    resource_id=member_id,
                    details=update_data.dict(exclude_unset=True),
                )

            return FamilyMember(**dict(row)) if row else None

    async def delete_family_member(
        self, member_id: UUID, deleted_by: Optional[UUID] = None
    ) -> bool:
        """Soft delete family member"""
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE family_members
                SET is_active = FALSE, updated_at = $1
                WHERE id = $2
                """,
                datetime.now(),
                member_id,
            )

            if result != "UPDATE 0":
                # Audit log
                await self._create_audit_log(
                    conn,
                    user_id=deleted_by,
                    action="delete_family_member",
                    resource_type="family_member",
                    resource_id=member_id,
                )
                return True

            return False

    async def list_family_members(
        self, include_inactive: bool = False
    ) -> List[FamilyMember]:
        """List all family members"""
        async with self.db.acquire() as conn:
            query = "SELECT * FROM family_members"
            if not include_inactive:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY created_at DESC"

            rows = await conn.fetch(query)
            return [FamilyMember(**dict(row)) for row in rows]

    async def update_last_active(self, member_id: UUID) -> None:
        """Update last_active_at timestamp"""
        async with self.db.acquire() as conn:
            await conn.execute(
                "UPDATE family_members SET last_active_at = $1 WHERE id = $2",
                datetime.now(),
                member_id,
            )

    # ==============================================================================
    # Permission Management
    # ==============================================================================

    async def check_permission(
        self, user_id: UUID, permission_name: str
    ) -> PermissionCheck:
        """Check if user has permission"""
        async with self.db.acquire() as conn:
            has_perm = await conn.fetchval(
                "SELECT has_permission($1, $2)",
                user_id,
                permission_name,
            )

            # Get reason
            reason = None
            if has_perm:
                # Check if user-specific override
                user_override = await conn.fetchrow(
                    """
                    SELECT up.granted, up.reason
                    FROM user_permissions up
                    JOIN permissions p ON up.permission_id = p.id
                    WHERE up.user_id = $1 AND p.name = $2
                      AND (up.expires_at IS NULL OR up.expires_at > NOW())
                    """,
                    user_id,
                    permission_name,
                )
                if user_override:
                    reason = user_override["reason"] or "User-specific permission"
                else:
                    reason = "Role-based permission"
            else:
                reason = "Permission denied"

            return PermissionCheck(
                user_id=user_id,
                permission_name=permission_name,
                has_permission=has_perm,
                reason=reason,
            )

    async def grant_permission(
        self, perm_data: UserPermissionCreate, granted_by: Optional[UUID] = None
    ) -> UserPermission:
        """Grant permission to user"""
        async with self.db.acquire() as conn:
            # Get permission ID
            perm_row = await conn.fetchrow(
                "SELECT id FROM permissions WHERE name = $1",
                perm_data.permission_name,
            )
            if not perm_row:
                raise ValueError(f"Permission '{perm_data.permission_name}' not found")

            permission_id = perm_row["id"]

            # Insert or update user permission
            row = await conn.fetchrow(
                """
                INSERT INTO user_permissions (
                    user_id, permission_id, granted, granted_by, reason, expires_at
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id, permission_id)
                DO UPDATE SET
                    granted = EXCLUDED.granted,
                    granted_by = EXCLUDED.granted_by,
                    reason = EXCLUDED.reason,
                    expires_at = EXCLUDED.expires_at,
                    created_at = NOW()
                RETURNING *
                """,
                perm_data.user_id,
                permission_id,
                perm_data.granted,
                granted_by,
                perm_data.reason,
                perm_data.expires_at,
            )

            # Audit log
            await self._create_audit_log(
                conn,
                user_id=granted_by,
                action="grant_permission" if perm_data.granted else "revoke_permission",
                resource_type="user_permission",
                resource_id=row["id"],
                details={
                    "user_id": str(perm_data.user_id),
                    "permission": perm_data.permission_name,
                    "granted": perm_data.granted,
                },
            )

            return UserPermission(**dict(row))

    async def revoke_permission(
        self, user_id: UUID, permission_name: str, revoked_by: Optional[UUID] = None
    ) -> bool:
        """Revoke permission from user"""
        perm_data = UserPermissionCreate(
            user_id=user_id,
            permission_name=permission_name,
            granted=False,
            reason="Permission revoked",
        )
        await self.grant_permission(perm_data, granted_by=revoked_by)
        return True

    async def list_user_permissions(self, user_id: UUID) -> List[UserPermission]:
        """List all permissions for user"""
        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT up.*
                FROM user_permissions up
                WHERE up.user_id = $1
                  AND (up.expires_at IS NULL OR up.expires_at > NOW())
                ORDER BY up.created_at DESC
                """,
                user_id,
            )
            return [UserPermission(**dict(row)) for row in rows]

    # ==============================================================================
    # Parental Controls
    # ==============================================================================

    async def create_parental_controls(
        self, controls_data: ParentalControlsCreate, created_by: Optional[UUID] = None
    ) -> ParentalControls:
        """Create parental controls for child"""
        async with self.db.acquire() as conn:
            # Verify parent-child relationship
            child = await self.get_family_member(controls_data.child_id)
            if not child:
                raise ValueError("Child not found")

            parent = await self.get_family_member(controls_data.parent_id)
            if not parent or parent.role not in [UserRole.PARENT, UserRole.GRANDPARENT]:
                raise ValueError("Parent must have parent or grandparent role")

            # Check if controls already exist
            existing = await conn.fetchrow(
                "SELECT id FROM parental_controls WHERE child_id = $1 AND parent_id = $2",
                controls_data.child_id,
                controls_data.parent_id,
            )
            if existing:
                raise ValueError("Parental controls already exist for this parent-child pair")

            # Insert parental controls
            row = await conn.fetchrow(
                """
                INSERT INTO parental_controls (
                    child_id, parent_id,
                    screen_time_enabled, daily_limit_minutes,
                    weekday_limit_minutes, weekend_limit_minutes,
                    quiet_hours_start, quiet_hours_end,
                    content_filter_level, blocked_keywords,
                    allowed_domains, blocked_domains,
                    activity_monitoring_enabled, conversation_review_enabled,
                    location_sharing_enabled,
                    notify_parent_on_flagged_content,
                    notify_parent_on_limit_exceeded,
                    notify_parent_on_emergency
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                RETURNING *
                """,
                controls_data.child_id,
                controls_data.parent_id,
                controls_data.screen_time_enabled,
                controls_data.daily_limit_minutes,
                controls_data.weekday_limit_minutes,
                controls_data.weekend_limit_minutes,
                controls_data.quiet_hours_start,
                controls_data.quiet_hours_end,
                controls_data.content_filter_level.value,
                controls_data.blocked_keywords,
                controls_data.allowed_domains,
                controls_data.blocked_domains,
                controls_data.activity_monitoring_enabled,
                controls_data.conversation_review_enabled,
                controls_data.location_sharing_enabled,
                controls_data.notify_parent_on_flagged_content,
                controls_data.notify_parent_on_limit_exceeded,
                controls_data.notify_parent_on_emergency,
            )

            # Audit log
            await self._create_audit_log(
                conn,
                user_id=created_by,
                action="create_parental_controls",
                resource_type="parental_controls",
                resource_id=row["id"],
                details={
                    "child_id": str(controls_data.child_id),
                    "parent_id": str(controls_data.parent_id),
                },
            )

            return ParentalControls(**dict(row))

    async def get_parental_controls(
        self, child_id: UUID, parent_id: Optional[UUID] = None
    ) -> Optional[ParentalControls]:
        """Get parental controls for child"""
        async with self.db.acquire() as conn:
            if parent_id:
                row = await conn.fetchrow(
                    "SELECT * FROM parental_controls WHERE child_id = $1 AND parent_id = $2",
                    child_id,
                    parent_id,
                )
            else:
                # Get primary parent's controls
                row = await conn.fetchrow(
                    """
                    SELECT pc.*
                    FROM parental_controls pc
                    JOIN family_members fm ON pc.parent_id = fm.id
                    WHERE pc.child_id = $1
                    ORDER BY fm.is_admin DESC, pc.created_at ASC
                    LIMIT 1
                    """,
                    child_id,
                )

            return ParentalControls(**dict(row)) if row else None

    async def update_parental_controls(
        self,
        child_id: UUID,
        parent_id: UUID,
        update_data: ParentalControlsUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[ParentalControls]:
        """Update parental controls"""
        async with self.db.acquire() as conn:
            # Build dynamic update query
            update_fields = []
            values = []
            param_count = 1

            for field, value in update_data.dict(exclude_unset=True).items():
                if value is not None:
                    if hasattr(value, "value"):
                        value = value.value
                    update_fields.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1

            if not update_fields:
                return await self.get_parental_controls(child_id, parent_id)

            # Add updated_at
            update_fields.append(f"updated_at = ${param_count}")
            values.append(datetime.now())
            param_count += 1

            # Add child_id and parent_id for WHERE clause
            values.extend([child_id, parent_id])

            query = f"""
                UPDATE parental_controls
                SET {', '.join(update_fields)}
                WHERE child_id = ${param_count} AND parent_id = ${param_count + 1}
                RETURNING *
            """

            row = await conn.fetchrow(query, *values)

            if row:
                await self._create_audit_log(
                    conn,
                    user_id=updated_by,
                    action="update_parental_controls",
                    resource_type="parental_controls",
                    resource_id=row["id"],
                    details=update_data.dict(exclude_unset=True),
                )

            return ParentalControls(**dict(row)) if row else None

    # ==============================================================================
    # Screen Time Management
    # ==============================================================================

    async def update_screen_time(self, screen_time: ScreenTimeUpdate) -> ScreenTimeStatus:
        """Update screen time log and return status"""
        async with self.db.acquire() as conn:
            # Get or create today's log
            row = await conn.fetchrow(
                """
                INSERT INTO screen_time_logs (user_id, date, total_minutes, session_count, activity_breakdown)
                VALUES ($1, $2, $3, 1, $4::jsonb)
                ON CONFLICT (user_id, date)
                DO UPDATE SET
                    total_minutes = screen_time_logs.total_minutes + EXCLUDED.total_minutes,
                    session_count = screen_time_logs.session_count + 1,
                    activity_breakdown = jsonb_set(
                        screen_time_logs.activity_breakdown,
                        ARRAY[$5],
                        (COALESCE((screen_time_logs.activity_breakdown->>$5)::int, 0) + $3)::text::jsonb
                    ),
                    updated_at = NOW()
                RETURNING *
                """,
                screen_time.user_id,
                screen_time.date,
                screen_time.minutes_to_add,
                {screen_time.activity_type: screen_time.minutes_to_add},
                screen_time.activity_type,
            )

            log = ScreenTimeLog(**dict(row))

            # Get parental controls for limits
            controls = await self.get_parental_controls(screen_time.user_id)

            if controls and controls.screen_time_enabled:
                # Determine applicable limit
                is_weekend = screen_time.date.weekday() >= 5  # Saturday = 5, Sunday = 6
                if is_weekend and controls.weekend_limit_minutes:
                    limit = controls.weekend_limit_minutes
                elif not is_weekend and controls.weekday_limit_minutes:
                    limit = controls.weekday_limit_minutes
                else:
                    limit = controls.daily_limit_minutes

                # Check if in quiet hours
                in_quiet_hours = False
                if controls.quiet_hours_start and controls.quiet_hours_end:
                    now = datetime.now().time()
                    if controls.quiet_hours_start <= now <= controls.quiet_hours_end:
                        in_quiet_hours = True

                remaining = max(0, limit - log.total_minutes)
                percentage = (log.total_minutes / limit * 100) if limit > 0 else 0
                is_exceeded = log.total_minutes >= limit

                return ScreenTimeStatus(
                    user_id=screen_time.user_id,
                    date=screen_time.date,
                    total_minutes=log.total_minutes,
                    limit_minutes=limit,
                    remaining_minutes=remaining,
                    percentage_used=percentage,
                    is_limit_exceeded=is_exceeded,
                    in_quiet_hours=in_quiet_hours,
                )
            else:
                # No limits set
                return ScreenTimeStatus(
                    user_id=screen_time.user_id,
                    date=screen_time.date,
                    total_minutes=log.total_minutes,
                    limit_minutes=0,
                    remaining_minutes=0,
                    percentage_used=0,
                    is_limit_exceeded=False,
                    in_quiet_hours=False,
                )

    async def get_screen_time_log(self, user_id: UUID, date: date) -> Optional[ScreenTimeLog]:
        """Get screen time log for specific date"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM screen_time_logs WHERE user_id = $1 AND date = $2",
                user_id,
                date,
            )
            return ScreenTimeLog(**dict(row)) if row else None

    # ==============================================================================
    # Audit Logging
    # ==============================================================================

    async def _create_audit_log(
        self,
        conn: asyncpg.Connection,
        user_id: Optional[UUID],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> UUID:
        """Internal method to create audit log entry"""
        row = await conn.fetchrow(
            """
            INSERT INTO audit_log (
                user_id, action, resource_type, resource_id,
                details, success, error_message
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            user_id,
            action,
            resource_type,
            resource_id,
            details,
            success,
            error_message,
        )
        return row["id"]

    async def get_audit_logs(
        self,
        user_id: Optional[UUID] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Retrieve audit logs with optional filtering"""
        async with self.db.acquire() as conn:
            conditions = []
            values = []
            param_count = 1

            if user_id:
                conditions.append(f"user_id = ${param_count}")
                values.append(user_id)
                param_count += 1

            if action:
                conditions.append(f"action = ${param_count}")
                values.append(action)
                param_count += 1

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            values.append(limit)

            query = f"""
                SELECT * FROM audit_log
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${param_count}
            """

            rows = await conn.fetch(query, *values)
            return [AuditLog(**dict(row)) for row in rows]

    # ==============================================================================
    # Authentication Support Methods
    # ==============================================================================

    async def get_family_member_by_email(self, email: str) -> Optional[FamilyMember]:
        """Get family member by email address"""
        async with self.db.acquire() as conn:
            # Try users table first (for admin accounts)
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND is_active = true",
                email,
            )
            if row:
                # Convert users table row to FamilyMember format
                import uuid
                # Get password hash for authentication
                password_row = await conn.fetchrow(
                    "SELECT password_hash FROM users WHERE username = $1",
                    row["username"],
                )

                # Generate deterministic UUID based on user ID
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"user-{row['id']}")
                return FamilyMember(
                    id=str(user_uuid),  # Use deterministic UUID
                    username=row["username"],
                    first_name="Admin",  # Default for users table
                    last_name="User",
                    email=row["email"],
                    role="parent" if row["is_admin"] else "member",
                    age_group="adult",
                    language_preference="en",
                    hashed_password=password_row["password_hash"] if password_row else None,
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            # Try family_members table (for family accounts)
            row = await conn.fetchrow(
                "SELECT * FROM family_members WHERE username = $1 AND is_active = true",
                email,
            )
            if row:
                return FamilyMember(
                    id=str(row["id"]),
                    username=row["username"],
                    first_name=row["first_name"] or "",
                    last_name=row["last_name"] or "",
                    email=row["username"],  # Use username as email fallback
                    role=row["role"],
                    age_group=row["age_group"],
                    language_preference=row["language_preference"],
                    is_active=row["is_active"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            return None

    async def verify_password(self, user: FamilyMember, password: str) -> bool:
        """Verify password against stored hash"""
        async with self.db.acquire() as conn:
            # Get password hash from users table
            row = await conn.fetchrow(
                "SELECT password_hash FROM users WHERE username = $1",
                user.username,
            )
            if not row:
                # Try family_members table
                row = await conn.fetchrow(
                    "SELECT hashed_password FROM family_members WHERE username = $1",
                    user.username,
                )
                if not row:
                    return False
                stored_hash = row["hashed_password"]
            else:
                stored_hash = row["password_hash"]

            # Import bcrypt for password verification
            import bcrypt
            try:
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            except:
                return False
