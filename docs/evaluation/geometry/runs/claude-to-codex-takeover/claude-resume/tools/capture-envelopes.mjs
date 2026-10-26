// Capture route-D envelopes from a JSON map {name: envelope} through the product store (0 provider calls; /api/*
// stubbed), Mode A and Mode B (analysis panel), five orbit gestures, desktop + mobile. Same loading and orbit
// mechanics as `../../../scene3d-to-hybrid-v2-replacement/tools/capture-p0.mjs`. Run from the repo root:
//   node docs/evaluation/geometry/runs/claude-to-codex-takeover/claude-resume/tools/capture-envelopes.mjs \
//     --url http://127.0.0.1:3197 --envelopes <map.json> --out <fresh dir>
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
import { createHash } from "node:crypto";
const { chromium } = createRequire(resolve("frontend/package.json"))("playwright");
const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const url = arg("--url", "http://127.0.0.1:3197"), out = resolve(arg("--out"));
if (existsSync(out)) throw Error("Fresh output required");
mkdirSync(out, { recursive: true });
const envelopes = JSON.parse(readFileSync(arg("--envelopes"), "utf8"));
const CAMERAS = { default: null, quarter: [0.25, 0], half: [0.5, 0], high: [0, 0.15], low: [0, -0.15] };
const sha = (b) => createHash("sha256").update(b).digest("hex");
const receipt = { tree_head: execFileSync("git", ["rev-parse", "HEAD"]).toString().trim(),
  tree_dirty: execFileSync("git", ["status", "--porcelain", "--", "frontend/src", "backend/app"]).toString().trim() !== "",
  envelopes_sha256: sha(readFileSync(arg("--envelopes"))), viewport_policy: "1440x900 DPR1 / 390x844 DPR2",
  modes: ["A (default)", "B (analysis panel open)"], url, provider_calls: 0, rows: [], errors: [] };
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
try {
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, deviceScaleFactor: width === 390 ? 2 : 1 });
    await ctx.route("**/*", (r) => { const u = new URL(r.request().url()); if (u.hostname !== "127.0.0.1") return r.abort();
      if (u.pathname.startsWith("/api/")) return r.fulfill({ json: u.pathname === "/api/health" ? { status: "ok" } : null }); return r.continue(); });
    const page = await ctx.newPage();
    await page.goto(url);
    page.on("pageerror", (e) => receipt.errors.push(e.message.split("\n")[0]));
    for (const [name, envelope] of Object.entries(envelopes)) for (const mode of ["A", "B"]) for (const [cam, drag] of Object.entries(CAMERAS)) {
      await page.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, envelope);
      const canvas = page.locator(".geo3d-canvas canvas");
      await canvas.waitFor();
      await page.locator(".geo3d-scrub input").evaluate((el) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, el.max);
        el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); });
      if (mode === "B") {
        const nut = page.locator("[data-mode-b-toggle]").first();
        if (await nut.count() === 0) { receipt.errors.push(`${name}: no Mode B toggle`); continue; }
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
      const meta = await page.evaluate(() => ({ witnesses: window.__geo3d_witness_ids ?? null }));
      const png = await page.screenshot(), file = `${name.replace(/[^\w-]/g, "_")}-${width}-${mode}-${cam}.png`;
      writeFileSync(join(out, file), png);
      receipt.rows.push({ name, width, mode, cam, file, sha256: sha(png), ...meta });
    }
    await ctx.close();
  }
} finally { await browser.close(); }
writeFileSync(join(out, "receipt.json"), JSON.stringify(receipt, null, 1) + "\n");
console.log(JSON.stringify({ rows: receipt.rows.length, errors: receipt.errors.length }));
