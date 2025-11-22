# Backend Requirements: Family Management API

## Context
The Family Admin Panel requires comprehensive family management functionality to manage family members, parental controls, and feature flags. The frontend is currently attempting to access family management endpoints but receiving `ERR_CONNECTION_REFUSED` errors.

## Current Frontend Implementation Status
- **Frontend Hook**: `useFamilyData.ts` - Implements family member management, parental controls, and activity reports
- **Frontend Page**: `family/members/page.tsx` - MyFamily section with CRUD operations
- **API Client**: Methods implemented in `api-client.ts` lines 376-426
- **Backend Status**: Family endpoints exist in OpenAPI spec but not accessible from admin frontend context

## Available Backend Endpoints (from OpenAPI spec)

### Family Member Management ✅
- **GET** `/api/v1/family/members` - List all family members
- **POST** `/api/v1/family/members` - Create new family member
- **GET** `/api/v1/family/members/{member_id}` - Get specific member
- **PATCH** `/api/v1/family/members/{member_id}` - Update member details
- **DELETE** `/api/v1/family/members/{member_id}` - Delete member

### Parental Controls ✅
- **GET** `/api/v1/family/parental-controls/{child_id}` - Get parental controls
- **POST** `/api/v1/family/parental-controls` - Create parental controls
- **PATCH** `/api/v1/family/parental-controls/{child_id}` - Update parental controls

### Screen Time Management ✅
- **GET** `/api/v1/family/screen-time/{user_id}/{date}` - Get screen time data
- **POST** `/api/v1/family/screen-time` - Log screen time

### Content Filtering ✅
- **POST** `/api/v1/family/content-filter/check` - Check content filter
- **GET** `/api/v1/family/content-filter/logs/{user_id}` - Get filter logs
- **POST** `/api/v1/family/content-filter/keywords/{child_id}` - Add blocked keywords
- **DELETE** `/api/v1/family/content-filter/keywords/{child_id}` - Remove keywords

### Activity & Analytics ✅
- **GET** `/api/v1/family/audit-logs` - Get family activity logs
- **GET** `/dashboard/stats` - Get dashboard statistics

## Required Backend Endpoints

### 1. Family Member Management

#### GET /api/v1/family/members
**Purpose**: Retrieve all family members
**Expected Response**:
```json
[
  {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "parent|teenager|child|grandparent",
    "avatar": "url_or_base64",
    "language_preference": "en|es",
    "parental_controls": {
      "safe_search": true,
      "content_filter": "strict|moderate|off",
      "screen_time_daily": 120,
      "screen_time_weekend": 180,
      "allowed_apps": ["app1", "app2"],
      "blocked_keywords": ["keyword1", "keyword2"]
    },
    "created_at": "2025-01-01T00:00:00Z",
    "last_active": "2025-01-01T12:00:00Z"
  }
]
```

#### POST /api/v1/family/members
**Purpose**: Create new family member
**Request Body**:
```json
{
  "name": "string",
  "email": "string",
  "role": "parent|teenager|child|grandparent",
  "avatar": "string (optional)",
  "language_preference": "en|es",
  "parental_controls": {
    "safe_search": true,
    "content_filter": "strict|moderate|off",
    "screen_time_daily": 120,
    "screen_time_weekend": 180,
    "allowed_apps": ["string"],
    "blocked_keywords": ["string"]
  }
}
```

#### PUT /api/family/members/{memberId}
**Purpose**: Update family member details
**Request Body**: Same as POST (partial updates supported)

#### DELETE /api/family/members/{memberId}
**Purpose**: Delete family member

### 2. Parental Controls Management

#### GET /api/family/members/{memberId}/controls
**Purpose**: Get parental controls for specific family member
**Expected Response**:
```json
{
  "safe_search": true,
  "content_filter": "strict|moderate|off",
  "screen_time_daily": 120,
  "screen_time_weekend": 180,
  "allowed_apps": ["app1", "app2"],
  "blocked_keywords": ["keyword1", "keyword2"]
}
```

#### PUT /api/family/members/{memberId}/controls
**Purpose**: Update parental controls for family member
**Request Body**: Same structure as GET response

### 3. Activity Reports

#### GET /api/reports/activity
**Purpose**: Get activity reports for date range
**Query Parameters**:
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string

**Expected Response**:
```json
[
  {
    "user_id": "uuid",
    "user_name": "John Doe",
    "date": "2025-01-01",
    "queries": 25,
    "screen_time_hours": 3.5,
    "topics": ["homework", "games", "family"],
    "sentiment": "positive|neutral|negative"
  }
]
```

