import { test, expect } from '@playwright/test';

test('theme toggle works only in profile page', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('token', 'theme-test-token');
    localStorage.setItem('role', 'USER');
    localStorage.setItem('theme', 'light');
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/users/me')) {
      return route.fulfill({ json: {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'USER',
        profile_settings: {
          ui: { theme: 'light', fontSize: 'md', customFontSize: 16, sentenceMode: true },
          assist: { level: 'easy', termDepth: 3, evidenceMode: 'panel' },
        },
      } });
    }
    return route.fulfill({ json: {} });
  });

  // 1. Go to Profile page with an isolated authenticated state.
  await page.goto('http://localhost:3000/profile');

  // 2. Check sidebar does NOT have theme toggle
  const sidebar = page.locator('.sidebar');
  await expect(sidebar.locator('.sb-item', { hasText: 'Dark' })).toBeHidden();
  await expect(sidebar.locator('.sb-item', { hasText: 'Light' })).toBeHidden();

  // 3. Find Theme settings in Content area
  // There are buttons "라이트" and "다크"
  const lightBtn = page.getByRole('button', { name: '밝게', exact: true });
  const darkBtn = page.getByRole('button', { name: '어둡게', exact: true });

  // Initial state check
  const html = page.locator('html');
  await expect(html).toHaveAttribute('data-theme', 'light');

  // 4. Switch to Dark
  await darkBtn.click();
  await expect(html).toHaveAttribute('data-theme', 'dark');
  await expect(darkBtn).toHaveClass(/active/); // Check active class

  // 5. Switch to Light
  await lightBtn.click();
  await expect(html).toHaveAttribute('data-theme', 'light');
  await expect(lightBtn).toHaveClass(/active/); // Check active class
});
