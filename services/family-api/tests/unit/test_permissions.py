"""
Unit tests for permission system and family role management.

Tests:
- Permission profile creation
- Time restriction validation
- Content filtering logic
- Role-based access control
"""

import pytest
from datetime import time
from tests.helpers.test_helpers import FamilyWorkflowHelpers


class TestPermissionProfiles:
    """Test permission profile creation and validation."""

    def test_parent_permission_profile(self):
        """Test parent permission profile has all required permissions."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("parent")

        # Verify all parent permissions are correct
        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is True
        assert permissions["can_send_voice"] is True
        assert permissions["can_manage_schedule"] is True
        assert permissions["can_approve_requests"] is True
        assert permissions["time_restrictions"] == {}
        assert permissions["content_filters"] == []

    def test_child_permission_profile(self):
        """Test child permission profile has appropriate restrictions."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        # Verify child permissions
        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is False
        assert permissions["can_send_voice"] is True
        assert permissions["can_manage_schedule"] is False
        assert permissions["can_approve_requests"] is False
        assert permissions["time_restrictions"]["start"] == "08:00"
        assert permissions["time_restrictions"]["end"] == "20:00"
        assert "profanity" in permissions["content_filters"]
        assert "adult_content" in permissions["content_filters"]

    def test_teenager_permission_profile(self):
        """Test teenager permission profile has balanced permissions."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("teenager")

        # Verify teenager permissions
        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is True
        assert permissions["can_send_voice"] is True
        assert permissions["can_manage_schedule"] is False
        assert permissions["can_approve_requests"] is False
        assert permissions["time_restrictions"]["start"] == "07:00"
        assert permissions["time_restrictions"]["end"] == "22:00"
        assert "profanity" in permissions["content_filters"]

    def test_grandparent_permission_profile(self):
        """Test grandparent permission profile."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("grandparent")

        # Verify grandparent permissions (similar to parent but no admin functions)
        assert permissions["can_chat"] is True
        assert permissions["can_send_images"] is True
        assert permissions["can_send_voice"] is True
        assert permissions["can_manage_schedule"] is False
        assert permissions["can_approve_requests"] is False
        assert permissions["time_restrictions"] == {}
        assert permissions["content_filters"] == []

    def test_invalid_role_defaults_to_child(self):
        """Test that invalid roles default to child permissions."""
        permissions = FamilyWorkflowHelpers.create_permission_profile("invalid_role")
        child_permissions = FamilyWorkflowHelpers.create_permission_profile("child")

        assert permissions == child_permissions


class TestTimeRestrictions:
    """Test time restriction validation."""

    def test_no_time_restrictions_always_allowed(self):
        """Test that empty restrictions always allow access."""
        restrictions = {}
        result = FamilyWorkflowHelpers.is_within_time_restrictions(restrictions)
        assert result is True

    @pytest.mark.parametrize("test_time,expected", [
        ("08:00", True),    # Exactly start time
        ("12:00", True),    # Midday
        ("19:59", True),    # Just before end time
        ("20:00", True),    # Exactly end time
        ("07:59", False),   # Just before start time
        ("20:01", False),   # Just after end time
        ("00:00", False),   # Midnight
        ("23:59", False),   # End of day
    ])
    def test_child_time_restrictions(self, test_time, expected):
        """Test child time restrictions throughout the day."""
        restrictions = {"start": "08:00", "end": "20:00"}
        result = FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, test_time)
        assert result is expected

    def test_teenager_time_restrictions(self):
        """Test teenager time restrictions."""
        restrictions = {"start": "07:00", "end": "22:00"}

        # Should be allowed during teenager hours
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "07:00") is True
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "15:00") is True
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "22:00") is True

        # Should be blocked outside teenager hours
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "06:59") is False
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "22:01") is False

    def test_parent_time_restrictions(self):
        """Test parent has no time restrictions."""
        restrictions = {}

        # Should always be allowed
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "03:00") is True
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "15:00") is True
        assert FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "23:00") is True


