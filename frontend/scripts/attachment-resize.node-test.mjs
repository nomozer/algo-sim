import test from "node:test";
import assert from "node:assert/strict";
import { chromium } from "playwright";

test("attachment draft survives viewport resize and scrollbar thumb tracks content", async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto(process.env.AXO_TEST_URL ?? "http://localhost:3001/app");
    const file = (i) => ({ name: `test-${i}.docx`, mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document", buffer: Buffer.from(`file-${i}`) });
    const measure = () => page.evaluate(() => ({
      count: document.querySelectorAll(".file-preview-card").length,
      thumb: parseFloat(document.querySelector(".composer-files-scroll-control")?.style.getPropertyValue("--thumb-width") || "0"),
    }));
    await page.locator("#home-file-input").setInputFiles(Array.from({ length: 8 }, (_, i) => file(i)));
    await page.locator(".composer-files-scroll-control").waitFor();
    const initial = await measure();
    await page.locator("#home-file-input").setInputFiles(file(8));
    await page.waitForFunction(() => document.querySelectorAll(".file-preview-card").length === 9);
    await page.waitForFunction((value) => parseFloat(document.querySelector(".composer-files-scroll-control")?.style.getPropertyValue("--thumb-width") || "0") < value, initial.thumb);
    const added = await measure();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForFunction(() => document.querySelectorAll(".file-preview-card").length === 9);
    await page.waitForFunction((value) => parseFloat(document.querySelector(".composer-files-scroll-control")?.style.getPropertyValue("--thumb-width") || "0") < value, added.thumb);
    const resized = await measure();
    assert.equal(resized.count, 9);
    assert.ok(resized.thumb > 0 && resized.thumb < added.thumb && added.thumb < initial.thumb);
  } finally {
    await browser.close();
  }
});
