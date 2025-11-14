"""
User Management Models - Phase 3

Pydantic models for family members, roles, permissions, and parental controls.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum
from uuid import UUID


# ==============================================================================
# Enums
# ==============================================================================

class UserRole(str, Enum):
    """User role in family hierarchy"""
    PARENT = "parent"
    TEENAGER = "teenager"
    CHILD = "child"
    GRANDPARENT = "grandparent"
    MEMBER = "member"


class AgeGroup(str, Enum):
    """Age group classification"""
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"
    SENIOR = "senior"


class LanguagePreference(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    BILINGUAL = "bilingual"


class PrivacyLevel(str, Enum):
    """Conversation privacy levels"""
    PRIVATE = "private"
    FAMILY = "family"
    PARENTAL_ONLY = "parental_only"


class SafetyLevel(str, Enum):
    """Content safety levels"""
    CHILD = "child"
    TEEN = "teen"
    ADULT = "adult"


class ContentFilterLevel(str, Enum):
    """Content filtering strictness"""
    OFF = "off"
    MODERATE = "moderate"
    STRICT = "strict"


class FilterSeverity(str, Enum):
    """Content filter severity"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FilterAction(str, Enum):
    """Action taken by content filter"""
    BLOCKED = "blocked"
    WARNED = "warned"
    ALLOWED_WITH_WARNING = "allowed_with_warning"
    FLAGGED = "flagged"


# ==============================================================================
# Family Member Models
# ==============================================================================

class FamilyMemberBase(BaseModel):
    """Base family member data"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None

    role: UserRole
    age_group: Optional[AgeGroup] = None
    is_admin: bool = False

    language_preference: LanguagePreference = LanguagePreference.ENGLISH
    timezone: str = "America/Los_Angeles"
    theme_preference: str = "mocha"

    privacy_level: PrivacyLevel = PrivacyLevel.FAMILY
    safety_level: SafetyLevel = SafetyLevel.ADULT
    content_filtering_enabled: bool = True

    active_skills: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class FamilyMemberCreate(FamilyMemberBase):
    """Create new family member"""
    telegram_id: Optional[int] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)


class FamilyMemberUpdate(BaseModel):
    """Update family member"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None

    role: Optional[UserRole] = None
    age_group: Optional[AgeGroup] = None

    language_preference: Optional[LanguagePreference] = None
    timezone: Optional[str] = None
    theme_preference: Optional[str] = None

    privacy_level: Optional[PrivacyLevel] = None
    safety_level: Optional[SafetyLevel] = None
    content_filtering_enabled: Optional[bool] = None

    active_skills: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None


class FamilyMember(FamilyMemberBase):
    """Complete family member with DB fields"""
    id: UUID
    telegram_id: Optional[int] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None

    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================================================================
# Permission Models
# ==============================================================================

class Permission(BaseModel):
    """Permission definition"""
    id: UUID
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RolePermission(BaseModel):
    """Permission granted to role"""
    id: UUID
    role: UserRole
    permission_id: UUID
    granted: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class UserPermissionCreate(BaseModel):
    """Grant/revoke user permission"""
    user_id: UUID
    permission_name: str
    granted: bool = True
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserPermission(BaseModel):
    """User-specific permission override"""
    id: UUID
    user_id: UUID
    permission_id: UUID
    granted: bool
    granted_by: Optional[UUID] = None
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionCheck(BaseModel):
    """Permission check request/response"""
    user_id: UUID
    permission_name: str
    has_permission: bool
    reason: Optional[str] = None


# ==============================================================================
# Parental Control Models
# ==============================================================================

