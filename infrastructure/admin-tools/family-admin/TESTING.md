# Testing Guide - Family Assistant Admin Panel

## Test Status

**Implementation Date**: 2025-11-18
**Status**: ✅ Core Implementation Complete - Manual Testing Required

## Prerequisites for Testing

### 1. Node.js Version
The application requires Node.js >= 20.9.0. Check your version:
```bash
node --version
```

If you need to upgrade:
```bash
# Using nvm (recommended)
nvm install 20
nvm use 20

# Or download from https://nodejs.org/
```

### 2. Backend API Running
Ensure the Family Assistant backend is running:
```bash
# Check backend health
curl http://100.81.76.55:30080/api/v1/health

# Should return:
# {"status": "healthy", "components": {...}}
```

### 3. Test User Credentials
Have valid credentials for testing:
- Username/Email
- Password

## Manual Testing Checklist

### Test Scenario 1: Authentication Flow

#### 1.1 Login with Valid Credentials ✅
**Steps**:
1. Start dev server: `npm run dev`
2. Navigate to http://localhost:3000
3. Should redirect to `/signin` (not authenticated)
4. Enter valid credentials
5. Click "Sign in"

**Expected Results**:
- ✅ Form submits without errors
- ✅ User is redirected to dashboard (`/`)
- ✅ User profile loaded in header/sidebar
- ✅ Token stored in localStorage

**Verification**:
```javascript
// Browser console
localStorage.getItem('access_token')
// Should return JWT token
```

#### 1.2 Login with Invalid Credentials ✅
**Steps**:
1. Navigate to `/signin`
2. Enter invalid credentials
3. Click "Sign in"

**Expected Results**:
- ✅ Error message displayed
- ✅ User remains on login page
- ✅ No token stored

#### 1.3 Logout ✅
**Steps**:
1. While logged in, click logout (header/sidebar)
2. Observe behavior

**Expected Results**:
- ✅ Token cleared from localStorage
- ✅ Redirected to `/signin`
- ✅ User profile cleared

### Test Scenario 2: Protected Routes

#### 2.1 Access Admin Page Without Authentication ✅
**Steps**:
1. Clear localStorage: `localStorage.clear()`
2. Navigate to `/` or `/dashboard`

**Expected Results**:
- ✅ Redirected to `/signin`
- ✅ Loading spinner shows briefly
- ✅ No flash of admin content

#### 2.2 Access Admin Page With Authentication ✅
**Steps**:
1. Login successfully
2. Navigate to `/dashboard`

**Expected Results**:
- ✅ Dashboard loads successfully
- ✅ User profile displayed
- ✅ System health loaded

### Test Scenario 3: Dashboard Functionality

#### 3.1 Dashboard Data Loading ✅
**Steps**:
1. Login and navigate to dashboard
2. Observe dashboard cards

**Expected Results**:
- ✅ User info card shows correct data
- ✅ System health card shows API status
- ✅ Quick actions buttons render
- ✅ No console errors

#### 3.2 Dashboard Error Handling ⚠️
**Steps**:
1. Stop backend API
2. Refresh dashboard

**Expected Results**:
- ✅ Error message displayed
- ✅ User info still shows (cached from auth)
- ✅ Graceful degradation

### Test Scenario 4: UI/UX Testing

#### 4.1 Dark Mode Toggle ✅
**Steps**:
1. Click dark mode toggle in header
2. Observe UI changes

**Expected Results**:
- ✅ All components adapt to dark mode
- ✅ Text remains readable
- ✅ Preference persisted on refresh

#### 4.2 Responsive Design ✅
**Steps**:
1. Test on desktop (1920x1080)
2. Test on tablet (768x1024)
3. Test on mobile (375x667)

**Expected Results**:
- ✅ Sidebar collapses on mobile
- ✅ Cards stack vertically on mobile
- ✅ Forms remain usable
- ✅ No horizontal scroll

