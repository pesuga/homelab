"""
Privacy and Parental Controls API Routes

Endpoints for content filtering, parental controls, and privacy management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..dependencies import get_db, get_current_family
from ...models.database import FamilySettings

router = APIRouter()


class ContentFilterSettings(BaseModel):
    enabled: bool
    blocked_topics: List[str]
    allowed_topics: List[str]
    strictness_level: int = 5  # 1-10, 10 being most strict


class ParentalControlSettings(BaseModel):
    enabled: bool
    member_restrictions: dict  # Per-member restrictions
    screen_time_limits: dict
    bedtime_hour: int = 21
    wakeup_hour: int = 7
    max_daily_interactions: int = 100


class PrivacySettings(BaseModel):
    data_retention_days: int = 365
    share_anonymous_usage: bool = False
    location_tracking: bool = False
    voice_data_retention: bool = True


@router.get("/settings", response_model=dict)
async def get_privacy_settings(
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Get current privacy and parental control settings."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings:
        # Create default settings
        settings = FamilySettings(family_id=current_family.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "content_filter": {
            "enabled": settings.content_filter_enabled,
            "blocked_topics": settings.blocked_topics or [],
            "strictness_level": 5
        },
        "parental_controls": {
            "enabled": settings.parental_controls_enabled,
            "screen_time_limits": settings.screen_time_limits or {},
            "bedtime_hour": settings.bedtime_hour,
            "wakeup_hour": settings.wakeup_hour,
            "max_daily_interactions": settings.max_daily_interactions
        },
        "privacy": {
            "data_retention_days": 365,
            "share_anonymous_usage": False,
            "location_tracking": False,
            "voice_data_retention": settings.voice_wake_word is not None
        }
    }


@router.put("/settings")
async def update_privacy_settings(
    settings_data: dict,
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Update privacy and parental control settings."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings:
        settings = FamilySettings(family_id=current_family.id)
        db.add(settings)

    # Update content filter settings
    if "content_filter" in settings_data:
        cf = settings_data["content_filter"]
        settings.content_filter_enabled = cf.get("enabled", True)
        settings.blocked_topics = cf.get("blocked_topics", [])

    # Update parental controls
    if "parental_controls" in settings_data:
        pc = settings_data["parental_controls"]
        settings.parental_controls_enabled = pc.get("enabled", True)
        settings.screen_time_limits = pc.get("screen_time_limits", {})
        settings.bedtime_hour = pc.get("bedtime_hour", 21)
        settings.wakeup_hour = pc.get("wakeup_hour", 7)
        settings.max_daily_interactions = pc.get("max_daily_interactions", 100)

    # Update voice settings
    if "voice" in settings_data:
        voice = settings_data["voice"]
        settings.voice_wake_word = voice.get("wake_word", "hola familia")

    db.commit()
    db.refresh(settings)

    return {"status": "updated", "settings": settings_data}


@router.post("/content/filter")
async def check_content_safety(
    content_check: dict,
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Check if content is safe based on family settings."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings or not settings.content_filter_enabled:
        return {"safe": True, "reason": "Content filtering disabled"}

    content = content_check.get("content", "").lower()
    blocked_topics = settings.blocked_topics or []

    # Simple keyword-based filtering
    for topic in blocked_topics:
        if topic.lower() in content:
            return {
                "safe": False,
                "reason": f"Content contains blocked topic: {topic}",
                "blocked_topic": topic
            }

    # Additional safety checks can be added here
    # - ML-based content classification
    # - Age-appropriate content checking
    # - Cultural context filtering

    return {"safe": True, "reason": "Content passed safety checks"}


@router.get("/usage/stats")
async def get_usage_statistics(
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Get family usage statistics for parental monitoring."""
    from ...models.database import FamilyInteraction
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta

    # Get today's interactions
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())

    daily_interactions = db.query(FamilyInteraction).filter(
        and_(
            FamilyInteraction.family_id == current_family.id,
            FamilyInteraction.timestamp >= today_start
        )
    ).count()

    # Get interactions by member
    member_stats = db.query(
        FamilyMember.name,
        func.count(FamilyInteraction.id).label("interaction_count")
    ).join(
        FamilyInteraction, FamilyMember.id == FamilyInteraction.member_id
    ).filter(
        and_(
            FamilyInteraction.family_id == current_family.id,
            FamilyInteraction.timestamp >= today_start
        )
    ).group_by(FamilyMember.id, FamilyMember.name).all()

    # Get interaction types distribution
    interaction_types = db.query(
        FamilyInteraction.interaction_type,
        func.count(FamilyInteraction.id).label("count")
    ).filter(
        and_(
            FamilyInteraction.family_id == current_family.id,
            FamilyInteraction.timestamp >= today_start
        )
    ).group_by(FamilyInteraction.interaction_type).all()

    return {
        "daily_interactions": daily_interactions,
        "member_stats": [
            {"name": name, "interactions": count}
            for name, count in member_stats
        ],
        "interaction_types": [
            {"type": itype, "count": count}
            for itype, count in interaction_types
        ],
        "date": today.isoformat()
    }


@router.delete("/data/cleanup")
async def cleanup_old_data(
    days: int = 365,
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Clean up old family data according to privacy settings."""
    from ...models.database import FamilyInteraction, FamilyMemory
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=days)

    # Delete old interactions
    deleted_interactions = db.query(FamilyInteraction).filter(
        and_(
            FamilyInteraction.family_id == current_family.id,
            FamilyInteraction.timestamp < cutoff_date
        )
    ).delete()

    # Delete old memories
    deleted_memories = db.query(FamilyMemory).filter(
        and_(
            FamilyMemory.family_id == current_family.id,
            FamilyMemory.created_at < cutoff_date,
            FamilyMemory.expires_at.isnot(None)
        )
    ).delete()

    db.commit()

    return {
        "status": "completed",
        "deleted_interactions": deleted_interactions,
        "deleted_memories": deleted_memories,
        "cutoff_date": cutoff_date.isoformat()
    }