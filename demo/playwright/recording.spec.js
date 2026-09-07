const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

// Helper for intentional presentation pauses
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Helper for smooth mouse movements and neutral parking
async function smoothClick(page, target) {
  const locator = typeof target === 'string' ? page.locator(target) : target;
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  if (box) {
    const targetX = box.x + box.width / 2;
    const targetY = box.y + box.height / 2;
    // Move mouse smoothly to element over 15 interpolation frames
    await page.mouse.move(targetX, targetY, { steps: 15 });
    await page.waitForTimeout(200);
    await page.mouse.click(targetX, targetY);
    // Park cursor in a neutral left margin position so it doesn't obstruct view
    await page.mouse.move(60, 540, { steps: 10 });
  } else {
    await locator.click();
  }
}

test.describe('ProcureAI 3-Minute Competition Recording Harness', () => {
  const recordingScreenshotsDir = path.resolve(__dirname, '../screenshots/recording');

  test.beforeAll(() => {
    if (!fs.existsSync(recordingScreenshotsDir)) {
      fs.mkdirSync(recordingScreenshotsDir, { recursive: true });
    }
  });

  test('Execute video recording presentation journey', async ({ page }) => {
    // Set 1920x1080 Desktop HD Viewport
    await page.setViewportSize({ width: 1920, height: 1080 });

    const contractPath = path.resolve(__dirname, '../../data/synthetic/contracts/c001_apex_logistics_contract.pdf');
    const invoice1Path = path.resolve(__dirname, '../../data/synthetic/invoices/c001_invoice_i001.pdf');
    const invoice2Path = path.resolve(__dirname, '../../data/synthetic/invoices/c001_invoice_i002.pdf');

    expect(fs.existsSync(contractPath)).toBe(true);
    expect(fs.existsSync(invoice1Path)).toBe(true);
    expect(fs.existsSync(invoice2Path)).toBe(true);

    const startTime = Date.now();

    // ==========================================
    // SCENE 1 — START: Opening ProcureAI...
    // ==========================================
    console.log('SCENE 1 — START: Opening ProcureAI...');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await pause(2000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene01_start.png') });

    // ==========================================
    // SCENE 2 — NEW AUDIT: Starting new audit...
    // ==========================================
    console.log('SCENE 2 — NEW AUDIT: Starting new audit...');
    const newAuditButton = page.locator('[data-testid="nav-new-audit"]');
    await expect(newAuditButton).toBeVisible();
    await smoothClick(page, newAuditButton);

    await page.waitForSelector('[data-testid="contract-input"]', { state: 'attached' });
    await pause(1500);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene02_new_audit.png') });

    // ==========================================
    // SCENE 3 — UPLOAD: Uploading contract and invoices...
    // ==========================================
    console.log('SCENE 3 — UPLOAD: Uploading contract and invoices...');
    await page.setInputFiles('[data-testid="contract-input"]', contractPath);
    await page.setInputFiles('[data-testid="invoices-input"]', [invoice1Path, invoice2Path]);

    const supplierInput = page.locator('[data-testid="supplier-name-input"]');
    await supplierInput.fill('Apex Logistics Ltd');

    await pause(2000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene03_upload.png') });

    // ==========================================
    // SCENE 4 — AUDIT: Starting audit...
    // ==========================================
    console.log('SCENE 4 — AUDIT: Starting audit...');
    const runButton = page.locator('[data-testid="run-audit-button"]');
    await expect(runButton).toBeEnabled();
    await smoothClick(page, runButton);

    const runningPage = page.locator('[data-testid="audit-running-page"]');
    const duplicateModalRunAgain = page.locator('[data-testid="duplicate-modal-run-again"]');
    const reportSummary = page.locator('[data-testid="total-leakage-amount"]');

    await Promise.race([
      runningPage.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {}),
      duplicateModalRunAgain.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {}),
      reportSummary.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {})
    ]);

    if (await duplicateModalRunAgain.isVisible()) {
      console.log('Duplicate audit prompt visible, clicking Run Again...');
      await smoothClick(page, duplicateModalRunAgain);
    }

    if (await runningPage.isVisible()) {
      // Toggle live agent diagnostic log console to highlight multi-agent pipeline
      const logToggle = page.locator('[data-testid="audit-log-toggle"]');
      if (await logToggle.isVisible()) {
        await smoothClick(page, logToggle);
        await page.waitForSelector('[data-testid="audit-log-console"]', { state: 'visible' }).catch(() => {});
      }
      await pause(4000);
      await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene04_audit_running.png') });
    }

    // Wait for audit report summary to complete
    await reportSummary.waitFor({ state: 'visible', timeout: 60000 });

    // ==========================================
    // SCENE 5 — RESULTS: Showing financial leakage...
    // ==========================================
    console.log('SCENE 5 — RESULTS: Showing financial leakage...');
    await page.locator('[data-testid="total-leakage-amount"]').scrollIntoViewIfNeeded();
    // HERO MOMENT: Pause 3.5s so viewer clearly sees financial result
    await pause(3500);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene05_results.png') });

    // ==========================================
    // SCENE 6 — EVIDENCE: Showing audit evidence...
    // ==========================================
    console.log('SCENE 6 — EVIDENCE: Showing audit evidence...');
    const discrepancyTable = page.locator('[data-testid="discrepancy-table"]');
    await expect(discrepancyTable).toBeVisible();

    const firstRow = page.locator('[data-testid^="discrepancy-row-"]').first();
    await expect(firstRow).toBeVisible();
    await smoothClick(page, firstRow);

    const evidenceBlock = page.locator('[data-testid="evidence-block"]').first();
    if (await evidenceBlock.isVisible()) {
      await evidenceBlock.scrollIntoViewIfNeeded();
    }
    // Pause 2.5s to show contract clause proof, invoice evidence, and calculation
    await pause(2500);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene06_evidence.png') });

    // ==========================================
    // SCENE 7 — DISPUTE: Generating dispute response...
    // ==========================================
    console.log('SCENE 7 — DISPUTE: Generating dispute response...');
    const generateDisputeBtn = page.locator('[data-testid="generate-dispute-button"]');
    await expect(generateDisputeBtn).toBeVisible();
    await smoothClick(page, generateDisputeBtn);

    const disputePreview = page.locator('[data-testid="dispute-letter-modal-preview"]');
    const submitDisputeBtn = page.locator('[data-testid="dispute-modal-submit-button"]');

    await Promise.race([
      disputePreview.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {}),
      submitDisputeBtn.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
    ]);

    if (!await disputePreview.isVisible() && await submitDisputeBtn.isVisible()) {
      await smoothClick(page, submitDisputeBtn);
    }

    await expect(disputePreview).toBeVisible({ timeout: 25000 });

    // Pause 3.0s on generated dispute letter
    await pause(3000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene07_dispute.png') });

    // Close dispute modal smoothly
    const modalCloseBtn = page.locator('[data-testid="modal-close-button"]').last();
    if (await modalCloseBtn.isVisible()) {
      await smoothClick(page, modalCloseBtn);
      await disputePreview.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
    }
    await pause(1000);

    // ==========================================
    // SCENE 8 — SCORECARD: Showing supplier scorecard...
    // ==========================================
    console.log('SCENE 8 — SCORECARD: Showing supplier scorecard...');
    const scorecardNav = page.locator('[data-testid="nav-item-scorecard"]');
    await expect(scorecardNav).toBeVisible();
    await smoothClick(page, scorecardNav);

    await page.waitForSelector('[data-testid="supplier-scorecard-page"]', { state: 'visible', timeout: 30000 });
    // Smooth controlled scroll if content extends below fold
    await page.mouse.wheel(0, 250);
    await pause(2000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene08_scorecard.png') });

    // ==========================================
    // SCENE 9 — ANALYTICS: Opening analytics...
    // ==========================================
    console.log('SCENE 9 — ANALYTICS: Opening analytics...');
    const analyticsNav = page.locator('[data-testid="nav-item-analytics"]');
    await expect(analyticsNav).toBeVisible();
    await smoothClick(page, analyticsNav);

    await page.waitForSelector('[data-testid="analytics-page"]', { state: 'visible', timeout: 30000 });
    await pause(1500);

    // SCENE 9A — ANALYTICS: Showing summary metrics...
    console.log('SCENE 9A — ANALYTICS: Showing summary metrics...');
    const kpiGrid = page.locator('[data-testid="analytics-kpi-grid"]');
    await kpiGrid.scrollIntoViewIfNeeded();
    await pause(2000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene09a_analytics_summary.png') });

    // SCENE 9B — ANALYTICS: Scrolling to charts...
    console.log('SCENE 9B — ANALYTICS: Scrolling to charts...');
    const primaryCharts = page.locator('[data-testid="analytics-primary-charts"]');
    await primaryCharts.scrollIntoViewIfNeeded();
    await page.mouse.wheel(0, 200);
    await pause(2000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene09b_analytics_charts.png') });

    // SCENE 9C — ANALYTICS: Showing detailed analytics...
    console.log('SCENE 9C — ANALYTICS: Showing detailed analytics...');
    const heatmapTable = page.locator('[data-testid="analytics-heatmap-table"]');
    await heatmapTable.scrollIntoViewIfNeeded();
    await page.mouse.wheel(0, 150);
    await pause(2000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene09c_analytics_detailed.png') });

    // ==========================================
    // SCENE 10 — END: Ending on executive analytics dashboard...
    // ==========================================
    console.log('SCENE 10 — END: Ending on executive analytics dashboard...');
    const analyticsPage = page.locator('[data-testid="analytics-page"]');
    await analyticsPage.scrollIntoViewIfNeeded();
    await page.mouse.wheel(0, 200);
    await pause(3000);
    await page.screenshot({ path: path.join(recordingScreenshotsDir, 'scene10_end.png') });

    const totalDurationSeconds = Math.round((Date.now() - startTime) / 1000);
    console.log(`Recording journey finished successfully in ${totalDurationSeconds} seconds.`);
  });
});
