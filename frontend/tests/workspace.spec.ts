import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { Claim, Investigation, Project, Session, Transition, User } from '../src/types';

async function signInDemo(page: Page) {
  const response = await page.request.get('/api/auth/demo-users');
  expect(response.ok()).toBeTruthy();
  const users: User[] = await response.json();
  const manager = users.find(user => user.role === 'admin') || users.find(user => user.role === 'manager');
  expect(manager).toBeTruthy();
  await page.goto('/');
  await page.getByRole('button', { name: new RegExp(manager!.name) }).click();
  await expect(page.getByRole('heading', { name: 'Keep knowledge moving.' })).toBeVisible();
  return users;
}

test('task navigation renders real API data without runtime errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await signInDemo(page);
  const pages = [
    ['/sources', 'Connected sources'], ['/memory', 'Project memory'], ['/decisions', 'Decision intelligence'],
    ['/investigation', 'Knowledge investigation'], ['/graph', 'Knowledge graph'], ['/risk', 'Continuity risk'],
    ['/team', 'Knowledge owners'], ['/handover', 'Handover workspace'], ['/validation', 'Verified knowledge transfer'],
    ['/successor', 'Ask the project’s memory'], ['/governance', 'Privacy & audit'],
  ];
  for (const [path, heading] of pages) {
    await page.goto(path);
    await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible();
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.locator('#main-content')).toBeVisible();
    if (path === '/graph') {
      const node = page.locator('.react-flow__node').first();
      await expect(node).toBeVisible();
      const before = await node.boundingBox();
      expect(before).toBeTruthy();
      await page.mouse.move(before!.x + before!.width / 2, before!.y + before!.height / 2);
      await page.mouse.down();
      await page.mouse.move(before!.x + before!.width / 2 + 55, before!.y + before!.height / 2 + 35, { steps: 8 });
      await page.mouse.up();
      const after = await node.boundingBox();
      expect(after!.x - before!.x).toBeGreaterThan(25);
      await node.click();
      await expect(page.getByRole('heading', { name: /^Relationships ·/ })).toBeVisible();
    }
  }
  expect(errors).toEqual([]);
});

