"""
Family Management API Routes

Endpoints for family context, members, and family-level operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

try:
    from ..dependencies import get_db, get_current_family
    from ..schemas.family import FamilyCreate, FamilyResponse, FamilyMemberCreate, FamilyMemberResponse
    from ...models.database import Family, FamilyMember, FamilyInteraction
    from ...services.family_context import FamilyContextService
except ImportError:
    from api.dependencies import get_db, get_current_family
    from api.schemas.family import FamilyCreate, FamilyResponse, FamilyMemberCreate, FamilyMemberResponse
    from api.models.database import Family, FamilyMember, FamilyInteraction
    from api.services.family_context import FamilyContextService

router = APIRouter()


@router.post("/", response_model=FamilyResponse)
async def create_family(
    family: FamilyCreate,
    db: Session = Depends(get_db)
):
    """Create a new family."""
    family_service = FamilyContextService(db)

    # Check if family code already exists
    existing = db.query(Family).filter(Family.family_code == family.family_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family code already exists"
        )

    db_family = Family(
        name=family.name,
        description=family.description,
        family_code=family.family_code,
        timezone=family.timezone,
        primary_language=family.primary_language,
        secondary_language=family.secondary_language
    )

    db.add(db_family)
    db.commit()
    db.refresh(db_family)

    return FamilyResponse.from_orm(db_family)


@router.get("/", response_model=List[FamilyResponse])
async def get_families(
    current_family: Family = Depends(get_current_family)
):
    """Get current family information."""
    return [FamilyResponse.from_orm(current_family)]


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: str,
    db: Session = Depends(get_db)
):
    """Get family by ID."""
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )
    return FamilyResponse.from_orm(family)


@router.post("/{family_id}/members", response_model=FamilyMemberResponse)
async def add_family_member(
    family_id: str,
    member: FamilyMemberCreate,
    db: Session = Depends(get_db)
):
    """Add a new member to the family."""
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )

    # Check if email already exists
    if member.email:
        existing = db.query(FamilyMember).filter(
            FamilyMember.email == member.email
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    db_member = FamilyMember(
        family_id=family_id,
        name=member.name,
        email=member.email,
        role=member.role,
        birth_year=member.birth_year,
        preferred_language=member.preferred_language,
        avatar_url=member.avatar_url
    )

    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    return FamilyMemberResponse.from_orm(db_member)


@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    family_id: str,
    db: Session = Depends(get_db)
):
    """Get all members of a family."""
    members = db.query(FamilyMember).filter(
        FamilyMember.family_id == family_id,
        FamilyMember.is_active == True
    ).all()

    return [FamilyMemberResponse.from_orm(member) for member in members]


@router.get("/{family_id}/interactions", response_model=List[dict])
async def get_family_interactions(
    family_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get recent family interactions."""
    interactions = db.query(FamilyInteraction).filter(
        FamilyInteraction.family_id == family_id
    ).order_by(FamilyInteraction.timestamp.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": interaction.id,
            "member_name": interaction.member.name if interaction.member else "Unknown",
            "type": interaction.interaction_type,
            "content": interaction.content,
            "response": interaction.response,
            "timestamp": interaction.timestamp,
            "language": interaction.language,
            "sentiment": interaction.sentiment
        }
        for interaction in interactions
    ]


@router.post("/{family_id}/interactions")
async def log_family_interaction(
    family_id: str,
    interaction_data: dict,
    db: Session = Depends(get_db)
):
    """Log a family interaction."""
    # Validate member exists
    member = db.query(FamilyMember).filter(
        FamilyMember.id == interaction_data.get("member_id"),
        FamilyMember.family_id == family_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid member ID"
        )

    interaction = FamilyInteraction(
        family_id=family_id,
        member_id=interaction_data.get("member_id"),
        interaction_type=interaction_data.get("type", "text"),
        content=interaction_data.get("content"),
        response=interaction_data.get("response"),
        context=interaction_data.get("context", {}),
        sentiment=interaction_data.get("sentiment", "neutral"),
        language=interaction_data.get("language", "es")
    )

    db.add(interaction)
    db.commit()

    return {"status": "logged", "interaction_id": interaction.id}