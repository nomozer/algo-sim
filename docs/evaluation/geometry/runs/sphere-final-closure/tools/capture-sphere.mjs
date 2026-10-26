// Sphere acceptance capture through the product store (0 provider calls; /api/* stubbed). Same loading and orbit
// mechanics as `../../scene3d-to-hybrid-v2-replacement/tools/capture-p0.mjs`. Run from the repo root:
//   node docs/evaluation/geometry/runs/sphere-final-closure/tools/capture-sphere.mjs --url http://127.0.0.1:3197 \
//     --envelopes <name→envelope json> --out <fresh dir>
// Per envelope × viewport: named cameras (canvas shots), a 24-step continuous orbit (canvas shots, analysed by
// `silhouette_scan.py`), and for section scenes: «Hình phụ» on, section selected, section deselected (full page).
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
const parts = new Set(arg("--parts", "named,orbit,interact").split(","));
// Orbit drags in canvas-height fractions: [dx, dy].
const CAMERAS = { front: null, right: [0.25, 0], back: [0.5, 0], left: [-0.25, 0], high: [0, 0.2], low: [0, -0.2],
  "near-edge-on": [0, -0.12] };
const sha = (b) => createHash("sha256").update(b).digest("hex");
const receipt = { tree_head: execFileSync("git", ["rev-parse", "HEAD"]).toString().trim(),
  tree_dirty: execFileSync("git", ["status", "--porcelain", "--", "frontend/src", "backend/app"]).toString().trim() !== "",
  envelopes_sha256: sha(readFileSync(arg("--envelopes"))), viewport_policy: "1440x900 DPR1 / 390x844 DPR2",
  url, provider_calls: 0, rows: [], errors: [] };
const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const settle = (page) => page.waitForFunction(() => { const s = JSON.stringify(window.__geo3d_camera_snapshot);
  window.__capStable = s === window.__capLast ? (window.__capStable ?? 0) + 1 : 0; window.__capLast = s; return window.__capStable >= 4; },
null, { polling: "raf", timeout: 20000 });
try {
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, deviceScaleFactor: width === 390 ? 2 : 1 });
    await ctx.route("**/*", (r) => { const u = new URL(r.request().url()); if (u.hostname !== "127.0.0.1") return r.abort();
      if (u.pathname.startsWith("/api/")) return r.fulfill({ json: u.pathname === "/api/health" ? { status: "ok" } : null }); return r.continue(); });
    const page = await ctx.newPage();
    await page.goto(url);
    page.on("pageerror", (e) => receipt.errors.push(e.message.split("\n")[0]));
    const load = async (envelope) => {
      await page.evaluate(async (e) => { const { useAppStore } = await import("/src/state/store.ts"); useAppStore.getState().loadEnvelope(e); }, envelope);
      const canvas = page.locator(".geo3d-canvas canvas");
      await canvas.waitFor();
      await page.locator(".geo3d-scrub input").evaluate((el) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, el.max);
        el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); });
      return canvas;
    };
    const drag = async (canvas, [dx, dy], steps = 20) => {
      const box = await canvas.boundingBox();
      await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5); await page.mouse.down();
      await page.mouse.move(box.x + box.width * 0.5 + box.height * dx, box.y + box.height * (0.5 + dy), { steps }); await page.mouse.up();
      await page.mouse.move(0, 0);
      await settle(page);
    };
    const shot = async (name, kind, node) => {
      const png = await node.screenshot(), file = `${name}-${width}-${kind}.png`;
      writeFileSync(join(out, file), png);
      receipt.rows.push({ name, width, kind, file, sha256: sha(png) });
    };
    for (const [name, envelope] of Object.entries(envelopes)) {
      if (parts.has("named")) for (const [cam, d] of Object.entries(CAMERAS)) {
        const canvas = await load(envelope);
        if (d) await drag(canvas, d); else await settle(page);
        await shot(name, cam, canvas);
      }
      // Continuous orbit: 24 equal horizontal steps from the default view (≈ one full turn over the sweep).
      if (parts.has("orbit")) {
        const canvas = await load(envelope);
        await settle(page);
        for (let k = 0; k < 24; k += 1) {
          if (k) await drag(canvas, [0.085, 0], 6);
          await shot(name, `orbit${String(k).padStart(2, "0")}`, canvas);
        }
      }
      const coVong = parts.has("interact") && envelope.scene3d.objects.some((o) => o.type === "circle3");
      if (coVong) {
        await load(envelope); await settle(page);
        const menu = page.getByRole("button", { name: "Hiển thị" });
        if (await menu.count()) {
          await menu.first().click();
          const phu = page.getByText("Hình phụ", { exact: true });
          if (await phu.count()) { await phu.first().click(); await page.keyboard.press("Escape"); await settle(page); await shot(name, "aux-on", page); }
          else receipt.errors.push(`${name}: no «Hình phụ» toggle (no auxiliary geometry in this scene)`);
          await page.keyboard.press("Escape");
        }
        await load(envelope); await settle(page);
        const khamPha = page.locator('[data-mo-nhom="kham-pha"]');
        if (await khamPha.count()) {
          await khamPha.first().click();
          const thanhPhan = page.getByText("Thành phần", { exact: true });
          if (await thanhPhan.count()) await thanhPhan.first().click();
          await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; }));
        }
        const muc = page.locator('[data-tree-id="C"]');
        if (await muc.count()) {
          await muc.first().click(); await settle(page); await shot(name, "section-selected", page);
          await muc.first().click(); await settle(page); await shot(name, "section-deselected", page);
        } else receipt.errors.push(`${name}: section tree item not reachable`);
        await page.keyboard.press("Escape");
      }
    }
    await ctx.close();
  }
} finally { await browser.close(); }
writeFileSync(join(out, "receipt.json"), JSON.stringify(receipt, null, 1) + "\n");
console.log(JSON.stringify({ rows: receipt.rows.length, errors: receipt.errors }));
