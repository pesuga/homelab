"""
Family-related Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class FamilyBase(BaseModel):
    name: str
    description: Optional[str] = None
    family_code: str
    timezone: str = "America/Mexico_City"
    primary_language: str = "es"
    secondary_language: str = "en"


class FamilyCreate(FamilyBase):
    pass


class FamilyResponse(FamilyBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class FamilyMemberBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    role: str  # parent, teenager, child, grandparent
    birth_year: Optional[int] = None
    preferred_language: str = "es"
    avatar_url: Optional[str] = None


class FamilyMemberCreate(FamilyMemberBase):
    password: Optional[str] = None


class FamilyMemberResponse(FamilyMemberBase):
    id: str
    family_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FamilyInteractionCreate(BaseModel):
    member_id: str
    type: str = "text"  # text, voice, command
    content: str
    response: Optional[str] = None
    context: Optional[dict] = {}
    language: str = "es"
    sentiment: str = "neutral"


class FamilyInteractionResponse(BaseModel):
    id: str
    family_id: str
    member_id: str
    member_name: str
    interaction_type: str
    content: str
    response: Optional[str]
    timestamp: datetime
    language: str
    sentiment: str
    processed: bool

    class Config:
        from_attributes = True


class FamilyMemoryCreate(BaseModel):
    category: str  # preference, schedule, event, knowledge
    title: str
    content: str
    importance: int = 5
    metadata: Optional[dict] = {}
    expires_at: Optional[datetime] = None


class FamilyMemoryResponse(FamilyMemoryCreate):
    id: str
    family_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FamilySettingsResponse(BaseModel):
    content_filter_enabled: bool
    parental_controls_enabled: bool
    blocked_topics: List[str]
    screen_time_limits: dict
    bedtime_hour: int
    wakeup_hour: int
    max_daily_interactions: int
    voice_wake_word: str
    ha_enabled: bool
    matrix_enabled: bool

    class Config:
        from_attributes = True