-- Phase 3: User Management & RBAC Schema
-- Migration 003: Family member profiles, roles, permissions, parental controls

-- ==============================================================================
-- Family Members Table (Enhanced)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS family_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) UNIQUE,

    -- Profile Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    display_name VARCHAR(100),
    avatar_url TEXT,
    date_of_birth DATE,

    -- Role and Permissions
    role VARCHAR(20) NOT NULL CHECK (role IN ('parent', 'teenager', 'child', 'grandparent', 'member')),
    age_group VARCHAR(20) CHECK (age_group IN ('child', 'teen', 'adult', 'senior')),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Language and Preferences
    language_preference VARCHAR(10) DEFAULT 'en' CHECK (language_preference IN ('en', 'es', 'bilingual')),
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
    theme_preference VARCHAR(20) DEFAULT 'mocha',

    -- Privacy and Safety
    privacy_level VARCHAR(20) DEFAULT 'family' CHECK (privacy_level IN ('private', 'family', 'parental_only')),
    safety_level VARCHAR(20) DEFAULT 'adult' CHECK (safety_level IN ('child', 'teen', 'adult')),
    content_filtering_enabled BOOLEAN DEFAULT TRUE,

    -- Active Skills
    active_skills JSONB DEFAULT '[]',

    -- Custom Preferences
    preferences JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_child_role CHECK (
        (role != 'child' OR safety_level = 'child')
    ),
    CONSTRAINT valid_age_group CHECK (
        (age_group IS NULL) OR
        (role = 'child' AND age_group = 'child') OR
        (role = 'teenager' AND age_group = 'teen') OR
        (role IN ('parent', 'grandparent', 'member') AND age_group IN ('adult', 'senior'))
    )
);

-- Indexes for performance
CREATE INDEX idx_family_members_telegram_id ON family_members(telegram_id);
CREATE INDEX idx_family_members_role ON family_members(role);
CREATE INDEX idx_family_members_is_active ON family_members(is_active);
CREATE INDEX idx_family_members_last_active ON family_members(last_active_at);

-- ==============================================================================
-- Permissions System
-- ==============================================================================

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL, -- calendar, messages, settings, family, admin
    action VARCHAR(50) NOT NULL, -- read, write, delete, manage
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Predefined permissions
INSERT INTO permissions (name, resource, action, description) VALUES
-- Calendar permissions
('calendar.read', 'calendar', 'read', 'View calendar events'),
('calendar.write', 'calendar', 'write', 'Create and edit calendar events'),
('calendar.delete', 'calendar', 'delete', 'Delete calendar events'),
('calendar.manage', 'calendar', 'manage', 'Full calendar management'),

-- Message permissions
('messages.read_own', 'messages', 'read', 'Read own messages'),
('messages.read_family', 'messages', 'read', 'Read family messages'),
('messages.read_all', 'messages', 'read', 'Read all messages (parental oversight)'),
('messages.send', 'messages', 'write', 'Send messages'),

-- Settings permissions
('settings.read', 'settings', 'read', 'View settings'),
('settings.update_own', 'settings', 'write', 'Update own settings'),
('settings.update_family', 'settings', 'write', 'Update family settings'),

-- Family management permissions
('family.view', 'family', 'read', 'View family member profiles'),
('family.invite', 'family', 'write', 'Invite family members'),
('family.remove', 'family', 'delete', 'Remove family members'),
('family.manage', 'family', 'manage', 'Full family management'),

-- Admin permissions
('admin.users', 'admin', 'manage', 'Manage users and permissions'),
('admin.system', 'admin', 'manage', 'System administration'),
('admin.security', 'admin', 'manage', 'Security settings')
ON CONFLICT (name) DO NOTHING;

-- ==============================================================================
-- Role Permissions (RBAC)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(20) NOT NULL CHECK (role IN ('parent', 'teenager', 'child', 'grandparent', 'member')),
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(role, permission_id)
);

-- Parent role permissions (full access)
INSERT INTO role_permissions (role, permission_id, granted)
SELECT 'parent', id, TRUE FROM permissions
ON CONFLICT (role, permission_id) DO NOTHING;

-- Teenager role permissions (moderate access)
INSERT INTO role_permissions (role, permission_id, granted)
SELECT 'teenager', id, TRUE FROM permissions
WHERE name IN (
    'calendar.read', 'calendar.write',
    'messages.read_own', 'messages.send',
    'settings.read', 'settings.update_own',
    'family.view'
)
ON CONFLICT (role, permission_id) DO NOTHING;

