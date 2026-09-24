/**
 * AUTOMATED BROWSER REPLAY FOR RECTANGULAR PYRAMID FAMILY — VISUAL INTEGRITY
 *
 * Task: RECTANGULAR_PYRAMID_POST_MERGE_VISUAL_INTEGRITY_REPAIR
 * Viewports: Desktop 1440x900, Mobile 390x844
 * Targets:
 *   - Rectangle (AB=3, AD=4, SA=6 => V=24)
 *   - Square (AB=3, AD=3, SA=6 => V=18)
 *   - Negative refusal case (fail-closed, Vietnamese explanation, no scene)
 *
 * Captures 13 individual scene screenshots + 1 contact sheet + 1 JSON result:
 *   - rectangle_desktop_default.png
 *   - rectangle_desktop_rotated.png
 *   - rectangle_mobile_default.png
 *   - rectangle_mobile_rotated.png
 *   - square_desktop_default.png
 *   - square_desktop_rotated.png
 *   - square_mobile_default.png
 *   - square_mobile_rotated.png
 *   - formation_initial.png
 *   - formation_middle.png
 *   - formation_final.png
 *   - causal_chain_highlight.png
 *   - negative_error.png
 *   - RECTANGULAR_PYRAMID_VISUAL_CONTACT_SHEET.png
 *   - BROWSER_VISUAL_RESULT.json
 */
import { createServer } from "node:http";
import { execSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, copyFileSync, mkdirSync, statSync } from "node:fs";
import { join, resolve, extname } from "node:path";
import { chromium } from "playwright";

const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const FE_DIR = join(REPO_ROOT, "frontend");
const DIST_DIR = join(FE_DIR, "dist");
const REPLAY_SRC_DIR = join(REPO_ROOT, "docs", "evaluation", "geometry", "rectangular-pyramid-replay");
const OUT_DIR = join(REPO_ROOT, "docs", "evaluation", "geometry", "rectangular-pyramid-visual-integrity");

mkdirSync(OUT_DIR, { recursive: true });

// Ensure envelopes exist in OUT_DIR
copyFileSync(join(REPLAY_SRC_DIR, "rect_pyramid_envelope.json"), join(OUT_DIR, "rect_pyramid_envelope.json"));
copyFileSync(join(REPLAY_SRC_DIR, "square_pyramid_envelope.json"), join(OUT_DIR, "square_pyramid_envelope.json"));

const RECT_ENV = JSON.parse(readFileSync(join(OUT_DIR, "rect_pyramid_envelope.json"), "utf8"));
const SQUARE_ENV = JSON.parse(readFileSync(join(OUT_DIR, "square_pyramid_envelope.json"), "utf8"));

const NEGATIVE_ENV = {
  status: "unsupported",
  reason: "Đề bài thiếu chiều cao hoặc mâu thuẫn hình học.",
  learner_reason: "Đề thuộc hình học không gian nhưng chưa đủ dữ kiện để dựng và kiểm chứng mô phỏng.",
  failure_category: "not_simulation_suitable",
  error_code: "GATE_NOT_SIMULATION_SUITABLE",
  stage_reached: "scope",
  representation_plan: {},
  analysis: {},
};

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

