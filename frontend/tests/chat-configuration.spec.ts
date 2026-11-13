import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const disabled = { provider: 'agentrouter', base_url: 'https://agentrouter.org/v1', model: '', models: ['gpt-6.1-sol', 'gpt-6-astra', 'gpt-5.6-sol'], protocol: 'responses', enabled: false, has_key: false };
const bynara = { provider: 'bynara', base_url: 'https://router.bynara.id/v1', model: 'agnes-2.5-flash', models: ['agnes-2.5-flash'], protocol: 'chat_completions', enabled: true, has_key: true };

async function judge(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open judge workspace' }).click();
  await expect(page.getByLabel('Active project', { exact: true })).toBeVisible();
}

test('settings loading and failure never advertise an unconfigured GPT model', async ({ page }) => {
  await judge(page);
  let release = () => {};
  const pending = new Promise<void>(resolve => { release = resolve; });
  let failed = false;
  await page.route('**/api/projects/*/ai-settings', async route => {
    await pending;
    if (failed) await route.fulfill({ json: disabled });
    else await route.fulfill({ status: 503, json: { detail: 'Settings temporarily unavailable.' } });
  });
  await page.goto('/successor');
  await expect(page.getByLabel('Chat model')).toContainText('Loading AI settings');
  await expect(page.getByRole('button', { name: 'AI settings', exact: true })).toBeDisabled();
  await expect(page.getByLabel('Ask a project question')).toBeDisabled();
  expect(await page.getByLabel('Chat model').locator('option').allTextContents()).toEqual(['Loading AI settings…']);
  release();
  await expect(page.getByText('Settings temporarily unavailable.')).toBeVisible();
  await expect(page.getByLabel('Chat model')).toContainText('AI settings unavailable');
  failed = true;
  await page.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(page.getByRole('region', { name: 'AI connection status' })).toBeVisible();
  await expect(page.getByLabel('Chat model')).toContainText('AI not connected');
});

test('saving enabled Bynara settings immediately selects Agnes and survives refresh', async ({ page }) => {
  await judge(page);
  let config = disabled;
  await page.route('**/api/projects/*/ai-settings', async route => {
    if (route.request().method() === 'PUT') {
      const body = route.request().postDataJSON();
      expect(body.base_url).toBe(bynara.base_url);
      expect(body.model).toBe(bynara.model);
      expect(body.protocol).toBe('chat_completions');
      expect(body.enabled).toBe(true);
      config = bynara;
    } else if (route.request().method() === 'DELETE') config = disabled;
    await route.fulfill({ json: config });
  });
  await page.goto('/successor');
  const status = page.getByRole('region', { name: 'AI connection status' });
  await expect(status).toContainText('does not inherit its API key');
  await expect(page.getByLabel('Chat model')).toBeDisabled();
  expect(await page.getByLabel('Chat model').locator('option').allTextContents()).toEqual(['AI not connected']);
  await status.getByRole('button', { name: 'Connect AI provider' }).click();
  const dialog = page.getByRole('dialog', { name: 'Organisation AI settings' });
  await dialog.getByLabel('API endpoint').selectOption(bynara.base_url);
  await expect(dialog.getByLabel('Default model')).toHaveValue('agnes-2.5-flash');
  await dialog.getByLabel('Provider API key').fill('not-a-real-provider-key');
  await dialog.getByLabel('Enable external AI processing for authorised users').check();
  await dialog.getByRole('button', { name: 'Save settings', exact: true }).click();
  await expect(dialog).toContainText('agnes-2.5-flash is selected for this workspace');
  await expect(dialog.getByLabel('Provider API key')).toHaveValue('');
  await dialog.getByRole('button', { name: 'Close dialog' }).click();
  await expect(page.getByLabel('Chat model')).toBeEnabled();
  await expect(page.getByLabel('Chat model')).toHaveValue('agnes-2.5-flash');
  expect(await page.getByLabel('Chat model').locator('option').allTextContents()).toEqual(['agnes-2.5-flash']);
  await expect(status).toHaveCount(0);
  await page.reload();
  await expect(page.getByLabel('Chat model')).toHaveValue('agnes-2.5-flash');
  let sentModel = '';
  await page.route('**/chat/conversations/*/messages', async route => {
    const payload = route.request().postDataJSON();
    sentModel = payload.model;
    const conversation = await (await page.request.get(route.request().url().replace(/\/messages$/, ''))).json();
    await route.fulfill({ json: { ...conversation, turns: [{ id: 'mock-selection-check', question: payload.message, effort: payload.effort, status: 'completed', response: { answer: 'Insufficient Evidence', parts: [], unknowns: [], engine: 'bynara', model: payload.model } }] } });
  });
  await page.getByLabel('Ask a project question').fill('Which current sources describe deployment?');
  await page.getByRole('button', { name: 'Send question' }).click();
  await expect(page.locator('.chat-turns')).toContainText('agnes-2.5-flash');
  expect(sentModel).toBe('agnes-2.5-flash');
  await page.getByRole('button', { name: 'AI settings', exact: true }).click();
  await dialog.getByRole('button', { name: 'Disconnect', exact: true }).click();
  await expect(dialog).toContainText('Provider disconnected');
  await dialog.getByRole('button', { name: 'Close dialog' }).click();
  await expect(page.getByLabel('Chat model')).toContainText('AI not connected');
});

test('disabled demo explains account isolation beside the model on mobile', async ({ page }) => {
  await judge(page);
  await page.route('**/api/projects/*/ai-settings', route => route.fulfill({ json: disabled }));
  await page.goto('/successor');
  await page.setViewportSize({ width: 390, height: 900 });
  await page.getByRole('button', { name: 'Switch to day mode' }).click();
  await expect(page.getByRole('region', { name: 'AI connection status' })).toContainText('This judge workspace is separate from your personal account');
  await expect(page.getByLabel('Chat model')).toContainText('AI not connected');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
  expect(axe.violations.map(v => v.id)).toEqual([]);
});