-- Child role permissions (restricted access)
INSERT INTO role_permissions (role, permission_id, granted)
SELECT 'child', id, TRUE FROM permissions
WHERE name IN (
    'calendar.read',
    'messages.read_own', 'messages.send',
    'settings.read',
    'family.view'
)
ON CONFLICT (role, permission_id) DO NOTHING;

-- Grandparent role permissions (full access, simplified interface)
INSERT INTO role_permissions (role, permission_id, granted)
SELECT 'grandparent', id, TRUE FROM permissions
WHERE name NOT LIKE 'admin.%'
ON CONFLICT (role, permission_id) DO NOTHING;

-- ==============================================================================
-- User Permissions (Override role permissions)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    granted BOOLEAN DEFAULT TRUE,
    granted_by UUID REFERENCES family_members(id),
    reason TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, permission_id)
);

CREATE INDEX idx_user_permissions_user ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_permission ON user_permissions(permission_id);

-- ==============================================================================
-- Parental Controls
-- ==============================================================================

CREATE TABLE IF NOT EXISTS parental_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES family_members(id) ON DELETE CASCADE,

    -- Screen Time Controls
    screen_time_enabled BOOLEAN DEFAULT FALSE,
    daily_limit_minutes INTEGER DEFAULT 120, -- 2 hours default
    weekday_limit_minutes INTEGER,
    weekend_limit_minutes INTEGER,
    quiet_hours_start TIME,
    quiet_hours_end TIME,

    -- Content Filtering
    content_filter_level VARCHAR(20) DEFAULT 'strict' CHECK (content_filter_level IN ('off', 'moderate', 'strict')),
    blocked_keywords JSONB DEFAULT '[]',
    allowed_domains JSONB DEFAULT '[]',
    blocked_domains JSONB DEFAULT '[]',

    -- Activity Monitoring
    activity_monitoring_enabled BOOLEAN DEFAULT TRUE,
    conversation_review_enabled BOOLEAN DEFAULT FALSE,
    location_sharing_enabled BOOLEAN DEFAULT FALSE,

    -- Notifications
    notify_parent_on_flagged_content BOOLEAN DEFAULT TRUE,
    notify_parent_on_limit_exceeded BOOLEAN DEFAULT TRUE,
    notify_parent_on_emergency BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(child_id, parent_id)
);

CREATE INDEX idx_parental_controls_child ON parental_controls(child_id);
CREATE INDEX idx_parental_controls_parent ON parental_controls(parent_id);

-- ==============================================================================
-- Screen Time Tracking
-- ==============================================================================

CREATE TABLE IF NOT EXISTS screen_time_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Time tracking
    total_minutes INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,

    -- Activity breakdown
    activity_breakdown JSONB DEFAULT '{}', -- {"messaging": 30, "homework": 45, "entertainment": 20}

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, date)
);

CREATE INDEX idx_screen_time_user_date ON screen_time_logs(user_id, date);

-- ==============================================================================
-- Content Filter Logs
-- ==============================================================================

CREATE TABLE IF NOT EXISTS content_filter_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,

    -- Content information
    content_type VARCHAR(50), -- message, search, image, url
    content_snippet TEXT,
    filter_reason VARCHAR(100),
    severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    -- Action taken
    action_taken VARCHAR(50), -- blocked, warned, allowed_with_warning, flagged
    parent_notified BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_content_filter_user ON content_filter_logs(user_id);
CREATE INDEX idx_content_filter_severity ON content_filter_logs(severity);
CREATE INDEX idx_content_filter_created ON content_filter_logs(created_at);

-- ==============================================================================
-- Family Relationships
-- ==============================================================================

CREATE TABLE IF NOT EXISTS family_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
    related_user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- parent, child, sibling, grandparent, grandchild, spouse, etc.
    is_primary BOOLEAN DEFAULT FALSE, -- Primary parent/guardian

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, related_user_id, relationship_type),
    CHECK (user_id != related_user_id)
);

CREATE INDEX idx_family_relationships_user ON family_relationships(user_id);
CREATE INDEX idx_family_relationships_related ON family_relationships(related_user_id);
CREATE INDEX idx_family_relationships_type ON family_relationships(relationship_type);

