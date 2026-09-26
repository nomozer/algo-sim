import { createServer } from "node:http";
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, resolve, extname } from "node:path";
import { chromium } from "playwright";

const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const DIST_DIR = join(REPO_ROOT, "frontend", "dist");
const OUT_DIR = join(REPO_ROOT, "docs", "evaluation", "geometry", "cuboid-cube-visual-integrity");
const CUBOID_ENV = JSON.parse(readFileSync(join(OUT_DIR, "cuboid_envelope.json"), "utf8"));

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

const server = createServer((rq, rp) => {
  let p = decodeURIComponent(rq.url.split("?")[0]);
  if (p === "/") p = "/index.html";
  let f = join(DIST_DIR, p);
  if (!existsSync(f) || statSync(f).isDirectory()) {
    if (extname(p) !== "") {
      rp.writeHead(404);
      rp.end("Not Found");
      return;
    }
    f = join(DIST_DIR, "index.html");
  }
  rp.writeHead(200, { "Content-Type": MIME[extname(f)] || "application/octet-stream" });
  rp.end(readFileSync(f));
});

server.listen(0, "127.0.0.1", async () => {
  try {
    const port = server.address().port;
    const origin = "http://127.0.0.1:" + port;
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 2,
      isMobile: true,
    });
    const page = await context.newPage();

    const failedRequests = [];
    page.on("requestfailed", req => failedRequests.push({ url: req.url(), error: req.failure()?.errorText }));

    await page.route("**/api/**", async (route) => {
      const pathname = new URL(route.request().url()).pathname;
      if (pathname === "/api/health") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
      if (pathname === "/api/auth/me") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
      if (pathname === "/api/analyze") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CUBOID_ENV) });
      return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
    });

    await page.goto(origin);
    await page.waitForSelector("textarea");

    const inputText = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.";
    await page.fill("textarea", inputText);

    const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
    await submitButton.click();

    const canvasLocator = page.locator(".geo3d-canvas canvas");
    await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

    const nextButton = page.locator('[aria-label="Bước sau"]');
    for (let i = 0; i < 15; i++) {
      const canNext = await nextButton.isEnabled().catch(() => false);
      if (!canNext) break;
      await nextButton.click();
      await new Promise(r => setTimeout(r, 50));
    }

    const audit = await page.evaluate(() => {
      const canvas = document.querySelector(".geo3d-canvas canvas");
      const readout = document.querySelector(".geo3d-readout");
      const toolbar = document.querySelector(".geo3d-thanh");
      const timeline = document.querySelector(".geo3d-dieu-khien");
      const body = document.body;
      const computedFont = window.getComputedStyle(body).fontFamily;
      const computedBg = window.getComputedStyle(body).backgroundColor;

      const styleSheets = Array.from(document.styleSheets).map(s => {
        try { return { href: s.href, rules: s.cssRules.length }; }
        catch (e) { return { href: s.href, err: String(e) }; }
      });

      function box(el) {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.x, y: r.y, width: r.width, height: r.height };
      }

      return {
        readyState: document.readyState,
        computedFont,
        computedBg,
        styleSheets,
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        canvasBox: box(canvas),
        readoutBox: box(readout),
        toolbarBox: box(toolbar),
        timelineBox: box(timeline),
      };
    });

    console.log("AUDIT_RESULT_JSON=" + JSON.stringify(audit, null, 2));
    console.log("FAILED_REQUESTS=" + JSON.stringify(failedRequests));

    await page.screenshot({ path: join(OUT_DIR, "cuboid_mobile_audit_check.png") });
    console.log("Wrote cuboid_mobile_audit_check.png");

    await browser.close();
  } catch (err) {
    console.error("AUDIT_ERROR:", err);
  } finally {
    server.close();
  }
});
