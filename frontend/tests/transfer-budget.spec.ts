import { expect, test } from '@playwright/test';

test('idle workspace does not poll; active work refreshes results once and stops', async ({ page }) => {
  test.setTimeout(90000);
  await page.goto('/');
  await page.getByRole('button', { name: 'Try a fresh handover' }).click();
  await expect(page.getByRole('region', { name: 'Your next handover step' })).toContainText('Reconstruct');
  await page.waitForLoadState('networkidle');
  const requests: string[] = [];
  page.on('request', request => { if (request.url().includes('/api/projects/')) requests.push(request.url()); });
  await page.waitForTimeout(12000);
  expect(requests).toEqual([]);

  // Keep one status signal active long enough to exercise polling even though
  // the real local extraction finishes quickly. Results themselves stay real.
  let statusChecks = 0;
  let tracking = false;
  await page.route('**/api/projects/*/activity-status', async route => {
    if (tracking && ++statusChecks < 3) {
      await route.fulfill({ json: [{ id: 'running-test-signal', kind: 'investigation', status: 'running' }] });
    } else await route.continue();
  });
  tracking = true;
  requests.length = 0;
  await page.getByRole('button', { name: 'Investigate project', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Your next handover step' })).toContainText('Verify & review', { timeout: 30000 });
  await expect.poll(() => statusChecks).toBeGreaterThanOrEqual(3);
  await expect(page.locator('.investigation-report').getByText('Completed', { exact: true })).toBeVisible();
  await page.waitForLoadState('networkidle');
  requests.length = 0;
  await page.waitForTimeout(12000);
  expect(requests).toEqual([]);
  await page.reload();
  await expect(page.getByRole('region', { name: 'Your next handover step' })).toContainText('Verify & review');
});

test('failed background work refreshes dependent state and stops polling', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Try a fresh handover' }).click();
  await expect(page.getByRole('region', { name: 'Your next handover step' })).toContainText('Reconstruct');
  let checks = 0;
  await page.route('**/api/projects/*/investigations', async route => {
    if (route.request().method() === 'POST') await route.fulfill({ json: { id: 'failed-job', status: 'queued', report: {}, created_at: new Date().toISOString() } });
    else await route.fulfill({ json: [{ id: 'failed-job', status: checks < 2 ? 'running' : 'failed', report: { findings: [], questions: [], limitations: [], unknowns: [] }, created_at: new Date().toISOString() }] });
  });
  await page.route('**/api/projects/*/activity-status', route => route.fulfill({ json: ++checks < 2 ? [{ id: 'failed-job', kind: 'investigation', status: 'running' }] : [] }));
  await page.getByRole('button', { name: 'Investigate project', exact: true }).click();
  await expect(page.locator('.investigation-report').getByText('Failed', { exact: true })).toBeVisible({ timeout: 20000 });
  const stoppedAt = checks;
  await page.waitForTimeout(6500);
  expect(checks).toBe(stoppedAt);
});
