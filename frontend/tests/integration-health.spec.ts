import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('repository scope and partial-sync warnings stay visible without exposing credentials', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Try a fresh handover' }).click();
  await expect(page.getByRole('combobox', { name: 'Active project' })).toBeVisible();
  await page.route('**/api/projects/*/connections', route => route.fulfill({ json: [{ id: 'qa-connection', name: 'owned/repository', provider: 'github', repository: 'owned/repository', status: 'partial', has_token: true, scope: 'Recent activity and up to five text documents; complete history is outside this snapshot.', warnings: ['Repository structure is truncated; absent files cannot be inferred as missing.'] }] }));
  await page.locator('.nav-link[href="/sources"]').click();
  const row = page.locator('.connection-row');
  await expect(row).toContainText('complete history is outside this snapshot');
  await expect(row).toContainText('Sync warning: Repository structure is truncated');
  await expect(row).toContainText('Encrypted access token');
  await expect(row.getByRole('textbox')).toHaveCount(0);
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const results = await new AxeBuilder({ page }).include('.connection-list').withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(results.violations.map(item => item.id)).toEqual([]);
  }
});
