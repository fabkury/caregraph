import { test, expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// Home page
// ---------------------------------------------------------------------------

test.describe('Home page', () => {
  test('loads and shows hero', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toHaveText('CareGraph');
    await expect(page).toHaveTitle(/CareGraph/);
  });

  test('has working Hospitals tile', async ({ page }) => {
    await page.goto('/');
    const tile = page.locator('.entity-tiles a', { hasText: 'Hospitals' });
    await expect(tile).toHaveAttribute('href', '/explore/hospitals/');
    await tile.click();
    await expect(page).toHaveURL(/\/explore\/hospitals/);
  });

  test('has working Counties tile', async ({ page }) => {
    await page.goto('/');
    const tile = page.locator('.entity-tiles a', { hasText: 'Counties' });
    await expect(tile).toHaveAttribute('href', '/explore/counties/');
    await tile.click();
    await expect(page).toHaveURL(/\/explore\/counties/);
  });

  test('disabled tiles are not links', async ({ page }) => {
    await page.goto('/');
    // SNFs tile should be a <span>, not an <a>
    const snfTile = page.locator('.entity-tiles span', { hasText: 'SNFs' });
    await expect(snfTile).toBeVisible();
  });

  test('nav bar has all links', async ({ page }) => {
    await page.goto('/');
    for (const label of ['Home', 'Explore', 'Maps', 'Methodology', 'Workspace', 'About']) {
      await expect(page.locator('.nav-links a', { hasText: label })).toBeVisible();
    }
  });

  test('footer has Report an error link', async ({ page }) => {
    await page.goto('/');
    const link = page.locator('footer a', { hasText: 'Report an error' });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', /github\.com.*issues/);
  });
});

// ---------------------------------------------------------------------------
// Hospital browse page
// ---------------------------------------------------------------------------

test.describe('Hospital browse page', () => {
  test('lists hospitals with sortable table', async ({ page }) => {
    await page.goto('/explore/hospitals/');
    await expect(page.locator('h1')).toHaveText('Hospitals');
    // Should have rows in the table
    const rows = page.locator('#data-table tbody tr');
    await expect(rows.first()).toBeVisible();
    expect(await rows.count()).toBeGreaterThan(100);
  });

  test('hospital name links to entity page', async ({ page }) => {
    await page.goto('/explore/hospitals/');
    const firstLink = page.locator('#data-table tbody tr:first-child td:first-child a');
    await expect(firstLink).toBeVisible();
    const href = await firstLink.getAttribute('href');
    expect(href).toMatch(/^\/hospital\/[A-Za-z0-9]{6}\/$/);
  });

  test('clicking column header sorts the table', async ({ page }) => {
    await page.goto('/explore/hospitals/');
    const stateHeader = page.locator('#data-table th', { hasText: 'State' });
    await stateHeader.click();
    // After sorting by State ascending, first row state should be early alphabet
    const firstState = await page.locator('#data-table tbody tr:first-child td:nth-child(4)').textContent();
    await stateHeader.click();
    // After second click (descending), first row state should differ
    const firstStateDesc = await page.locator('#data-table tbody tr:first-child td:nth-child(4)').textContent();
    expect(firstState).not.toEqual(firstStateDesc);
  });
});

// ---------------------------------------------------------------------------
// County browse page
// ---------------------------------------------------------------------------

test.describe('County browse page', () => {
  test('lists counties', async ({ page }) => {
    await page.goto('/explore/counties/');
    await expect(page.locator('h1')).toHaveText('Counties');
    const rows = page.locator('#data-table tbody tr');
    expect(await rows.count()).toBeGreaterThan(100);
  });

  test('county name links to entity page', async ({ page }) => {
    await page.goto('/explore/counties/');
    const firstLink = page.locator('#data-table tbody tr:first-child td:first-child a');
    const href = await firstLink.getAttribute('href');
    expect(href).toMatch(/^\/county\/\d{5}\/$/);
  });
});

// ---------------------------------------------------------------------------
// Hospital entity page
// ---------------------------------------------------------------------------

