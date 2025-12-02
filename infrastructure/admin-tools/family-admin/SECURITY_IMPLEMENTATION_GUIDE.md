# Security Implementation Guide - Family Admin Dashboard

**Priority**: 🔴 CRITICAL
**Timeline**: 2-3 weeks
**Status**: NOT STARTED

This guide provides step-by-step implementation instructions for the critical security improvements identified in the architecture review.

---

## Phase 1: Server-Side Route Protection (2 days)

### Step 1: Create Middleware File

**File**: `middleware.ts` (project root, next to `next.config.ts`)

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'your-secret-key-change-in-production'
);

interface JWTPayload {
  user_id: string;
  email: string;
  is_admin: boolean;
  role: string;
  exp: number;
}

async function verifyToken(token: string): Promise<JWTPayload | null> {
  try {
    const { payload } = await jwtVerify(token, JWT_SECRET);
    return payload as unknown as JWTPayload;
  } catch (error) {
    console.error('JWT verification failed:', error);
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (
    pathname.startsWith('/signin') ||
    pathname.startsWith('/signup') ||
    pathname.startsWith('/api/auth/login') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon.ico')
  ) {
    return NextResponse.next();
  }

  // Get token from cookie or Authorization header
  const tokenFromCookie = request.cookies.get('auth_token')?.value;
  const authHeader = request.headers.get('authorization');
  const tokenFromHeader = authHeader?.replace('Bearer ', '');
  const token = tokenFromCookie || tokenFromHeader;

  if (!token) {
    console.warn(`No token found for ${pathname}`);
    return NextResponse.redirect(new URL('/signin', request.url));
  }

  // Verify token
  const payload = await verifyToken(token);

  if (!payload) {
    console.warn(`Invalid token for ${pathname}`);
    const response = NextResponse.redirect(new URL('/signin', request.url));
    response.cookies.delete('auth_token');
    return response;
  }

  // Check token expiration
  if (payload.exp && Date.now() >= payload.exp * 1000) {
    console.warn(`Expired token for ${pathname}`);
    const response = NextResponse.redirect(new URL('/signin', request.url));
    response.cookies.delete('auth_token');
    return response;
  }

  // Check admin permission for admin routes
  if (!payload.is_admin) {
    console.warn(`Non-admin access attempt to ${pathname} by ${payload.email}`);
    return NextResponse.redirect(new URL('/unauthorized', request.url));
  }

  // Add user info to headers for server components
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-user-id', payload.user_id);
  requestHeaders.set('x-user-email', payload.email);
  requestHeaders.set('x-user-role', payload.role);

  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
```

### Step 2: Install Dependencies

```bash
npm install jose
```

### Step 3: Update API Client to Store Token in Cookies

**File**: `src/lib/api-client.ts`

```typescript
// Add cookie management
private setTokenInCookie(token: string): void {
  // Set cookie with httpOnly equivalent behavior
  document.cookie = `auth_token=${token}; path=/; max-age=86400; SameSite=Strict`;
}

private clearTokenFromCookie(): void {
  document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Strict';
}

// Update login method
async login(credentials: LoginCredentials): Promise<void> {
  const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    throw new Error('Invalid email or password');
  }

  const data: TokenResponse = await response.json();
  this.setToken(data.access_token);
  this.setTokenInCookie(data.access_token); // NEW: Store in cookie
}

// Update logout method
logout(): void {
  this.clearToken();
  this.clearTokenFromCookie(); // NEW: Clear cookie
}
```

### Step 4: Create Unauthorized Page

**File**: `src/app/unauthorized/page.tsx`

```typescript
export default function UnauthorizedPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-4">
          403 - Unauthorized
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          You do not have permission to access this resource.
        </p>
        <a
          href="/signin"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Return to Sign In
        </a>
      </div>
    </div>
  );
}
```

### Step 5: Test Server-Side Protection

```bash
# 1. Start dev server
npm run dev

# 2. Try accessing protected route without auth
curl http://localhost:3000/dashboard
# Should redirect to /signin

# 3. Login and get token
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'

# 4. Access with valid token
curl http://localhost:3000/dashboard \
  -H "Cookie: auth_token=YOUR_JWT_TOKEN"
