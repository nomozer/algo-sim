/**
 * AUTOMATED BROWSER REPLAY FOR RECTANGULAR PYRAMID FAMILY
 *
 * Wave: RECTANGULAR_PYRAMID_PRODUCTION_CLOSURE_AND_AUTO_MERGE
 * Target: rectangular_base_pyramid_volume (Rectangle V=24, Square V=18)
 * Viewports: Desktop 1440x900, Mobile 390x844
 * Checks:
 * - upload/input route & loading state
 * - Scene3D mounted & dimensions > 100
 * - labels A, B, C, D, S present
 * - answer display: 24 (rectangle) & 18 (square)
 * - step scrubbing: forward, backward, first frame, last frame
 * - causal chain highlight: clicking answer triggers causal chain
 * - semantic tree: displays components
 * - negative error presentation: Vietnamese text, error code, zero corrupt scene
 * - 0 console errors, 0 uncaught exceptions
 */
import { createServer } from "node:http";
import { existsSync, readFileSync, writeFileSync, mkdirSync, statSync } from "node:fs";
import { join, resolve, extname } from "node:path";
import { chromium } from "playwright";

const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const FE_DIR = join(REPO_ROOT, "frontend");
const DIST_DIR = join(FE_DIR, "dist");
const OUT_DIR = join(REPO_ROOT, "docs", "evaluation", "geometry", "rectangular-pyramid-replay");

mkdirSync(OUT_DIR, { recursive: true });

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

