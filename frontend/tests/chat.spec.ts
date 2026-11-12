import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { Cookie } from '@playwright/test';

let chatCookies: Cookie[] = [];
// Pace real API tests to respect the application's shared-IP limits.
test.beforeEach(async () => { await new Promise(resolve => setTimeout(resolve, 5000)); });

async function signIn(page: Page) {
  if (chatCookies.length) await page.context().addCookies(chatCookies);
  await page.goto('/');
  if (!chatCookies.length) await page.getByRole('button', { name: /Maya Chen/ }).click();
  await expect(page.getByRole('heading', { name: 'Keep knowledge moving.' })).toBeVisible();
  if (!chatCookies.length) chatCookies = await page.context().cookies();
  await page.goto('/successor');
  await expect(page.getByRole('heading', { name: 'Ask the project’s memory' })).toBeVisible();
  await expect(page.locator('.chat-history .loading')).toHaveCount(0);
  await page.getByRole('button', { name: 'New conversation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Delete conversation', exact: true })).toBeEnabled();
}

test('private chat persists, abstains, and only runs a confirmed action', async ({ page, browser }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await signIn(page);
  await page.getByRole('button', { name: 'High effort', exact: true }).click();
  await expect(page.getByRole('button', { name: 'High effort' })).toHaveAttribute('aria-pressed', 'true');
  await page.getByLabel('Ask a project question').fill('What is the verified production teleportation protocol?');
  await page.getByLabel('Ask a project question').press('Enter');
  await expect(page.locator('.chat-turns .mini-label').filter({ hasText: 'Insufficient evidence' }).last()).toBeVisible();
  await expect(page.locator('.chat-turns')).toContainText('high effort');
  await expect(page.locator('.chat-turns')).toContainText('AI provider is not enabled');
  await page.reload();
  await expect(page.locator('.chat-turns')).toContainText('teleportation protocol');
  await expect(page.locator('.chat-history button.selected')).toBeVisible();
  const projects = await (await page.request.get('/api/projects')).json();
  const base = `/api/projects/${projects[0].id}`;
  const count = (await (await page.request.get(base + '/investigations')).json()).length;
  await page.getByRole('button', { name: 'Project actions' }).click();
  await page.getByRole('button', { name: /Investigate this project/ }).click();
  await expect(page.getByRole('button', { name: 'Confirm action' })).toBeVisible();
  expect((await (await page.request.get(base + '/investigations')).json()).length).toBe(count);
  await page.getByRole('button', { name: 'Confirm action' }).click();
  await expect(page.getByRole('link', { name: 'Open result' })).toBeVisible();
  expect((await (await page.request.get(base + '/investigations')).json()).length).toBe(count + 1);
  const other = await browser.newContext();
  const incoming = await other.newPage();
  await incoming.goto('/');
  await incoming.getByRole('button', { name: /Jordan Lee/ }).click();
  await expect(incoming.getByRole('heading', { name: 'Keep knowledge moving.' })).toBeVisible();
  await incoming.goto('/successor');
  await expect(incoming.locator('.chat-history')).toContainText('Your saved conversations will appear here');
  await expect(incoming.getByRole('button', { name: 'AI settings' })).toHaveCount(0);
  await expect(incoming.getByRole('button', { name: 'Project actions' })).toBeDisabled();
  await other.close();
  await page.getByRole('button', { name: 'Delete conversation', exact: true }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Delete conversation', exact: true }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  expect(errors).toEqual([]);
});

test('AI settings offer actual model options and clear unsaved credentials on close', async ({ page }) => {
  await signIn(page);
  await page.getByRole('button', { name: 'AI settings' }).click();
  const dialog = page.getByRole('dialog', { name: 'Organisation AI settings' });
  await expect(dialog.getByLabel('Provider API key')).toHaveAttribute('type', 'password');
  expect(await dialog.getByLabel('Default model').locator('option').allTextContents()).toEqual(['gpt-6.1-sol', 'gpt-6-astra', 'gpt-5.6-sol']);
  await dialog.getByLabel('Default model').selectOption('gpt-5.6-sol');
  await dialog.getByLabel('API endpoint').selectOption('https://router.bynara.id/v1');
  await expect(dialog.getByLabel('Default model')).toHaveValue('agnes-2.5-flash');
  expect(await dialog.getByLabel('Default model').locator('option').allTextContents()).toEqual(['agnes-2.5-flash']);
  await expect(dialog.getByLabel('API protocol')).toHaveValue('chat_completions');
  expect(await dialog.getByLabel('API protocol').locator('option').allTextContents()).toEqual(['Chat Completions']);
  await expect(dialog).toContainText('messages to Bynara');
  await dialog.getByLabel('Provider API key').fill('not-a-real-provider-key');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'AI settings' }).click();
  await expect(dialog.getByLabel('Provider API key')).toHaveValue('');
  await expect(dialog.getByLabel('Default model')).toHaveValue('gpt-6.1-sol');
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
  expect(results.violations.map(v => v.id)).toEqual([]);
});

