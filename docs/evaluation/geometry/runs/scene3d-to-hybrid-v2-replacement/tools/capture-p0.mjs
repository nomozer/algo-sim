// P0 right-angle capture: the three scenes the Owner's report touches, Mode A (default) and Mode B (analysis open),
// five orbit gestures, desktop + mobile. Derived from `../../scene3d-codex-takeover/tools/capture-final.mjs` (unchanged).
// Run from the repo root against a dev server of the tree under test (0 provider calls; /api/* is stubbed):
//   node docs/evaluation/geometry/runs/scene3d-to-hybrid-v2-replacement/tools/capture-p0.mjs --url http://127.0.0.1:3191 --out <fresh dir>
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
import { createHash } from "node:crypto";
const { chromium } = createRequire(resolve("frontend/package.json"))("playwright");
const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const url = arg("--url", "http://127.0.0.1:3191"), out = resolve(arg("--out"));
if (existsSync(out)) throw Error("Fresh output required");
mkdirSync(out, { recursive: true });
const samples = JSON.parse(readFileSync("frontend/src/data/geometry-samples.json", "utf8")).samples;
const IDS = (arg("--only") ?? "mp-vuong-goc-duong,vuong-goc-chop,the-tich-chop").split(",");
const fixtures = samples.filter((s) => IDS.includes(s.id)).map((s) => ({ id: s.id, envelope: s.envelope }));
const CAMERAS = { default: null, quarter: [0.25, 0], half: [0.5, 0], high: [0, 0.15], low: [0, -0.15] };
const sha = (b) => createHash("sha256").update(b).digest("hex");
const receipt = { tree_head: execFileSync("git", ["rev-parse", "HEAD"]).toString().trim(),
  tree_dirty: execFileSync("git", ["status", "--porcelain", "--", "frontend/src", "frontend/src/data"]).toString().trim() !== "",
  viewport_policy: "1440x900 DPR1 / 390x844 DPR2", selection: "unselected", modes: ["A (default)", "B (analysis panel open)"],
  source_mode: "offline samples through product store", url, provider_calls: 0, rows: [], errors: [] };
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
try {
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, deviceScaleFactor: width === 390 ? 2 : 1 });
    await ctx.route("**/*", (r) => { const u = new URL(r.request().url()); if (u.hostname !== "127.0.0.1") return r.abort();
      if (u.pathname.startsWith("/api/")) return r.fulfill({ json: u.pathname === "/api/health" ? { status: "ok" } : null }); return r.continue(); });
    const page = await ctx.newPage();
    await page.goto(url);
    page.on("pageerror", (e) => receipt.errors.push(e.message.split("\n")[0]));
    for (const f of fixtures) for (const mode of ["A", "B"]) for (const [cam, drag] of Object.entries(CAMERAS)) {
      await page.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, f.envelope);
      const canvas = page.locator(".geo3d-canvas canvas");
      await canvas.waitFor();
      await page.locator(".geo3d-scrub input").evaluate((el) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, el.max);
        el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); });
      if (mode === "B") {
        const nut = page.locator("[data-mode-b-toggle]").first();
        if (await nut.count() === 0) { receipt.errors.push(`${f.id}: no Mode B toggle`); continue; }
        if ((await nut.getAttribute("aria-expanded")) !== "true") await nut.click();
      }
      if (drag) {
        const box = await canvas.boundingBox();
        await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5); await page.mouse.down();
        await page.mouse.move(box.x + box.width * 0.5 + box.height * drag[0], box.y + box.height * (0.5 + drag[1]), { steps: 20 }); await page.mouse.up();
      }
      await page.mouse.move(0, 0);
      await page.waitForFunction(() => { const s = JSON.stringify(window.__geo3d_camera_snapshot);
        window.__capStable = s === window.__capLast ? (window.__capStable ?? 0) + 1 : 0; window.__capLast = s; return window.__capStable >= 4; }, null, { polling: "raf", timeout: 20000 });
      const meta = await page.evaluate(() => ({ camera: window.__geo3d_camera_snapshot, witnesses: window.__geo3d_witness_ids ?? [],
        planeLabels: [...document.querySelectorAll(".geo3d-nhan-mp")].map((x) => x.textContent),
        labels: window.__geo3d_point_label_boxes }));
      const png = await canvas.screenshot(), file = `${f.id}-${width}-${mode}-${cam}.png`;
      writeFileSync(join(out, file), png);
      receipt.rows.push({ id: f.id, width, mode, cam, file, sha256: sha(png), ...meta });
    }
    await ctx.close();
  }
} finally { await browser.close(); }
writeFileSync(join(out, "receipt.json"), JSON.stringify(receipt, null, 1) + "\n");
console.log(JSON.stringify({ rows: receipt.rows.length, errors: receipt.errors }));