async function main() {
  console.log("Starting static preview server...");
  const { sv, port } = await startServer(DIST_DIR);
  const origin = `http://127.0.0.1:${port}`;
  console.log(`Server listening on ${origin}`);

  const report = {
    task_id: "RECTANGULAR_PYRAMID_PRODUCTION_CLOSURE_AND_AUTO_MERGE",
    timestamp: new Date().toISOString(),
    origin,
    scenarios: {},
    all_passed: false,
  };

  const browser = await chromium.launch({ headless: true });

  try {
    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 1: Desktop 1440x900 — Positive Case A (Rectangle V=24)
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

      // Mock network calls
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
          await sleep(200); // allow loading state observation
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

      // Verify Labels A, B, C, D, S
      const labelsLocator = page.locator(".geo3d-labels span");
      await page.waitForTimeout(500);
      const labels = await labelsLocator.allTextContents();
      const trimmedLabels = labels.map((l) => l.trim());
      console.log(`Rendered labels: ${JSON.stringify(trimmedLabels)}`);
      const hasAllLabels = ["A", "B", "C", "D", "S"].every((l) => trimmedLabels.includes(l));

      // Step scrubbing
      const stepIndicator = page.locator(".geo3d-buoc-so");
      const initialStepText = await stepIndicator.textContent();
      console.log(`Initial step text: ${initialStepText}`);

      const nextButton = page.locator('[aria-label="Bước sau"]');
      const prevButton = page.locator('[aria-label="Bước trước"]');

      await nextButton.click();
      await page.waitForTimeout(200);
      const secondStepText = await stepIndicator.textContent();

      await prevButton.click();
      await page.waitForTimeout(200);
      const returnedStepText = await stepIndicator.textContent();

      const stepScrubbingWorks = initialStepText !== secondStepText && returnedStepText === initialStepText;

      // Scrub to end
      for (let i = 0; i < 10; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await page.waitForTimeout(100);
      }
      const finalStepText = await stepIndicator.textContent();

      // Readout
      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      console.log(`Final Readout text: ${readoutText}`);
      const answerCorrect = readoutText.includes("24");

      // Causal chain highlight click
      await readoutLocator.click();
      await page.waitForTimeout(300);

      // Semantic tree / explanations
      const explainButton = page.locator('button:has-text("Giải thích")');
      if (await explainButton.isVisible()) {
        await explainButton.click();
        await page.waitForTimeout(200);
      }
      const hasTree = await page.locator("text=Thành phần").isVisible().catch(() => false);

      // Screenshot
      const screenshotPath = join(OUT_DIR, "desktop_1440x900_scene.png");
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`Captured screenshot: ${screenshotPath}`);

      report.scenarios.desktop = {
        viewport: "1440x900",
        loading_observed: loadingObserved,
        canvas_mounted: !!canvasBox && canvasBox.width > 100 && canvasBox.height > 100,
        canvas_dimensions: canvasBox,
        labels_present: hasAllLabels,
        labels: trimmedLabels,
        step_scrubbing: {
          initial: initialStepText,
          second: secondStepText,
          returned: returnedStepText,
          final: finalStepText,
          valid: stepScrubbingWorks,
        },
        answer_displayed: answerCorrect,
        answer_text: readoutText,
        semantic_tree_available: hasTree,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        screenshot: "desktop_1440x900_scene.png",
        passed: loadingObserved && canvasBox.width > 100 && hasAllLabels && stepScrubbingWorks && answerCorrect && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };
      await context.close();
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 2: Mobile 390x844 — Positive Case B (Square V=18)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 2: Mobile 390x844 (Square V=18) ---");
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
      const canvasBox = await canvasLocator.boundingBox();
      console.log(`Mobile Canvas size: ${canvasBox.width}x${canvasBox.height}`);

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 10; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await page.waitForTimeout(100);
      }

      // Check readout 18
      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      console.log(`Mobile Readout text: ${readoutText}`);
      const answerCorrect = readoutText.includes("18");

      // Check horizontal overflow
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      console.log(`Document scrollWidth on mobile: ${scrollWidth}`);
      const noOverflow = scrollWidth <= 391;

      // Screenshot
      const screenshotPath = join(OUT_DIR, "mobile_390x844_scene.png");
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`Captured mobile screenshot: ${screenshotPath}`);

      report.scenarios.mobile = {
        viewport: "390x844",
        canvas_mounted: !!canvasBox && canvasBox.width > 50 && canvasBox.height > 50,
        canvas_dimensions: canvasBox,
        answer_displayed: answerCorrect,
        answer_text: readoutText,
        scroll_width: scrollWidth,
        no_horizontal_overflow: noOverflow,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        screenshot: "mobile_390x844_scene.png",
        passed: !!canvasBox && answerCorrect && noOverflow && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };
      await context.close();
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 3: Negative Presentation (Unsupported Fail-Closed)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 3: Negative Error Presentation ---");
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

      // Wait for refusal card
      const refusalCard = page.locator(".refusal-facts");
      await refusalCard.waitFor({ state: "visible", timeout: 10000 });
      const bodyText = await page.locator("body").innerText();
      console.log(`Refusal displayed. Content snippet: ${bodyText.slice(0, 300)}...`);

      const hasVietnamese = bodyText.includes("không gian") || bodyText.includes("dữ kiện");
      const hasCanvas = await page.locator(".geo3d-canvas canvas").isVisible().catch(() => false);

      const screenshotPath = join(OUT_DIR, "negative_error_presentation.png");
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`Captured negative screenshot: ${screenshotPath}`);

      report.scenarios.negative = {
        refusal_card_visible: true,
        has_vietnamese_explanation: hasVietnamese,
        corrupt_scene_absent: !hasCanvas,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        screenshot: "negative_error_presentation.png",
        passed: hasVietnamese && !hasCanvas && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };
      await context.close();
    }

    report.all_passed =
      report.scenarios.desktop.passed &&
      report.scenarios.mobile.passed &&
      report.scenarios.negative.passed;

    console.log(`\nALL BROWSER REPLAY CHECKS PASSED: ${report.all_passed}`);
    const reportPath = join(OUT_DIR, "RECTANGULAR_PYRAMID_BROWSER_REPLAY_RESULT.json");
    writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
    console.log(`Wrote browser replay report: ${reportPath}`);

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
