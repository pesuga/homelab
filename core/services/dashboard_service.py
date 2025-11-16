"""
Dashboard Service

Web dashboard service for family management and interaction interface.
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
from sqlalchemy import extract

logger = logging.getLogger(__name__)

class DashboardWidget(BaseModel):
    id: str
    type: str  # chart, metric, list, alert, etc.
    title: str
    data: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: Optional[int] = None  # seconds

class FamilyDashboard(BaseModel):
    family_id: str
    family_name: str
    layout: List[DashboardWidget]
    last_updated: datetime
    theme: str = "light"
    permissions: Dict[str, List[str]]  # role -> allowed widgets

class DashboardMetric(BaseModel):
    name: str
    value: float
    unit: str
    trend: Optional[float] = None  # percentage change
    status: str = "normal"  # normal, warning, critical

class DashboardAlert(BaseModel):
    id: str
    type: str  # info, warning, error, success
    title: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    family_id: str

class ActivityFeedItem(BaseModel):
    id: str
    type: str  # message, voice, memory, system
    title: str
    description: str
    timestamp: datetime
    member_name: Optional[str] = None
    metadata: Dict[str, Any] = {}

class DashboardService:
    """Service for managing family dashboards and web interface."""

    def __init__(self, db_session):
        self.db = db_session

    async def get_family_dashboard(self, family_id: str, member_role: str) -> FamilyDashboard:
        """Get dashboard configuration for a family."""
        try:
            # Get family information
            try:
                from ..models.database import Family
            except ImportError:
                from models.database import Family
            family = self.db.query(Family).filter(Family.id == family_id).first()
            if not family:
                raise Exception("Family not found")

            # Create default widgets based on family role
            widgets = self._create_default_widgets(member_role, family_id)

            # Define permissions by role
            permissions = self._get_role_permissions(member_role)

            dashboard = FamilyDashboard(
                family_id=family_id,
                family_name=family.name,
                layout=widgets,
                last_updated=datetime.now(),
                permissions=permissions
            )

            return dashboard

        except Exception as e:
            logger.error(f"Failed to get family dashboard: {e}")
            raise

    def _create_default_widgets(self, role: str, family_id: str) -> List[DashboardWidget]:
        """Create default dashboard widgets based on user role."""
        widgets = []

        # Common widgets for all roles
        widgets.extend([
            DashboardWidget(
                id="recent-activity",
                type="activity-feed",
                title="Actividad Reciente / Recent Activity",
                data={"limit": 10, "family_id": family_id},
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                refresh_interval=30
            ),
            DashboardWidget(
                id="quick-chat",
                type="chat-widget",
                title="Chat Familiar / Family Chat",
                data={"placeholder": "Escribe un mensaje..."},
                position={"x": 6, "y": 0, "width": 6, "height": 4}
            )
        ])

        # Parent-specific widgets
        if role in ["parent", "grandparent"]:
            widgets.extend([
                DashboardWidget(
                    id="family-summary",
                    type="summary-metrics",
                    title="Resumen Familiar / Family Summary",
                    data={},
                    position={"x": 0, "y": 4, "width": 4, "height": 3},
                    refresh_interval=60
                ),
                DashboardWidget(
                    id="sentiment-chart",
                    type="sentiment-chart",
                    title="Estado de Ánimo / Sentiment Analysis",
                    data={"period": "7d"},
                    position={"x": 4, "y": 4, "width": 4, "height": 3},
                    refresh_interval=300
                ),
                DashboardWidget(
                    id="parental-controls",
                    type="controls-panel",
                    title="Controles Parentales / Parental Controls",
                    data={},
                    position={"x": 8, "y": 4, "width": 4, "height": 3}
                ),
                DashboardWidget(
                    id="memory-browser",
                    type="memory-list",
                    title="Memorias Familiares / Family Memories",
                    data={"limit": 20},
                    position={"x": 0, "y": 7, "width": 6, "height": 4},
                    refresh_interval=120
                ),
                DashboardWidget(
                    id="usage-analytics",
                    type="usage-chart",
                    title="Estadísticas de Uso / Usage Analytics",
                    data={"period": "30d"},
                    position={"x": 6, "y": 7, "width": 6, "height": 4},
                    refresh_interval=600
                )
            ])

        # Child/teenager-specific widgets
        elif role == "teenager":
            widgets.extend([
                DashboardWidget(
                    id="my-stats",
                    type="personal-metrics",
                    title="Mis Estadísticas / My Stats",
                    data={},
                    position={"x": 0, "y": 4, "width": 6, "height": 3},
                    refresh_interval=60
                ),
                DashboardWidget(
                    id="study-helper",
                    type="study-tools",
                    title="Ayuda con Estudios / Study Helper",
                    data={},
                    position={"x": 6, "y": 4, "width": 6, "height": 3}
                )
            ])

        elif role == "child":
            widgets.extend([
                DashboardWidget(
                    id="fun-activities",
                    type="activity-suggestions",
                    title="Actividades Divertidas / Fun Activities",
                    data={"age_group": "child"},
                    position={"x": 0, "y": 4, "width": 12, "height": 3},
                    refresh_interval=300
                )
            ])

        return widgets

    def _get_role_permissions(self, role: str) -> Dict[str, List[str]]:
        """Get widget permissions by role."""
        permissions = {
            "parent": [
                "recent-activity", "quick-chat", "family-summary", "sentiment-chart",
                "parental-controls", "memory-browser", "usage-analytics"
            ],
            "grandparent": [
                "recent-activity", "quick-chat", "family-summary", "sentiment-chart",
                "memory-browser", "usage-analytics"
            ],
            "teenager": [
                "recent-activity", "quick-chat", "my-stats", "study-helper"
            ],
            "child": [
                "recent-activity", "quick-chat", "fun-activities"
            ]
        }
        return permissions.get(role, [])

    async def get_dashboard_data(self, widget_id: str, family_id: str, **params) -> Dict[str, Any]:
        """Get data for a specific dashboard widget."""
        try:
            if widget_id == "recent-activity":
                return await self._get_activity_feed(family_id, limit=params.get("limit", 10))

            elif widget_id == "family-summary":
                return await self._get_family_summary_metrics(family_id)

            elif widget_id == "sentiment-chart":
                return await self._get_sentiment_data(family_id, period=params.get("period", "7d"))

            elif widget_id == "memory-browser":
                return await self._get_memory_data(family_id, limit=params.get("limit", 20))

            elif widget_id == "usage-analytics":
                return await self._get_usage_analytics(family_id, period=params.get("period", "30d"))

            elif widget_id == "my-stats":
                return await self._get_personal_stats(family_id, member_id=params.get("member_id"))

            elif widget_id == "activity-suggestions":
                return await self._get_activity_suggestions(age_group=params.get("age_group", "child"))

            else:
                return {"error": f"Unknown widget type: {widget_id}"}

        except Exception as e:
            logger.error(f"Failed to get dashboard data for {widget_id}: {e}")
            return {"error": str(e)}

    async def _get_activity_feed(self, family_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent activity feed."""
        try:
            # Get recent interactions from database
            try:
                from ..models.database import FamilyInteraction, FamilyMember
            except ImportError:
                from models.database import FamilyInteraction, FamilyMember
            from sqlalchemy import desc

            interactions = self.db.query(FamilyInteraction).join(FamilyMember).filter(
                FamilyInteraction.family_id == family_id
            ).order_by(desc(FamilyInteraction.timestamp)).limit(limit).all()

            activities = []
            for interaction in interactions:
                activity = ActivityFeedItem(
                    id=interaction.id,
                    type=interaction.interaction_type,
                    title=f"Mensaje de {interaction.member.name}",
                    description=interaction.content[:100] + "..." if len(interaction.content) > 100 else interaction.content,
                    timestamp=interaction.timestamp,
                    member_name=interaction.member.name,
                    metadata={"language": interaction.language, "sentiment": interaction.sentiment}
                )
                activities.append(activity)

            return {"activities": [activity.dict() for activity in activities]}

        except Exception as e:
            logger.error(f"Failed to get activity feed: {e}")
            return {"activities": []}

    async def _get_family_summary_metrics(self, family_id: str) -> Dict[str, Any]:
        """Get family summary metrics."""
        try:
            try:
                from ..models.database import FamilyInteraction
            except ImportError:
                from models.database import FamilyInteraction
            from sqlalchemy import func, desc
            from datetime import datetime, timedelta

            # Get stats for last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)

            total_interactions = self.db.query(FamilyInteraction).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= seven_days_ago
            ).count()

            # Sentiment distribution
            sentiments = self.db.query(
                FamilyInteraction.sentiment,
                func.count(FamilyInteraction.id).label('count')
            ).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= seven_days_ago
            ).group_by(FamilyInteraction.sentiment).all()

            sentiment_counts = {s[0]: s[1] for s in sentiments}

            # Most active member
            most_active = self.db.query(
                FamilyInteraction.family_member_id,
                func.count(FamilyInteraction.id).label('count')
            ).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= seven_days_ago
            ).group_by(FamilyInteraction.family_member_id).order_by(desc('count')).first()

            # Language distribution
            languages = self.db.query(
                FamilyInteraction.language,
                func.count(FamilyInteraction.id).label('count')
            ).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= seven_days_ago
            ).group_by(FamilyInteraction.language).all()

            language_counts = {l[0]: l[1] for l in languages}

            metrics = [
                DashboardMetric(name="Interacciones 7 días", value=total_interactions, unit="mensajes"),
                DashboardMetric(name="Promedio diario", value=total_interactions/7, unit="mensajes/día"),
                DashboardMetric(name="Sentimiento positivo", value=sentiment_counts.get("positive", 0), unit="mensajes"),
                DashboardMetric(name="Miembros activos", value=len(sentiments), unit="personas")
            ]

            return {
                "metrics": [metric.dict() for metric in metrics],
                "sentiment_distribution": sentiment_counts,
                "language_distribution": language_counts,
                "most_active_member_id": most_active[0] if most_active else None
            }

        except Exception as e:
            logger.error(f"Failed to get family summary: {e}")
            return {"metrics": []}

    async def _get_sentiment_data(self, family_id: str, period: str = "7d") -> Dict[str, Any]:
        """Get sentiment analysis data for charting."""
        try:
            from models.database import FamilyInteraction
            from sqlalchemy import func, extract
            from datetime import datetime, timedelta

            # Calculate date range
            days_map = {"1d": 1, "7d": 7, "30d": 30}
            days = days_map.get(period, 7)
            start_date = datetime.now() - timedelta(days=days)

            # Group by day and sentiment
            daily_sentiments = self.db.query(
                extract('day', FamilyInteraction.timestamp).label('day'),
                extract('month', FamilyInteraction.timestamp).label('month'),
                FamilyInteraction.sentiment,
                func.count(FamilyInteraction.id).label('count')
            ).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= start_date
            ).group_by(
                extract('day', FamilyInteraction.timestamp),
                extract('month', FamilyInteraction.timestamp),
                FamilyInteraction.sentiment
            ).all()

            # Format for charting
            chart_data = {
                "labels": [],
                "positive": [],
                "neutral": [],
                "negative": []
            }

            # This is simplified - in production, we'd handle date formatting better
            for record in daily_sentiments:
                day_str = f"{int(record.month)}/{int(record.day)}"
                if day_str not in chart_data["labels"]:
                    chart_data["labels"].append(day_str)

                index = chart_data["labels"].index(day_str)
                while len(chart_data["positive"]) <= index:
                    chart_data["positive"].append(0)
                    chart_data["neutral"].append(0)
                    chart_data["negative"].append(0)

                if record.sentiment == "positive":
                    chart_data["positive"][index] = record.count
                elif record.sentiment == "neutral":
                    chart_data["neutral"][index] = record.count
                elif record.sentiment == "negative":
                    chart_data["negative"][index] = record.count

            return {
                "chart_data": chart_data,
                "period": period,
                "total_days": days
            }

        except Exception as e:
            logger.error(f"Failed to get sentiment data: {e}")
            return {"chart_data": {"labels": [], "positive": [], "neutral": [], "negative": []}}

    async def _get_memory_data(self, family_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get memory data for family."""
        try:
            # This would integrate with Mem0 service
            # For now, return mock data structure
            return {
                "memories": [
                    {
                        "id": "mem-1",
                        "title": "Cumpleaños de María",
                        "content": "A María le gustó mucho el pastel de chocolate",
                        "category": "event",
                        "importance": 8,
                        "created_at": "2025-01-10T15:30:00Z"
                    },
                    {
                        "id": "mem-2",
                        "title": "Prefiere jugar al fútbol",
                        "content": "Carlos prefiere jugar al fútbol que al básquetbol",
                        "category": "preference",
                        "importance": 6,
                        "created_at": "2025-01-09T18:45:00Z"
                    }
                ],
                "total_count": 2,
                "categories": {"event": 1, "preference": 1}
            }

        except Exception as e:
            logger.error(f"Failed to get memory data: {e}")
            return {"memories": [], "total_count": 0}

    async def _get_usage_analytics(self, family_id: str, period: str = "30d") -> Dict[str, Any]:
        """Get usage analytics data."""
        try:
            from models.database import FamilyInteraction, FamilyMember
            from sqlalchemy import func
            from datetime import datetime, timedelta

            days_map = {"7d": 7, "30d": 30, "90d": 90}
            days = days_map.get(period, 30)
            start_date = datetime.now() - timedelta(days=days)

            # Activity by member
            member_activity = self.db.query(
                FamilyMember.name,
                func.count(FamilyInteraction.id).label('interactions')
            ).join(FamilyInteraction).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= start_date
            ).group_by(FamilyMember.name).all()

            # Activity by hour
            hourly_activity = self.db.query(
                extract('hour', FamilyInteraction.timestamp).label('hour'),
                func.count(FamilyInteraction.id).label('count')
            ).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= start_date
            ).group_by(extract('hour', FamilyInteraction.timestamp)).all()

            return {
                "member_activity": [{"name": name, "interactions": count} for name, count in member_activity],
                "hourly_activity": [{"hour": int(hour), "count": count} for hour, count in hourly_activity],
                "period": period
            }

        except Exception as e:
            logger.error(f"Failed to get usage analytics: {e}")
            return {"member_activity": [], "hourly_activity": []}

    async def _get_personal_stats(self, family_id: str, member_id: Optional[str] = None) -> Dict[str, Any]:
        """Get personal statistics for a family member."""
        try:
            from models.database import FamilyInteraction
            from sqlalchemy import func
            from datetime import datetime, timedelta

            if not member_id:
                return {"error": "member_id required"}

            # Personal stats for last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)

            total_interactions = self.db.query(FamilyInteraction).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.family_member_id == member_id,
                FamilyInteraction.timestamp >= thirty_days_ago
            ).count()

            avg_sentiment = self.db.query(
                func.avg(
                    func.case(
                        (FamilyInteraction.sentiment == "positive", 1),
                        (FamilyInteraction.sentiment == "neutral", 0),
                        (FamilyInteraction.sentiment == "negative", -1),
                        else_=0
                    )
                )
            ).filter(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.family_member_id == member_id,
                FamilyInteraction.timestamp >= thirty_days_ago
            ).scalar() or 0

            return {
                "total_interactions": total_interactions,
                "daily_average": total_interactions / 30,
                "sentiment_score": float(avg_sentiment),
                "most_active_hour": 15,  # Placeholder
                "preferred_language": "es"  # Placeholder
            }

        except Exception as e:
            logger.error(f"Failed to get personal stats: {e}")
            return {"total_interactions": 0}

    async def _get_activity_suggestions(self, age_group: str = "child") -> Dict[str, Any]:
        """Get age-appropriate activity suggestions."""
        try:
            suggestions = {
                "child": [
                    {"title": "Jugar a las adivinanzas", "description": "Divertido juego de preguntas y respuestas"},
                    {"title": "Cuentos para dormir", "description": "Historias divertidas antes de dormir"},
                    {"title": "Dibujar y colorear", "description": "Actividades creativas con colores"}
                ],
                "teenager": [
                    {"title": "Retos matemáticos", "description": "Problemas interesantes para resolver"},
                    {"title": "Tutor de estudios", "description": "Ayuda con las tareas escolares"},
                    {"title": "Consejos para amigos", "description": "Guía sobre relaciones sociales"}
                ]
            }

            return {
                "suggestions": suggestions.get(age_group, suggestions["child"]),
                "age_group": age_group
            }

        except Exception as e:
            logger.error(f"Failed to get activity suggestions: {e}")
            return {"suggestions": []}

    async def create_alert(
        self,
        family_id: str,
        alert_type: str,
        title: str,
        message: str
    ) -> DashboardAlert:
        """Create a dashboard alert."""
        try:
            alert = DashboardAlert(
                id=f"alert-{int(datetime.now().timestamp())}",
                type=alert_type,
                title=title,
                message=message,
                timestamp=datetime.now(),
                family_id=family_id
            )

            # In production, this would be stored in database
            logger.info(f"Created alert for family {family_id}: {title}")

            return alert

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise

    async def acknowledge_alert(self, alert_id: str, family_id: str) -> bool:
        """Acknowledge a dashboard alert."""
        try:
            # In production, this would update the database
            logger.info(f"Acknowledged alert {alert_id} for family {family_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False