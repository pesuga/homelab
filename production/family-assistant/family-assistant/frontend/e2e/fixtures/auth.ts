import { test as base, Page } from '@playwright/test';

/**
 * Authentication fixtures for E2E tests
 *
 * Provides reusable authentication utilities and test data
 */

export const TEST_USERS = {
  parent: {
    username: 'parent_user',
    password: 'parent_pass',
    role: 'parent',
  },
  teen: {
    username: 'teen_user',
    password: 'teen_pass',
    role: 'teen',
  },
  child: {
    username: 'child_user',
    password: 'child_pass',
    role: 'child',
  },
  default: {
    username: 'testuser',
    password: 'testpass123',
    role: 'parent',
  },
};

/**
 * Login helper function
 */
export async function login(page: Page, credentials = TEST_USERS.default) {
  await page.goto('/login');

  // Fill credentials
  await page.locator('input[name="username"]').fill(credentials.username);
  await page.locator('input[name="password"]').fill(credentials.password);

  // Submit form
  await page.locator('button[type="submit"]').click();

  // Wait for redirect
  await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });

  // Verify token is stored
  const token = await page.evaluate(() => localStorage.getItem('auth_token'));
  if (!token) {
    throw new Error('Login failed: No token stored');
  }

  return token;
}

/**
 * Logout helper function
 */
export async function logout(page: Page) {
  const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign Out")');
  await logoutButton.click();

  // Wait for redirect to login
  await page.waitForURL(/\/login/, { timeout: 5000 });

  // Verify token is cleared
  const token = await page.evaluate(() => localStorage.getItem('auth_token'));
  if (token) {
    throw new Error('Logout failed: Token still present');
  }
}

/**
 * Set authentication token directly (for testing authenticated states)
 */
export async function setAuthToken(page: Page, token: string, expiresIn = 3600) {
  await page.evaluate(
    ({ token, expiresIn }) => {
      localStorage.setItem('auth_token', token);
      const expiry = Date.now() + expiresIn * 1000;
      localStorage.setItem('token_expiry', expiry.toString());
    },
    { token, expiresIn }
  );
}

/**
 * Clear authentication token
 */
export async function clearAuthToken(page: Page) {
  await page.evaluate(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('token_expiry');
  });
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  return page.evaluate(() => {
    const token = localStorage.getItem('auth_token');
    const expiry = localStorage.getItem('token_expiry');

    if (!token || !expiry) return false;

    return Date.now() < parseInt(expiry);
  });
}

/**
 * Extended test fixture with authentication helpers
 */
export const test = base.extend({
  authenticatedPage: async ({ page }, use) => {
    // Login before test
    await login(page);

    // Run test
    await use(page);

    // Cleanup (logout) after test
    await logout(page).catch(() => {
      // Ignore logout errors (page might be closed)
    });
  },
});

export { expect } from '@playwright/test';
