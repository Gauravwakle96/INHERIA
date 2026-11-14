import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('incomplete handover explains blockers before closure and links to recovery work', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Try a fresh handover' }).click();
  await expect(page.getByRole('combobox', { name: 'Active project' })).toBeVisible();
  await page.locator('.nav-link[href="/handover"]').click();
  const readiness = page.getByRole('region', { name: 'Handover closure readiness' });
  await expect(readiness).toContainText('A verified handover has not been generated.');
  await expect(readiness.getByRole('link', { name: 'Knowledge access', exact: true })).toHaveAttribute('href', '/team');
  await expect(readiness.getByRole('link', { name: 'Source versions & evidence' })).toHaveAttribute('href', '/sources');
  await expect(readiness.getByRole('link', { name: 'Required readiness checks', exact: true })).toHaveAttribute('href', '#required-readiness-checks');
  await readiness.getByRole('link', { name: 'Acceptance & supervisor review' }).click();
  await expect(page.getByRole('heading', { name: 'Verified knowledge transfer', exact: true })).toBeVisible();
});

test('changed evidence and readiness failures stop closure; refresh recovers the panel', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open judge workspace' }).click();
  await expect(page.getByRole('region', { name: 'Handover closure readiness' })).toContainText('still meets its current checks');
  const pid = await page.getByRole('combobox', { name: 'Active project' }).inputValue();
  const transitions = await (await page.request.get(`/api/projects/${pid}/transitions`)).json();
  const original = transitions[0];
  await page.route(`**/api/projects/${pid}/transitions`, route => route.fulfill({ json: [{ ...original, status: 'approved' }] }));
  let state: 'blocked' | 'error' | 'ready' = 'blocked';
  await page.route(`**/api/projects/${pid}/transitions/${original.id}/readiness`, route => state === 'error'
    ? route.fulfill({ status: 503, json: { detail: 'Readiness temporarily unavailable.' } })
    : route.fulfill({ json: { accepted: 8, total: 8, validated: 11, exercise_total: 11, ready: state === 'ready', blockers: state === 'ready' ? [] : ['Handover sources changed, were revoked or are inaccessible; revalidation is required.'], evidence_coverage: { numerator: state === 'ready' ? 8 : 7, denominator: 8 }, limitations: ['Checks record human review, not cloud execution.'] } }));
  await page.reload();
  const panel = page.getByRole('region', { name: 'Handover closure readiness' });
  const close = page.getByRole('button', { name: 'Close transition', exact: true });
  await expect(panel).toContainText('revalidation is required');
  await expect(close).toBeDisabled();
  state = 'error';
  await panel.getByRole('button', { name: 'Refresh readiness' }).click();
  await expect(panel.getByRole('alert')).toContainText('Readiness temporarily unavailable.');
  await expect(close).toBeDisabled();
  state = 'ready';
  await panel.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(close).toBeEnabled();
  await expect(panel).toContainText('All required checks pass.');
  for (const width of [390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const results = await new AxeBuilder({ page }).include('[aria-label="Handover closure readiness"]').withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(results.violations.map(v => v.id)).toEqual([]);
  }
});

test('request limits show cooldown and do not trigger immediate automatic retries', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Try a fresh handover' }).click();
  await expect(page.getByRole('combobox', { name: 'Active project' })).toBeVisible();
  let calls = 0;
  await page.route('**/api/projects/*/transitions/*/readiness', route => ++calls === 1
    ? route.fulfill({ status: 429, headers: { 'Retry-After': '3' }, json: { detail: 'Request limit reached. Retry shortly.' } })
    : route.continue());
  await page.locator('.nav-link[href="/handover"]').click();
  const panel = page.getByRole('region', { name: 'Handover closure readiness' });
  const retry = panel.getByRole('button', { name: 'Try again', exact: true });
  await expect(panel).toContainText('Retry available in');
  await expect(retry).toBeDisabled();
  await expect(panel.getByRole('button', { name: 'Refresh readiness' })).toHaveCount(0);
  await page.waitForTimeout(1200);
  expect(calls).toBe(1);
  await expect(retry).toBeEnabled({ timeout: 4000 });
  await retry.click();
  await expect(panel).toContainText('A verified handover has not been generated.');
  expect(calls).toBe(2);
});

test('public guide explains the submitted improvements in both themes and mobile layouts', async ({ page }) => {
  await page.goto('/demo');
  const improvements = page.getByRole('region', { name: 'Three delivered improvements' });
  await expect(improvements).toContainText('one-time invitation');
  await expect(improvements).toContainText('Sources → New version → Impact');
  await expect(improvements).toContainText('Required checks must pass');
  for (const theme of ['dark', 'light']) {
    if (theme === 'light') await page.getByRole('button', { name: 'Switch to day mode' }).click();
    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      const result = await new AxeBuilder({ page }).include('[aria-label="Three delivered improvements"]').withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      expect(result.violations.map(v => v.id)).toEqual([]);
    }
  }
});

test('manual access refresh updates externally changed membership and source permissions', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open judge workspace' }).click();
  await expect(page.getByRole('combobox', { name: 'Active project' })).toBeVisible();
  const pid = await page.getByRole('combobox', { name: 'Active project' }).inputValue();
  const members: { id: string; name: string }[] = await (await page.request.get(`/api/team?project_id=${pid}`)).json();
  await page.locator('.nav-link[href="/team"]').click();
  await expect(page.getByRole('heading', { name: 'Savinay', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Refresh access', exact: true })).toBeEnabled();
  let sourceReads = 0;
  await page.route(`**/api/projects/${pid}/sources`, route => { sourceReads++; return route.continue(); });
  await page.route(`**/api/team?project_id=${pid}`, route => route.fulfill({ json: members.filter(member => member.name !== 'Savinay') }));
  await page.getByRole('button', { name: 'Refresh access', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Savinay', exact: true })).toHaveCount(0);
  await expect.poll(() => sourceReads).toBeGreaterThan(0);
  await expect(page.getByRole('button', { name: 'Refresh access', exact: true })).toBeEnabled();
});
