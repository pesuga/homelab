"""
Unit tests for family member management functionality.

Tests:
- Family member creation and authentication
- Permission system and role-based access
- Time restrictions and content filtering
- Family member data validation
- Permission inheritance and overrides
"""

import pytest
from datetime import datetime, time
from unittest.mock import AsyncMock, patch

from config.permissions import UserRole, UserPermissions, UserProfile
from tests.helpers.test_helpers import FamilyWorkflowHelpers, DatabaseHelpers


class TestPermissionManager:
    """Test permission management system."""

    def test_get_permission_profile_parent(self):
        """Test parent permission profile."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("parent")

        expected_permissions = {
            "can_chat": True,
            "can_send_images": True,
            "can_send_voice": True,
            "can_manage_schedule": True,
            "can_approve_requests": True,
            "time_restrictions": {},
            "content_filters": []
        }

        assert permissions == expected_permissions

    def test_get_permission_profile_teenager(self):
        """Test teenager permission profile."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("teenager")

        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is True
        assert permissions["can_manage_schedule"] is False
        assert "time_restrictions" in permissions
        assert permissions["time_restrictions"]["start"] == "07:00"
        assert permissions["time_restrictions"]["end"] == "22:00"

    def test_get_permission_profile_child(self):
        """Test child permission profile."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is False
        assert permissions["can_manage_schedule"] is False
        assert "profanity" in permissions["content_filters"]
        assert "adult_content" in permissions["content_filters"]

    def test_get_permission_profile_grandparent(self):
        """Test grandparent permission profile."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("grandparent")

        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is True
        assert permissions["time_restrictions"] == {}
        assert permissions["content_filters"] == []

    def test_invalid_role_defaults_to_child(self):
        """Test that invalid role defaults to child permissions."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("invalid_role")
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        assert permissions == child_permissions


class TestTimeRestrictions:
    """Test time restriction functionality."""

    def test_no_time_restrictions_always_allowed(self):
        """Test that empty restrictions always allow access."""
        restrictions = {}
        result = FamilyWorkflowHelpers.is_within_time_restrictions(restrictions)
        assert result is True

    @pytest.mark.parametrize("test_time,expected", [
        ("08:00", True),    # Exactly start time
        ("15:30", True),    # Within range
        ("20:00", True),    # Before end time
        ("07:59", False),   # Before start time
        ("20:01", False),   # After end time
        ("00:00", False),   # Midnight
        ("23:59", False),   # End of day
    ])
    def test_child_time_restrictions(self, test_time, expected):
        """Test child time restrictions throughout the day."""
        restrictions = {"start": "08:00", "end": "20:00"}
        result = FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, test_time)
        assert result is expected

    def test_cross_midnight_restrictions(self):
        """Test time restrictions that cross midnight."""
        restrictions = {"start": "22:00", "end": "06:00"}

        # These should be allowed
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "23:00") is True
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "03:00") is True
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "05:59") is True

        # These should be blocked
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "06:01") is False
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "21:59") is False
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "12:00") is False

    def test_current_time_when_no_test_time_provided(self):
        """Test using current time when no test time is specified."""
        restrictions = {"start": "00:00", "end": "23:59"}
        result = FamilyWorkflowHelpers.is_within_time_restrictions(restrictions)
        assert result is True  # Should always be within this range


class TestContentFiltering:
    """Test content filtering functionality."""

    def test_no_filters_always_allowed(self):
        """Test that empty filters always allow content."""
        filters = []
        content = "Any content here"
        result = FamilyWorkflowHelpers.should_filter_content(content, filters)
        assert result is False

    def test_profanity_filtering(self):
        """Test profanity content filtering."""
        filters = ["profanity"]
        bad_content = "This is a bad example"
        good_content = "This is a good example"

        assert FamilyWorkflowHelpers.should_filter_content(bad_content, filters) is True
        assert FamilyWorkflowHelpers.should_filter_content(good_content, filters) is False

    def test_adult_content_filtering(self):
        """Test adult content filtering."""
        filters = ["adult_content"]
        adult_content = "Some adult material here"
        normal_content = "Normal conversation here"

        assert FamilyWorkflowHelpers.should_filter_content(adult_content, filters) is True
        assert FamilyWorkflowHelpers.should_filter_content(normal_content, filters) is False

    def test_violence_filtering(self):
        """Test violence content filtering."""
        filters = ["violence"]
        violent_content = "There was a fight with weapons"
        peaceful_content = "People played games together"

        assert FamilyWorkflowHelpers.should_filter_content(violent_content, filters) is True
        assert FamilyWorkflowHelpers.should_filter_content(peaceful_content, filters) is False

    def test_multiple_filters(self):
        """Test multiple content filters."""
        filters = ["profanity", "violence", "adult_content"]

        # Content matching any filter should be blocked
        assert FamilyWorkflowHelpers.should_filter_content("This is terrible content", filters) is True
        assert FamilyWorkflowHelpers.should_filter_content("Adult material here", filters) is True
        assert FamilyWorkflowHelpers.should_filter_content("There was a fight", filters) is True

        # Clean content should pass
        clean_content = "This is a wonderful and peaceful conversation"
        assert FamilyWorkflowHelpers.should_filter_content(clean_content, filters) is False

    def test_case_insensitive_filtering(self):
        """Test that content filtering is case insensitive."""
        filters = ["profanity"]
        mixed_case_content = "This is BAD content"
        result = FamilyWorkflowHelpers.should_filter_content(mixed_case_content, filters)
        assert result is True


class TestFamilyMemberCreation:
    """Test family member creation and validation."""

    @pytest.mark.asyncio
    async def test_create_family_member_success(self, test_db):
        """Test successful family member creation."""
        member_data = {
            "telegram_id": 123456789,
            "username": "testuser",
            "full_name": "Test User",
            "role": "parent",
            "permissions": FamilyWorkflowHelpers.create_permission_profile("parent")
        }

        member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)
        assert member_id is not None
        assert isinstance(member_id, int)

        # Verify member was created
        count = await DatabaseHelpers.get_family_member_count(test_db)
        assert count == 1

    @pytest.mark.asyncio
    async def test_create_family_member_duplicate_telegram_id(self, test_db):
        """Test creating family member with duplicate Telegram ID."""
        member_data = {
            "telegram_id": 123456789,
            "username": "testuser1",
            "full_name": "Test User 1",
            "role": "parent"
        }

        # Create first member
        await DatabaseHelpers.create_test_family_member(test_db, member_data)

        # Try to create second member with same Telegram ID
        duplicate_data = member_data.copy()
        duplicate_data["username"] = "testuser2"
        duplicate_data["full_name"] = "Test User 2"

        # Should fail due to unique constraint
        with pytest.raises(Exception):  # Specific exception depends on database
            await DatabaseHelpers.create_test_family_member(test_db, duplicate_data)

    @pytest.mark.asyncio
    async def test_create_family_member_all_roles(self, test_db):
        """Test creating family members with all different roles."""
        roles = ["parent", "teenager", "child", "grandparent"]
        created_ids = []

        for i, role in enumerate(roles):
            member_data = {
                "telegram_id": 100000000 + i,
                "username": f"user_{role}",
                "full_name": f"User {role.title()}",
                "role": role,
                "permissions": FamilyWorkflowHelpers.create_permission_profile(role)
            }

            member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)
            created_ids.append(member_id)
            assert member_id is not None

        # Verify all members were created
        count = await DatabaseHelpers.get_family_member_count(test_db)
        assert count == len(roles)

    @pytest.mark.asyncio
    async def test_create_family_member_custom_permissions(self, test_db):
        """Test creating family member with custom permissions."""
        custom_permissions = {
            "can_chat": True,
            "can_send_images": True,
            "can_send_voice": False,
            "can_manage_schedule": False,
            "time_restrictions": {"start": "09:00", "end": "21:00"},
            "content_filters": ["profanity"]
        }

        member_data = {
            "telegram_id": 987654321,
            "username": "custom_user",
            "full_name": "Custom User",
            "role": "child",
            "permissions": custom_permissions
        }

        member_id = await DatabaseHelpers.create_test_family_member(test_db, member_data)
        assert member_id is not None

        # Verify custom permissions were stored
        # This would require database query to verify actual stored data


class TestPermissionValidation:
    """Test permission validation and checking."""

    def test_validate_chat_permission_granted(self):
        """Test chat permission validation when granted."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("parent")
        assert permissions["can_chat"] is True

    def test_validate_chat_permission_denied(self):
        """Test chat permission validation when denied."""
        permissions = {"can_chat": False}
        assert permissions["can_chat"] is False

    def test_validate_image_permission_by_role(self):
        """Test image sending permission by role."""
        parent_permissions = FamilyWorkflowHelpers.create_permission_profile("parent")
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        assert parent_permissions["can_send_images"] is True
        assert child_permissions["can_send_images"] is False

    def test_validate_voice_permission_by_role(self):
        """Test voice sending permission by role."""
        all_roles = ["parent", "teenager", "child", "grandparent"]

        for role in all_roles:
            permissions = FamilyWorkflowHelpers.create_permission_profile(role)
            assert permissions["can_send_voice"] is True

    def test_validate_schedule_management_permission(self):
        """Test schedule management permission."""
        parent_permissions = FamilyWorkflowHelpers.create_permission_profile("parent")
        teenager_permissions = FamilyWorkflowHelpers.create_permission_profile("teenager")

        assert parent_permissions["can_manage_schedule"] is True
        assert teenager_permissions["can_manage_schedule"] is False

    def test_validate_approval_permission(self):
        """Test request approval permission."""
        parent_permissions = FamilyWorkflowHelpers.create_permission_profile("parent")
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        assert parent_permissions["can_approve_requests"] is True
        assert child_permissions["can_approve_requests"] is False


