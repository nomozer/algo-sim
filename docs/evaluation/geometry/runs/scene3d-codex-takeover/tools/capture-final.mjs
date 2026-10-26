// Before/after capture for the Owner-reported scenes: same fixtures, same orbit drags, same viewports, fresh output.
// node docs/evaluation/geometry/runs/scene3d-owner-math-visual-final/tools/capture.mjs --url http://127.0.0.1:3161 --out <dir> [--only id,id]
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
import { createHash } from "node:crypto";
const { chromium } = createRequire(resolve("frontend/package.json"))("playwright");
const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const url = arg("--url", "http://127.0.0.1:3161"), out = resolve(arg("--out"));
if (existsSync(out)) throw Error("Fresh output required");
mkdirSync(out, { recursive: true });
const read = (f) => JSON.parse(readFileSync(f, "utf8"));
const samples = read("frontend/src/data/geometry-samples.json").samples;
const fx = (f) => read(`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${f}.json`).envelope;
const audit = read("docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json");
const fixtures = [
  ...samples.map((s) => ({ id: s.id, envelope: s.envelope })),
  ...audit.filter(s => ["family01_triangular_pyramid", "family12_cylinder_ellipse_section"].includes(s.id) && s.scene).map(s => ({id:s.id,envelope:s.envelope ?? {...samples[0].envelope,scene3d:s.scene}})),
  ...["cuboid_positive", "triangular_prism_positive", "cross_section_positive", "w18_projection_line"].map((f) => ({ id: f, envelope: fx(f) })),
].filter((f) => !arg("--only") || arg("--only").split(",").includes(f.id));
// Orbit drags in canvas-height fractions (relative to the product's default framing): [dx, dy].
const CAMERAS = { default: null, quarter: [0.25, 0], half: [0.5, 0], back: [1.0, 0], high: [0, 0.15], low: [0, -0.15] };
const sha = (b) => createHash("sha256").update(b).digest("hex");
const receipt = { product_commit: execFileSync("git", ["log", "-1", "--format=%H", "--", "frontend/src/simulations/domains/geometry/scene3d-view.tsx"]).toString().trim(), viewport_policy: "1440x900 DPR1 / 390x844 DPR2", selection: "unselected", source_mode: "offline replay through product store", url, provider_calls: 0, rows: [], errors: [] };
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
try {
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, deviceScaleFactor: width === 390 ? 2 : 1 });
    await ctx.route("**/*", (r) => { const u = new URL(r.request().url()); if (u.hostname !== "127.0.0.1") return r.abort();
      if (u.pathname.startsWith("/api/")) return r.fulfill({ json: u.pathname === "/api/health" ? { status: "ok" } : null }); return r.continue(); });
    const page = await ctx.newPage();
    await page.goto(url);
    page.on("pageerror", (e) => receipt.errors.push(e.message.split("\n")[0]));
    for (const f of fixtures) for (const [cam, drag] of Object.entries(CAMERAS)) {

      await page.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, f.envelope);
      const canvas = page.locator(".geo3d-canvas canvas");
      await canvas.waitFor();
      await page.locator(".geo3d-scrub input").evaluate((el) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, el.max);
        el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); });
      if (drag) {
        const box = await canvas.boundingBox();
        await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5); await page.mouse.down();
        await page.mouse.move(box.x + box.width * 0.5 + box.height * drag[0], box.y + box.height * (0.5 + drag[1]), { steps: 20 }); await page.mouse.up();
      }
      await page.mouse.move(0, 0);
      await page.waitForFunction(() => { const s = JSON.stringify(window.__geo3d_camera_snapshot);
        window.__capStable = s === window.__capLast ? (window.__capStable ?? 0) + 1 : 0; window.__capLast = s; return window.__capStable >= 4; }, null, { polling: "raf", timeout: 20000 });
      const meta = await page.evaluate(() => ({ camera: window.__geo3d_camera_snapshot, hidden: window.__geo3d_hidden_edge_ids, mixed: window.__geo3d_mixed_edge_ids,
        visible: window.__geo3d_visible_edge_ids, labels: window.__geo3d_point_label_boxes }));
      const png = await canvas.screenshot(), file = `${f.id}-${width}-${cam}.png`;
      writeFileSync(join(out, file), png);
      receipt.rows.push({ id: f.id, width, cam, file, sha256: sha(png), ...meta });
    }
    await ctx.close();
  }
} finally { await browser.close(); }
writeFileSync(join(out, "receipt.json"), JSON.stringify(receipt, null, 1) + "\n");
console.log(JSON.stringify({ rows: receipt.rows.length, errors: receipt.errors.length }));
