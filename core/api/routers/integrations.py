"""
Platform Integrations API Routes

Endpoints for Home Assistant, Matrix, Voice, and other integrations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from ..dependencies import get_db, get_current_family
from ...models.database import FamilySettings

router = APIRouter()


@router.get("/home-assistant/status")
async def get_home_assistant_status(
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Check Home Assistant integration status."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings or not settings.ha_enabled:
        return {
            "enabled": False,
            "status": "not_configured",
            "message": "Home Assistant integration is not enabled"
        }

    # TODO: Add actual Home Assistant connection check
    # This would involve testing the connection to the HA instance

    return {
        "enabled": True,
        "configured": True,
        "connected": True,  # Placeholder - would check actual connection
        "ha_url": settings.ha_url,
        "entities_count": 0,  # Placeholder - would fetch from HA
        "status": "connected"
    }


@router.post("/home-assistant/configure")
async def configure_home_assistant(
    ha_config: Dict[str, Any],
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Configure Home Assistant integration."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings:
        settings = FamilySettings(family_id=current_family.id)
        db.add(settings)

    # Validate configuration
    required_fields = ["ha_url", "ha_token"]
    for field in required_fields:
        if field not in ha_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )

    # Update settings
    settings.ha_enabled = True
    settings.ha_url = ha_config["ha_url"]
    settings.ha_token = ha_config["ha_token"]

    db.commit()

    return {
        "status": "configured",
        "ha_url": settings.ha_url,
        "connected": True  # Placeholder - would test actual connection
    }


@router.get("/matrix/status")
async def get_matrix_status(
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Check Matrix integration status."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings or not settings.matrix_enabled:
        return {
            "enabled": False,
            "status": "not_configured",
            "message": "Matrix integration is not enabled"
        }

    # TODO: Add actual Matrix bot status check
    # This would involve checking if the bot is online and connected

    return {
        "enabled": True,
        "configured": True,
        "connected": True,  # Placeholder - would check actual bot status
        "homeserver": settings.matrix_homeserver,
        "bot_username": settings.matrix_bot_username,
        "status": "connected"
    }


@router.post("/matrix/configure")
async def configure_matrix(
    matrix_config: Dict[str, Any],
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Configure Matrix integration."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings:
        settings = FamilySettings(family_id=current_family.id)
        db.add(settings)

    # Validate configuration
    required_fields = ["homeserver", "bot_username"]
    for field in required_fields:
        if field not in matrix_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )

    # Update settings
    settings.matrix_enabled = True
    settings.matrix_homeserver = matrix_config["homeserver"]
    settings.matrix_bot_username = matrix_config["bot_username"]
    if "access_token" in matrix_config:
        settings.matrix_access_token = matrix_config["access_token"]

    db.commit()

    return {
        "status": "configured",
        "homeserver": settings.matrix_homeserver,
        "bot_username": settings.matrix_bot_username,
        "connected": True  # Placeholder - would test actual connection
    }


@router.get("/voice/status")
async def get_voice_service_status():
    """Check voice service status."""
    # TODO: Check if Whisper service is running and configured
    return {
        "enabled": True,
        "whisper_model": "small",
        "language": "es",
        "status": "ready",
        "capabilities": [
            "speech_to_text",
            "multilingual",
            "real_time"
        ]
    }


@router.post("/voice/configure")
async def configure_voice_service(
    voice_config: Dict[str, Any],
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Configure voice service settings."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    if not settings:
        settings = FamilySettings(family_id=current_family.id)
        db.add(settings)

    # Update voice settings
    if "wake_word" in voice_config:
        settings.voice_wake_word = voice_config["wake_word"]

    if "model" in voice_config:
        settings.preferred_llm_model = voice_config["model"]

    if "language" in voice_config:
        settings.preferred_language = voice_config["language"]

    db.commit()

    return {
        "status": "configured",
        "wake_word": settings.voice_wake_word,
        "model": settings.preferred_llm_model,
        "language": settings.preferred_language
    }


@router.get("/all/status")
async def get_all_integrations_status(
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Get status of all platform integrations."""
    settings = db.query(FamilySettings).filter(
        FamilySettings.family_id == current_family.id
    ).first()

    # TODO: Get actual status for each integration
    # For now, returning configured status based on settings

    return {
        "home_assistant": {
            "enabled": settings.ha_enabled if settings else False,
            "configured": settings.ha_enabled if settings else False,
            "connected": settings.ha_enabled if settings else False
        },
        "matrix": {
            "enabled": settings.matrix_enabled if settings else False,
            "configured": settings.matrix_enabled if settings else False,
            "connected": settings.matrix_enabled if settings else False
        },
        "voice": {
            "enabled": True,  # Voice is always available in our platform
            "configured": True,
            "connected": True,
            "model": "whisper-small"
        },
        "ai_engine": {
            "enabled": True,
            "configured": True,
            "connected": True,
            "model": settings.preferred_llm_model if settings else "local"
        }
    }


@router.post("/test/{integration}")
async def test_integration(
    integration: str,
    test_data: Optional[Dict[str, Any]] = None,
    current_family: Family = Depends(get_current_family),
    db: Session = Depends(get_db)
):
    """Test connection to a specific integration."""

    # TODO: Implement actual integration testing
    if integration == "home-assistant":
        # Test HA connection
        return {
            "status": "success",
            "integration": "home-assistant",
            "message": "Connection successful",
            "response_time": "150ms"
        }
    elif integration == "matrix":
        # Test Matrix bot connection
        return {
            "status": "success",
            "integration": "matrix",
            "message": "Bot is online and responsive",
            "response_time": "200ms"
        }
    elif integration == "voice":
        # Test voice service
        return {
            "status": "success",
            "integration": "voice",
            "message": "Whisper model loaded and ready",
            "model": "small",
            "language": "es"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown integration: {integration}"
        )