class TestContentFiltering:
    """Test content filtering logic."""

    def test_no_filters_always_allowed(self):
        """Test that empty filters always allow content."""
        filters = []
        content = "Any content here"
        result = FamilyWorkflowHelpers.should_filter_content(content, filters)
        assert result is False

    def test_profanity_filtering(self):
        """Test profanity content filtering."""
        filters = ["profanity"]

        # Content that should be filtered
        bad_content = "This is really bad"
        good_content = "This is really good"

        assert FamilyWorkflowHelpers.should_filter_content(bad_content, filters) is True
        assert FamilyWorkflowHelpers.should_filter_content(good_content, filters) is False

    def test_multiple_filters(self):
        """Test multiple content filters."""
        filters = ["profanity", "violence", "adult_content"]

        # Content matching different filters
        assert FamilyWorkflowHelpers.should_filter_content("This is terrible and violent", filters) is True
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

    def test_partial_word_filtering(self):
        """Test filtering works on partial words."""
        filters = ["profanity"]

        # Should filter based on substring match
        assert FamilyWorkflowHelpers.should_filter_content("This has badness in it", filters) is True


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_role_hierarchy(self):
        """Test permission hierarchy between roles."""
        parent_perms = FamilyWorkflowHelpers.create_permission_profile("parent")
        child_perms = FamilyWorkflowHelpers.create_permission_profile("child")
        teen_perms = FamilyWorkflowHelpers.create_permission_profile("teenager")

        # Parents should have more permissions than children
        assert parent_perms["can_manage_schedule"] > child_perms["can_manage_schedule"]
        assert parent_perms["can_approve_requests"] > child_perms["can_approve_requests"]
        assert parent_perms["can_send_images"] > child_perms["can_send_images"]

        # Teenagers should have more permissions than children
        assert teen_perms["can_send_images"] > child_perms["can_send_images"]
        assert teen_perms["time_restrictions"]["end"] > child_perms["time_restrictions"]["end"]

    def test_permission_inheritance(self):
        """Test that all roles inherit basic permissions."""
        roles = ["parent", "teenager", "child", "grandparent"]

        for role in roles:
            permissions = FamilyWorkflowHelpers.create_permission_profile(role)

            # All roles should have basic chat and voice permissions
            assert permissions["can_chat"] is True
            assert permissions["can_send_voice"] is True

    def test_time_restriction_progression(self):
        """Test that time restrictions progress appropriately by age."""
        child_perms = FamilyWorkflowHelpers.create_permission_profile("child")
        teen_perms = FamilyWorkflowHelpers.create_permission_profile("teenager")
        parent_perms = FamilyWorkflowHelpers.create_permission_profile("parent")

        # Children should have most restrictive time limits
        child_start = int(child_perms["time_restrictions"]["start"].replace(":", ""))
        child_end = int(child_perms["time_restrictions"]["end"].replace(":", ""))

        # Teenagers should have less restrictive limits
        teen_start = int(teen_perms["time_restrictions"]["start"].replace(":", ""))
        teen_end = int(teen_perms["time_restrictions"]["end"].replace(":", ""))

        # Parents should have no restrictions
        parent_restriction = parent_perms["time_restrictions"]

        assert teen_start <= child_start  # Teens can start earlier
        assert teen_end >= child_end      # Teens can stay up later
        assert parent_restriction == {}   # Parents have no restrictions


class TestPermissionValidation:
    """Test permission validation edge cases."""

    def test_empty_time_restrictions(self):
        """Test handling of empty time restrictions."""
        restrictions = {}
        result = FamilyWorkflowHelpers.is_within_time_restrictions(restrictions)
        assert result is True

    def test_invalid_time_format(self):
        """Test handling of invalid time format."""
        restrictions = {"start": "invalid", "end": "20:00"}

        # Should raise ValueError for invalid time format
        with pytest.raises(ValueError):
            FamilyWorkflowHelpers.is_within_time_restrictions(restrictions, "10:00")

    def test_empty_content_filters(self):
        """Test handling of empty content filters."""
        filters = []
        content = "Any content"
        result = FamilyWorkflowHelpers.should_filter_content(content, filters)
        assert result is False

    def test_empty_content_with_filters(self):
        """Test filtering empty content."""
        filters = ["profanity"]
        content = ""
        result = FamilyWorkflowHelpers.should_filter_content(content, filters)
        assert result is False  # Empty content shouldn't be filtered