for (const theme of ['dark', 'light'] as const) {
for (const viewport of [{ width: 390, height: 844 }, { width: 768, height: 1024 }, { width: 1440, height: 900 }]) {
  test(`responsive overview and keyboard navigation ${theme} ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await signInDemo(page);
    if (theme === 'light') await page.getByRole('button', { name: 'Switch to day mode' }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await expect(page.locator('.metrics-grid .metric').first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.activeElement?.tagName !== 'BODY')).toBeTruthy();
    if (viewport.width <= 1024) {
      await page.getByRole('button', { name: 'Open navigation' }).click();
      await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
      await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Connected sources', exact: true }).click();
      await expect(page.getByRole('heading', { name: 'Connected sources', level: 1 })).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
      await page.goto('/');
    }
    await expect(page.getByRole('heading', { name: 'Keep knowledge moving.' })).toBeVisible();
    await expect(page.locator('.metrics-grid .metric').first()).toBeVisible();
    await expect(page.locator('#main-content .loading')).toHaveCount(0);
    await page.screenshot({ path: `docs/ui-artifacts/overview-${theme === 'light' ? 'light-' : ''}${viewport.width}x${viewport.height}.png`, fullPage: true });
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
    expect(results.violations.map(item => ({ id: item.id, impact: item.impact, nodes: item.nodes.map(node => ({ html: node.html, reason: node.failureSummary })) }))).toEqual([]);
  });
}
}

test('day and night preferences persist across sign-in, refresh, graph and browser tabs', async ({ page, context }) => {
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.getByRole('button', { name: 'Switch to day mode' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  expect(await page.evaluate(() => localStorage.getItem('inheria-theme'))).toBe('light');
  await page.reload();
  await expect(page.getByRole('button', { name: 'Switch to night mode' })).toBeVisible();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.screenshot({ path: 'docs/ui-artifacts/login-light.png', fullPage: true });
  await signInDemo(page);
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.goto('/graph');
  await expect(page.locator('.react-flow')).toHaveClass(/light/);
  await expect(page.locator('.react-flow__node').first()).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/graph-light.png', fullPage: false });
  const second = await context.newPage();
  await second.goto('/');
  await expect(second.getByRole('button', { name: 'Switch to night mode' })).toBeVisible();
  const night = page.getByRole('button', { name: 'Switch to night mode' });
  await night.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(second.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('.react-flow')).toHaveClass(/dark/);
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#0b1019');
  await page.reload();
  await expect(page.getByRole('button', { name: 'Switch to day mode' })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem('inheria-theme'))).toBe('dark');
  await second.close();
});

test('document upload, investigation, evidence and human review work in the UI', async ({ page }) => {
  await signInDemo(page);
  await page.goto('/sources');
  await expect(page.locator('#main-content .loading')).toHaveCount(0);
  await page.getByRole('button', { name: 'Upload document' }).click();
  const identifier = String(Date.now()).replace(/\d/g, digit => 'abcdefghij'[Number(digit)]);
  const title = `ui-validation-${identifier}.md`;
  await page.getByLabel('Select a technical document').setInputFiles({ name: title, mimeType: 'text/markdown', buffer: Buffer.from(`# UI validation procedure ${title}\nProcedure: UI validation deployment ${title}\nRun tests in the staging sandbox. Review the release pipeline before any rollout. Never execute production operations during knowledge validation.\n`) });
  const uploadResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/sources/upload'));
  await page.getByRole('button', { name: 'Process document' }).click();
  expect((await uploadResponse).status()).toBe(201);
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await page.getByRole('searchbox', { name: 'Search sources' }).fill(title);
  await expect(page.locator('.source-name').filter({ hasText: title })).toBeVisible();
  await page.locator('.source-name').filter({ hasText: title }).click();
  await expect(page.getByRole('dialog', { name: 'Source evidence' })).toBeVisible();
  await expect(page.getByRole('dialog').getByText('UI validation procedure', { exact: false }).first()).toBeVisible();
  await page.keyboard.press('Escape');
  await page.goto('/investigation');
  const investigationResponse = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/investigations'));
  await page.getByRole('button', { name: 'Investigate project' }).click();
  const started: Investigation = await (await investigationResponse).json();
  await expect(page.getByRole('heading', { name: 'What the project needs next' })).toBeVisible();
  const currentProject: Project[] = await (await page.request.get('/api/projects')).json();
  await expect.poll(async () => {
    const reports: Investigation[] = await (await page.request.get(`/api/projects/${currentProject[0].id}/investigations`)).json();
    return reports.find(report => report.id === started.id)?.status;
  }, { timeout: 30_000 }).toBe('completed');
  await page.goto('/memory');
  await page.getByRole('searchbox', { name: 'Search knowledge' }).fill(title);
  const claimButton = page.locator('.knowledge-title').first();
  await expect(claimButton).toBeVisible();
  await claimButton.click();
  await expect(page.getByRole('heading', { name: 'Supporting evidence' })).toBeVisible();
  await expect(page.getByRole('dialog').locator('.detail-meta .badge')).toContainText('Pending');
  await page.screenshot({ path: 'docs/ui-artifacts/state-partial.png', fullPage: true });
  await page.getByLabel('Review note').fill('Reviewed the staging-only procedure against the uploaded source and confirmed the safe operating constraints.');
  await page.getByRole('button', { name: 'Approve claim' }).click();
  await expect(page.getByRole('dialog').locator('.detail-meta .badge')).toContainText('Verified');
  await page.screenshot({ path: 'docs/ui-artifacts/state-success.png', fullPage: true });
});

test('unknown successor answers and incoming role controls remain explicit', async ({ page }) => {
  const users = await signInDemo(page);
  await page.goto('/successor');
  await page.getByLabel('Ask a project question').fill('What is the verified production teleportation protocol?');
  await page.getByRole('button', { name: 'Send question' }).click();
  await expect(page.locator('.answer-heading .badge')).toContainText('Insufficient Evidence');
  const incoming = users.find(user => user.role === 'incoming') || users.find(user => user.role === 'employee');
  expect(incoming).toBeTruthy();
  await page.getByLabel('Switch demo role').selectOption(incoming!.id);
  await expect(page.getByLabel('Switch demo role')).toHaveValue(incoming!.id);
  await page.goto('/sources');
  await expect(page.getByRole('button', { name: 'Connect GitHub' })).toHaveCount(0);
  await expect(page.getByText('Source connections and access changes require')).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/state-permission.png', fullPage: true });
});

test('loading, empty and recoverable network-error states are visible', async ({ page }) => {
  await signInDemo(page);
  await page.route('**/api/projects/*/overview', async route => {
    const response = await route.fetch();
    await new Promise(resolve => setTimeout(resolve, 1600));
    await route.fulfill({ response });
  });
  await page.goto('/');
  await expect(page.getByRole('status').filter({ hasText: 'Loading authorised project knowledge' })).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/state-loading.png', fullPage: true });
  await expect(page.getByRole('heading', { name: 'Keep knowledge moving.' })).toBeVisible();
  await page.unroute('**/api/projects/*/overview');
  await page.goto('/sources');
  await page.getByRole('searchbox', { name: 'Search sources' }).fill('NoSuchEvidence-QA-EmptyState-973827');
  await expect(page.getByRole('heading', { name: 'No matching sources' })).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/state-empty.png', fullPage: true });
  await page.route('**/api/projects/*/sources', route => route.abort('failed'));
  await page.reload();
  await expect(page.getByText('Unable to complete this request')).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/state-error.png', fullPage: true });
  await page.unroute('**/api/projects/*/sources');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.locator('.source-name').first()).toBeVisible();
});

