const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

// Helper for human-readable video delays
const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

test.describe('ProcureAI 3-Minute Product Demonstration Harness', () => {
  const screenshotDir = path.resolve(__dirname, '../screenshots');

  test.beforeAll(() => {
    if (!fs.existsSync(screenshotDir)) {
      fs.mkdirSync(screenshotDir, { recursive: true });
    }
  });

  test('Execute complete ProcureAI demonstration journey', async ({ page }) => {
    // Set high resolution viewport
    await page.setViewportSize({ width: 1920, height: 1080 });

    // File paths for synthetic test documents (Apex Logistics contract and invoices)
    const contractPath = path.resolve(__dirname, '../../data/synthetic/contracts/c001_apex_logistics_contract.pdf');
    const invoice1Path = path.resolve(__dirname, '../../data/synthetic/invoices/c001_invoice_i001.pdf');
    const invoice2Path = path.resolve(__dirname, '../../data/synthetic/invoices/c001_invoice_i002.pdf');

    expect(fs.existsSync(contractPath)).toBe(true);
    expect(fs.existsSync(invoice1Path)).toBe(true);
    expect(fs.existsSync(invoice2Path)).toBe(true);

    // ==========================================
    // STEP 1: Open ProcureAI Application
    // ==========================================
    console.log('Step 1: Navigating to ProcureAI Dashboard...');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await pause(1500);
    await page.screenshot({ path: path.join(screenshotDir, '01_landing_audit_history.png') });

    // ==========================================
    // STEP 2: Navigate to Upload / New Audit Flow
    // ==========================================
    console.log('Step 2: Clicking New Audit...');
    const newAuditButton = page.locator('[data-testid="nav-new-audit"]');
    await expect(newAuditButton).toBeVisible();
    await newAuditButton.click();

    await page.waitForSelector('[data-testid="contract-input"]', { state: 'attached' });
    await pause(1500);
    await page.screenshot({ path: path.join(screenshotDir, '02_new_audit_upload_page.png') });

    // ==========================================
    // STEP 3: Upload Contract & Invoice PDFs
    // ==========================================
    console.log('Step 3: Uploading Contract & Invoice PDFs...');
    await page.setInputFiles('[data-testid="contract-input"]', contractPath);
    await page.setInputFiles('[data-testid="invoices-input"]', [invoice1Path, invoice2Path]);

    const supplierInput = page.locator('[data-testid="supplier-name-input"]');
    await supplierInput.fill('Apex Logistics Ltd');

    await pause(2000);
    await page.screenshot({ path: path.join(screenshotDir, '03_uploaded_documents_ready.png') });

    // ==========================================
    // STEP 4: Start Compliance Audit
    // ==========================================
    console.log('Step 4: Running Compliance Audit...');
    const runButton = page.locator('[data-testid="run-audit-button"]');
    await expect(runButton).toBeEnabled();
    await runButton.click();

    // Handle upload processing & duplicate audit modal if present
    const runningPage = page.locator('[data-testid="audit-running-page"]');
    const duplicateModalRunAgain = page.locator('[data-testid="duplicate-modal-run-again"]');
    const reportSummary = page.locator('[data-testid="total-leakage-amount"]');

    console.log('Waiting for audit execution or duplicate confirmation modal...');
    await Promise.race([
      runningPage.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {}),
      duplicateModalRunAgain.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {}),
      reportSummary.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {})
    ]);

    if (await duplicateModalRunAgain.isVisible()) {
      console.log('Duplicate audit detected, clicking Run Again...');
      await duplicateModalRunAgain.click();
    }

    // ==========================================
    // STEP 5: Monitor Live Multi-Agent Execution Progress
    // ==========================================
    console.log('Step 5: Observing live agent progress & logs...');
    await Promise.race([
      runningPage.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {}),
      reportSummary.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {})
    ]);

    if (await runningPage.isVisible()) {
      await page.screenshot({ path: path.join(screenshotDir, '04_audit_running_agent_progress.png') });

      // Open live diagnostic log stream if available
      const logToggle = page.locator('[data-testid="audit-log-toggle"]');
      if (await logToggle.isVisible()) {
        await logToggle.click();
        await page.waitForSelector('[data-testid="audit-log-console"]', { state: 'visible' }).catch(() => {});
        await pause(1500);
        await page.screenshot({ path: path.join(screenshotDir, '05_agent_diagnostic_logs.png') });
      }
    }

    // ==========================================
    // STEP 6: Review Audit Report Summary & Leakage
    // ==========================================
    console.log('Step 6: Waiting for completed audit report summary...');
    await reportSummary.waitFor({ state: 'visible', timeout: 60000 });

    const complianceScore = page.locator('[data-testid="compliance-score"]');
    await expect(complianceScore).toBeVisible();

    await pause(2000);
    await page.screenshot({ path: path.join(screenshotDir, '06_audit_report_summary.png') });

    // ==========================================
    // STEP 7: Inspect Discrepancies & Contract Evidence Clause
    // ==========================================
    console.log('Step 7: Expanding discrepancy finding and contract clause...');
    const discrepancyTable = page.locator('[data-testid="discrepancy-table"]');
    await expect(discrepancyTable).toBeVisible();

    const firstRow = page.locator('[data-testid^="discrepancy-row-"]').first();
    await expect(firstRow).toBeVisible();
    await firstRow.click();

    const evidenceBlock = page.locator('[data-testid="evidence-block"]').first();
    await expect(evidenceBlock).toBeVisible();

    const clauseQuote = page.locator('[data-testid="clause-text"]').first();
    await expect(clauseQuote).toBeVisible();

    await pause(2500);
    await page.screenshot({ path: path.join(screenshotDir, '07_discrepancy_evidence_clause.png') });

    // ==========================================
    // STEP 8: Generate Vendor Dispute Letter
    // ==========================================
    console.log('Step 8: Generating dispute letter...');
    const generateDisputeBtn = page.locator('[data-testid="generate-dispute-button"]');
    await expect(generateDisputeBtn).toBeVisible();
    await generateDisputeBtn.click();

    const disputePreview = page.locator('[data-testid="dispute-letter-modal-preview"]');
    const submitDisputeBtn = page.locator('[data-testid="dispute-modal-submit-button"]');

    // Wait until either form submit button OR existing preview appears
    await Promise.race([
      disputePreview.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {}),
      submitDisputeBtn.waitFor({ state: 'visible', timeout: 15000 }).catch(() => {})
    ]);

    if (!await disputePreview.isVisible() && await submitDisputeBtn.isVisible()) {
      console.log('Form step visible, submitting dispute letter generation form...');
      await submitDisputeBtn.click();
    }

    await expect(disputePreview).toBeVisible({ timeout: 25000 });

    await pause(3000);
    await page.screenshot({ path: path.join(screenshotDir, '08_dispute_letter_generated.png') });

    // Close Modal via explicit Close Button
    const modalCloseBtn = page.locator('[data-testid="modal-close-button"]').last();
    if (await modalCloseBtn.isVisible()) {
      await modalCloseBtn.click();
      await disputePreview.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
    }
    await pause(1000);

    // ==========================================
    // STEP 9: Navigate to Supplier Risk Scorecard
    // ==========================================
    console.log('Step 9: Navigating to Supplier Scorecard...');
    const scorecardNav = page.locator('[data-testid="nav-item-scorecard"]');
    await expect(scorecardNav).toBeVisible();
    await scorecardNav.click();

    await page.waitForSelector('[data-testid="supplier-scorecard-page"]', { state: 'visible', timeout: 30000 });
    await pause(2000);
    await page.screenshot({ path: path.join(screenshotDir, '09_supplier_scorecard.png') });

    // ==========================================
    // STEP 10: Navigate to Executive Leakage Analytics
    // ==========================================
    console.log('Step 10: Navigating to Analytics Dashboard...');
    const analyticsNav = page.locator('[data-testid="nav-item-analytics"]');
    await expect(analyticsNav).toBeVisible();
    await analyticsNav.click();

    await page.waitForSelector('[data-testid="analytics-page"]', { state: 'visible', timeout: 45000 });
    await pause(2500);
    await page.screenshot({ path: path.join(screenshotDir, '10_analytics_dashboard.png') });

    console.log('Demonstration journey completed successfully!');
  });
});