test.describe('Hospital entity page', () => {
  const url = '/hospital/010001/'; // Southeast Health Medical Center

  test('renders hospital name and CCN', async ({ page }) => {
    await page.goto(url);
    await expect(page.locator('h1')).toContainText('SOUTHEAST HEALTH MEDICAL CENTER');
    await expect(page.locator('.subtitle')).toContainText('010001');
  });

  test('shows badge', async ({ page }) => {
    await page.goto(url);
    await expect(page.locator('.badge-hospital')).toHaveText('Hospital');
  });

  test('shows star rating', async ({ page }) => {
    await page.goto(url);
    await expect(page.locator('.star-rating')).toBeVisible();
  });

  test('Explore/Table toggle works', async ({ page }) => {
    await page.goto(url);
    const exploreView = page.locator('#explore-view');
    const tableView = page.locator('#table-view');

    // Default: Explore visible, Table hidden
    await expect(exploreView).toBeVisible();
    await expect(tableView).toBeHidden();

    // Click Table
    await page.locator('#mode-toggle button[data-mode="table"]').click();
    await expect(exploreView).toBeHidden();
    await expect(tableView).toBeVisible();

    // Click Explore
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(exploreView).toBeVisible();
    await expect(tableView).toBeHidden();
  });

  test('mode toggle persists across pages via localStorage', async ({ page }) => {
    await page.goto(url);
    // Switch to Table mode
    await page.locator('#mode-toggle button[data-mode="table"]').click();
    await expect(page.locator('#table-view')).toBeVisible();

    // Navigate to a county page — should still be in Table mode
    await page.goto('/county/06037/');
    await expect(page.locator('#table-view')).toBeVisible();
    await expect(page.locator('#explore-view')).toBeHidden();

    // Clean up: reset to explore
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
  });

  test('CSV download link is valid', async ({ page }) => {
    await page.goto(url);
    const csvLink = page.locator('a.btn', { hasText: 'Download CSV' });
    await expect(csvLink).toBeVisible();
    const href = await csvLink.getAttribute('href');
    expect(href).toContain('data:text/csv');
    expect(href).toContain('010001');
  });

  test('methodology stub shows provenance', async ({ page }) => {
    await page.goto(url);
    const methodology = page.locator('.methodology-stub');
    await expect(methodology).toContainText('Hospital General Information');
    await expect(methodology).toContainText('xubh-q36u');
  });

  test('Table mode shows data rows', async ({ page }) => {
    await page.goto(url);
    await page.locator('#mode-toggle button[data-mode="table"]').click();
    const rows = page.locator('#table-view #data-table tbody tr');
    expect(await rows.count()).toBeGreaterThan(5);
    // Clean up
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
  });
});

// ---------------------------------------------------------------------------
// County entity page
// ---------------------------------------------------------------------------

test.describe('County entity page', () => {
  const url = '/county/06037/'; // Los Angeles, CA

  test('renders county name and FIPS', async ({ page }) => {
    await page.goto(url);
    await expect(page.locator('h1')).toContainText('Los Angeles');
    await expect(page.locator('.subtitle')).toContainText('06037');
  });

  test('shows badge', async ({ page }) => {
    await page.goto(url);
    await expect(page.locator('.badge-county')).toHaveText('County');
  });

  test('shows metric cards in Explore mode', async ({ page }) => {
    await page.goto(url);
    // Ensure explore mode
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    const metricCards = page.locator('.metric-card');
    expect(await metricCards.count()).toBeGreaterThanOrEqual(8);
  });

  test('metric cards have labels and values', async ({ page }) => {
    await page.goto(url);
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    const firstCard = page.locator('.metric-card').first();
    await expect(firstCard.locator('.label')).not.toBeEmpty();
    await expect(firstCard.locator('.value')).not.toBeEmpty();
  });

  test('Explore/Table toggle works', async ({ page }) => {
    await page.goto(url);
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(page.locator('#explore-view')).toBeVisible();
    await expect(page.locator('#table-view')).toBeHidden();

    await page.locator('#mode-toggle button[data-mode="table"]').click();
    await expect(page.locator('#explore-view')).toBeHidden();
    await expect(page.locator('#table-view')).toBeVisible();

    // Clean up
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
  });

  test('CSV download link is valid', async ({ page }) => {
    await page.goto(url);
    const csvLink = page.locator('a.btn', { hasText: 'Download CSV' });
    const href = await csvLink.getAttribute('href');
    expect(href).toContain('data:text/csv');
    expect(href).toContain('06037');
  });

  test('methodology stub shows provenance', async ({ page }) => {
    await page.goto(url);
    const methodology = page.locator('.methodology-stub');
    await expect(methodology).toContainText('Geographic Variation');
    await expect(methodology).toContainText('geo-var-county');
  });
});

// ---------------------------------------------------------------------------
// 404 handling
// ---------------------------------------------------------------------------

test('nonexistent page returns 404', async ({ page }) => {
  const resp = await page.goto('/hospital/999999/');
  expect(resp?.status()).toBe(404);
});