#### 4.3 Sidebar Behavior ✅
**Steps**:
1. Click sidebar toggle
2. Hover over collapsed sidebar
3. Test on mobile

**Expected Results**:
- ✅ Sidebar expands/collapses
- ✅ Content margin adjusts
- ✅ Icons visible when collapsed
- ✅ Mobile sidebar overlay works

### Test Scenario 5: Error States

#### 5.1 Network Errors ✅
**Steps**:
1. Disconnect network
2. Try to login
3. Try to load dashboard

**Expected Results**:
- ✅ Clear error messages
- ✅ No app crash
- ✅ Retry possible

#### 5.2 API Errors ✅
**Steps**:
1. Modify API URL to invalid endpoint
2. Try operations

**Expected Results**:
- ✅ Error messages displayed
- ✅ App remains functional
- ✅ Can navigate back

## Automated Testing

### Run Type Checks
```bash
npm run type-check
# Or (if not configured):
npx tsc --noEmit
```

**Expected**: No type errors

### Run ESLint
```bash
npm run lint
```

**Expected**: No linting errors (warnings acceptable)

### Run Build Test
```bash
npm run build
```

**Expected**:
- ✅ Build completes successfully
- ✅ No critical warnings
- ✅ Optimized bundle created

### Run Production Server
```bash
npm run build
npm start
```

**Expected**:
- ✅ Server starts on port 3000
- ✅ All pages accessible
- ✅ API calls work correctly

## Performance Testing

### Lighthouse Audit
1. Build production version
2. Run Lighthouse in Chrome DevTools
3. Check scores

**Target Scores**:
- Performance: > 90
- Accessibility: > 90
- Best Practices: > 90
- SEO: > 80

### Bundle Size Analysis
```bash
npm run build
# Check .next/standalone size
```

**Expected**: < 5MB total bundle

## Integration Testing

### API Integration Tests
```bash
# Test backend connectivity
curl http://100.81.76.55:30080/api/v1/health

# Test auth endpoint
curl -X POST http://100.81.76.55:30080/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test123"

# Test authenticated endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://100.81.76.55:30080/api/v1/auth/me
```

## Known Issues

### Issue 1: Node Version Requirement
**Status**: Known
**Impact**: Build fails with Node < 20
**Workaround**: Upgrade to Node 20+

### Issue 2: First Load Performance
**Status**: Expected
**Impact**: Initial page load may be slow
**Reason**: Next.js compiling on first request in dev mode
**Workaround**: Use production build for testing

## Test Results Template

```markdown
## Test Session

**Date**: YYYY-MM-DD
**Tester**: Name
**Environment**: Development/Production
**Backend**: Running/Stopped

### Results

| Test Scenario | Status | Notes |
|--------------|--------|-------|
| 1.1 Valid Login | ✅/❌ | |
| 1.2 Invalid Login | ✅/❌ | |
| 1.3 Logout | ✅/❌ | |
| 2.1 Unauth Access | ✅/❌ | |
| 2.2 Auth Access | ✅/❌ | |
| 3.1 Dashboard Load | ✅/❌ | |
| 3.2 Error Handling | ✅/❌ | |
| 4.1 Dark Mode | ✅/❌ | |
| 4.2 Responsive | ✅/❌ | |
| 4.3 Sidebar | ✅/❌ | |
| 5.1 Network Errors | ✅/❌ | |
| 5.2 API Errors | ✅/❌ | |

### Issues Found
1. [Description]
   - Severity: High/Medium/Low
   - Steps to reproduce:
   - Expected vs Actual:

### Recommendations
- [Recommendation]
```

## Next Steps After Testing

Once all tests pass:
1. Update tasks.md: Mark test task as complete
2. Create test results document
3. Deploy to staging environment
4. Perform user acceptance testing
5. Plan production deployment

## Support

For testing issues:
- Check backend logs: `kubectl logs -n homelab deployment/family-assistant-backend`
- Check Next.js logs: `npm run dev` output
- Browser console: Check for JavaScript errors
- Network tab: Verify API calls
