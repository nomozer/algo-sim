// Every construction step of chosen samples at the default camera (and one orbit), desktop.
// node .../tools/capture-steps.mjs --url http://127.0.0.1:3161 --out <dir> --only id,id [--drag 0.25]
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
const { chromium } = createRequire(resolve("frontend/package.json"))("playwright");
const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const url = arg("--url", "http://127.0.0.1:3161"), out = resolve(arg("--out")), drag = Number(arg("--drag", "0"));
if (existsSync(out)) throw Error("Fresh output required");
mkdirSync(out, { recursive: true });
const read = (f) => JSON.parse(readFileSync(f, "utf8"));
const samples = read("frontend/src/data/geometry-samples.json").samples;
const fxDir = "docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/";
const ids = arg("--only").split(",");
const env = (id) => samples.find((s) => s.id === id)?.envelope ?? read(`${fxDir}${id}.json`).envelope;
const receipt = { url, rows: [], errors: [] };
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.route("**/*", (r) => { const u = new URL(r.request().url()); if (u.hostname !== "127.0.0.1") return r.abort();
    if (u.pathname.startsWith("/api/")) return r.fulfill({ json: null }); return r.continue(); });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => receipt.errors.push(e.message.split("\n")[0]));
  for (const id of ids) {
    await page.goto(url);
    await page.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, env(id));
    const canvas = page.locator(".geo3d-canvas canvas");
    await canvas.waitFor();
    if (drag) {
      const box = await canvas.boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + box.height * drag, box.y + box.height / 2, { steps: 20 }); await page.mouse.up(); await page.mouse.move(0, 0);
    }
    const max = Number(await page.locator(".geo3d-scrub input").getAttribute("max"));
    for (let k = 0; k <= max; k++) {
      await page.locator(".geo3d-scrub input").evaluate((el, v) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, String(v));
        el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); }, k);
      await page.waitForTimeout(600);
      const status = await page.locator(".geo3d-trang-thai, [data-step-status]").first().textContent().catch(() => null);
      const file = `${id}-step${String(k).padStart(2, "0")}.png`;
      writeFileSync(join(out, file), await canvas.screenshot());
      receipt.rows.push({ id, step: k, file, status, camera: await page.evaluate(() => window.__geo3d_camera_snapshot) });
    }
  }
} finally { await browser.close(); }
writeFileSync(join(out, "receipt.json"), JSON.stringify(receipt, null, 1) + "\n");
console.log(JSON.stringify({ rows: receipt.rows.length, errors: receipt.errors }));
