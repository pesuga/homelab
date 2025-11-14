"""
Family Management API Routes - Phase 3

Endpoints for family member management, permissions, parental controls,
screen time tracking, and content filtering.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import date

from ..models.user_management import (
    FamilyMember,
    FamilyMemberCreate,
    FamilyMemberUpdate,
    FamilyMemberListResponse,
    Permission,
    PermissionCheck,
    UserPermission,
    UserPermissionCreate,
    PermissionListResponse,
    ParentalControls,
    ParentalControlsCreate,
    ParentalControlsUpdate,
    ParentalControlsListResponse,
    ScreenTimeLog,
    ScreenTimeUpdate,
    ScreenTimeStatus,
    ScreenTimeReport,
    ContentFilterLog,
    ContentFilterCheck,
    ContentFilterResult,
    ContentFilterReport,
    AuditLog,
)
from ..services.user_manager import UserManager
from ..services.content_filter import ContentFilter
from ..dependencies import get_db_pool, get_current_user

router = APIRouter(prefix="/api/v1/family", tags=["Family Management"])


# ==============================================================================
# Family Member Endpoints
# ==============================================================================


@router.post("/members", response_model=FamilyMember, status_code=status.HTTP_201_CREATED)
async def create_family_member(
    member_data: FamilyMemberCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Create new family member (requires parent/admin permission)"""
    user_mgr = UserManager(db_pool)

    # Check permission
    perm_check = await user_mgr.check_permission(current_user.id, "family.member.create")
    if not perm_check.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create family members",
        )

    try:
        member = await user_mgr.create_family_member(member_data, created_by=current_user.id)
        return member
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/members", response_model=FamilyMemberListResponse)
async def list_family_members(
    include_inactive: bool = False,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """List all family members"""
    user_mgr = UserManager(db_pool)
    members = await user_mgr.list_family_members(include_inactive=include_inactive)
    return FamilyMemberListResponse(members=members, total=len(members))


@router.get("/members/{member_id}", response_model=FamilyMember)
async def get_family_member(
    member_id: UUID,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Get family member by ID"""
    user_mgr = UserManager(db_pool)
    member = await user_mgr.get_family_member(member_id)

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found")

    return member


@router.patch("/members/{member_id}", response_model=FamilyMember)
async def update_family_member(
    member_id: UUID,
    update_data: FamilyMemberUpdate,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Update family member profile"""
    user_mgr = UserManager(db_pool)

    # Check permission (must be self or parent/admin)
    if member_id != current_user.id:
        perm_check = await user_mgr.check_permission(current_user.id, "family.member.update")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update other family members",
            )

    member = await user_mgr.update_family_member(member_id, update_data, updated_by=current_user.id)

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found")

    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_member(
    member_id: UUID,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Delete (deactivate) family member"""
    user_mgr = UserManager(db_pool)

    # Check permission
    perm_check = await user_mgr.check_permission(current_user.id, "family.member.delete")
    if not perm_check.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete family members",
        )

    success = await user_mgr.delete_family_member(member_id, deleted_by=current_user.id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found")


# ==============================================================================
# Permission Endpoints
# ==============================================================================


@router.post("/permissions/check", response_model=PermissionCheck)
async def check_permission(
    user_id: UUID,
    permission_name: str,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Check if user has specific permission"""
    user_mgr = UserManager(db_pool)
    return await user_mgr.check_permission(user_id, permission_name)


@router.post("/permissions/grant", response_model=UserPermission)
async def grant_permission(
    perm_data: UserPermissionCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Grant permission to user (requires admin)"""
    user_mgr = UserManager(db_pool)

    # Check permission
    perm_check = await user_mgr.check_permission(current_user.id, "family.permissions.manage")
    if not perm_check.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage permissions",
        )

    try:
        return await user_mgr.grant_permission(perm_data, granted_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/permissions/{user_id}/{permission_name}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    user_id: UUID,
    permission_name: str,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Revoke permission from user (requires admin)"""
    user_mgr = UserManager(db_pool)

    # Check permission
    perm_check = await user_mgr.check_permission(current_user.id, "family.permissions.manage")
    if not perm_check.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage permissions",
        )

    await user_mgr.revoke_permission(user_id, permission_name, revoked_by=current_user.id)


@router.get("/permissions/{user_id}", response_model=List[UserPermission])
async def list_user_permissions(
    user_id: UUID,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """List all permissions for user"""
    user_mgr = UserManager(db_pool)

    # Check permission (must be self or parent/admin)
    if user_id != current_user.id:
        perm_check = await user_mgr.check_permission(current_user.id, "family.permissions.view")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view permissions",
            )

    return await user_mgr.list_user_permissions(user_id)


# ==============================================================================
# Parental Control Endpoints
# ==============================================================================


@router.post("/parental-controls", response_model=ParentalControls, status_code=status.HTTP_201_CREATED)
async def create_parental_controls(
    controls_data: ParentalControlsCreate,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Create parental controls for child (requires parent permission)"""
    user_mgr = UserManager(db_pool)

    # Verify current user is the parent
    if controls_data.parent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create parental controls as yourself",
        )

    try:
        return await user_mgr.create_parental_controls(controls_data, created_by=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/parental-controls/{child_id}", response_model=ParentalControls)
async def get_parental_controls(
    child_id: UUID,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Get parental controls for child"""
    user_mgr = UserManager(db_pool)

    # Check permission (must be parent or admin)
    if child_id != current_user.id:  # Children can view their own controls
        perm_check = await user_mgr.check_permission(current_user.id, "family.parental_controls.view")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view parental controls",
            )

    controls = await user_mgr.get_parental_controls(child_id)

    if not controls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parental controls not found")

    return controls


@router.patch("/parental-controls/{child_id}", response_model=ParentalControls)
async def update_parental_controls(
    child_id: UUID,
    update_data: ParentalControlsUpdate,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Update parental controls for child"""
    user_mgr = UserManager(db_pool)

    # Get existing controls to verify parent
    controls = await user_mgr.get_parental_controls(child_id, parent_id=current_user.id)
    if not controls:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own parental controls",
        )

    updated = await user_mgr.update_parental_controls(
        child_id, current_user.id, update_data, updated_by=current_user.id
    )

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parental controls not found")

    return updated


# ==============================================================================
# Screen Time Endpoints
# ==============================================================================


@router.post("/screen-time", response_model=ScreenTimeStatus)
async def update_screen_time(
    screen_time: ScreenTimeUpdate,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Update screen time log for user"""
    user_mgr = UserManager(db_pool)

    # Must be updating own screen time or have permission
    if screen_time.user_id != current_user.id:
        perm_check = await user_mgr.check_permission(current_user.id, "family.screen_time.manage")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage screen time",
            )

    return await user_mgr.update_screen_time(screen_time)


@router.get("/screen-time/{user_id}/{date}", response_model=ScreenTimeLog)
async def get_screen_time_log(
    user_id: UUID,
    date: date,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Get screen time log for specific date"""
    user_mgr = UserManager(db_pool)

    # Must be viewing own screen time or have permission
    if user_id != current_user.id:
        perm_check = await user_mgr.check_permission(current_user.id, "family.screen_time.view")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view screen time",
            )

    log = await user_mgr.get_screen_time_log(user_id, date)

    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screen time log not found")

    return log


# ==============================================================================
# Content Filter Endpoints
# ==============================================================================


@router.post("/content-filter/check", response_model=ContentFilterResult)
async def check_content(
    check_data: ContentFilterCheck,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Check content against filtering rules"""
    content_filter = ContentFilter(db_pool)

    # Must be checking own content or have permission
    if check_data.user_id != current_user.id:
        user_mgr = UserManager(db_pool)
        perm_check = await user_mgr.check_permission(current_user.id, "family.content_filter.manage")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to check content",
            )

    return await content_filter.check_content(
        check_data.user_id,
        check_data.content_type,
        check_data.content,
    )


@router.get("/content-filter/logs/{user_id}", response_model=List[ContentFilterLog])
async def get_content_filter_logs(
    user_id: UUID,
    limit: int = 100,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Get content filter logs for user"""
    content_filter = ContentFilter(db_pool)

    # Must be viewing own logs or have permission
    if user_id != current_user.id:
        user_mgr = UserManager(db_pool)
        perm_check = await user_mgr.check_permission(current_user.id, "family.content_filter.view")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view content filter logs",
            )

    return await content_filter.get_content_filter_logs(user_id=user_id, limit=limit)


@router.get("/content-filter/stats/{user_id}")
async def get_content_filter_stats(
    user_id: UUID,
    days: int = 7,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Get content filtering statistics"""
    content_filter = ContentFilter(db_pool)

    # Must be viewing own stats or have permission
    if user_id != current_user.id:
        user_mgr = UserManager(db_pool)
        perm_check = await user_mgr.check_permission(current_user.id, "family.content_filter.view")
        if not perm_check.has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view content filter stats",
            )

    return await content_filter.get_filter_stats(user_id, days)


@router.post("/content-filter/keywords/{child_id}", status_code=status.HTTP_201_CREATED)
async def add_blocked_keyword(
    child_id: UUID,
    keyword: str,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Add custom blocked keyword"""
    content_filter = ContentFilter(db_pool)

    try:
        await content_filter.add_blocked_keyword(child_id, current_user.id, keyword)
        return {"message": f"Keyword '{keyword}' added to blocked list"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/content-filter/keywords/{child_id}/{keyword}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_blocked_keyword(
    child_id: UUID,
    keyword: str,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Remove custom blocked keyword"""
    content_filter = ContentFilter(db_pool)

    try:
        await content_filter.remove_blocked_keyword(child_id, current_user.id, keyword)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/content-filter/domains/{child_id}/blocked", status_code=status.HTTP_201_CREATED)
async def add_blocked_domain(
    child_id: UUID,
    domain: str,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Add blocked domain"""
    content_filter = ContentFilter(db_pool)

    try:
        await content_filter.add_blocked_domain(child_id, current_user.id, domain)
        return {"message": f"Domain '{domain}' added to blocked list"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/content-filter/domains/{child_id}/allowed", status_code=status.HTTP_201_CREATED)
async def add_allowed_domain(
    child_id: UUID,
    domain: str,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Add allowed domain (whitelist)"""
    content_filter = ContentFilter(db_pool)

    try:
        await content_filter.add_allowed_domain(child_id, current_user.id, domain)
        return {"message": f"Domain '{domain}' added to allowed list"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==============================================================================
# Audit Log Endpoints
# ==============================================================================


@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    limit: int = 100,
    current_user: FamilyMember = Depends(get_current_user),
    db_pool=Depends(get_db_pool),
):
    """Get audit logs (requires admin permission)"""
    user_mgr = UserManager(db_pool)

    # Check permission
    perm_check = await user_mgr.check_permission(current_user.id, "family.audit.view")
    if not perm_check.has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs",
        )

    return await user_mgr.get_audit_logs(user_id=user_id, action=action, limit=limit)
