import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('completed judge account shows source evidence, graph and role contributions on refresh', async ({ page }) => {
  test.setTimeout(180000);
  await page.goto('/');
  await page.getByRole('button', { name:'Open judge workspace' }).click();
  const banner = page.getByRole('region', { name:'Completed knowledge handover' });
  await expect(banner).toContainText('8/8', { timeout:40000 });
  await expect(banner).toContainText('11/11');
  await expect(page.getByRole('region', { name:'Your next handover step' })).toContainText('Continue');
  const pid = await page.getByRole('combobox', { name:'Active project' }).inputValue();
  await page.locator('.nav-link[href="/graph"]').click();
  await expect(page.locator('.react-flow__node')).not.toHaveCount(1);
  await page.locator('.nav-link[href="/continue"]').click();
  await expect(page.getByRole('heading', { name:'Rudransh’s continuation plan' })).toBeVisible();
  const people = await (await page.request.get('/api/auth/judge-demo/people')).json();
  await page.getByRole('combobox', { name:'Switch demo role' }).selectOption(people.find((p:{name:string}) => p.name === 'Savinay').id);
  await expect(page.getByRole('heading', { name:'Savinay’s continuation plan' })).toBeVisible();
  await expect(page.getByRole('heading', { name:'My responsibilities', exact:true })).toBeVisible();
  await page.reload();
  await expect(banner).toContainText('8/8');
  await expect(page.getByRole('combobox', { name:'Active project' })).toHaveValue(pid);
  for (const width of [390,768,1440]) {
    await page.setViewportSize({ width, height:1000 });
    await page.emulateMedia({ reducedMotion:'reduce' });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const result = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
    expect(result.violations.map(v => v.id)).toEqual([]);
  }
});

test('fresh handover remains available with real reconstruction action', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name:'Try a fresh handover' }).click();
  await expect(page.getByRole('region', { name:'Your next handover step' })).toContainText('Reconstruct');
  await expect(page.getByRole('region', { name:'Completed knowledge handover' })).toHaveCount(0);
  await page.getByRole('button', { name:'Investigate project', exact:true }).click();
  await expect(page.getByRole('region', { name:'Your next handover step' })).toContainText('Verify & review', {timeout:30000});
});
