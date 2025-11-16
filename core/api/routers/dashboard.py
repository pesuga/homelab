"""
Dashboard API Routes

Endpoints for family dashboard, analytics, and web interface management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..dependencies import get_db, get_current_member, CurrentMember
from ..schemas.dashboard import (
    DashboardResponse, WidgetDataResponse, DashboardAlertResponse,
    FamilyAnalyticsResponse, ActivityFeedResponse
)
from ...services.dashboard_service import DashboardService, DashboardAlert
from ...services.family_context import FamilyContextService
from ...services.memory_service import MemoryService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=DashboardResponse)
async def get_family_dashboard(
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get family dashboard configuration and widgets.

    Returns role-appropriate dashboard layout with widgets and permissions.
    """
    try:
        # Initialize dashboard service
        dashboard_service = DashboardService(db)

        # Get family dashboard
        dashboard = await dashboard_service.get_family_dashboard(
            family_id=current_member.family_id,
            member_role=current_member.role
        )

        # Convert to response format
        return DashboardResponse(
            family_id=dashboard.family_id,
            family_name=dashboard.family_name,
            layout=[widget.dict() for widget in dashboard.layout],
            permissions=dashboard.permissions,
            theme=dashboard.theme,
            last_updated=dashboard.last_updated
        )

    except Exception as e:
        logger.error(f"Failed to get family dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard"
        )

