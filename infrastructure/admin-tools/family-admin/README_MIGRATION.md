# Family Assistant Admin Panel Migration

This directory contains the new Next.js admin panel replacing the previous React/Vite frontend.

## What Changed

### Technology Stack
- **Framework**: Next.js 16 with App Router (previously Vite + React)
- **Styling**: Tailwind CSS v4 (previously Tailwind v3)
- **Template**: TailAdmin Next.js admin template
- **Authentication**: JWT integration with FastAPI backend
- **State Management**: React Context for auth and app state

### Key Features
- ✅ Modern Next.js 16 App Router architecture
- ✅ JWT authentication flow with backend
- ✅ Protected admin routes
- ✅ Dashboard with backend health monitoring
- ✅ Dark mode support
- ✅ Responsive design
- ✅ 500+ UI components from TailAdmin template

## Setup Instructions

### 1. Install Dependencies
```bash
cd production/family-assistant/family-assistant/admin-nextjs
npm install --legacy-peer-deps
```

### 2. Configure Environment
Copy `.env.local.example` to `.env.local`:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` and set your backend API URL:
```env
NEXT_PUBLIC_API_URL=http://100.81.76.55:30080/api/v1
```

### 3. Run Development Server
```bash
npm run dev
```

The admin panel will be available at http://localhost:3000

### 4. Production Build
```bash
npm run build
npm start
```

## File Structure

```
admin-nextjs/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (admin)/           # Protected admin pages
│   │   │   ├── dashboard/     # Main dashboard
│   │   │   ├── layout.tsx     # Admin layout with ProtectedRoute
│   │   │   └── page.tsx       # Default admin page
│   │   ├── (auth)/            # Authentication pages
│   │   │   └── signin/        # Login page
│   │   └── layout.tsx         # Root layout with providers
│   ├── components/
│   │   ├── auth/              # Auth components
│   │   │   ├── SignInFormIntegrated.tsx  # Backend-integrated login
│   │   │   └── ProtectedRoute.tsx        # Route protection
│   │   ├── charts/            # Chart components
│   │   ├── forms/             # Form components
│   │   └── ui/                # Reusable UI components
│   ├── context/
│   │   ├── AuthContext.tsx    # Authentication state management
│   │   ├── SidebarContext.tsx # Sidebar state
│   │   └── ThemeContext.tsx   # Theme management
│   ├── lib/
│   │   └── api-client.ts      # Backend API client
│   └── layout/                # Layout components
│       ├── AppHeader.tsx
│       └── AppSidebar.tsx
├── public/                    # Static assets
├── .env.local                 # Environment variables (git ignored)
├── .env.local.example         # Example environment config
└── README_MIGRATION.md        # This file
```

## Backend Integration

### Authentication Flow
1. User submits login form (email/password)
2. Frontend calls `/api/v1/auth/login` with OAuth2 password flow
3. Backend validates credentials and returns JWT token
4. Token stored in localStorage and used for subsequent requests
5. Protected routes check authentication before rendering

### API Endpoints Used
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get user profile
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/health` - System health check

### API Client (`src/lib/api-client.ts`)
The API client handles:
- Token storage and retrieval
- Automatic Authorization header injection
- Error handling
- Type-safe API calls

## Authentication Context

The `AuthContext` provides:
- `user` - Current user profile
- `isAuthenticated` - Boolean authentication status
- `isLoading` - Loading state
- `login(credentials)` - Login function
- `logout()` - Logout function
- `refreshProfile()` - Refresh user profile

Usage:
```tsx
import { useAuth } from '@/context/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  // Use authentication state
}
```

## Protected Routes

All admin pages are automatically protected by the `ProtectedRoute` component in the admin layout. Unauthenticated users are redirected to `/signin`.

## Migration from Old Frontend

### What Was Removed
- Previous React/Vite frontend in `../frontend/`
- Old authentication implementation
- Separate dashboard standalone HTML

### What Was Added
- Next.js admin panel with modern architecture
- Backend-integrated authentication
- Protected route system
- Dashboard with real backend data

### Deployment Changes
The new admin can be deployed as:
1. **Standalone**: Run Next.js server separately
2. **Static Export**: Build and serve with nginx
3. **Docker**: Containerize with Next.js or nginx

## Testing

### Manual Testing Checklist
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (should show error)
- [ ] Protected routes redirect to login when not authenticated
- [ ] Dashboard loads user profile
- [ ] Dashboard shows system health
- [ ] Logout clears session
- [ ] Dark mode toggle works
- [ ] Responsive design on mobile

### Run Playwright Tests
```bash
npm run test:e2e
```

## Troubleshooting

### API Connection Issues
- Verify backend is running at the configured API URL
- Check network connectivity
- Verify CORS is configured on backend
- Check browser console for errors

### Authentication Issues
- Clear localStorage and try again
- Verify JWT token is being set correctly
- Check backend authentication endpoint
- Review backend logs for errors

### Build Issues
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install --legacy-peer-deps`
- Clear Next.js cache: `rm -rf .next`
- Verify Node.js version >= 20.9.0

## Next Steps

1. **Add More Pages**: Family management, memory browser, settings
2. **Enhance Dashboard**: Add metrics, charts, real-time updates
3. **WebSocket Integration**: Real-time notifications and updates
4. **Role-Based Access**: Different views for different user roles
5. **Spanish i18n**: Add bilingual support
6. **Mobile App**: Consider React Native or PWA

## Support

For issues or questions:
- Check `../HOW_TO_ACCESS.md` for backend setup
- Review `../IMPLEMENTATION_PROGRESS.md` for project status
- Consult TailAdmin docs: https://tailadmin.com/docs