test('handover approval, ownership acceptance and supervisor validation are separate UI actions', async ({ page }) => {
  test.setTimeout(120_000);
  const users = await signInDemo(page);
  const manager = users.find(user => user.role === 'admin') || users.find(user => user.role === 'manager');
  const session: Session = await (await page.request.get('/api/auth/me')).json();
  const projects: Project[] = await (await page.request.get('/api/projects')).json();
  const project = projects.find(item => item.is_demo)!;
  const base = `/api/projects/${project.id}`;
  const identifier = String(Date.now()).replace(/\d/g, digit => 'abcdefghij'[Number(digit)]);
  const owner = users.find(user => user.name === 'Alex Morgan') || users.find(user => user.role === 'employee')!;
  const sourceResponse = await page.request.post(`${base}/sources/upload`, {
    headers: { 'X-CSRF-Token': session.csrf_token },
    multipart: { file: { name: `demo-transfer-${identifier}.md`, mimeType: 'text/markdown', buffer: Buffer.from(`# Demo transfer evaluation ${identifier}\nResponsibility: Demo staging release ${identifier}\nOwner: ${owner.name}\nComponent: demo-staging-${identifier}\nCritical: true\nBackup: none\nDocumented: yes\nProcedure: Demo staging procedure ${identifier}\nComponent: demo-staging-${identifier}\nRun the local staging test suite. Verify the release checklist and rollback plan with the lead. Stop before any production change.\n`) } },
  });
  expect(sourceResponse.ok()).toBeTruthy();
  const uploaded = await sourceResponse.json();
  const investigationResponse = await page.request.post(`${base}/investigations`, { headers: { 'X-CSRF-Token': session.csrf_token }, data: { focus: `Demo staging ${identifier}` } });
  expect(investigationResponse.ok()).toBeTruthy();
  const started: Investigation = await investigationResponse.json();
  await expect.poll(async () => {
    const reports: Investigation[] = await (await page.request.get(`${base}/investigations`)).json();
    return reports.find(report => report.id === started.id)?.status;
  }, { timeout: 30_000 }).toBe('completed');
  const claims: Claim[] = await (await page.request.get(`${base}/claims`)).json();
  const fixtureClaims = claims.filter(claim => claim.evidence.some(citation => citation.source_id === uploaded.source.id));
  const responsibility = fixtureClaims.find(claim => claim.kind === 'responsibility' && typeof claim.data.owner_id === 'string' && claim.status === 'pending')!;
  expect(responsibility).toBeTruthy();
  const departingId = String(responsibility.data.owner_id);
  const incoming = users.find(user => user.role === 'incoming' && user.id !== departingId) || users.find(user => user.role === 'employee' && user.id !== departingId)!;
  expect(incoming).toBeTruthy();
  // Authorised API fixture preparation uses the labelled synthetic source evidence.
  for (const claim of fixtureClaims) {
    if (claim.status !== 'pending') continue;
    const response = await page.request.post(`${base}/claims/${claim.id}/review`, { headers: { 'X-CSRF-Token': session.csrf_token }, data: { action: 'approve', note: 'Browser evaluation fixture: reviewed the labelled synthetic source supporting this claim for transfer validation.' } });
    expect(response.ok()).toBeTruthy();
  }
  await page.goto('/handover');
  await page.getByRole('button', { name: 'New transition' }).click();
  const title = `Demo UI transfer validation ${Date.now()}`;
  await page.getByLabel('Transition title').fill(title);
  await page.getByLabel('Departing employee').selectOption(departingId);
  await page.getByLabel('Incoming employee').selectOption(incoming.id);
  await page.getByLabel('Departure date').fill('2026-12-01');
  await page.getByRole('dialog', { name: 'Create employee transition' }).getByRole('button', { name: 'Create transition', exact: true }).click();
  await expect(page.locator('.handover-title')).toContainText(title);
  await page.getByRole('button', { name: 'Generate handover', exact: true }).click();
  await page.getByRole('button', { name: 'Review & approve' }).click();
  await page.getByLabel('Approval note').fill('Reviewed the evidence-backed handover, unresolved gaps and safe practical validation conditions for this synthetic evaluation.');
  await page.getByRole('button', { name: 'Approve handover', exact: true }).click();
  await page.getByRole('button', { name: 'Assign responsibility', exact: true }).click();
  await page.getByLabel('Verified responsibility').selectOption(responsibility.id);
  await page.getByLabel('Proposed incoming owner').selectOption(incoming.id);
  await page.getByRole('button', { name: 'Propose transfer' }).click();
  await expect(page.locator('.transfer-list')).toContainText(responsibility.title);
  await page.getByRole('button', { name: 'Create validation tasks' }).click();
  await expect(page.getByText('Practical validation exercises created with predefined evidence criteria.')).toBeVisible();
  const transitions: Transition[] = await (await page.request.get(`${base}/transitions`)).json();
  const transition = transitions.find(item => item.title === title)!;
  expect(transition.exercises.length).toBeGreaterThan(0);
  await page.getByLabel('Switch demo role').selectOption(incoming.id);
  await expect(page.getByLabel('Switch demo role')).toHaveValue(incoming.id);
  await page.goto('/validation');
  await page.getByLabel('Active handover').selectOption(transition.id);
  await page.getByRole('button', { name: 'Accept', exact: true }).click();
  await page.getByLabel('Acceptance note').fill('I reviewed the responsibility and its evidence, and accept the proposed ownership subject to practical supervisor validation.');
  await page.getByRole('button', { name: 'Accept ownership' }).click();
  await expect(page.locator('.acceptance-list .badge')).toContainText('Accepted');
  const exercise = transition.exercises[0];
  const card = page.locator('.exercise-card').filter({ has: page.getByRole('heading', { name: exercise.title, exact: true }) });
  await card.getByRole('button', { name: 'Open practical task' }).click();
  await page.getByLabel('Your practical explanation').fill('I located the cited operational procedure and checked its version, dependencies and unresolved risk notes. I would verify the staging pipeline and rollback safeguards in the safe test environment, record the result, and ask the authorised technical lead before making any production change.');
  const checkboxes = page.getByRole('dialog').locator('.evidence-options input[type="checkbox"]');
  expect(await checkboxes.count()).toBeGreaterThan(0);
  for (const box of await checkboxes.all()) await box.check();
  await page.getByLabel('When and to whom would you escalate?').fill('Escalate missing evidence, conflicting procedures or failed staging checks to the authorised technical lead and incident owner. Stop before any unsafe production action.');
  await page.getByRole('button', { name: 'Submit for supervisor review' }).click();
  await expect(card.locator('.badge')).toContainText('Submitted');
  await page.screenshot({ path: 'docs/ui-artifacts/validation-submitted.png', fullPage: true });
  await page.getByLabel('Switch demo role').selectOption(manager!.id);
  await expect(page.getByLabel('Switch demo role')).toHaveValue(manager!.id);
  await page.goto('/validation');
  await page.getByLabel('Active handover').selectOption(transition.id);
  const supervisorCard = page.locator('.exercise-card').filter({ has: page.getByRole('heading', { name: exercise.title, exact: true }) });
  await supervisorCard.getByRole('button', { name: 'Inspect submission' }).click();
  await expect(page.getByRole('heading', { name: 'Incoming employee submission' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Evidence checks' })).toBeVisible();
  await page.getByRole('button', { name: 'Close dialog' }).click();
  await supervisorCard.getByRole('button', { name: 'Validate', exact: true }).click();
  await page.getByLabel('Evidence-backed assessment note').fill('Inspected the participant explanation and cited source versions against each predefined criterion. They identified the safe test procedure, dependency checks and human escalation boundary. This validates the exercise only, not production competence.');
  await page.getByRole('button', { name: 'Validate practical completion' }).click();
  await expect(supervisorCard.locator('.badge')).toContainText('Passed');
  await page.screenshot({ path: 'docs/ui-artifacts/validation-supervisor.png', fullPage: true });
});

test('new organisation registration, empty project and member creation work without demo data', async ({ page }) => {
  const identifier = String(Date.now()).replace(/\d/g, digit => 'abcdefghij'[Number(digit)]);
  const password = `QA-${crypto.randomUUID()}`;
  await page.goto('/');
  await page.getByRole('button', { name: 'Create an account' }).click();
  await page.getByLabel('Full name').fill('QA Manager');
  await page.getByLabel('Organisation', { exact: true }).fill(`QA browser onboarding ${identifier}`);
  await page.getByLabel('Email address').fill(`qa.manager.${identifier}@example.com`);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Create account', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Your first continuity project' })).toBeVisible();
  await page.getByLabel('Project name').fill(`QA onboarding project ${identifier}`);
  await page.getByLabel('Description', { exact: true }).fill('Isolated browser evaluation of a fresh organisation. No demonstration evidence has been inserted.');
  await page.getByRole('button', { name: 'Create project', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Keep knowledge moving.' })).toBeVisible();
  await page.goto('/sources');
  await expect(page.getByRole('heading', { name: 'Connect your first evidence source' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'No repository connected' })).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/real-org-empty-sources.png', fullPage: true });
  await page.goto('/team');
  await page.getByRole('button', { name: 'Add project member' }).click();
  const dialog = page.getByRole('dialog', { name: 'Add authorised project member' });
  await dialog.getByLabel('Full name').fill('QA Incoming Engineer');
  await dialog.getByLabel('Email address').fill(`qa.incoming.${identifier}@example.com`);
  await dialog.getByLabel('Role title').fill('Incoming engineer · browser evaluation');
  await dialog.getByLabel('Project role').selectOption('incoming');
  await dialog.getByLabel('Initial password').fill(`QA-${crypto.randomUUID()}`);
  await dialog.getByRole('button', { name: 'Create member', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'QA Incoming Engineer' })).toBeVisible();
  await page.screenshot({ path: 'docs/ui-artifacts/real-org-team.png', fullPage: true });
});