@router.get("/widgets/{widget_id}/data", response_model=WidgetDataResponse)
async def get_widget_data(
    widget_id: str,
    family_id: Optional[str] = None,
    limit: Optional[int] = None,
    period: Optional[str] = None,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get data for a specific dashboard widget.

    Supports various widget types: activity-feed, family-summary, sentiment-chart, etc.
    """
    try:
        # Verify family access
        target_family_id = family_id or current_member.family_id
        if target_family_id != current_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Initialize dashboard service
        dashboard_service = DashboardService(db)

        # Get widget data
        params = {}
        if limit:
            params["limit"] = limit
        if period:
            params["period"] = period
        if family_id:
            params["family_id"] = family_id

        widget_data = await dashboard_service.get_dashboard_data(
            widget_id=widget_id,
            family_id=target_family_id,
            **params
        )

        if "error" in widget_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Widget not found: {widget_id}"
            )

        return WidgetDataResponse(
            widget_id=widget_id,
            data=widget_data,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get widget data for {widget_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve widget data"
        )

@router.get("/activity", response_model=ActivityFeedResponse)
async def get_activity_feed(
    limit: int = 20,
    family_id: Optional[str] = None,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get recent family activity feed.

    Shows messages, voice interactions, memories, and system events.
    """
    try:
        # Verify family access
        target_family_id = family_id or current_member.family_id
        if target_family_id != current_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Initialize dashboard service
        dashboard_service = DashboardService(db)

        # Get activity feed
        activity_data = await dashboard_service.get_dashboard_data(
            widget_id="recent-activity",
            family_id=target_family_id,
            limit=limit
        )

        activities = activity_data.get("activities", [])

        return ActivityFeedResponse(
            activities=activities,
            total_count=len(activities),
            family_id=target_family_id,
            last_updated=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get activity feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity feed"
        )

@router.get("/analytics", response_model=FamilyAnalyticsResponse)
async def get_family_analytics(
    period: str = "30d",
    family_id: Optional[str] = None,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get family analytics and insights.

    Only available to parents and grandparents.
    """
    try:
        # Check permissions
        if current_member.role not in ["parent", "grandparent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parental access required for analytics"
            )

        # Verify family access
        target_family_id = family_id or current_member.family_id
        if target_family_id != current_member.family_id and current_member.role != "grandparent":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Initialize dashboard service
        dashboard_service = DashboardService(db)

        # Get various analytics data
        summary_data = await dashboard_service.get_dashboard_data(
            widget_id="family-summary",
            family_id=target_family_id
        )

        usage_data = await dashboard_service.get_dashboard_data(
            widget_id="usage-analytics",
            family_id=target_family_id,
            period=period
        )

        sentiment_data = await dashboard_service.get_dashboard_data(
            widget_id="sentiment-chart",
            family_id=target_family_id,
            period=period
        )

        return FamilyAnalyticsResponse(
            family_id=target_family_id,
            period=period,
            summary_metrics=summary_data.get("metrics", []),
            sentiment_analysis=sentiment_data,
            usage_analytics=usage_data,
            generated_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get family analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )

@router.post("/alerts", response_model=DashboardAlertResponse)
async def create_dashboard_alert(
    alert_type: str,
    title: str,
    message: str,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Create a dashboard alert.

    Used by system processes and automated monitoring.
    """
    try:
        # Initialize dashboard service
        dashboard_service = DashboardService(db)

        # Create alert
        alert = await dashboard_service.create_alert(
            family_id=current_member.family_id,
            alert_type=alert_type,
            title=title,
            message=message
        )

        return DashboardAlertResponse(
            id=alert.id,
            type=alert.type,
            title=alert.title,
            message=alert.message,
            timestamp=alert.timestamp,
            acknowledged=alert.acknowledged,
            family_id=alert.family_id
        )

    except Exception as e:
        logger.error(f"Failed to create dashboard alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a dashboard alert.
    """
    try:
        # Initialize dashboard service
        dashboard_service = DashboardService(db)

        # Acknowledge alert
        success = await dashboard_service.acknowledge_alert(
            alert_id=alert_id,
            family_id=current_member.family_id
        )

        if success:
            return {"message": "Alert acknowledged successfully", "alert_id": alert_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )

@router.get("/memories")
async def get_family_memories(
    limit: int = 50,
    category: Optional[str] = None,
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get family memories for dashboard display.
    """
    try:
        # Initialize services
        dashboard_service = DashboardService(db)
        memory_service = MemoryService()

        # Get memory data
        memory_data = await dashboard_service.get_dashboard_data(
            widget_id="memory-browser",
            family_id=current_member.family_id,
            limit=limit
        )

        # Also try to get from Mem0 service if available
        try:
            if await memory_service.health_check():
                mem0_memories = await memory_service.get_family_memories(
                    family_id=current_member.family_id,
                    category=category,
                    limit=limit
                )

                # Combine dashboard data with Mem0 data
                combined_memories = memory_data.get("memories", [])
                if mem0_memories:
                    combined_memories.extend(mem0_memories[:10])  # Add some from Mem0

                return {
                    "memories": combined_memories,
                    "total_count": len(combined_memories),
                    "sources": ["database", "mem0"]
                }
        except:
            pass  # Fall back to dashboard data only

        return {
            "memories": memory_data.get("memories", []),
            "total_count": memory_data.get("total_count", 0),
            "categories": memory_data.get("categories", {}),
            "sources": ["database"]
        }

    except Exception as e:
        logger.error(f"Failed to get family memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memories"
        )

@router.get("/settings")
async def get_dashboard_settings(
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Get dashboard settings and preferences for the current user.
    """
    try:
        # Initialize family context service
        family_context_service = FamilyContextService()

        # Get user and family settings
        family_settings = family_context_service.get_family_settings(current_member.family_id)

        # Default dashboard settings
        dashboard_settings = {
            "theme": "light",
            "language": current_member.preferences.get("preferred_language", "es"),
            "auto_refresh": True,
            "refresh_interval": 30,  # seconds
            "notifications": {
                "enabled": True,
                "alerts": True,
                "new_messages": True,
                "voice_activity": False
            },
            "widgets": {
                "expanded": ["recent-activity", "quick-chat"],
                "collapsed": [],
                "hidden": []
            },
            "privacy": {
                "show_member_names": True,
                "show_timestamps": True,
                "anonymize_others": False
            }
        }

        return {
            "user_preferences": current_member.preferences or {},
            "family_settings": family_settings,
            "dashboard_settings": dashboard_settings,
            "available_themes": ["light", "dark", "auto"],
            "available_languages": ["es", "en"]
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard settings"
        )

@router.put("/settings")
async def update_dashboard_settings(
    settings: Dict[str, Any],
    current_member: CurrentMember = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    Update dashboard settings and preferences.
    """
    try:
        # Validate settings
        allowed_settings = [
            "theme", "language", "auto_refresh", "refresh_interval",
            "notifications", "widgets", "privacy"
        ]

        for key in settings:
            if key not in allowed_settings:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid setting: {key}"
                )

        # Update member preferences
        if not current_member.preferences:
            current_member.preferences = {}

        current_member.preferences.update(settings)
        db.commit()

        return {"message": "Dashboard settings updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update dashboard settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update dashboard settings"
        )

@router.get("/status")
async def get_dashboard_status(
    current_member: CurrentMember = Depends(get_current_member)
):
    """
    Get dashboard system status and health information.
    """
    try:
        # Check service health
        services = {
            "database": "healthy",  # Assuming database is healthy if we're here
            "memory_service": "unknown",
            "voice_service": "unknown",
            "matrix_service": "unknown"
        }

        # Try to check memory service
        try:
            memory_service = MemoryService()
            if await memory_service.health_check():
                services["memory_service"] = "healthy"
            else:
                services["memory_service"] = "unhealthy"
        except:
            services["memory_service"] = "unhealthy"

        return {
            "status": "healthy" if all(s == "healthy" for s in services.values() if s != "unknown") else "degraded",
            "services": services,
            "last_updated": datetime.now(),
            "version": "1.0.0",
            "features": {
                "voice_interactions": services["voice_service"] == "healthy",
                "matrix_integration": services["matrix_service"] == "healthy",
                "memory_search": services["memory_service"] == "healthy",
                "real_time_updates": True,
                "multi_language": True
            }
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard status"
        )