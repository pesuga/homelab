# E2E Testing with Playwright

Comprehensive end-to-end testing suite for the Family Assistant frontend application.

## Overview

This E2E test suite validates:
- **Authentication flows**: Login, logout, token management, session persistence
- **Family member management**: CRUD operations, optimistic updates, error handling
- **User experience**: Loading states, error messages, responsive design
- **Error recovery**: API failures, rollback mechanisms, retry logic

## Test Structure

```
e2e/
├── auth.spec.ts              # Authentication flow tests (10 tests)
├── family-members.spec.ts    # Family member CRUD tests (11 tests)
├── fixtures/
│   └── auth.ts               # Reusable authentication helpers
└── README.md                 # This file
```

## Prerequisites

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Or install specific browsers
npx playwright install chromium firefox
```

## Running Tests

### Run all E2E tests
```bash
npm run test:e2e
```

### Run tests in UI mode (interactive)
```bash
npm run test:e2e:ui
```

### Run tests with browser visible (headed mode)
```bash
npm run test:e2e:headed
```

### Run tests in debug mode
```bash
npm run test:e2e:debug
```

### Run specific test file
```bash
npx playwright test auth.spec.ts
```

### Run specific test by name
```bash
npx playwright test -g "should successfully login"
```

### Run tests on specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Reports

### View HTML report
```bash
npm run test:e2e:report
```

Reports are generated in `playwright-report/` directory.

### CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

Results are available in GitHub Actions artifacts.

## Writing New Tests

### Basic test structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

### Using authentication fixtures

```typescript
import { test, expect, login } from './fixtures/auth';

test.describe('Protected Feature', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should access protected route', async ({ page }) => {
    await page.goto('/protected');
    // Test authenticated behavior
  });
});
```

### Using authenticated page fixture

```typescript
import { test, expect } from './fixtures/auth';

test('should work with authenticated page', async ({ authenticatedPage }) => {
  // authenticatedPage is already logged in
  await authenticatedPage.goto('/dashboard');
  await expect(authenticatedPage).toHaveURL(/\/dashboard/);
});
```

## Test Coverage

### Authentication Tests (10 tests)
- ✅ Display login page for unauthenticated users
- ✅ Show error for invalid credentials
- ✅ Successfully login with valid credentials
- ✅ Protect routes from unauthenticated access
- ✅ Allow access to protected routes when authenticated
- ✅ Successfully logout
- ✅ Handle token expiration
- ✅ Handle 401 responses with redirect
- ✅ Maintain session across page reloads
- ✅ Clear token on logout

### Family Member Management Tests (11 tests)
- ✅ Display family members list
- ✅ Display member details
- ✅ Create new family member
- ✅ Update member with optimistic update
- ✅ Handle update failure with rollback
- ✅ Delete family member
- ✅ Handle delete failure with rollback
- ✅ Filter members by role
- ✅ Search members by name
- ✅ Handle loading states
- ✅ Handle API errors gracefully

## Configuration

### `playwright.config.ts`

Key configuration options:
- **testDir**: `./e2e` - Test directory location
- **baseURL**: `http://localhost:5173` - Default base URL
- **retries**: 2 on CI, 0 locally
- **workers**: 1 on CI, automatic locally
- **timeout**: 30 seconds per test
- **projects**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari

### Environment Variables

```bash
# Override base URL
PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e

# CI mode (more retries, single worker)
CI=true npm run test:e2e
```

## Best Practices

### 1. Use data-testid for stable selectors
```typescript
// Good
await page.locator('[data-testid="login-button"]').click();

// Avoid
await page.locator('button:has-text("Login")').click();
```

### 2. Wait for network idle before assertions
```typescript
await page.goto('/family');
await page.waitForLoadState('networkidle');
await expect(page.locator('.member-card')).toBeVisible();
```

### 3. Use explicit waits for dynamic content
```typescript
await expect(page.locator('.member-card')).toBeVisible({ timeout: 10000 });
```

### 4. Test error scenarios
```typescript
// Intercept API to simulate errors
await page.route('**/api/family/members', (route) => {
  route.fulfill({ status: 500, body: '{"detail":"Error"}' });
});
```

### 5. Clean up state between tests
```typescript
test.beforeEach(async ({ page }) => {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
});
```

## Debugging Tests

### Interactive debugging
```bash
# Open Playwright Inspector
npm run test:e2e:debug

# Run single test in debug mode
npx playwright test auth.spec.ts:10 --debug
```

### Generate tests with Codegen
```bash
npm run test:e2e:codegen
```

### View trace files
```bash
npx playwright show-trace trace.zip
```

### Console logs
```typescript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

## Troubleshooting

### Tests failing on CI but passing locally
- Check browser versions: `npx playwright --version`
- Review CI environment variables
- Check for timing issues (add explicit waits)
- Review screenshots and videos in artifacts

### Authentication tests failing
- Verify backend is running: `curl http://localhost:8000/health`
- Check test credentials match database
- Verify JWT token configuration

### Timeout errors
- Increase timeout in `playwright.config.ts`
- Add explicit waits: `await page.waitForLoadState('networkidle')`
- Check network performance

### Element not found errors
- Use Playwright Inspector to debug selectors
- Add explicit waits before assertions
- Check if element is in viewport: `await element.scrollIntoViewIfNeeded()`

## Performance Targets

- **Test suite execution**: < 5 minutes (all browsers)
- **Single test**: < 30 seconds
- **Page load**: < 3 seconds
- **API response**: < 1 second

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
- [GitHub Actions Integration](https://playwright.dev/docs/ci-intro)
