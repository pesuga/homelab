import { test, expect } from '@playwright/test';

/**
 * E2E tests for authentication flow
 *
 * Tests login, logout, protected routes, and token management
 */

const TEST_USER = {
  username: 'testuser',
  password: 'testpass123',
};

const INVALID_CREDENTIALS = {
  username: 'invalid',
  password: 'wrongpass',
};

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any stored tokens before each test
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('should display login page for unauthenticated users', async ({ page }) => {
    await page.goto('/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);

    // Login form elements should be visible
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill login form with invalid credentials
    await page.locator('input[name="username"]').fill(INVALID_CREDENTIALS.username);
    await page.locator('input[name="password"]').fill(INVALID_CREDENTIALS.password);

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Should show error message
    await expect(page.locator('text=/incorrect.*username.*password/i')).toBeVisible({
      timeout: 5000,
    });

    // Should remain on login page
    await expect(page).toHaveURL(/\/login/);
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill login form
    await page.locator('input[name="username"]').fill(TEST_USER.username);
    await page.locator('input[name="password"]').fill(TEST_USER.password);

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Should redirect to dashboard after successful login
    await expect(page).toHaveURL(/\/(dashboard|home)/, {
      timeout: 10000,
    });

    // Token should be stored in localStorage
    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token).toBeTruthy();

    // User should see their profile or dashboard
    await expect(page.locator('text=/welcome|dashboard/i')).toBeVisible();
  });

  test('should protect routes from unauthenticated access', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/family');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, {
      timeout: 5000,
    });
  });

  test('should allow access to protected routes when authenticated', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(TEST_USER.username);
    await page.locator('input[name="password"]').fill(TEST_USER.password);
    await page.locator('button[type="submit"]').click();

    // Wait for redirect to complete
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });

    // Navigate to protected route
    await page.goto('/family');

    // Should stay on family page
    await expect(page).toHaveURL(/\/family/);

    // Page content should be visible
    await expect(page.locator('text=/family.*member/i')).toBeVisible();
  });

  test('should successfully logout', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(TEST_USER.username);
    await page.locator('input[name="password"]').fill(TEST_USER.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });

    // Click logout button (adjust selector based on actual UI)
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign Out")');
    await logoutButton.click();

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, {
      timeout: 5000,
    });

    // Token should be cleared
    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token).toBeNull();
  });

  test('should handle token expiration', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(TEST_USER.username);
    await page.locator('input[name="password"]').fill(TEST_USER.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });

    // Manually expire token in localStorage
    await page.evaluate(() => {
      const expiry = Date.now() - 1000; // Expired 1 second ago
      localStorage.setItem('token_expiry', expiry.toString());
    });

    // Try to access protected route
    await page.goto('/family');

    // Should redirect to login due to expired token
    await expect(page).toHaveURL(/\/login/, {
      timeout: 5000,
    });
  });

  test('should handle 401 responses by redirecting to login', async ({ page }) => {
    // Set invalid token in localStorage
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'invalid_token_12345');
      localStorage.setItem('token_expiry', (Date.now() + 3600000).toString());
    });

    // Try to make authenticated request (navigate to protected page)
    await page.goto('/family');

    // API will return 401, axios interceptor should redirect to login
    await expect(page).toHaveURL(/\/login/, {
      timeout: 10000,
    });

    // Token should be cleared
    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token).toBeNull();
  });

  test('should maintain session across page reloads', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(TEST_USER.username);
    await page.locator('input[name="password"]').fill(TEST_USER.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });

    // Reload page
    await page.reload();

    // Should remain authenticated (not redirect to login)
    await expect(page).toHaveURL(/\/(dashboard|home)/);

    // User should still see their profile
    await expect(page.locator('text=/welcome|dashboard/i')).toBeVisible();
  });
});