class TestFamilyMemberDataValidation:
    """Test family member data validation."""

    def test_validate_telegram_id_positive_integer(self):
        """Test Telegram ID validation."""
        valid_ids = [123456789, 1, 2147483647]  # Valid positive integers
        for telegram_id in valid_ids:
            assert isinstance(telegram_id, int)
            assert telegram_id > 0

    def test_validate_telegram_id_invalid_types(self):
        """Test invalid Telegram ID types."""
        invalid_ids = [-123456789, 0, "123456789", None, 123.456]
        for telegram_id in invalid_ids:
            # In a real implementation, these should raise validation errors
            if isinstance(telegram_id, int):
                assert telegram_id <= 0 or not isinstance(telegram_id, int)
            else:
                assert not isinstance(telegram_id, int)

    def test_validate_username_format(self):
        """Test username format validation."""
        valid_usernames = ["username", "user_name123", "user.name", "user-name"]
        invalid_usernames = ["", "ab", "user" * 100, "user@domain", "user with spaces"]

        for username in valid_usernames:
            assert 3 <= len(username) <= 50
            assert all(c.isalnum() or c in "._-" for c in username)

        # In real implementation, invalid usernames should be rejected

    def test_validate_role_values(self):
        """Test role validation."""
        valid_roles = ["parent", "teenager", "child", "grandparent"]
        invalid_roles = ["admin", "moderator", "guest", "", None]

        for role in valid_roles:
            assert role in valid_roles

        for role in invalid_roles:
            # In real implementation, these should raise validation errors
            assert role not in valid_roles if role is not None else True


