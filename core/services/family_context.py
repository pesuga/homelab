"""
Family Context Service

Core business logic for family management, context understanding, and member relationships.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.database import Family, FamilyMember, FamilyInteraction, FamilyMemory


class FamilyContextService:
    """Service for managing family context and relationships."""

    def __init__(self, db: Session):
        self.db = db

    def create_family(self, family_data: Dict[str, Any]) -> Family:
        """Create a new family with initial setup."""
        family = Family(
            name=family_data["name"],
            family_code=family_data["family_code"],
            description=family_data.get("description"),
            timezone=family_data.get("timezone", "America/Mexico_City"),
            primary_language=family_data.get("primary_language", "es"),
            secondary_language=family_data.get("secondary_language", "en")
        )

        self.db.add(family)
        self.db.commit()
        self.db.refresh(family)

        return family

    def add_family_member(self, family_id: str, member_data: Dict[str, Any]) -> FamilyMember:
        """Add a new member to the family."""
        member = FamilyMember(
            family_id=family_id,
            name=member_data["name"],
            email=member_data.get("email"),
            role=member_data["role"],
            birth_year=member_data.get("birth_year"),
            preferred_language=member_data.get("preferred_language", "es"),
            avatar_url=member_data.get("avatar_url"),
            voice_profile=member_data.get("voice_profile", {})
        )

        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        return member

    def get_family_context(self, family_id: str) -> Dict[str, Any]:
        """Get comprehensive family context for AI interactions."""
        family = self.db.query(Family).filter(Family.id == family_id).first()
        if not family:
            return {}

        members = self.db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id,
            FamilyMember.is_active == True
        ).all()

        # Get recent interactions for context
        recent_interactions = self.db.query(FamilyInteraction).filter(
            FamilyInteraction.family_id == family_id
        ).order_by(FamilyInteraction.timestamp.desc()).limit(10).all()

        # Get important family memories
        important_memories = self.db.query(FamilyMemory).filter(
            and_(
                FamilyMemory.family_id == family_id,
                FamilyMemory.importance >= 7
            )
        ).order_by(FamilyMemory.importance.desc()).limit(5).all()

        return {
            "family": {
                "id": family.id,
                "name": family.name,
                "primary_language": family.primary_language,
                "secondary_language": family.secondary_language,
                "timezone": family.timezone
            },
            "members": [
                {
                    "id": member.id,
                    "name": member.name,
                    "role": member.role,
                    "preferred_language": member.preferred_language,
                    "birth_year": member.birth_year
                }
                for member in members
            ],
            "recent_context": [
                {
                    "member": member.name if member else "Unknown",
                    "content": interaction.content,
                    "timestamp": interaction.timestamp,
                    "type": interaction.interaction_type
                }
                for interaction in recent_interactions
                for member in [self.db.query(FamilyMember).filter(
                    FamilyMember.id == interaction.member_id
                ).first()] if interaction.member_id
            ],
            "important_memories": [
                {
                    "title": memory.title,
                    "content": memory.content,
                    "category": memory.category,
                    "importance": memory.importance
                }
                for memory in important_memories
            ]
        }

    def log_interaction(
        self,
        family_id: str,
        member_id: str,
        interaction_data: Dict[str, Any]
    ) -> FamilyInteraction:
        """Log a family interaction for context and learning."""
        interaction = FamilyInteraction(
            family_id=family_id,
            member_id=member_id,
            interaction_type=interaction_data.get("type", "text"),
            content=interaction_data.get("content"),
            response=interaction_data.get("response"),
            context=interaction_data.get("context", {}),
            sentiment=interaction_data.get("sentiment", "neutral"),
            language=interaction_data.get("language", "es"),
            processed=True
        )

        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)

        return interaction

    def store_family_memory(
        self,
        family_id: str,
        memory_data: Dict[str, Any]
    ) -> FamilyMemory:
        """Store important family information and memories."""
        memory = FamilyMemory(
            family_id=family_id,
            category=memory_data["category"],
            title=memory_data["title"],
            content=memory_data["content"],
            metadata=memory_data.get("metadata", {}),
            importance=memory_data.get("importance", 5),
            expires_at=memory_data.get("expires_at")
        )

        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)

        return memory

    def get_member_by_role(self, family_id: str, role: str) -> Optional[FamilyMember]:
        """Get family member(s) by role."""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.role == role,
                FamilyMember.is_active == True
            )
        ).first()

    def get_parents(self, family_id: str) -> List[FamilyMember]:
        """Get all parent/grandparent members for parental controls."""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.role.in_(["parent", "grandparent"]),
                FamilyMember.is_active == True
            )
        ).all()

    def get_children(self, family_id: str) -> List[FamilyMember]:
        """Get all child members for content filtering."""
        return self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.role == "child",
                FamilyMember.is_active == True
            )
        ).all()

    def get_interaction_stats(self, family_id: str, days: int = 7) -> Dict[str, Any]:
        """Get family interaction statistics for monitoring."""
        start_date = datetime.now() - timedelta(days=days)

        total_interactions = self.db.query(FamilyInteraction).filter(
            and_(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= start_date
            )
        ).count()

        # Get stats by member
        member_stats = self.db.query(
            FamilyMember.name,
            func.count(FamilyInteraction.id).label("count")
        ).join(
            FamilyInteraction, FamilyMember.id == FamilyInteraction.member_id
        ).filter(
            and_(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= start_date
            )
        ).group_by(FamilyMember.id, FamilyMember.name).all()

        # Get interaction types
        type_stats = self.db.query(
            FamilyInteraction.interaction_type,
            func.count(FamilyInteraction.id).label("count")
        ).filter(
            and_(
                FamilyInteraction.family_id == family_id,
                FamilyInteraction.timestamp >= start_date
            )
        ).group_by(FamilyInteraction.interaction_type).all()

        return {
            "total_interactions": total_interactions,
            "period_days": days,
            "member_stats": [
                {"name": name, "interactions": count}
                for name, count in member_stats
            ],
            "type_distribution": [
                {"type": itype, "count": count}
                for itype, count in type_stats
            ]
        }