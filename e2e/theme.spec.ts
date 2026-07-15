import { test, expect } from '@playwright/test';

test('theme toggle works only in profile page', async ({ page }) => {
  // Mock API
  await page.route('**/api/v1/auth/login', async route => {
    await route.fulfill({ json: { access_token: 'fake-token' } });
  });
  await page.route('**/api/v1/users/me', async route => {
    await route.fulfill({ 
      json: { 
        id: '1', 
        email: 'test@example.com', 
        name: 'Test User', 
        role: 'USER',
        profile_settings: {
            ui: { fontSize: 'md', sentenceMode: true },
            assist: { level: 'mid', termDepth: 3, evidenceMode: 'panel' }
        }
      } 
    });
  });
  await page.route('**/api/v1/users/me', async route => {
      // Handle PATCH for saving settings
      if (route.request().method() === 'PATCH') {
          await route.fulfill({ json: { id: '1', email: 'test@example.com' } });
      } else {
          await route.continue();
      }
  });

  // 1. Go to Profile page (will redirect to login first)
  await page.goto('http://localhost:3000/profile');
  
  // Login flow
  if (page.url().includes('login')) {
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password');
    await page.click('button[type="submit"]');
    // Wait for navigation
    await page.waitForURL('**/');
  }

  // Ensure we are on Profile page
  await page.goto('http://localhost:3000/profile');

  // 2. Check sidebar does NOT have theme toggle
  const sidebar = page.locator('.sidebar');
  await expect(sidebar.locator('.sb-item', { hasText: 'Dark' })).toBeHidden();
  await expect(sidebar.locator('.sb-item', { hasText: 'Light' })).toBeHidden();

  // 3. Find Theme settings in Content area
  // There are buttons "라이트" and "다크"
  const lightBtn = page.locator('button', { hasText: '라이트' });
  const darkBtn = page.locator('button', { hasText: '다크' });

  // Initial state check
  const html = page.locator('html');
  await expect(html).toHaveAttribute('data-theme', 'light');

  // 4. Switch to Dark
  await darkBtn.click();
  await expect(html).toHaveAttribute('data-theme', 'dark');
  await expect(darkBtn).toHaveClass(/on/); // Check active class

  // 5. Switch to Light
  await lightBtn.click();
  await expect(html).toHaveAttribute('data-theme', 'light');
  await expect(lightBtn).toHaveClass(/on/); // Check active class
});