test('Bynara model selection is used in the chat request', async ({ page }) => {
  await page.route('**/api/projects/*/ai-settings', route => route.fulfill({ json: {
    provider: 'bynara', base_url: 'https://router.bynara.id/v1', model: 'agnes-2.5-flash',
    models: ['agnes-2.5-flash'], protocol: 'chat_completions', enabled: true, has_key: true,
  } }));
  // Keep this browser contract test independent of paid provider access.
  await page.route('**/chat/conversations/*/messages', async route => {
    const payload = route.request().postDataJSON();
    expect(payload.model).toBe('agnes-2.5-flash');
    expect(payload.effort).toBe('high');
    const conversation = (await (await page.request.get(route.request().url().replace(/\/messages$/, ''))).json());
    await route.fulfill({ json: { ...conversation, turns: [{
      id: 'mock-bynara-turn', question: payload.message, effort: payload.effort, status: 'completed',
      response: { answer: 'Insufficient Evidence', parts: [{ kind: 'unknown', text: 'Insufficient Evidence', references: [] }], unknowns: ['Insufficient Evidence'], engine: 'bynara', model: 'agnes-2.5-flash' },
    }] } });
  });
  await signIn(page);
  await expect(page.getByLabel('Chat model')).toHaveValue('agnes-2.5-flash');
  expect(await page.getByLabel('Chat model').locator('option').allTextContents()).toEqual(['agnes-2.5-flash']);
  await page.getByRole('button', { name: 'High effort', exact: true }).click();
  await page.getByLabel('Ask a project question').fill('What is the verified deployment procedure?');
  await page.getByRole('button', { name: 'Send question' }).click();
  await expect(page.locator('.chat-turns')).toContainText('high effort · agnes-2.5-flash');
  await expect(page.locator('.chat-turns')).toContainText('Insufficient Evidence');
});

for (const theme of ['dark', 'light']) {
  for (const width of [390, 768, 1440]) {
    test(`chat layout and accessibility ${theme} ${width}`, async ({ page }) => {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 1024 });
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await signIn(page);
      if (theme === 'light') await page.getByRole('button', { name: 'Switch to day mode' }).click();
      await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
      await page.getByLabel('Ask a project question').fill('What procedure is not documented?');
      await page.getByRole('button', { name: 'Send question' }).click();
      await expect(page.locator('.chat-turns .successor-answer')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
      await page.getByRole('button', { name: 'High effort' }).focus();
      await page.keyboard.press('Space');
      await expect(page.getByRole('button', { name: 'High effort' })).toHaveAttribute('aria-pressed', 'true');
      const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      expect(results.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.failureSummary) }))).toEqual([]);
      await page.screenshot({ path: `docs/ui-artifacts/chat-${theme}-${width}.png`, fullPage: true });
    });
  }
}
