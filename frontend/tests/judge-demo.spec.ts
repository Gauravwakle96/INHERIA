import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { Claim, Transition, User } from '../src/types';

async function begin(page: Page) {
  await page.goto('/');
  await page.getByRole('link', { name: 'Explore demo' }).click();
  await expect(page.getByRole('heading', { name: 'Gaurav leaves. Savinay can continue.' })).toBeVisible();
  await page.getByRole('button', { name: 'Start interactive demo' }).click();
  await expect(page.getByRole('combobox', { name: 'Switch demo role' })).toHaveValue(/.+/);
  return await page.getByRole('combobox', { name: 'Active project' }).inputValue();
}

async function role(page: Page, name: string) {
  const people: User[] = await (await page.request.get('/api/auth/judge-demo/people')).json();
  await page.getByRole('combobox', { name: 'Switch demo role' }).selectOption(people.find(p => p.name === name)!.id);
  await expect(page.locator('.user-summary strong')).toHaveText(name);
}

test('judge opens an isolated workspace directly from sign-in and keeps it on refresh', async ({ page, browser }) => {
  await page.goto('/');
  const entry = page.getByRole('region', { name: 'Judge demo access' });
  await expect(entry).toContainText('No email, password or API key needed.');
  await expect(entry.locator('input')).toHaveCount(0);
  await entry.getByRole('button', { name: 'Open judge workspace' }).click();
  await expect(page.getByRole('heading', { name: 'Handover workspace', level: 1 })).toBeVisible();
  await expect(page.locator('.user-summary strong')).toHaveText('Rudransh');
  const projectId = await page.getByRole('combobox', { name: 'Active project' }).inputValue();
  await page.reload();
  await expect(page.getByRole('combobox', { name: 'Active project' })).toHaveValue(projectId);
  await expect(page.locator('.user-summary strong')).toHaveText('Rudransh');
  const isolated = await browser.newContext();
  const other = await isolated.newPage();
  await other.goto('/');
  await other.getByRole('button', { name: 'Open judge workspace' }).click();
  await expect(other.getByRole('combobox', { name: 'Active project' })).toBeVisible();
  expect(await other.getByRole('combobox', { name: 'Active project' }).inputValue()).not.toBe(projectId);
  expect((await other.request.get(`/api/projects/${projectId}/sources`)).status()).toBe(404);
  await isolated.close();
});

test('judge entry blocks duplicate clicks and offers retry when starting fails', async ({ page }) => {
  let attempts = 0;
  await page.route('**/api/auth/judge-demo/start', async route => {
    attempts++;
    if (attempts === 1) {
      await new Promise(resolve => setTimeout(resolve, 400));
      await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Demo preparation is temporarily unavailable. Retry.' }) });
    } else await route.continue();
  });
  await page.goto('/');
  const entry = page.getByRole('region', { name: 'Judge demo access' });
  const button = entry.getByRole('button', { name: 'Open judge workspace' });
  await expect(button).toBeEnabled();
  await button.evaluate((element: HTMLButtonElement) => { element.click(); element.click(); });
  await expect(entry.getByRole('alert')).toContainText('Demo preparation is temporarily unavailable.');
  expect(attempts).toBe(1);
  await entry.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(page.getByRole('combobox', { name: 'Switch demo role' })).toBeVisible();
  expect(attempts).toBe(2);
});

test('judge entry explains when the interactive workspace is unavailable', async ({ page }) => {
  await page.route('**/api/auth/judge-demo', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ enabled: false, expires_hours: 4 }) }));
  await page.goto('/');
  const entry = page.getByRole('region', { name: 'Judge demo access' });
  await expect(entry.getByRole('button', { name: 'Open judge workspace' })).toBeDisabled();
  await expect(entry).toContainText('Judge workspace is currently unavailable.');
  await expect(entry.getByRole('link', { name: 'Explore demo' })).toHaveAttribute('href', '/demo');
});

