-- ============================================================================
-- Add hashed_password column for JWT authentication
-- ============================================================================

-- Add hashed_password column to family_members table
ALTER TABLE family_members
ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);

-- Add index for faster lookups by username (used in login)
CREATE INDEX IF NOT EXISTS idx_family_members_username
ON family_members(username)
WHERE username IS NOT NULL;

-- Verification
DO $$
BEGIN
    RAISE NOTICE 'Migration 002: hashed_password column added successfully!';
END $$;
