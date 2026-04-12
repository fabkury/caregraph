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
    // Clinicians tile should be a <span>, not an <a> (not yet built)
    const tile = page.locator('.entity-tiles span', { hasText: 'Clinicians' });
    await expect(tile).toBeVisible();
  });

  test('SNFs and ACOs tiles are active links', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.entity-tiles a', { hasText: 'SNFs' })).toHaveAttribute('href', '/explore/snfs/');
    await expect(page.locator('.entity-tiles a', { hasText: 'ACOs' })).toHaveAttribute('href', '/explore/acos/');
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

// ---------------------------------------------------------------------------
// M2: SNF browse page
// ---------------------------------------------------------------------------

test.describe('SNF browse page', () => {
  test('lists SNFs with sortable table', async ({ page }) => {
    await page.goto('/explore/snfs/');
    await expect(page.locator('h1')).toHaveText('Skilled Nursing Facilities');
    const rows = page.locator('#data-table tbody tr');
    expect(await rows.count()).toBeGreaterThan(100);
  });

  test('SNF name links to entity page', async ({ page }) => {
    await page.goto('/explore/snfs/');
    const firstLink = page.locator('#data-table tbody tr:first-child td:first-child a');
    const href = await firstLink.getAttribute('href');
    expect(href).toMatch(/^\/snf\/[A-Za-z0-9]{6}\/$/);
  });
});

// ---------------------------------------------------------------------------
// M2: ACO browse page
// ---------------------------------------------------------------------------

test.describe('ACO browse page', () => {
  test('lists ACOs', async ({ page }) => {
    await page.goto('/explore/acos/');
    await expect(page.locator('h1')).toHaveText('Accountable Care Organizations');
    const rows = page.locator('#data-table tbody tr');
    expect(await rows.count()).toBeGreaterThan(50);
  });

  test('ACO name links to entity page', async ({ page }) => {
    await page.goto('/explore/acos/');
    const firstLink = page.locator('#data-table tbody tr:first-child td:first-child a');
    const href = await firstLink.getAttribute('href');
    expect(href).toMatch(/^\/aco\/[A-Z0-9]+\/$/);
  });
});

// ---------------------------------------------------------------------------
// M2: SNF entity page
// ---------------------------------------------------------------------------

test.describe('SNF entity page', () => {
  test('renders SNF name and CCN', async ({ page }) => {
    await page.goto('/snf/015009/');
    await expect(page.locator('h1')).not.toBeEmpty();
    await expect(page.locator('.subtitle')).toContainText('015009');
  });

  test('shows SNF badge', async ({ page }) => {
    await page.goto('/snf/015009/');
    await expect(page.locator('.badge-snf')).toBeVisible();
  });

  test('Explore/Table toggle works', async ({ page }) => {
    await page.goto('/snf/015009/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(page.locator('#explore-view')).toBeVisible();
    await page.locator('#mode-toggle button[data-mode="table"]').click();
    await expect(page.locator('#table-view')).toBeVisible();
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
  });

  test('shows related entities', async ({ page }) => {
    await page.goto('/snf/015009/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    const related = page.locator('.related-list');
    // May or may not have related depending on cross-link data
    if (await related.count() > 0) {
      await expect(related.locator('li').first()).toBeVisible();
    }
  });
});

// ---------------------------------------------------------------------------
// M2: ACO entity page
// ---------------------------------------------------------------------------

test.describe('ACO entity page', () => {
  test('renders ACO name and ID', async ({ page }) => {
    await page.goto('/aco/A1001/');
    await expect(page.locator('h1')).not.toBeEmpty();
    await expect(page.locator('.subtitle')).toContainText('A1001');
  });

  test('shows ACO badge', async ({ page }) => {
    await page.goto('/aco/A1001/');
    await expect(page.locator('.badge-aco')).toBeVisible();
  });

  test('shows metric cards', async ({ page }) => {
    await page.goto('/aco/A1001/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    const cards = page.locator('.metric-card');
    expect(await cards.count()).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// M2: Hospital enrichment (HRRP + HVBP)
// ---------------------------------------------------------------------------

test.describe('Hospital enrichment', () => {
  test('shows HRRP readmissions data', async ({ page }) => {
    await page.goto('/hospital/010001/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    // Hospital 010001 should have readmission data
    await expect(page.getByRole('heading', { name: 'Readmissions (HRRP)' })).toBeVisible();
  });

  test('shows VBP performance scores', async ({ page }) => {
    await page.goto('/hospital/010001/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(page.getByRole('heading', { name: 'Value-Based Purchasing' })).toBeVisible();
  });

  test('shows related entities with county link', async ({ page }) => {
    await page.goto('/hospital/010001/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(page.locator('.related-list')).toBeVisible();
    // Should have a county link
    const countyLink = page.locator('.related-list a[href*="/county/"]');
    expect(await countyLink.count()).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// M2: County enrichment (PLACES + cross-links)
// ---------------------------------------------------------------------------

test.describe('County enrichment', () => {
  test('shows CDC PLACES chronic conditions', async ({ page }) => {
    await page.goto('/county/06037/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(page.locator('text=Chronic Conditions')).toBeVisible();
  });

  test('shows related hospitals and SNFs', async ({ page }) => {
    await page.goto('/county/06037/');
    await page.locator('#mode-toggle button[data-mode="explore"]').click();
    await expect(page.locator('.related-list')).toBeVisible();
    const hospitalLinks = page.locator('.related-list a[href*="/hospital/"]');
    expect(await hospitalLinks.count()).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// M2: Search
// ---------------------------------------------------------------------------

test.describe('Search', () => {
  test('search page loads', async ({ page }) => {
    await page.goto('/search/');
    await expect(page.locator('h1')).toContainText('Search');
  });

  test('nav search navigates to search page', async ({ page }) => {
    await page.goto('/');
    const searchInput = page.locator('#nav-search-input');
    await searchInput.fill('Cleveland');
    await searchInput.press('Enter');
    await expect(page).toHaveURL(/\/search\?q=Cleveland/);
  });

  test('home search navigates to search page', async ({ page }) => {
    await page.goto('/');
    const searchInput = page.locator('#home-search');
    await searchInput.fill('Los Angeles');
    await searchInput.press('Enter');
    await expect(page).toHaveURL(/\/search\?q=Los%20Angeles/);
  });
});

// ---------------------------------------------------------------------------
// M3: Methodology Hub
// ---------------------------------------------------------------------------

test.describe('Methodology hub', () => {
  test('methodology hub page loads', async ({ page }) => {
    await page.goto('/methodology/');
    await expect(page.locator('h1')).toContainText('Methodology');
    await expect(page).toHaveTitle(/Methodology/);
  });

  test('per-dataset methodology page loads (HRRP)', async ({ page }) => {
    await page.goto('/methodology/dataset/hrrp/');
    await expect(page.locator('h1')).toBeVisible();
    // Should have some content about the dataset
    await expect(page.locator('body')).toContainText('HRRP');
  });

  test('methodology page has required sections', async ({ page }) => {
    await page.goto('/methodology/');
    // Should list datasets or have navigable content
    const links = page.locator('a[href*="/methodology/dataset/"]');
    expect(await links.count()).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// M4: Map, Compare, and Workspace pages
// ---------------------------------------------------------------------------

test.describe('Map page', () => {
  test('map page loads with map container', async ({ page }) => {
    await page.goto('/map/');
    await expect(page).toHaveTitle(/Map Explorer/);
    // Map container should be present
    await expect(page.locator('#map')).toBeVisible();
  });
});

test.describe('Compare page', () => {
  test('compare page loads', async ({ page }) => {
    await page.goto('/compare/');
    await expect(page.locator('h1')).toContainText('Compare');
    await expect(page).toHaveTitle(/Compare/);
  });
});

test.describe('Workspace page', () => {
  test('workspace page loads', async ({ page }) => {
    await page.goto('/workspace/');
    await expect(page.locator('h1')).toContainText('Workspace');
  });

  test('workspace shows empty state message', async ({ page }) => {
    // Clear any existing workspace data
    await page.goto('/workspace/');
    await page.evaluate(() => localStorage.removeItem('caregraph-workspace'));
    await page.reload();
    // Should show an empty state indicator
    await expect(page.locator('body')).toContainText(/empty|no items|nothing|get started|saved|pinned/i);
  });
});

// ---------------------------------------------------------------------------
// M5: About page
// ---------------------------------------------------------------------------

test.describe('About page', () => {
  test('about page loads with pitch text', async ({ page }) => {
    await page.goto('/about/');
    await expect(page.locator('h1')).toContainText('About');
    await expect(page.locator('body')).toContainText('Public CMS Data');
  });

  test('about page has citation section', async ({ page }) => {
    await page.goto('/about/');
    await expect(page.locator('#cite')).toBeVisible();
    await expect(page.locator('body')).toContainText('How to Cite');
    await expect(page.locator('body')).toContainText('BibTeX');
  });

  test('about page has license info', async ({ page }) => {
    await page.goto('/about/');
    await expect(page.locator('body')).toContainText('MIT License');
    await expect(page.locator('body')).toContainText('CMS');
    // Should have the license table
    await expect(page.locator('.data-table')).toBeVisible();
  });

  test('about page has GitHub link', async ({ page }) => {
    await page.goto('/about/');
    const ghLink = page.locator('a[href*="github.com/fabkury/caregraph"]').first();
    await expect(ghLink).toBeVisible();
  });

  test('about page has error reporting link', async ({ page }) => {
    await page.goto('/about/');
    const issuesLink = page.locator('a[href*="github.com/fabkury/caregraph/issues"]');
    await expect(issuesLink).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// M5: Accessibility
// ---------------------------------------------------------------------------

test.describe('Accessibility', () => {
  test('skip-to-content link exists', async ({ page }) => {
    await page.goto('/');
    const skipLink = page.locator('a.skip-link');
    await expect(skipLink).toHaveAttribute('href', '#main-content');
    // Should be visually hidden but exist in DOM
    await expect(skipLink).toBeAttached();
  });

  test('main content has id for skip link target', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('main#main-content')).toBeVisible();
  });

  test('nav has proper ARIA attributes', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('nav.nav');
    await expect(nav).toHaveAttribute('role', 'navigation');
    await expect(nav).toHaveAttribute('aria-label', 'Main navigation');
  });

  test('search has proper ARIA attributes', async ({ page }) => {
    await page.goto('/');
    const search = page.locator('.nav-search');
    await expect(search).toHaveAttribute('role', 'search');
    await expect(search).toHaveAttribute('aria-label', 'Search');
  });

  test('all nav links point to real pages (not #)', async ({ page }) => {
    await page.goto('/');
    const links = page.locator('.nav-links a');
    const count = await links.count();
    for (let i = 0; i < count; i++) {
      const href = await links.nth(i).getAttribute('href');
      const text = await links.nth(i).textContent();
      // Allow # only for "Explore" which is a placeholder for the browse pages
      if (text?.trim() === 'Explore') continue;
      expect(href, `Nav link "${text}" should not point to #`).not.toBe('#');
    }
  });
});