class ParentalControlsBase(BaseModel):
    """Base parental control settings"""
    # Screen Time
    screen_time_enabled: bool = False
    daily_limit_minutes: int = Field(120, ge=0, le=1440)
    weekday_limit_minutes: Optional[int] = Field(None, ge=0, le=1440)
    weekend_limit_minutes: Optional[int] = Field(None, ge=0, le=1440)
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

    # Content Filtering
    content_filter_level: ContentFilterLevel = ContentFilterLevel.STRICT
    blocked_keywords: List[str] = Field(default_factory=list)
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)

    # Monitoring
    activity_monitoring_enabled: bool = True
    conversation_review_enabled: bool = False
    location_sharing_enabled: bool = False

    # Notifications
    notify_parent_on_flagged_content: bool = True
    notify_parent_on_limit_exceeded: bool = True
    notify_parent_on_emergency: bool = True


class ParentalControlsCreate(ParentalControlsBase):
    """Create parental controls"""
    child_id: UUID
    parent_id: UUID


class ParentalControlsUpdate(BaseModel):
    """Update parental controls"""
    screen_time_enabled: Optional[bool] = None
    daily_limit_minutes: Optional[int] = Field(None, ge=0, le=1440)
    weekday_limit_minutes: Optional[int] = Field(None, ge=0, le=1440)
    weekend_limit_minutes: Optional[int] = Field(None, ge=0, le=1440)
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

    content_filter_level: Optional[ContentFilterLevel] = None
    blocked_keywords: Optional[List[str]] = None
    allowed_domains: Optional[List[str]] = None
    blocked_domains: Optional[List[str]] = None

    activity_monitoring_enabled: Optional[bool] = None
    conversation_review_enabled: Optional[bool] = None
    location_sharing_enabled: Optional[bool] = None

    notify_parent_on_flagged_content: Optional[bool] = None
    notify_parent_on_limit_exceeded: Optional[bool] = None
    notify_parent_on_emergency: Optional[bool] = None


class ParentalControls(ParentalControlsBase):
    """Complete parental controls with DB fields"""
    id: UUID
    child_id: UUID
    parent_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Screen Time Models
# ==============================================================================

class ScreenTimeLog(BaseModel):
    """Daily screen time tracking"""
    id: UUID
    user_id: UUID
    date: date
    total_minutes: int = 0
    session_count: int = 0
    activity_breakdown: Dict[str, int] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScreenTimeUpdate(BaseModel):
    """Update screen time log"""
    user_id: UUID
    date: date = Field(default_factory=date.today)
    minutes_to_add: int = Field(..., ge=1)
    activity_type: str = "general"


class ScreenTimeStatus(BaseModel):
    """Screen time status response"""
    user_id: UUID
    date: date
    total_minutes: int
    limit_minutes: int
    remaining_minutes: int
    percentage_used: float
    is_limit_exceeded: bool
    in_quiet_hours: bool


# ==============================================================================
# Content Filter Models
# ==============================================================================

class ContentFilterLogCreate(BaseModel):
    """Create content filter log"""
    user_id: UUID
    content_type: str  # message, search, image, url
    content_snippet: str = Field(..., max_length=500)
    filter_reason: str
    severity: FilterSeverity
    action_taken: FilterAction
    parent_notified: bool = False


class ContentFilterLog(BaseModel):
    """Content filter log entry"""
    id: UUID
    user_id: UUID
    content_type: str
    content_snippet: str
    filter_reason: str
    severity: FilterSeverity
    action_taken: FilterAction
    parent_notified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContentFilterCheck(BaseModel):
    """Content filter check request"""
    user_id: UUID
    content_type: str
    content: str


class ContentFilterResult(BaseModel):
    """Content filter result"""
    allowed: bool
    action: FilterAction
    reason: Optional[str] = None
    severity: Optional[FilterSeverity] = None
    filtered_content: Optional[str] = None


# ==============================================================================
# Family Relationship Models
# ==============================================================================

class FamilyRelationshipCreate(BaseModel):
    """Create family relationship"""
    user_id: UUID
    related_user_id: UUID
    relationship_type: str  # parent, child, sibling, grandparent, etc.
    is_primary: bool = False

    @validator('user_id', 'related_user_id')
    def ids_must_be_different(cls, v, values):
        if 'user_id' in values and v == values['user_id']:
            raise ValueError('user_id and related_user_id must be different')
        return v