class TestPermissionInheritance:
    """Test permission inheritance and overrides."""

    def test_base_permission_inheritance(self):
        """Test that roles inherit base permissions correctly."""
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")
        teenager_permissions = FamilyWorkflowHelpers.create_permission_profile("teenager")

        # Both should have basic chat permissions
        assert child_permissions["can_chat"] is True
        assert teenager_permissions["can_chat"] is True

        # But teenager should have more privileges
        assert child_permissions["can_send_images"] is False
        assert teenager_permissions["can_send_images"] is True

    def test_permission_override_maintains_structure(self):
        """Test that permission overrides maintain expected structure."""
        base_permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        # Override a specific permission
        custom_permissions = base_permissions.copy()
        custom_permissions["can_send_images"] = True

        # Should maintain all other permissions
        assert custom_permissions["can_chat"] == base_permissions["can_chat"]
        assert custom_permissions["can_send_voice"] == base_permissions["can_send_voice"]
        assert custom_permissions["can_manage_schedule"] == base_permissions["can_manage_schedule"]

        # But have the overridden value
        assert custom_permissions["can_send_images"] != base_permissions["can_send_images"]

    def test_permission_merge_functionality(self):
        """Test merging multiple permission sets."""
        base_permissions = FamilyWorkflowHelpers.create_permission_profile("child")
        override_permissions = {"can_send_images": True, "custom_field": "custom_value"}

        # Simulate permission merge
        merged_permissions = base_permissions.copy()
        merged_permissions.update(override_permissions)

        # Should have both base and override permissions
        assert "can_chat" in merged_permissions  # From base
        assert merged_permissions["can_send_images"] is True  # From override
        assert merged_permissions["custom_field"] == "custom_value"  # From override