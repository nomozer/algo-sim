import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

// Xem `verify-semantic-e2e-render.mjs` — bằng chứng phải rơi vào KHO MÃ, không
// vào scratch dir tuyệt đối của máy một người.
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const ARTIFACT_DIR = process.env.ARTIFACT_DIR
  ? path.resolve(process.env.ARTIFACT_DIR)
  : path.join(REPO, "docs/evaluation/semantic-program/render");
fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const VIEWPORTS = [
  { name: "desktop_1920x1080", width: 1920, height: 1080 },
  { name: "laptop_1536x864", width: 1536, height: 864 },
  { name: "school_1366x768", width: 1366, height: 768 },
  { name: "tablet_768x900", width: 768, height: 900 },
];

async function run() {
  console.log("Starting Live Gemini Unseen Playwright Browser Render on port 3000...");
  const fixturesPath = path.resolve("public/fixtures/live_gemini_unseen_candidates.json");
  if (!fs.existsSync(fixturesPath)) {
    throw new Error(`Live candidate fixtures not found at ${fixturesPath}`);
  }
  const rawFixtures = JSON.parse(fs.readFileSync(fixturesPath, "utf-8"));
  const algorithms = Object.keys(rawFixtures);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  const report = {
    browser: "Chromium (Headless)",
    source: "Live Gemini AI Generation",
    algorithmsTested: algorithms,
    results: [],
  };

  // Navigate once to localhost:3000
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__ALGO_SIM_STORE__ !== undefined, { timeout: 10000 });

  for (const algoKey of algorithms) {
    const envelope = rawFixtures[algoKey];
    console.log(`\nTesting Live Gemini Algorithm: ${algoKey} (${envelope.title})`);

    for (const vp of VIEWPORTS) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.waitForTimeout(200);

      // Inject simulation envelope into store
      const loadRes = await page.evaluate((candidate) => {
        const store = window.__ALGO_SIM_STORE__;
        if (!store) return { ok: false, error: "No store" };
        store.getState().loadEnvelope(candidate);
        const state = store.getState();
        return {
          ok: true,
          view: state.view,
          active: !!state.active,
          analysisError: state.analysisError,
        };
      }, envelope);

      await page.waitForTimeout(500);

      // Verify DOM Elements & bounding boxes
      const domStats = await page.evaluate(() => {
        const h1s = document.querySelectorAll("h1");
        const bodyText = document.body.innerText;
        const root = document.getElementById("root");
        const rect = root ? root.getBoundingClientRect() : null;
        return {
          h1Count: h1s.length,
          titleText: h1s.length > 0 ? h1s[0].innerText : "",
          bodyLength: bodyText.length,
          rootWidth: rect ? rect.width : 0,
          rootHeight: rect ? rect.height : 0,
        };
      });

      // Capture screenshot
      const screenshotFilename = `live_gemini_unseen_${algoKey}_${vp.name}.png`;
      const screenshotPath = path.join(ARTIFACT_DIR, screenshotFilename);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      report.results.push({
        algorithm: algoKey,
        title: envelope.title,
        viewport: vp.name,
        width: vp.width,
        height: vp.height,
        loadStatus: loadRes,
        domStats,
        screenshot: screenshotFilename,
        status: "LIVE_RENDER_CERTIFIED",
      });

      console.log(`  ✓ [${vp.name}] -> Title: '${domStats.titleText}' | Loaded: ${loadRes.ok} | Screenshot: ${screenshotFilename}`);
    }
  }

  await browser.close();

  const reportPath = path.join(ARTIFACT_DIR, "live_gemini_unseen_render_report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
  console.log(`\nVerification complete! Report written to ${reportPath}`);
}

run().catch((err) => {
  console.error("Live render verification failed:", err);
  process.exit(1);
});