function startServer(directory) {
  return new Promise((res) => {
    const sv = createServer((rq, rp) => {
      let p = decodeURIComponent(rq.url.split("?")[0]);
      if (p === "/") p = "/index.html";
      let f = join(directory, p);
      if (!existsSync(f) || statSync(f).isDirectory()) {
        if (extname(p) !== "") {
          rp.writeHead(404);
          rp.end("Not Found");
          return;
        }
        f = join(directory, "index.html");
      }
      rp.writeHead(200, { "Content-Type": MIME[extname(f)] ?? "application/octet-stream" });
      rp.end(readFileSync(f));
    });
    sv.listen(0, "127.0.0.1", () => res({ sv, port: sv.address().port }));
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function orbitCanvas(page, canvasSelector, dx = 180, dy = 40) {
  const canvas = page.locator(canvasSelector);
  const box = await canvas.boundingBox();
  if (!box) return false;
  const startX = box.x + box.width * 0.5;
  const startY = box.y + box.height * 0.5;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + dx, startY + dy, { steps: 15 });
  await page.mouse.up();
  await sleep(400); // allow OrbitControls damping to settle
  return true;
}

function buffersDiffer(b1, b2) {
  if (b1.length !== b2.length) return true;
  for (let i = 0; i < b1.length; i++) {
    if (b1[i] !== b2[i]) return true;
  }
  return false;
}

async function main() {
  console.log("Starting static preview server...");
  const { sv, port } = await startServer(DIST_DIR);
  const origin = `http://127.0.0.1:${port}`;
  console.log(`Server listening on ${origin}`);

  const report = {
    task_id: "RECTANGULAR_PYRAMID_POST_MERGE_VISUAL_INTEGRITY_REPAIR",
    timestamp: new Date().toISOString(),
    origin,
    scenarios: {},
    all_passed: false,
  };

  const browser = await chromium.launch({ headless: true });

  try {
    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 1: Desktop 1440x900 — Rectangle (AB=3, AD=4, SA=6 => V=24)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 1: Desktop 1440x900 (Rectangle V=24) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 200));
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      let loadingObserved = false;

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          loadingObserved = true;
          await sleep(150);
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECT_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await page.goto(origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.waitFor({ state: "visible" });
      await submitButton.click();

      // Wait for scene3d canvas
      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });
      const canvasBox = await canvasLocator.boundingBox();
      console.log(`Desktop Canvas size: ${canvasBox.width}x${canvasBox.height}`);

      // Scrub to end for default scene view
      const nextButton = page.locator('[aria-label="Bước sau"]');
      const prevButton = page.locator('[aria-label="Bước trước"]');
      for (let i = 0; i < 10; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      // Check readout 24
      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const answerCorrect = readoutText.includes("24");
      console.log(`Rectangle Desktop Readout: ${readoutText}`);

      // Verify labels
      await sleep(300);
      const labelsLocator = page.locator(".geo3d-labels span");
      const labels = (await labelsLocator.allTextContents()).map((l) => l.trim());
      console.log(`Rectangle Desktop Labels: ${JSON.stringify(labels)}`);
      const hasAllLabels = ["A", "B", "C", "D", "S"].every((l) => labels.includes(l));

      // 1. Capture rectangle_desktop_default.png
      const defaultBuf = await page.screenshot({ path: join(OUT_DIR, "rectangle_desktop_default.png") });
      console.log("Captured: rectangle_desktop_default.png");

      // 2. Orbit scene & Capture rectangle_desktop_rotated.png
      await orbitCanvas(page, ".geo3d-canvas canvas", 220, 45);
      const rotatedBuf = await page.screenshot({ path: join(OUT_DIR, "rectangle_desktop_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: rectangle_desktop_rotated.png (orbit changed: ${orbitChanged})`);

      // Reset view
      const resetBtn = page.locator('button:has-text("Xem lại toàn hình")');
      if (await resetBtn.isVisible()) {
        await resetBtn.click();
        await sleep(300);
      }

      // 3. Formation frames:
      // Scrub to Step 0 (Bước 1/4)
      for (let i = 0; i < 10; i++) {
        const canPrev = await prevButton.isEnabled().catch(() => false);
        if (!canPrev) break;
        await prevButton.click();
        await sleep(50);
      }
      await sleep(200);
      await page.screenshot({ path: join(OUT_DIR, "formation_initial.png") });
      console.log("Captured: formation_initial.png (Bước 1/4)");

      // Scrub to Step 1 (Bước 2/4)
      await nextButton.click();
      await sleep(200);
      await page.screenshot({ path: join(OUT_DIR, "formation_middle.png") });
      console.log("Captured: formation_middle.png (Bước 2/4)");

      // Scrub to Step 3 (Bước 4/4)
      await nextButton.click();
      await sleep(50);
      await nextButton.click();
      await sleep(200);
      await page.screenshot({ path: join(OUT_DIR, "formation_final.png") });
      console.log("Captured: formation_final.png (Bước 4/4)");

      // 4. Causal chain highlight click
      await readoutLocator.click();
      await sleep(300);
      await page.screenshot({ path: join(OUT_DIR, "causal_chain_highlight.png") });
      console.log("Captured: causal_chain_highlight.png");

      report.scenarios.rectangle_desktop = {
        viewport: "1440x900",
        canvas_mounted: !!canvasBox && canvasBox.width > 100 && canvasBox.height > 100,
        labels_present: hasAllLabels,
        labels,
        answer_displayed: answerCorrect,
        answer_text: readoutText,
        orbit_changed: orbitChanged,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: hasAllLabels && answerCorrect && orbitChanged && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 2: Mobile 390x844 — Rectangle (V=24)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 2: Mobile 390x844 (Rectangle V=24) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
        isMobile: true,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 200));
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(RECT_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await page.goto(origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 10; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const answerCorrect = readoutText.includes("24");

      const defaultBuf = await page.screenshot({ path: join(OUT_DIR, "rectangle_mobile_default.png") });
      console.log("Captured: rectangle_mobile_default.png");

      await orbitCanvas(page, ".geo3d-canvas canvas", 120, 30);
      const rotatedBuf = await page.screenshot({ path: join(OUT_DIR, "rectangle_mobile_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: rectangle_mobile_rotated.png (orbit changed: ${orbitChanged})`);

      report.scenarios.rectangle_mobile = {
        viewport: "390x844",
        answer_displayed: answerCorrect,
        orbit_changed: orbitChanged,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: answerCorrect && orbitChanged && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 3: Desktop 1440x900 — Square (AB=3, AD=3, SA=6 => V=18)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 3: Desktop 1440x900 (Square V=18) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 200));
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SQUARE_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await page.goto(origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh AB = 3. Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 10; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const answerCorrect = readoutText.includes("18");
      console.log(`Square Desktop Readout: ${readoutText}`);

      await sleep(300);
      const labelsLocator = page.locator(".geo3d-labels span");
      const labels = (await labelsLocator.allTextContents()).map((l) => l.trim());
      console.log(`Square Desktop Labels: ${JSON.stringify(labels)}`);
      const hasAllLabels = ["A", "B", "C", "D", "S"].every((l) => labels.includes(l));

      const defaultBuf = await page.screenshot({ path: join(OUT_DIR, "square_desktop_default.png") });
      console.log("Captured: square_desktop_default.png");

      await orbitCanvas(page, ".geo3d-canvas canvas", 200, 45);
      const rotatedBuf = await page.screenshot({ path: join(OUT_DIR, "square_desktop_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: square_desktop_rotated.png (orbit changed: ${orbitChanged})`);

      report.scenarios.square_desktop = {
        viewport: "1440x900",
        labels_present: hasAllLabels,
        labels,
        answer_displayed: answerCorrect,
        answer_text: readoutText,
        orbit_changed: orbitChanged,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: hasAllLabels && answerCorrect && orbitChanged && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 4: Mobile 390x844 — Square (V=18)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 4: Mobile 390x844 (Square V=18) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
        isMobile: true,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 200));
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SQUARE_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await page.goto(origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh AB = 3. Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 10; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const answerCorrect = readoutText.includes("18");

      const defaultBuf = await page.screenshot({ path: join(OUT_DIR, "square_mobile_default.png") });
      console.log("Captured: square_mobile_default.png");

      await orbitCanvas(page, ".geo3d-canvas canvas", 120, 30);
      const rotatedBuf = await page.screenshot({ path: join(OUT_DIR, "square_mobile_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: square_mobile_rotated.png (orbit changed: ${orbitChanged})`);

      report.scenarios.square_mobile = {
        viewport: "390x844",
        answer_displayed: answerCorrect,
        orbit_changed: orbitChanged,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: answerCorrect && orbitChanged && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 5: Negative Error Presentation (Fail-Closed)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 5: Negative Error Presentation ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 200));
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(NEGATIVE_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await page.goto(origin);
      await page.waitForSelector("textarea");

      const invalidText = "Cho hình chóp tam giác bất kỳ thiếu chiều cao và mâu thuẫn dữ kiện.";
      await page.fill("textarea", invalidText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const refusalCard = page.locator(".refusal-facts");
      await refusalCard.waitFor({ state: "visible", timeout: 10000 });
      const bodyText = await page.locator("body").innerText();
      console.log(`Refusal content snippet: ${bodyText.slice(0, 250)}...`);

      const hasVietnamese = bodyText.includes("không gian") || bodyText.includes("dữ kiện");
      const hasCanvas = await page.locator(".geo3d-canvas canvas").isVisible().catch(() => false);

      await page.screenshot({ path: join(OUT_DIR, "negative_error.png"), fullPage: false });
      console.log("Captured: negative_error.png");

      report.scenarios.negative = {
        refusal_card_visible: true,
        has_vietnamese_explanation: hasVietnamese,
        corrupt_scene_absent: !hasCanvas,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: hasVietnamese && !hasCanvas && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
    }

    report.all_passed =
      report.scenarios.rectangle_desktop.passed &&
      report.scenarios.rectangle_mobile.passed &&
      report.scenarios.square_desktop.passed &&
      report.scenarios.square_mobile.passed &&
      report.scenarios.negative.passed;

    console.log(`\nALL BROWSER VISUAL CHECKS PASSED: ${report.all_passed}`);
    const reportPath = join(OUT_DIR, "BROWSER_VISUAL_RESULT.json");
    writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
    console.log(`Wrote browser visual report: ${reportPath}`);

    // Generate contact sheet
    console.log("\nGenerating contact sheet...");
    const pythonExe = join(REPO_ROOT, "backend", ".venv", "Scripts", "python.exe");
    const sheetOutput = join(OUT_DIR, "RECTANGULAR_PYRAMID_VISUAL_CONTACT_SHEET.png");
    const tempPy = join(OUT_DIR, "_generate_sheet.py");

    const pyCode = `
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def make_contact_sheet(img_dir, output_path):
    print(f"Generating contact sheet from {img_dir} to {output_path}...")
    panels = [
        ("rectangle_desktop_default.png", "Rectangle Desktop Default (V=24)"),
        ("rectangle_desktop_rotated.png", "Rectangle Desktop Rotated (Orbit View)"),
        ("rectangle_mobile_default.png", "Rectangle Mobile Default (V=24)"),
        ("rectangle_mobile_rotated.png", "Rectangle Mobile Rotated (Orbit View)"),
        ("square_desktop_default.png", "Square Desktop Default (V=18)"),
        ("square_desktop_rotated.png", "Square Desktop Rotated (Orbit View)"),
        ("square_mobile_default.png", "Square Mobile Default (V=18)"),
        ("square_mobile_rotated.png", "Square Mobile Rotated (Orbit View)"),
        ("formation_initial.png", "Formation Initial (Buoc 1/4)"),
        ("formation_middle.png", "Formation Middle (Buoc 2/4)"),
        ("formation_final.png", "Formation Final (Buoc 4/4)"),
        ("causal_chain_highlight.png", "Causal Chain Highlight (Readout 24)"),
        ("negative_error.png", "Negative Error Presentation (Fail-Closed Refusal)")
    ]
    cell_w, cell_h = 480, 300
    cols, rows = 4, 4
    margin_top, margin_side, margin_bottom = 100, 30, 30
    pad, header_h = 20, 28
    total_w = margin_side * 2 + cols * cell_w + (cols - 1) * pad
    total_h = margin_top + margin_bottom + rows * (cell_h + header_h) + (rows - 1) * pad

    sheet = Image.new("RGB", (total_w, total_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    try:
        title_font = ImageFont.truetype("arial.ttf", 26)
        sub_font = ImageFont.truetype("arial.ttf", 15)
        label_font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    draw.rectangle([(0, 0), (total_w, 80)], fill=(20, 35, 60))
    draw.text((30, 15), "ALGO-SIM - RECTANGULAR PYRAMID VISUAL INTEGRITY ACCEPTANCE", fill=(255, 255, 255), font=title_font)
    draw.text((30, 48), "Non-Degenerate 3D Projection * Orbit Occlusion Verification * Step Scrubbing * Refusal Safety (1440x900 & 390x844)", fill=(180, 205, 235), font=sub_font)

    for idx, (fname, label) in enumerate(panels):
        fpath = os.path.join(img_dir, fname)
        if idx < 12:
            r = idx // cols
            c = idx % cols
            x = margin_side + c * (cell_w + pad)
            y = margin_top + r * (cell_h + header_h + pad)
            w = cell_w
        else:
            r, c = 3, 1
            x = margin_side + c * (cell_w + pad)
            y = margin_top + r * (cell_h + header_h + pad)
            w = cell_w * 2 + pad

        draw.rectangle([(x, y), (x + w, y + header_h)], fill=(45, 65, 95))
        draw.text((x + 10, y + 6), label, fill=(255, 255, 255), font=label_font)
        draw.rectangle([(x, y + header_h), (x + w, y + header_h + cell_h)], fill=(255, 255, 255), outline=(200, 210, 225), width=1)

        if os.path.exists(fpath):
            img = Image.open(fpath)
            img.thumbnail((w - 6, cell_h - 6), Image.Resampling.LANCZOS)
            offset_x = x + (w - img.width) // 2
            offset_y = y + header_h + (cell_h - img.height) // 2
            sheet.paste(img, (offset_x, offset_y))
        else:
            draw.text((x + 20, y + header_h + 100), f"MISSING: {fname}", fill=(200, 0, 0), font=label_font)

    sheet.save(output_path, "PNG", optimize=True)
    print(f"Contact sheet saved: {output_path} ({total_w}x{total_h})")

if __name__ == '__main__':
    make_contact_sheet(sys.argv[1], sys.argv[2])
`;
    writeFileSync(tempPy, pyCode, "utf8");
    try {
      execSync(`"${pythonExe}" "${tempPy}" "${OUT_DIR}" "${sheetOutput}"`, { stdio: "inherit" });
    } finally {
      if (existsSync(tempPy)) {
        import("node:fs").then((fs) => fs.unlinkSync(tempPy));
      }
    }
    console.log(`Contact sheet generated: ${sheetOutput}`);

  } finally {
    await browser.close();
    sv.close();
  }

  if (!report.all_passed) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("FATAL ERROR IN REPLAY:", err);
  process.exit(1);
});