#### GET /api/reports/activity
**Purpose**: Get activity report for specific user
**Query Parameters**:
- `user_id` (required): UUID
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string

## Database Schema Requirements

### Family Members Table
```sql
CREATE TABLE family_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('parent', 'teenager', 'child', 'grandparent')),
    avatar TEXT,
    language_preference VARCHAR(10) DEFAULT 'en' CHECK (language_preference IN ('en', 'es')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE
);
```

### Parental Controls Table
```sql
CREATE TABLE parental_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
    safe_search BOOLEAN DEFAULT true,
    content_filter VARCHAR(20) DEFAULT 'moderate' CHECK (content_filter IN ('strict', 'moderate', 'off')),
    screen_time_daily INTEGER DEFAULT 120, -- minutes
    screen_time_weekend INTEGER DEFAULT 180, -- minutes
    allowed_apps TEXT[] DEFAULT '{}',
    blocked_keywords TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Activity Logs Table
```sql
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES family_members(id),
    date DATE NOT NULL,
    queries INTEGER DEFAULT 0,
    screen_time_hours DECIMAL(5,2) DEFAULT 0,
    topics TEXT[] DEFAULT '{}',
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Frontend Requirements Met

### UI Components Implemented
- Family member list with avatars and roles
- Add/Edit member forms with validation
- Parental controls configuration interface
- Activity reports dashboard
- Role-based filtering and search
- Real-time status indicators

### Features Ready
- CRUD operations for family members
- Parental controls management
- Activity tracking and reporting
- Multi-language support (EN/ES)
- Age-appropriate content filtering
- Screen time management
- Safe search controls

## Integration Points

### Authentication
- All endpoints should use JWT authentication
- Role-based access control (parents can manage all members, children limited to own profile)

### Validation
- Email uniqueness validation
- Role hierarchy validation (prevents circular dependencies)
- Screen time limits validation
- Safe search and content filter validation

### Error Handling
- Consistent error response format
- Detailed validation messages
- Rate limiting for sensitive operations

## Immediate Issues to Resolve

### 1. Backend Connectivity 🔴 **HIGH PRIORITY**
**Problem**: Frontend receives `ERR_CONNECTION_REFUSED` when accessing `family-assistant-backend:8001/api/v1/family/members`

**Status**: Backend endpoints exist in OpenAPI spec but not accessible from admin frontend

**Required Actions**:
1. Verify backend service is running and accessible from admin pod
2. Check network policies allow admin pod to access backend service
3. Ensure proper service discovery in Kubernetes
4. Test direct connectivity from admin frontend pod to backend

**Test Command**:
```bash
kubectl exec deploy/family-admin -n homelab -- curl -v "http://family-assistant-backend:8001/api/v1/family/members"
```

### 2. API Client Alignment 🟡 **MEDIUM PRIORITY**
**Problem**: Frontend API client methods may not match backend endpoint structures exactly

**Required Actions**:
1. Review actual API request/response formats from backend
2. Update `api-client.ts` methods to match OpenAPI spec
3. Ensure proper error handling and response parsing
4. Test each endpoint individually

## Current Frontend vs Backend API Mapping

| Frontend Method | Backend Endpoint | Status |
|----------------|------------------|---------|
| `getFamilyMembers()` | `GET /api/v1/family/members` | ⚠️ Connection Issue |
| `createFamilyMember()` | `POST /api/v1/family/members` | ⚠️ Connection Issue |
| `updateFamilyMember()` | `PATCH /api/v1/family/members/{id}` | ⚠️ Wrong Method |
| `deleteFamilyMember()` | `DELETE /api/v1/family/members/{id}` | ⚠️ Connection Issue |
| `getParentalControls()` | `GET /api/v1/family/parental-controls/{id}` | ⚠️ Connection Issue |
| `updateParentalControls()` | `PATCH /api/v1/family/parental-controls/{id}` | ⚠️ Connection Issue |

**Note**: Frontend uses PUT but backend expects PATCH for updates.

## Priority
**CRITICAL** - Backend connectivity must be resolved before any frontend testing can proceed. The endpoints exist but are not accessible from the admin frontend context.

## OpenAPI Spec Reference
The backend team should reference the existing OpenAPI spec at: https://api.fa.pesulabs.net/openapi.json

Ensure consistency with existing authentication patterns and response formats already implemented in the Phase 2 endpoints.

## Testing Requirements
- Unit tests for all CRUD operations
- Integration tests for parental controls
- Performance tests for activity reports
- Security tests for role-based access control

---

**Generated**: 2025-01-20
**Frontend Status**: Complete and Ready for Backend Integration
**Backend Priority**: HIGH - Core family management functionality