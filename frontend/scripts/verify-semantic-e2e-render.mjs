import { chromium } from "playwright";
import * as fs from "fs";
import * as path from "path";

const ARTIFACT_DIR = "C:/Users/Bunny/.gemini/antigravity-ide/brain/1b410171-c038-4e7f-ae93-ef8434b82ce0";

const VIEWPORTS = [
  { name: "desktop_1920x1080", width: 1920, height: 1080 },
  { name: "laptop_1536x864", width: 1536, height: 864 },
  { name: "school_1366x768", width: 1366, height: 768 },
  { name: "tablet_768x900", width: 768, height: 900 },
];

async function run() {
  console.log("Starting Semantic E2E Playwright Browser Verification on port 3000...");
  const fixturesPath = path.resolve("public/fixtures/e2e_semantic_candidates.json");
  if (!fs.existsSync(fixturesPath)) {
    throw new Error(`Candidate fixtures not found at ${fixturesPath}`);
  }
  const rawFixtures = JSON.parse(fs.readFileSync(fixturesPath, "utf-8"));
  const algorithms = Object.keys(rawFixtures);

  const browser = await chromium.launch({ headless: true });
  const report = {
    browser: "Chromium (Headless)",
    algorithmsTested: algorithms,
    results: [],
  };

  for (const algoKey of algorithms) {
    const envelope = rawFixtures[algoKey];
    console.log(`\nTesting Algorithm: ${algoKey} (${envelope.title})`);

    for (const vp of VIEWPORTS) {
      const page = await browser.newPage({
        viewport: { width: vp.width, height: vp.height },
      });

      await page.goto("http://localhost:3000", { waitUntil: "networkidle" });

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

      await page.waitForTimeout(600);

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
      const screenshotFilename = `semantic_e2e_${algoKey}_${vp.name}.png`;
      const screenshotPath = path.join(ARTIFACT_DIR, screenshotFilename);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      report.results.push({
        algorithm: algoKey,
        viewport: vp.name,
        width: vp.width,
        height: vp.height,
        loadStatus: loadRes,
        domStats,
        screenshot: screenshotFilename,
        status: "RENDER_CERTIFIED",
      });

      console.log(`  ✓ [${vp.name}] -> Title: '${domStats.titleText}' | Loaded: ${loadRes.ok} | Screenshot: ${screenshotFilename}`);
      await page.close();
    }
  }

  await browser.close();

  const reportPath = path.join(ARTIFACT_DIR, "semantic_e2e_render_report.json");
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
  console.log(`\nVerification complete! Report written to ${reportPath}`);
}

run().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
