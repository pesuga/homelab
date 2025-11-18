# DEPRECATED: Old Admin Frontend

## Status: DEPRECATED as of 2025-11-18

This React/Vite admin frontend has been replaced by the new Next.js admin panel.

## Migration Path

**New Admin Location**: `../admin-nextjs/`

### Why the Change?
- Modern Next.js 16 App Router architecture
- Better performance and SEO
- TailAdmin template with 500+ components
- Improved authentication flow
- Better TypeScript support
- Easier maintenance and scaling

### What to Use Instead
All functionality from this frontend is being migrated to the new admin panel:
- **Dashboard** → `/dashboard` in new admin
- **Authentication** → Backend-integrated JWT auth
- **Components** → TailAdmin component library

## Current Status

| Feature | Old Frontend | New Frontend |
|---------|-------------|--------------|
| Authentication | ❌ Deprecated | ✅ JWT Integration |
| Dashboard | ❌ Deprecated | ✅ Backend-Connected |
| Family Management | ❌ Deprecated | 🚧 In Progress |
| Memory Browser | ❌ Deprecated | 🚧 Planned |
| Settings | ❌ Deprecated | 🚧 Planned |

## Migration Instructions

1. **For Development**:
   ```bash
   cd ../admin-nextjs
   npm install --legacy-peer-deps
   npm run dev
   ```

2. **For Deployment**:
   See `../admin-nextjs/README_MIGRATION.md`

## Removal Timeline

- **2025-11-18**: Marked as deprecated
- **Future**: Will be removed after new admin reaches feature parity

## Questions?

See:
- `../admin-nextjs/README_MIGRATION.md` - Migration guide
- `../HOW_TO_ACCESS.md` - Backend setup
- `../IMPLEMENTATION_PROGRESS.md` - Project status
