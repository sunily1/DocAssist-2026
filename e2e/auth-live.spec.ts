import { expect, test } from '@playwright/test';

const liveEnabled = process.env.LIVE_E2E === '1';
const testEmail = process.env.LIVE_AUTH_EMAIL || 'docassist-auth-e2e-20260716@example.com';
const testPassword = process.env.LIVE_AUTH_PASSWORD || 'DocAssist!2026Test';

test.describe('live authentication UI', () => {
  test.skip(!liveEnabled, 'LIVE_E2E=1 is required because this suite uses the real backend.');
  test.describe.configure({ mode: 'serial' });

  test('guest validation, signup, login persistence, and logout', async ({ page, context }) => {
    const pageErrors: string[] = [];
    page.on('pageerror', (error) => pageErrors.push(error.message));

    await page.goto('http://localhost:3000/');
    await expect(page).toHaveURL(/\/login\?redirect=(?:%2F|\/)$/);
    await expect(page.getByRole('heading', { name: '다시 오신 걸 환영해요' })).toBeVisible();

    await page.getByRole('button', { name: '로그인', exact: true }).click();
    await expect(page.locator('input[autocomplete="username"]')).toBeFocused();

    const passwordInput = page.locator('input[autocomplete="current-password"]');
    await passwordInput.fill('visibility-check');
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await page.getByRole('button', { name: '비밀번호 보기' }).click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
    await expect(passwordInput).toHaveValue('visibility-check');
    await page.getByRole('button', { name: '비밀번호 숨기기' }).click();

    await page.locator('input[autocomplete="username"]').fill('missing-user@docassist.test');
    await passwordInput.fill('WrongPassword!');
    const failedLogin = page.waitForResponse((response) => response.url().includes('/auth/login') && response.request().method() === 'POST');
    await page.getByRole('button', { name: '로그인', exact: true }).click();
    expect((await failedLogin).status()).toBe(400);
    await expect(page.getByRole('alert')).toContainText('이메일 또는 비밀번호가 올바르지 않습니다.');
    await expect(page.getByRole('button', { name: '로그인', exact: true })).toBeEnabled();

    await page.getByRole('button', { name: '회원가입' }).click();
    await expect(page).toHaveURL(/\/signup$/);
    await page.locator('input[autocomplete="name"]').fill('인증 기능 테스트');
    await page.locator('input[autocomplete="email"]').fill(testEmail);
    await page.locator('input[autocomplete="new-password"]').nth(0).fill(testPassword);
    await page.locator('input[autocomplete="new-password"]').nth(1).fill(testPassword);
    const signupResponse = page.waitForResponse((response) => response.url().includes('/auth/signup') && response.request().method() === 'POST');
    await page.getByRole('button', { name: '확인' }).click();
    expect((await signupResponse).status()).toBe(200);
    await expect(page).toHaveURL(/\/login$/);

    await page.locator('input[autocomplete="username"]').fill(testEmail);
    await page.locator('input[autocomplete="current-password"]').fill('ExistingUserWrong!');
    const wrongPasswordResponse = page.waitForResponse((response) => response.url().includes('/auth/login') && response.request().method() === 'POST');
    await page.getByRole('button', { name: '로그인', exact: true }).click();
    expect((await wrongPasswordResponse).status()).toBe(400);
    await expect(page.getByRole('alert')).toContainText('이메일 또는 비밀번호가 올바르지 않습니다.');

    await page.locator('input[autocomplete="current-password"]').fill(testPassword);
    const loginResponse = page.waitForResponse((response) => response.url().includes('/auth/login') && response.request().method() === 'POST');
    await page.getByRole('button', { name: '로그인', exact: true }).click();
    expect((await loginResponse).status()).toBe(200);
    await expect(page).toHaveURL('http://localhost:3000/');
    await expect(page.locator('.account-card')).toContainText('인증 기능 테스트');
    await expect(page.locator('.account-card')).toContainText(testEmail);

    await page.reload();
    await expect(page).toHaveURL('http://localhost:3000/');
    await expect(page.locator('.account-card')).toContainText(testEmail);

    const sessionOnlyPage = await context.newPage();
    await sessionOnlyPage.goto('http://localhost:3000/');
    await expect(sessionOnlyPage).toHaveURL(/\/login\?redirect=(?:%2F|\/)$/);
    await sessionOnlyPage.close();

    await page.getByRole('button', { name: '로그아웃' }).click();
    await expect(page).toHaveURL(/\/login$/);

    await page.locator('input[autocomplete="username"]').fill(testEmail);
    await page.locator('input[autocomplete="current-password"]').fill(testPassword);
    await page.getByLabel('로그인 유지').check();
    await page.getByRole('button', { name: '로그인', exact: true }).click();
    await expect(page).toHaveURL('http://localhost:3000/');

    const rememberedPage = await context.newPage();
    await rememberedPage.goto('http://localhost:3000/');
    await expect(rememberedPage).toHaveURL('http://localhost:3000/');
    await expect(rememberedPage.locator('.account-card')).toContainText(testEmail);
    await rememberedPage.getByRole('button', { name: '로그아웃' }).click();
    await expect(rememberedPage).toHaveURL(/\/login$/);
    await page.goto('http://localhost:3000/profile');
    await expect(page).toHaveURL(/\/login\?redirect=(?:%2F|\/)profile$/);
    expect(pageErrors).toEqual([]);
    await page.screenshot({ path: '/tmp/docassist-auth-live-final.png', fullPage: true });
  });
});