-- ==============================================================================
-- User Preferences (Detailed)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES family_members(id) ON DELETE CASCADE,

    -- Communication preferences
    prompt_style VARCHAR(20) DEFAULT 'balanced' CHECK (prompt_style IN ('brief', 'balanced', 'detailed')),
    response_length VARCHAR(20) DEFAULT 'medium' CHECK (response_length IN ('short', 'medium', 'long')),
    formality_level VARCHAR(20) DEFAULT 'casual' CHECK (formality_level IN ('formal', 'balanced', 'casual')),
    emoji_usage VARCHAR(20) DEFAULT 'moderate' CHECK (emoji_usage IN ('none', 'minimal', 'moderate', 'frequent')),

    -- Notification preferences
    notification_email BOOLEAN DEFAULT TRUE,
    notification_telegram BOOLEAN DEFAULT TRUE,
    notification_quiet_hours_start TIME,
    notification_quiet_hours_end TIME,

    -- Assistant behavior
    proactive_suggestions BOOLEAN DEFAULT TRUE,
    context_awareness_level VARCHAR(20) DEFAULT 'high' CHECK (context_awareness_level IN ('low', 'medium', 'high')),
    memory_retention_days INTEGER DEFAULT 90,

    -- UI preferences
    dashboard_layout JSONB DEFAULT '{}',
    favorite_skills JSONB DEFAULT '[]',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- User Sessions
-- ==============================================================================

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,

    -- Session info
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);

-- ==============================================================================
-- Audit Log
-- ==============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id) ON DELETE SET NULL,

    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,

    -- Details
    details JSONB,
    ip_address INET,
    user_agent TEXT,

    -- Result
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- ==============================================================================
-- Functions and Triggers
-- ==============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to tables
CREATE TRIGGER update_family_members_updated_at
    BEFORE UPDATE ON family_members
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_parental_controls_updated_at
    BEFORE UPDATE ON parental_controls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_screen_time_logs_updated_at
    BEFORE UPDATE ON screen_time_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to check user permission
CREATE OR REPLACE FUNCTION has_permission(
    p_user_id UUID,
    p_permission_name VARCHAR
)
RETURNS BOOLEAN AS $$
DECLARE
    v_role VARCHAR(20);
    v_has_permission BOOLEAN;
    v_permission_id UUID;
BEGIN
    -- Get user role
    SELECT role INTO v_role FROM family_members WHERE id = p_user_id;

    IF v_role IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Get permission ID
    SELECT id INTO v_permission_id FROM permissions WHERE name = p_permission_name;

    IF v_permission_id IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check user-specific permission override
    SELECT granted INTO v_has_permission
    FROM user_permissions
    WHERE user_id = p_user_id
      AND permission_id = v_permission_id
      AND (expires_at IS NULL OR expires_at > NOW());

    IF v_has_permission IS NOT NULL THEN
        RETURN v_has_permission;
    END IF;

    -- Check role permission
    SELECT granted INTO v_has_permission
    FROM role_permissions
    WHERE role = v_role
      AND permission_id = v_permission_id;

    RETURN COALESCE(v_has_permission, FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to log audit event
CREATE OR REPLACE FUNCTION log_audit_event(
    p_user_id UUID,
    p_action VARCHAR,
    p_resource_type VARCHAR DEFAULT NULL,
    p_resource_id UUID DEFAULT NULL,
    p_details JSONB DEFAULT NULL,
    p_success BOOLEAN DEFAULT TRUE,
    p_error_message TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO audit_log (
        user_id, action, resource_type, resource_id,
        details, success, error_message
    ) VALUES (
        p_user_id, p_action, p_resource_type, p_resource_id,
        p_details, p_success, p_error_message
    )
    RETURNING id INTO v_audit_id;

    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- Sample Data (Development/Testing)
-- ==============================================================================

-- Note: Sample data should be added via application code or separate seed script
-- to avoid polluting production migrations

-- ==============================================================================
-- Migration Complete
-- ==============================================================================

COMMENT ON TABLE family_members IS 'Family member profiles with role-based access';
COMMENT ON TABLE permissions IS 'System permissions for RBAC';
COMMENT ON TABLE role_permissions IS 'Permissions assigned to roles';
COMMENT ON TABLE user_permissions IS 'User-specific permission overrides';
COMMENT ON TABLE parental_controls IS 'Parental control settings for children';
COMMENT ON TABLE screen_time_logs IS 'Daily screen time tracking';
COMMENT ON TABLE content_filter_logs IS 'Content filtering activity log';
COMMENT ON TABLE family_relationships IS 'Family member relationships';
COMMENT ON TABLE user_preferences IS 'User preference settings';
COMMENT ON TABLE user_sessions IS 'Active user sessions';
COMMENT ON TABLE audit_log IS 'System audit trail';
