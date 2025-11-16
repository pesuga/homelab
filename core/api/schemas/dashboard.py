"""
Dashboard Schemas

Pydantic models for dashboard requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""
    id: str
    type: str = Field(..., pattern="^(activity-feed|chat-widget|summary-metrics|sentiment-chart|controls-panel|memory-list|usage-chart|personal-metrics|study-tools|activity-suggestions)$")
    title: str
    data: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: Optional[int] = Field(None, ge=1, description="Refresh interval in seconds")

class DashboardResponse(BaseModel):
    """Dashboard configuration response."""
    family_id: str
    family_name: str
    layout: List[DashboardWidget]
    permissions: Dict[str, List[str]]
    theme: str = Field(default="light", pattern="^(light|dark|auto)$")
    last_updated: datetime

class WidgetDataResponse(BaseModel):
    """Widget data response."""
    widget_id: str
    data: Dict[str, Any]
    timestamp: datetime

class ActivityFeedItem(BaseModel):
    """Activity feed item."""
    id: str
    type: str = Field(..., pattern="^(message|voice|memory|system)$")
    title: str
    description: str
    timestamp: datetime
    member_name: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ActivityFeedResponse(BaseModel):
    """Activity feed response."""
    activities: List[ActivityFeedItem]
    total_count: int
    family_id: str
    last_updated: datetime

class DashboardAlert(BaseModel):
    """Dashboard alert."""
    id: str
    type: str = Field(..., pattern="^(info|warning|error|success)$")
    title: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    family_id: str

class DashboardAlertResponse(BaseModel):
    """Dashboard alert response."""
    id: str
    type: str
    title: str
    message: str
    timestamp: datetime
    acknowledged: bool
    family_id: str

class DashboardMetric(BaseModel):
    """Dashboard metric."""
    name: str
    value: float
    unit: str
    trend: Optional[float] = Field(None, ge=-100, le=100, description="Percentage change")
    status: str = Field(default="normal", pattern="^(normal|warning|critical)$")

class FamilyAnalyticsResponse(BaseModel):
    """Family analytics response."""
    family_id: str
    period: str = Field(..., pattern="^(1d|7d|30d|90d)$")
    summary_metrics: List[DashboardMetric]
    sentiment_analysis: Dict[str, Any]
    usage_analytics: Dict[str, Any]
    generated_at: datetime

class MemoryItem(BaseModel):
    """Memory item for dashboard."""
    id: str
    title: str
    content: str
    category: str = Field(..., pattern="^(preference|schedule|event|knowledge|interaction)$")
    importance: int = Field(ge=1, le=10)
    created_at: datetime
    relevance_score: Optional[float] = Field(None, ge=0, le=1)

class MemoryListResponse(BaseModel):
    """Memory list response."""
    memories: List[MemoryItem]
    total_count: int
    categories: Dict[str, int]
    sources: List[str]

class DashboardSettings(BaseModel):
    """Dashboard settings."""
    theme: str = Field(default="light", pattern="^(light|dark|auto)$")
    language: str = Field(default="es", pattern="^(es|en)$")
    auto_refresh: bool = True
    refresh_interval: int = Field(default=30, ge=5, le=300, description="Refresh interval in seconds")
    notifications: Dict[str, bool]
    widgets: Dict[str, List[str]]
    privacy: Dict[str, bool]

class PersonalStats(BaseModel):
    """Personal statistics."""
    total_interactions: int
    daily_average: float
    sentiment_score: float = Field(ge=-1, le=1)
    most_active_hour: int = Field(ge=0, le=23)
    preferred_language: str = Field(pattern="^(es|en)$")

class UsageAnalytics(BaseModel):
    """Usage analytics data."""
    member_activity: List[Dict[str, Any]]
    hourly_activity: List[Dict[str, Any]]
    period: str
    total_interactions: int

class SentimentChart(BaseModel):
    """Sentiment chart data."""
    labels: List[str]
    positive: List[int]
    neutral: List[int]
    negative: List[int]
    period: str
    total_days: int

class ActivitySuggestion(BaseModel):
    """Activity suggestion for children/teenagers."""
    title: str
    description: str
    category: str = Field(..., pattern="^(educational|fun|creative|social)$")
    age_appropriate: List[str]

class SystemStatus(BaseModel):
    """System status information."""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    services: Dict[str, str]
    last_updated: datetime
    version: str
    features: Dict[str, bool]

class DashboardTheme(BaseModel):
    """Dashboard theme configuration."""
    name: str
    primary_color: str
    secondary_color: str
    background_color: str
    text_color: str
    accent_color: str

class CustomWidget(BaseModel):
    """Custom widget configuration."""
    id: str
    type: str = "custom"
    title: str
    data_source: str
    display_config: Dict[str, Any]
    position: Dict[str, int]
    is_public: bool = False
    created_by: str
    created_at: datetime

class WidgetTemplate(BaseModel):
    """Widget template for creating custom widgets."""
    id: str
    name: str
    description: str
    widget_type: str
    default_config: Dict[str, Any]
    required_data: List[str]
    preview_image: Optional[str] = None