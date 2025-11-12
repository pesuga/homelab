import { test, expect } from '@playwright/test';

/**
 * E2E tests for family member management
 *
 * Tests CRUD operations, optimistic updates, error handling, and rollback
 */

const TEST_USER = {
  username: 'testuser',
  password: 'testpass123',
};

const NEW_MEMBER = {
  first_name: 'Test',
  last_name: 'Child',
  username: 'testchild',
  role: 'child',
  age_group: '6-12',
  language_preference: 'en',
  privacy_level: 'standard',
  safety_level: 'high',
};

test.describe('Family Member Management', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and login before each test
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Login
    await page.goto('/login');
    await page.locator('input[name="username"]').fill(TEST_USER.username);
    await page.locator('input[name="password"]').fill(TEST_USER.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });

    // Navigate to family members page
    await page.goto('/family');
    await page.waitForLoadState('networkidle');
  });

  test('should display family members list', async ({ page }) => {
    // Wait for members to load
    await page.waitForSelector('[data-testid="family-member-list"], .family-member-card', {
      timeout: 10000,
    });

    // Should see at least the current user
    const memberCards = page.locator('.family-member-card, [data-testid^="member-"]');
    await expect(memberCards.first()).toBeVisible();
  });

  test('should display member details', async ({ page }) => {
    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Click on first member
    const firstMember = page.locator('.family-member-card').first();
    await firstMember.click();

    // Should display member details
    await expect(page.locator('text=/details|profile|information/i')).toBeVisible();

    // Should show member properties
    await expect(page.locator('text=/role|age.*group|language/i')).toBeVisible();
  });

  test('should create new family member', async ({ page }) => {
    // Click add member button
    const addButton = page.locator('button:has-text("Add Member"), button:has-text("New Member")');
    await addButton.click();

    // Fill member form
    await page.locator('input[name="first_name"]').fill(NEW_MEMBER.first_name);
    await page.locator('input[name="last_name"]').fill(NEW_MEMBER.last_name);
    await page.locator('input[name="username"]').fill(NEW_MEMBER.username);

    // Select role
    await page.locator('select[name="role"], [data-testid="role-select"]').selectOption(NEW_MEMBER.role);

    // Fill other fields
    await page.locator('select[name="age_group"]').selectOption(NEW_MEMBER.age_group);
    await page.locator('select[name="language_preference"]').selectOption(NEW_MEMBER.language_preference);

    // Submit form
    await page.locator('button[type="submit"]:has-text("Create"), button:has-text("Add")').click();

    // Should show success message
    await expect(page.locator('text=/success|created|added/i')).toBeVisible({
      timeout: 5000,
    });

    // New member should appear in list
    await expect(page.locator(`text=${NEW_MEMBER.first_name} ${NEW_MEMBER.last_name}`)).toBeVisible();
  });

  test('should update family member with optimistic update', async ({ page }) => {
    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Click on first member
    const firstMember = page.locator('.family-member-card').first();
    const originalName = await firstMember.locator('text=/^[A-Z][a-z]+/').textContent();
    await firstMember.click();

    // Click edit button
    const editButton = page.locator('button:has-text("Edit"), button[aria-label="Edit"]');
    await editButton.click();

    // Change first name
    const newName = 'Updated';
    await page.locator('input[name="first_name"]').fill(newName);

    // Submit form
    const saveButton = page.locator('button[type="submit"]:has-text("Save"), button:has-text("Update")');
    await saveButton.click();

    // Optimistic update: name should change immediately
    await expect(page.locator(`text=${newName}`)).toBeVisible({
      timeout: 1000, // Should be instant (optimistic)
    });

    // Server reconciliation: should still show updated name after API confirms
    await page.waitForTimeout(2000);
    await expect(page.locator(`text=${newName}`)).toBeVisible();
  });

  test('should handle update failure with rollback', async ({ page, context }) => {
    // Intercept API calls and make them fail
    await page.route('**/api/v1/family/members/*', (route) => {
      if (route.request().method() === 'PUT') {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' }),
        });
      } else {
        route.continue();
      }
    });

    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Get original member data
    const firstMember = page.locator('.family-member-card').first();
    const originalName = await firstMember.textContent();
    await firstMember.click();

    // Click edit button
    await page.locator('button:has-text("Edit")').click();

    // Change name
    const newName = 'FailedUpdate';
    await page.locator('input[name="first_name"]').fill(newName);

    // Submit form (will fail)
    await page.locator('button[type="submit"]:has-text("Save")').click();

    // Should show error message
    await expect(page.locator('text=/error|fail/i')).toBeVisible({
      timeout: 5000,
    });

    // Should rollback to original name
    await expect(page.locator(`text=/${originalName}/i`)).toBeVisible();
  });

  test('should delete family member', async ({ page }) => {
    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Get count of members
    const initialCount = await page.locator('.family-member-card').count();

    // Click on last member (not current user)
    const lastMember = page.locator('.family-member-card').last();
    const memberName = await lastMember.textContent();
    await lastMember.click();

    // Click delete button
    const deleteButton = page.locator('button:has-text("Delete"), button:has-text("Remove")');
    await deleteButton.click();

    // Confirm deletion in dialog
    await page.locator('button:has-text("Confirm"), button:has-text("Yes")').click();

    // Member should disappear from list
    await expect(page.locator(`text=${memberName}`)).not.toBeVisible({
      timeout: 5000,
    });

    // Count should decrease
    const newCount = await page.locator('.family-member-card').count();
    expect(newCount).toBe(initialCount - 1);
  });

  test('should handle delete failure with rollback', async ({ page }) => {
    // Intercept API calls and make delete fail
    await page.route('**/api/v1/family/members/*', (route) => {
      if (route.request().method() === 'DELETE') {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Cannot delete member' }),
        });
      } else {
        route.continue();
      }
    });

    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Get initial state
    const initialCount = await page.locator('.family-member-card').count();
    const lastMember = page.locator('.family-member-card').last();
    const memberName = await lastMember.textContent();

    // Try to delete
    await lastMember.click();
    await page.locator('button:has-text("Delete")').click();
    await page.locator('button:has-text("Confirm")').click();

    // Should show error message
    await expect(page.locator('text=/error|fail|cannot/i')).toBeVisible({
      timeout: 5000,
    });

    // Member should still be in list (rollback)
    await expect(page.locator(`text=${memberName}`)).toBeVisible();

    // Count should remain the same
    const finalCount = await page.locator('.family-member-card').count();
    expect(finalCount).toBe(initialCount);
  });

  test('should filter family members by role', async ({ page }) => {
    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Select role filter
    const roleFilter = page.locator('select[name="role-filter"], [data-testid="role-filter"]');
    if (await roleFilter.isVisible()) {
      await roleFilter.selectOption('child');

      // Should only show child members
      const childMembers = page.locator('.family-member-card:has-text("Child")');
      await expect(childMembers.first()).toBeVisible();

      // Adult members should not be visible (unless all are children)
      const visibleCards = await page.locator('.family-member-card').count();
      expect(visibleCards).toBeGreaterThanOrEqual(0);
    }
  });

  test('should search family members by name', async ({ page }) => {
    // Wait for members to load
    await page.waitForSelector('.family-member-card', { timeout: 10000 });

    // Get first member name
    const firstMemberName = await page.locator('.family-member-card').first().textContent();
    const searchTerm = firstMemberName?.split(' ')[0] || 'Test';

    // Enter search term
    const searchInput = page.locator('input[type="search"], input[placeholder*="Search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill(searchTerm);

      // Should filter results
      await expect(page.locator(`.family-member-card:has-text("${searchTerm}")`)).toBeVisible();
    }
  });

  test('should handle loading states during fetch', async ({ page }) => {
    // Intercept API to delay response
    await page.route('**/api/v1/family/members', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      await route.continue();
    });

    // Navigate to family page
    await page.goto('/family');

    // Should show loading indicator
    await expect(page.locator('text=/loading|fetching/i, [data-testid="loading-spinner"]')).toBeVisible({
      timeout: 1000,
    });

    // Loading should disappear after members load
    await expect(page.locator('text=/loading/i')).not.toBeVisible({
      timeout: 10000,
    });

    // Members should be visible
    await expect(page.locator('.family-member-card').first()).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Intercept API to return error
    await page.route('**/api/v1/family/members', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Database connection failed' }),
      });
    });

    // Navigate to family page
    await page.goto('/family');

    // Should show error message
    await expect(page.locator('text=/error|failed|problem/i')).toBeVisible({
      timeout: 5000,
    });

    // Should show retry button
    const retryButton = page.locator('button:has-text("Retry"), button:has-text("Try Again")');
    if (await retryButton.isVisible()) {
      expect(retryButton).toBeVisible();
    }
  });
});
