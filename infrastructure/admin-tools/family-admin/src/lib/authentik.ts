/**
 * Authentik Authentication Integration
 *
 * Handles authentication through Authentik Proxy Provider
 * Extracts user information from HTTP headers set by Authentik
 */

export interface AuthentikUser {
  id: string;
  username: string;
  email: string;
  name: string;
  groups: string[];
  is_admin: boolean;
}

/**
 * Extract user information from Authentik headers
 *
 * Headers set by Authentik ForwardAuth middleware:
 * - X-authentik-username: Username
 * - X-authentik-email: Email address
 * - X-authentik-name: Full name
 * - X-authentik-groups: Comma-separated groups
 * - X-authentik-uid: User UUID
 */
export function extractUserFromHeaders(headers: Headers): AuthentikUser | null {
  // Check if required headers are present
  const username = headers.get('x-authentik-username');
  const email = headers.get('x-authentik-email');
  const uid = headers.get('x-authentik-uid');

  if (!username || !email || !uid) {
    return null; // No authentication headers present
  }

  const name = headers.get('x-authentik-name') || username;
  const groupsHeader = headers.get('x-authentik-groups') || '';
  const groups = groupsHeader ? groupsHeader.split(',').map(g => g.trim()) : [];

  // Check if user is in admin group
  const is_admin = groups.includes('admins') || groups.includes('family-admins');

  return {
    id: uid,
    username,
    email,
    name,
    groups,
    is_admin,
  };
}

/**
 * Check if the current request is authenticated via Authentik
 */
export function isAuthenticated(headers: Headers): boolean {
  return extractUserFromHeaders(headers) !== null;
}

/**
 * Get user profile in the format expected by the frontend
 */
export function getUserProfile(user: AuthentikUser) {
  const [firstName, lastName] = user.name.split(' ', 2);

  return {
    id: user.id,
    email: user.email,
    username: user.username,
    role: user.is_admin ? 'admin' : 'user',
    is_admin: user.is_admin,
    display_name: user.name,
    first_name: firstName || '',
    last_name: lastName || '',
    groups: user.groups,
  };
}

/**
 * Development helper - create mock user for local development
 */
export function createMockUser(): AuthentikUser {
  return {
    id: 'dev-user-123',
    username: 'dev-admin',
    email: 'admin@dev.local',
    name: 'Development Admin',
    groups: ['admins'],
    is_admin: true,
  };
}