# Should return dashboard HTML
```

---

## Phase 2: Audit Logging System (2 days)

### Step 1: Create Audit Log Types

**File**: `src/lib/api-client.ts` (add to interfaces section)

```typescript
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: 'CREATE' | 'READ' | 'UPDATE' | 'DELETE';
  resource_type: 'family_member' | 'knowledge_item' | 'parental_controls' | 'system_config';
  resource_id: string;
  changes?: Record<string, { old: any; new: any }>;
  ip_address?: string;
  user_agent?: string;
}

export interface AuditLogFilters {
  user_id?: string;
  action?: string;
  resource_type?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}
```

### Step 2: Add Audit Logging to API Client

**File**: `src/lib/api-client.ts`

```typescript
export class ApiClient {
  // Add audit logging method
  private async logAuditEvent(
    action: AuditLogEntry['action'],
    resourceType: AuditLogEntry['resource_type'],
    resourceId: string,
    changes?: Record<string, { old: any; new: any }>
  ): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/audit-logs`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          action,
          resource_type: resourceType,
          resource_id: resourceId,
          changes,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      // Don't fail the main operation if audit logging fails
      console.error('Audit logging failed:', error);
    }
  }

  // Update CRUD methods to include audit logging
  async createFamilyMember(member: Partial<FamilyMember>): Promise<FamilyMember> {
    const response = await fetch(`${this.baseUrl}/api/v1/family/members`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(member),
    });

    if (!response.ok) throw new Error('Failed to create family member');

    const newMember = await response.json();

    // Audit log
    await this.logAuditEvent('CREATE', 'family_member', newMember.id);

    return newMember;
  }

  async updateFamilyMember(id: string, updates: Partial<FamilyMember>): Promise<FamilyMember> {
    const response = await fetch(`${this.baseUrl}/api/v1/family/members/${id}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(updates),
    });

    if (!response.ok) throw new Error('Failed to update family member');

    const updatedMember = await response.json();

    // Audit log with changes
    const changes = Object.keys(updates).reduce((acc, key) => {
      acc[key] = { old: 'previous_value', new: updates[key] }; // Backend should provide old value
      return acc;
    }, {} as Record<string, { old: any; new: any }>);

    await this.logAuditEvent('UPDATE', 'family_member', id, changes);

    return updatedMember;
  }

  async deleteFamilyMember(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/family/members/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });

    if (!response.ok) throw new Error('Failed to delete family member');

    // Audit log
    await this.logAuditEvent('DELETE', 'family_member', id);
  }

  // Add method to fetch audit logs
  async getAuditLogs(filters?: AuditLogFilters): Promise<AuditLogEntry[]> {
    const params = new URLSearchParams();
    if (filters?.user_id) params.append('user_id', filters.user_id);
    if (filters?.action) params.append('action', filters.action);
    if (filters?.resource_type) params.append('resource_type', filters.resource_type);
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.limit) params.append('limit', String(filters.limit));
    if (filters?.offset) params.append('offset', String(filters.offset));

    const response = await fetch(`${this.baseUrl}/api/audit-logs?${params}`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) throw new Error('Failed to fetch audit logs');

    return response.json();
  }
}
```

### Step 3: Create Audit Log Viewer Page

**File**: `src/app/(admin)/audit-logs/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { apiClient, AuditLogEntry, AuditLogFilters } from '@/lib/api-client';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<AuditLogFilters>({
    limit: 50,
    offset: 0,
  });

  useEffect(() => {
    fetchAuditLogs();
  }, [filters]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getAuditLogs(filters);
      setLogs(data);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'CREATE': return 'bg-green-100 text-green-800';
      case 'UPDATE': return 'bg-blue-100 text-blue-800';
      case 'DELETE': return 'bg-red-100 text-red-800';
      case 'READ': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-semibold text-gray-800 dark:text-white mb-6">
        Audit Logs
      </h1>

      {/* Filters */}
      <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Action</label>
            <select
              className="w-full px-3 py-2 border rounded"
              value={filters.action || ''}
              onChange={(e) => setFilters({ ...filters, action: e.target.value || undefined })}
            >
              <option value="">All</option>
              <option value="CREATE">Create</option>
              <option value="UPDATE">Update</option>
              <option value="DELETE">Delete</option>
              <option value="READ">Read</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Resource Type</label>
            <select
              className="w-full px-3 py-2 border rounded"
              value={filters.resource_type || ''}
              onChange={(e) => setFilters({ ...filters, resource_type: e.target.value || undefined })}
            >
              <option value="">All</option>
              <option value="family_member">Family Member</option>
              <option value="knowledge_item">Knowledge Item</option>
              <option value="parental_controls">Parental Controls</option>
              <option value="system_config">System Config</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Start Date</label>
            <input
              type="date"
              className="w-full px-3 py-2 border rounded"
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">End Date</label>
            <input
              type="date"
              className="w-full px-3 py-2 border rounded"
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            />
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Changes
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {log.user_email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded ${getActionColor(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {log.resource_type} #{log.resource_id}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {log.changes && (
                      <details>
                        <summary className="cursor-pointer text-blue-600">View Changes</summary>
                        <pre className="mt-2 text-xs">
                          {JSON.stringify(log.changes, null, 2)}
                        </pre>
                      </details>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

### Step 4: Add Audit Logs to Sidebar

**File**: `src/config/sidebarMenu.tsx`

```typescript
// Add to SYSTEM menu group
{
  name: "SYSTEM",
  menuItems: [
    {
      icon: <PlugIcon />,
      label: "MCP & Tools",
      route: "/mcp",
    },
    {
      icon: <ClipboardIcon />, // Add icon
      label: "Audit Logs",
      route: "/audit-logs",
    },
    {
      icon: <SettingsIcon />,
      label: "Settings",
      route: "/settings",
    },
  ],
}
```

---

## Phase 3: Input Validation with Zod (1 day)

### Step 1: Install Zod

```bash
npm install zod
```

### Step 2: Create Validation Schemas

**File**: `src/lib/validation-schemas.ts`

```typescript
import { z } from 'zod';

// Family Member Schema
export const FamilyMemberSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(100, 'Name must be less than 100 characters')
    .regex(/^[a-zA-Z\s'-]+$/, 'Name can only contain letters, spaces, hyphens, and apostrophes'),
  email: z
    .string()
    .email('Invalid email address')
    .max(255, 'Email must be less than 255 characters'),
  role: z.enum(['parent', 'teenager', 'child', 'grandparent'], {
    errorMap: () => ({ message: 'Invalid role selected' }),
  }),
  language_preference: z.enum(['en', 'es']).default('en'),
});

export type FamilyMemberInput = z.infer<typeof FamilyMemberSchema>;

// Knowledge Item Schema
export const KnowledgeItemSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be less than 200 characters'),
  content: z
    .string()
    .min(1, 'Content is required')
    .max(10000, 'Content must be less than 10,000 characters'),
  category: z
    .string()
    .min(1, 'Category is required')
    .max(50, 'Category must be less than 50 characters'),
  tags: z
    .array(z.string().max(30))
    .max(10, 'Maximum 10 tags allowed')
    .optional(),
});

export type KnowledgeItemInput = z.infer<typeof KnowledgeItemSchema>;

// Parental Controls Schema
export const ParentalControlsSchema = z.object({
  safe_search: z.boolean(),
  content_filter: z.enum(['strict', 'moderate', 'off']),
  screen_time_daily: z
    .number()
    .min(0, 'Screen time cannot be negative')
    .max(1440, 'Screen time cannot exceed 24 hours'),
  screen_time_weekend: z
    .number()
    .min(0, 'Screen time cannot be negative')
    .max(1440, 'Screen time cannot exceed 24 hours'),
  allowed_apps: z.array(z.string()).max(50, 'Maximum 50 allowed apps'),
  blocked_keywords: z.array(z.string()).max(100, 'Maximum 100 blocked keywords'),
});

export type ParentalControlsInput = z.infer<typeof ParentalControlsSchema>;

// System Config Schema
export const SystemConfigSchema = z.object({
  key: z.string().regex(/^[A-Z_]+$/, 'Key must be uppercase letters and underscores'),
  value: z.string().max(1000, 'Value must be less than 1,000 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
});

export type SystemConfigInput = z.infer<typeof SystemConfigSchema>;
```

### Step 3: Add Validation to Forms

**File**: `src/components/forms/AddFamilyMemberForm.tsx` (create new)

```typescript
'use client';

import { useState } from 'react';
import { FamilyMemberSchema, FamilyMemberInput } from '@/lib/validation-schemas';
import { z } from 'zod';

interface AddFamilyMemberFormProps {
  onSubmit: (data: FamilyMemberInput) => Promise<void>;
  onCancel: () => void;
}

export function AddFamilyMemberForm({ onSubmit, onCancel }: AddFamilyMemberFormProps) {
  const [formData, setFormData] = useState<Partial<FamilyMemberInput>>({
    role: 'child',
    language_preference: 'en',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    try {
      // Validate with Zod
      const validatedData = FamilyMemberSchema.parse(formData);

      setSubmitting(true);
      await onSubmit(validatedData);
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            fieldErrors[err.path[0] as string] = err.message;
          }
        });
        setErrors(fieldErrors);
      } else {
        console.error('Form submission error:', error);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Name Field */}
      <div>
        <label className="block text-sm font-medium mb-1">Name *</label>
        <input
          type="text"
          className={`w-full px-3 py-2 border rounded ${errors.name ? 'border-red-500' : ''}`}
          value={formData.name || ''}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
        {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
      </div>

      {/* Email Field */}
      <div>
        <label className="block text-sm font-medium mb-1">Email *</label>
        <input
          type="email"
          className={`w-full px-3 py-2 border rounded ${errors.email ? 'border-red-500' : ''}`}
          value={formData.email || ''}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />
        {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
      </div>

      {/* Role Field */}
      <div>
        <label className="block text-sm font-medium mb-1">Role *</label>
        <select
          className={`w-full px-3 py-2 border rounded ${errors.role ? 'border-red-500' : ''}`}
          value={formData.role || 'child'}
          onChange={(e) => setFormData({ ...formData, role: e.target.value as any })}
        >
          <option value="parent">Parent</option>
          <option value="teenager">Teenager</option>
          <option value="child">Child</option>
          <option value="grandparent">Grandparent</option>
        </select>
        {errors.role && <p className="text-red-500 text-sm mt-1">{errors.role}</p>}
      </div>

      {/* Language Field */}
      <div>
        <label className="block text-sm font-medium mb-1">Language Preference</label>
        <select
          className="w-full px-3 py-2 border rounded"
          value={formData.language_preference || 'en'}
          onChange={(e) => setFormData({ ...formData, language_preference: e.target.value as any })}
        >
          <option value="en">English</option>
          <option value="es">Spanish</option>
        </select>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded hover:bg-gray-50"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          disabled={submitting}
        >
          {submitting ? 'Adding...' : 'Add Family Member'}
        </button>
      </div>
    </form>
  );
}
```

---

## Testing Checklist

### Server-Side Protection
- [ ] Access /dashboard without auth → redirects to /signin
- [ ] Access with expired token → redirects to /signin
- [ ] Access with invalid token → redirects to /signin
- [ ] Access as non-admin → redirects to /unauthorized
- [ ] Access with valid admin token → works correctly

### Audit Logging
- [ ] Create family member → audit log created
- [ ] Update family member → audit log with changes
- [ ] Delete family member → audit log created
- [ ] Audit log viewer shows all logs
- [ ] Filters work correctly (action, resource, date)

### Input Validation
- [ ] Submit empty form → validation errors shown
- [ ] Submit invalid email → error shown
- [ ] Submit invalid characters in name → error shown
- [ ] Submit valid data → form submits successfully
- [ ] Error messages are user-friendly

---

## Environment Variables

Add to `.env.local`:

```bash
# JWT Configuration
JWT_SECRET=your-secure-secret-key-change-this-in-production
JWT_EXPIRES_IN=86400

# Audit Logging
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_RETENTION_DAYS=90

# Rate Limiting
ENABLE_RATE_LIMITING=true
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

---

## Next Steps

After completing these security implementations:

1. **Code Review**: Have security review middleware and validation logic
2. **Penetration Testing**: Test for security vulnerabilities
3. **Documentation**: Update API documentation with security requirements
4. **Training**: Ensure team understands security patterns
5. **Monitoring**: Set up alerts for security events (failed auth, audit log anomalies)

---

**Timeline Summary**:
- Day 1-2: Server-side protection with middleware
- Day 3-4: Audit logging system
- Day 5: Input validation with Zod
- Day 6: Testing and documentation
- Day 7: Security review and fixes

**Total**: 1 week for critical security foundation