class FamilyRelationship(BaseModel):
    """Family relationship"""
    id: UUID
    user_id: UUID
    related_user_id: UUID
    relationship_type: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# User Preference Models
# ==============================================================================

class UserPreferencesBase(BaseModel):
    """User preference settings"""
    # Communication
    prompt_style: str = Field("balanced", pattern="^(brief|balanced|detailed)$")
    response_length: str = Field("medium", pattern="^(short|medium|long)$")
    formality_level: str = Field("casual", pattern="^(formal|balanced|casual)$")
    emoji_usage: str = Field("moderate", pattern="^(none|minimal|moderate|frequent)$")

    # Notifications
    notification_email: bool = True
    notification_telegram: bool = True
    notification_quiet_hours_start: Optional[time] = None
    notification_quiet_hours_end: Optional[time] = None

    # Assistant behavior
    proactive_suggestions: bool = True
    context_awareness_level: str = Field("high", pattern="^(low|medium|high)$")
    memory_retention_days: int = Field(90, ge=1, le=365)

    # UI
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict)
    favorite_skills: List[str] = Field(default_factory=list)


class UserPreferencesUpdate(BaseModel):
    """Update user preferences"""
    prompt_style: Optional[str] = Field(None, pattern="^(brief|balanced|detailed)$")
    response_length: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    formality_level: Optional[str] = Field(None, pattern="^(formal|balanced|casual)$")
    emoji_usage: Optional[str] = Field(None, pattern="^(none|minimal|moderate|frequent)$")

    notification_email: Optional[bool] = None
    notification_telegram: Optional[bool] = None
    notification_quiet_hours_start: Optional[time] = None
    notification_quiet_hours_end: Optional[time] = None

    proactive_suggestions: Optional[bool] = None
    context_awareness_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    memory_retention_days: Optional[int] = Field(None, ge=1, le=365)

    dashboard_layout: Optional[Dict[str, Any]] = None
    favorite_skills: Optional[List[str]] = None


class UserPreferences(UserPreferencesBase):
    """User preferences with DB fields"""
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Audit Log Models
# ==============================================================================

class AuditLogCreate(BaseModel):
    """Create audit log entry"""
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class AuditLog(BaseModel):
    """Audit log entry"""
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# API Response Models
# ==============================================================================

class FamilyMemberListResponse(BaseModel):
    """List of family members response"""
    members: List[FamilyMember]
    total: int


class PermissionListResponse(BaseModel):
    """List of permissions response"""
    permissions: List[Permission]
    total: int


class ParentalControlsListResponse(BaseModel):
    """List of parental controls response"""
    controls: List[ParentalControls]
    total: int


class ScreenTimeReport(BaseModel):
    """Screen time report"""
    user_id: UUID
    start_date: date
    end_date: date
    total_minutes: int
    average_minutes_per_day: float
    daily_logs: List[ScreenTimeLog]


class ContentFilterReport(BaseModel):
    """Content filter report"""
    user_id: UUID
    start_date: date
    end_date: date
    total_filtered: int
    by_severity: Dict[str, int]
    by_action: Dict[str, int]
    recent_logs: List[ContentFilterLog]


# ==============================================================================
# Validation and Helper Models
# ==============================================================================

class BulkPermissionUpdate(BaseModel):
    """Bulk update permissions for users"""
    user_ids: List[UUID]
    permission_names: List[str]
    granted: bool
    reason: Optional[str] = None


class FamilyInviteRequest(BaseModel):
    """Invite family member"""
    email: Optional[EmailStr] = None
    telegram_id: Optional[int] = None
    role: UserRole
    relationship_type: str
    message: Optional[str] = None


class FamilyInviteResponse(BaseModel):
    """Family invite response"""
    invite_id: UUID
    status: str  # pending, accepted, rejected, expired
    expires_at: datetime