for (const theme of ['dark', 'light'] as const) {
  for (const width of [390, 768, 1440]) {
    test(`public judge walkthrough ${theme} ${width}: readable, keyboard, accessibility`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto('/');
      if (theme === 'light') await page.getByRole('button', { name: 'Switch to day mode' }).click();
      await expect(page.getByRole('button', { name: 'Open judge workspace' })).toBeEnabled();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      const signIn = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      expect(signIn.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.failureSummary) }))).toEqual([]);
      await page.getByRole('link', { name: 'Explore demo' }).click();
      await expect(page.getByRole('button', { name: 'Start interactive demo' })).toBeEnabled();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
      await page.keyboard.press('Tab');
      expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe('BODY');
      const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      expect(result.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.failureSummary) }))).toEqual([]);
      await page.screenshot({ path: `docs/ui-artifacts/judge-demo-${theme}-${width}.png`, fullPage: true });
    });
  }
}

test('judge can reconstruct, inspect evidence, approve, transfer and validate through the UI', async ({ page }) => {
  test.setTimeout(480_000);
  await page.waitForTimeout(60_000); // Respect the real shared-IP request window across the full suite.
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  const pid = await begin(page);
  await page.getByRole('button', { name: 'Investigate project', exact: true }).click();
  await expect(page.locator('.investigation-report').getByText('Completed', { exact: true })).toBeVisible();
  await page.goto('/memory');
  await expect(page.locator('.knowledge-item').first()).toBeVisible();
  const claims: Claim[] = await (await page.request.get(`/api/projects/${pid}/claims`)).json();
  const targets = claims.filter(c => c.kind === 'responsibility' || c.kind === 'procedure' || c.kind === 'incident' || c.kind === 'task');
  for (const claim of targets) {
    await page.getByRole('button', { name: claim.title, exact: true }).click();
    const dialog = page.getByRole('dialog', { name: claim.title, exact: true });
    await expect(dialog.locator('blockquote').first()).toBeVisible();
    await dialog.getByLabel('Review note').fill('Inspected exact case-study evidence for this controlled browser test.');
    await dialog.getByRole('button', { name: 'Approve claim', exact: true }).click();
    await expect(dialog.locator('.detail-meta').getByText('Verified', { exact: true })).toBeVisible();
    await dialog.getByRole('button', { name: 'Close dialog' }).click();
  }
  await page.goto('/handover');
  await page.getByRole('button', { name: 'Generate handover', exact: true }).click();
  await expect(page.locator('.handover-overview').getByText('Generated', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Review & approve' }).click();
  await page.getByRole('dialog', { name: 'Approve handover version' }).getByLabel('Approval note').fill('Reviewed evidence, incomplete recovery checks and incoming source permissions.');
  await page.getByRole('button', { name: 'Approve handover', exact: true }).click();
  await expect(page.locator('.handover-overview').getByText('Approved', { exact: true })).toBeVisible();
  const people: User[] = await (await page.request.get(`/api/team?project_id=${pid}`)).json();
  for (const claim of targets.filter(c => c.kind === 'responsibility')) {
    await page.getByRole('button', { name: 'Assign responsibility', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Propose responsibility transfer' });
    await dialog.getByLabel('Verified responsibility').selectOption(claim.id);
    await dialog.getByLabel('Backup owner').selectOption(people.find(p => p.name === 'Rudransh')!.id);
    await dialog.getByRole('button', { name: 'Propose transfer' }).click();
    await expect(dialog).not.toBeVisible();
  }
  await page.getByRole('button', { name: 'Create validation tasks' }).click();
  await role(page, 'Savinay');
  await page.goto('/validation');
  await expect(page.locator('.acceptance-item')).toHaveCount(3);
  for (const item of await page.locator('.acceptance-item').all()) {
    await item.getByRole('button', { name: 'Accept', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Accept responsibility' });
    await dialog.getByLabel('Acceptance note').fill('Reviewed my assignment and accepted this case-study ownership.');
    await dialog.getByRole('button', { name: 'Accept ownership' }).click();
    await expect(dialog).not.toBeVisible();
  }
  const transition: Transition = (await (await page.request.get(`/api/projects/${pid}/transitions`)).json())[0];
  for (const exercise of transition.exercises) {
    const card = page.locator('.exercise-card').filter({ has: page.getByRole('heading', { name: exercise.title, exact: true }) });
    await card.getByRole('button', { name: 'Open practical task' }).click();
    const dialog = page.getByRole('dialog', { name: exercise.title, exact: true });
    await dialog.getByLabel('Your practical explanation').fill('I inspected the procedure, identified approval and schema constraints, and explained staging-only validation with health checks. This is an evidence walkthrough, not an actual cloud execution.');
    for (const checkbox of await dialog.getByRole('group', { name: 'Supporting evidence references' }).getByRole('checkbox').all()) await checkbox.check();
    await dialog.getByLabel('When and to whom would you escalate?').fill('Escalate missing restore evidence or schema uncertainty to Rudransh and the database specialist before execution.');
    await dialog.getByRole('button', { name: 'Submit for supervisor review' }).click();
    await expect(dialog).not.toBeVisible();
  }
  await role(page, 'Rudransh');
  await expect(page.locator('.exercise-card')).toHaveCount(transition.exercises.length);
  for (const card of await page.locator('.exercise-card').all()) {
    await card.getByRole('button', { name: 'Validate', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Supervisor validation' });
    for (const checkbox of await dialog.getByRole('checkbox').all()) await checkbox.check();
    await dialog.getByLabel('Evidence-backed assessment note').fill('Independently reviewed explanation against each criterion. This controlled demonstration records no cloud test success.');
    await dialog.getByRole('button', { name: 'Validate practical completion' }).click();
    await expect(dialog).not.toBeVisible();
  }
  await page.goto('/handover');
  await expect(page.getByRole('button', { name: 'Review check', exact: true }).first()).toBeVisible();
  const latest: Transition = (await (await page.request.get(`/api/projects/${pid}/transitions`)).json())[0];
  for (const prerequisite of latest.report.prerequisites as { id: string; title: string; gap_source_ids?: string[] }[]) {
    const row = page.locator('.transfer-row').filter({ has: page.getByText(prerequisite.title, { exact: true }) });
    await row.getByRole('button', { name: 'Review check', exact: true }).click();
    const check = page.getByRole('dialog', { name: 'Review a readiness prerequisite' });
    const people: User[] = await (await page.request.get('/api/auth/judge-demo/people')).json();
    await expect(check).toBeVisible();
    await check.getByRole('combobox', { name: 'Accountable person', exact: true }).selectOption(people.find(p => p.name === 'Savinay')!.id);
    await check.getByLabel('Follow-up due date').fill('2027-01-01');
    // All current evidence is inspected; the API checks this specific gap's source.
    const ref = (latest.report.knowledge as Claim[]).flatMap(c => c.evidence).find(e => prerequisite.gap_source_ids?.length ? prerequisite.gap_source_ids.includes(e.source_id) : true)!;
    await check.locator(`input[value="${ref.id}"]`).check();
    await check.getByLabel('Review note').fill('Reviewed recovery gap; Savinay owns the dated follow-up. No actual cloud restore claimed.');
    await check.getByRole('button', { name: 'Record prerequisite review' }).click();
    await expect(check).not.toBeVisible();
    await expect(row).toContainText('Confirmed');
  }
  await page.getByRole('button', { name: 'Close transition' }).click();
  await expect(page.locator('.handover-overview').getByText('Closed', { exact: true })).toBeVisible();
  const summary = await (await page.request.get(`/api/projects/${pid}/continuity-summary`)).json();
  expect(summary.completed_handovers).toBe(1);
  expect(summary.completion.current).toBe(true);
  const completed = page.getByRole('region', { name: 'Completed knowledge handover' });
  await page.waitForTimeout(61_000); // Honour the unchanged API budget after the accelerated review/closure loop.
  const routes = ['/', '/sources', '/memory', '/decisions', '/investigation', '/graph', '/risk', '/team', '/handover', '/validation', '/successor', '/governance'];
  for (const [index, path] of routes.entries()) {
    if (index === 6) await page.waitForTimeout(61_000); // A real user takes time inspecting these evidence-heavy pages.
    await page.locator(`.nav-link[href="${path}"]`).click();
    await expect(completed).toContainText('Knowledge handover completed');
    await expect(completed).toContainText('3/3');
    await expect(completed).toContainText('Gaurav → Savinay');
  }
  await page.locator('.nav-link[href="/team"]').click();
  const savinay = page.locator('.person-panel').filter({ has: page.getByRole('heading', { name: 'Savinay', exact: true }) });
  await expect(savinay).toContainText('3 responsibilities accepted');
  await expect(savinay).toContainText(`${transition.exercises.length} walkthroughs submitted`);
  for (const [theme, width] of [['dark', 1440], ['light', 390]] as const) {
    await page.setViewportSize({ width, height: 900 });
    if (theme === 'light') await page.getByRole('button', { name: 'Switch to day mode' }).click();
    if (!await completed.locator('.completion-team').isVisible()) await completed.getByText('See team contributions and scope', { exact: true }).click();
    await expect(completed.locator('.completion-team')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    expect(result.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.failureSummary) }))).toEqual([]);
    await completed.getByRole('link', { name: 'Inspect completed handover' }).click();
    await expect(page).toHaveURL(new RegExp(`/handover\\?transition=${summary.completion.id}`));
    await expect(page.locator('.handover-overview')).toContainText('Closed');
  }
  expect(errors).toEqual([]);
});


test('secure invitation joins a new member; incoming role cannot approve access', async ({ page, browser }) => {
  const pid = await begin(page);
  await page.goto('/team');
  await page.getByRole('button', { name: 'Invite member', exact: true }).click();
  const invite = page.getByRole('dialog', { name: 'Invite a project member' });
  await invite.getByLabel('Name', { exact: true }).fill('Judge Teammate');
  await invite.getByLabel('Email', { exact: true }).fill(`judge-${Date.now()}@example.com`);
  await invite.getByLabel('Role title').fill('Incoming reliability engineer');
  await invite.getByRole('button', { name: 'Create invitation' }).click();
  const share = page.getByRole('dialog', { name: 'Share the invitation privately' });
  const link = await share.getByLabel('One-time invitation link').inputValue();
  const other = await browser.newContext();
  const member = await other.newPage();
  await member.goto(link);
  await member.getByLabel('Your new password').fill('controlled-browser-test-password');
  await member.getByRole('button', { name: 'Accept invitation' }).click();
  await expect(member.getByRole('heading', { name: 'Knowledge owners' })).toBeVisible();
  await expect(member.getByRole('button', { name: 'Invite member', exact: true })).toHaveCount(0);
  await member.getByRole('button', { name: 'Request knowledge access' }).click();
  await member.getByLabel('What knowledge do you need and why?').fill('Need approved staging recovery instructions for my reviewed handover.');
  await member.getByRole('button', { name: 'Submit request', exact: true }).click();
  await expect(member.getByRole('dialog', { name: 'Request knowledge access' })).not.toBeVisible();
  const requests = await (await member.request.get(`/api/projects/${pid}/access-requests`)).json();
  expect(requests).toHaveLength(1);
  await expect(member.getByRole('button', { name: 'Review', exact: true })).toHaveCount(0);
  await other.close();
});


test('uploaded source replacement exposes impact and current citations after re-investigation', async ({ page }) => {
  test.setTimeout(120_000);
  await page.waitForTimeout(60_000); // The prior journey uses the same local API rate window.
  await begin(page);
  await page.goto('/investigation');
  await page.getByRole('button', { name: 'Investigate project', exact: true }).click();
  await expect(page.locator('.investigation-report').getByText('Completed', { exact: true })).toBeVisible();
  await page.goto('/sources');
  const row = page.getByRole('row').filter({ hasText: '03-deployment-runbook.md' });
  await row.getByRole('button', { name: 'New version', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Publish a new document version' });
  await dialog.getByLabel('Updated authorised document').setInputFiles({ name: 'deployment-current.md', mimeType: 'text/markdown', buffer: Buffer.from('Procedure: Current staging release\nSystem: release-pipeline\nCheck approved image digest, review build results, confirm schema compatibility and document health evidence. No production changes in this example.') });
  await dialog.getByRole('button', { name: 'Save new version' }).click();
  await expect(dialog).not.toBeVisible();
  const changed = page.getByRole('row').filter({ hasText: 'deployment-current.md' });
  await expect(changed).toContainText('Version 2');
  await changed.getByRole('button', { name: 'Impact', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Source change impact' })).toContainText('invalidated');
});
