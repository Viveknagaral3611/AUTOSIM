/* Optional end-to-end check. Requires Playwright + Chromium; see README. */
const assert = require("node:assert/strict");
const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  try {
    const base = process.env.AUTOSIM_URL || "http://127.0.0.1:8000";
    // The CI server is started immediately before this script.
    for (let attempt = 0; attempt < 50; attempt++) {
      try { if ((await fetch(`${base}/api/health`)).ok) break; }
      catch (error) { if (attempt === 49) throw error; }
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    await page.goto(base);
    await page.getByText("Local API connected", { exact: true }).waitFor();
    assert.equal(await page.locator(".waypoint-row").count(), 4);
    await page.getByRole("button", { name: "Generate preview" }).click();
    await page.getByText("PREVIEW SAVED", { exact: true }).waitFor();
    assert.notEqual(await page.locator("#distance").textContent(), "—");
    await page.locator("#timeline").evaluate((input) => {
      input.value = "100";
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    assert.notEqual(await page.locator("#time-label").textContent(), "0.0 s");
    await page.getByRole("button", { name: "Play preview", exact: true }).click();
    await page.getByRole("button", { name: "Pause preview", exact: true }).waitFor();
    await page.getByRole("button", { name: "Pause preview", exact: true }).click();
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export JSON" }).click();
    const download = await downloadPromise;
    assert.match(download.suggestedFilename(), /^autosim-.*\.json$/);
    const stream = await download.createReadStream();
    const chunks = [];
    for await (const chunk of stream) chunks.push(chunk);
    const saved = JSON.parse(Buffer.concat(chunks).toString());
    assert.equal(saved.fidelity, "kinematic_preview");
    assert.equal(saved.metrics.mission_success, null);
    await page.locator("#drone-name").fill("Changed aircraft");
    assert.equal(await page.locator("#preview-state").textContent(), "NOT RUN");
    assert.equal(await page.locator("#download").isDisabled(), true);
    await page.locator(".history-row").first().click();
    await page.getByText("PREVIEW SAVED", { exact: true }).waitFor();
    assert.equal(await page.locator("#drone-name").inputValue(), "Explorer Q1");
    await page.locator("#drone-name").fill('<img src=x onerror="alert(1)">');
    await page.getByRole("button", { name: "Generate preview" }).click();
    await page.getByText("PREVIEW SAVED", { exact: true }).waitFor();
    assert.equal(await page.locator("#history img").count(), 0);
    assert.equal(await page.locator("#history strong").first().textContent(), '<img src=x onerror="alert(1)">');
    await page.locator("#drone-name").fill("Explorer Q1");
    await page.getByRole("button", { name: "Generate preview" }).click();
    await page.getByText("PREVIEW SAVED", { exact: true }).waitFor();
    if (process.env.AUTOSIM_SCREENSHOT) await page.screenshot({ path: process.env.AUTOSIM_SCREENSHOT, fullPage: true });
    // Persistence survives a browser reload.
    await page.reload();
    await page.locator(".history-row").first().waitFor();
    await page.locator(".history-row").first().click();
    await page.getByText("PREVIEW SAVED", { exact: true }).waitFor();
    for (const sensor of ["gps", "imu"]) await page.locator(`[name="sensor"][value="${sensor}"]`).uncheck();
    await page.getByRole("button", { name: "Generate preview" }).click();
    await page.getByRole("alert").waitFor();
    assert.match(await page.getByRole("alert").textContent(), /sensors/);
    await page.locator('[name="sensor"][value="gps"]').check();
    await page.getByRole("button", { name: "Add waypoint" }).click();
    assert.equal(await page.locator(".waypoint-row").count(), 5);
    await page.getByRole("button", { name: "Remove waypoint 5", exact: true }).click();
    assert.equal(await page.locator(".waypoint-row").count(), 4);
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, "Mobile layout overflows");
    if (process.env.AUTOSIM_MOBILE_SCREENSHOT) await page.screenshot({ path: process.env.AUTOSIM_MOBILE_SCREENSHOT, fullPage: true });
    assert.deepEqual(errors, []);
    console.log("Browser smoke passed: submit, playback, export, history, validation, safe text, mobile layout.");
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
