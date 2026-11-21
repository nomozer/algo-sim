/**
 * V17 pointer trace: why did a drag starting at the canvas centre not rotate the /10 V17 scene (2/2 passes)?
 * Real app (vite preview + live backend). For each start delay after the canvas appears, a fresh problem load, then:
 * element under the drag start, which targets received pointerdown/move/up (capture on document and canvas), whether
 * OrbitControls changed the frame (pixel diff with the cursor parked off-canvas) and whether labels moved.
 * usage: node v17_pointer_probe.mjs --out <dir> [--base http://127.0.0.1:4173] [--text "<problem>"] [--tag v17]
 */
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const FE = resolve(join(import.meta.dirname, "../../../../../../frontend"));
const { chromium } = createRequire(join(FE, "package.json"))("playwright");
const { docPNG } = await import(pathToFileURL(join(FE, "scripts/png-pixels.mjs")).href);
const BASE = arg("base", "http://127.0.0.1:4173");
const OUT = resolve(arg("out")); mkdirSync(OUT, { recursive: true });
const TAG = arg("tag", "v17");
const TEXT = arg("text", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SB vuông góc với (ABC), SB = a. Hãy mô phỏng hình chóp.");
const OUTF = join(OUT, `pointer_trace_${TAG}.json`);
if (existsSync(OUTF)) throw new Error(`refusing to overwrite ${OUTF}`);

function diff(a, b) {
  const A = docPNG(a), B = docPNG(b); let d = 0;
  for (let i = 0; i < A.w * A.h * 4; i += 4) if (Math.abs(A.rgba[i] - B.rgba[i]) + Math.abs(A.rgba[i + 1] - B.rgba[i + 1]) + Math.abs(A.rgba[i + 2] - B.rgba[i + 2]) > 24) d++;
  return +(d / (A.w * A.h)).toFixed(5);
}
const HOOK = `(() => { const L = []; window.__PTR__ = L;
  for (const t of ["pointerdown", "pointermove", "pointerup", "lostpointercapture"]) document.addEventListener(t, (e) => {
    if (t === "pointermove" && L.filter((x) => x.t === t).length > 3) return;
    const el = e.target; L.push({ t, tag: el.tagName, cls: String(el.className || "").slice(0, 60), def: e.defaultPrevented, x: e.clientX, y: e.clientY });
  }, true); })();`;

const browser = await chromium.launch();
const results = [];
for (const [where, delay] of [["centre", 0], ["centre", 500], ["centre", 1500], ["centre", 3000], ["empty", 0]]) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  await ctx.addInitScript(HOOK);
  const tag = `${Date.now()}${Math.random().toString(16).slice(2, 6)}`;
  await ctx.request.post(`${BASE}/api/auth/register`, { data: { email: `v17-${tag}@example.com`, displayName: "v17", password: "LiveAcceptance!2026" } });
  const page = await ctx.newPage();
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.locator(".composer-text").fill(TEXT);
  await page.locator("#btn-composer-send").click();
  const cv = page.locator(".geo3d-canvas canvas").first();
  await cv.waitFor({ state: "visible", timeout: 60000 });
  await page.waitForTimeout(delay);
  const box = await cv.boundingBox();
  const start = where === "centre" ? { x: box.x + box.width / 2, y: box.y + box.height / 2 }
    : await page.evaluate(() => { const c = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect(); return { x: c.x + c.width * 0.12, y: c.y + c.height * 0.15 }; });
  const under = await page.evaluate(({ x, y }) => { const e = document.elementFromPoint(x, y); const cs = e && getComputedStyle(e);
    return e && { tag: e.tagName, cls: String(e.className || "").slice(0, 80), text: (e.textContent || "").slice(0, 30), pointerEvents: cs.pointerEvents }; }, start);
  const labels0 = await page.evaluate(() => [...document.querySelectorAll(".geo3d-label")].map((e) => { const r = e.getBoundingClientRect(); return [e.dataset.id, Math.round(r.x), Math.round(r.y)]; }));
  await page.mouse.move(2, 2); const s0 = await cv.screenshot();
  await page.evaluate(() => { window.__PTR__.length = 0; });
  await page.mouse.move(start.x, start.y); await page.mouse.down();
  await page.mouse.move(start.x + 140, start.y + 50, { steps: 8 }); await page.mouse.up();
  await page.waitForTimeout(250); await page.mouse.move(2, 2); await page.waitForTimeout(150);
  const s1 = await cv.screenshot();
  const labels1 = await page.evaluate(() => [...document.querySelectorAll(".geo3d-label")].map((e) => { const r = e.getBoundingClientRect(); return [e.dataset.id, Math.round(r.x), Math.round(r.y)]; }));
  const moved = labels0.filter(([id, x, y]) => { const b = labels1.find((l) => l[0] === id); return b && Math.abs(b[1] - x) + Math.abs(b[2] - y) > 3; }).length;
  const events = await page.evaluate(() => window.__PTR__);
  const rec = { where, delay_ms: delay, start, element_under_start: under, events, frame_pixel_diff: diff(s0, s1), labels_moved: moved, labels: labels0.length,
    rotated: diff(s0, s1) > 0.002 && moved > 0 };
  results.push(rec);
  writeFileSync(join(OUT, `${TAG}_${where}_${delay}.png`), await page.screenshot());
  console.log(where, delay, JSON.stringify({ under, rotated: rec.rotated, diff: rec.frame_pixel_diff, moved, firstDown: events.find((e) => e.t === "pointerdown") }));
  await ctx.close();
}
// a CLICK (no movement) on the centre chip must still select its quantity (aria-pressed) and must not rotate
{
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } });
  const tag = `${Date.now()}c`;
  await ctx.request.post(`${BASE}/api/auth/register`, { data: { email: `v17c-${tag}@example.com`, displayName: "v17", password: "LiveAcceptance!2026" } });
  const page = await ctx.newPage();
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.locator(".composer-text").fill(TEXT);
  await page.locator("#btn-composer-send").click();
  const cv = page.locator(".geo3d-canvas canvas").first();
  await cv.waitFor({ state: "visible", timeout: 60000 });
  await page.waitForTimeout(800);
  const box = await cv.boundingBox();
  const c = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  const annId = await page.evaluate(({ x, y }) => document.elementFromPoint(x, y)?.closest("[data-ann-id]")?.getAttribute("data-ann-id") ?? null, c);
  await page.mouse.move(2, 2); const s0 = await cv.screenshot();
  await page.mouse.click(c.x, c.y); await page.waitForTimeout(300);
  const pressed = annId ? await page.evaluate((id) => document.querySelector(`[data-ann-id="${id}"]`)?.getAttribute("aria-pressed"), annId) : null;
  await page.mouse.move(2, 2); await page.waitForTimeout(150);
  results.push({ where: "chip_click", ann_id: annId, aria_pressed_after_click: pressed, frame_pixel_diff: diff(s0, await cv.screenshot()) });
  console.log("chip_click", annId, pressed);
  await ctx.close();
}
await browser.close();
writeFileSync(OUTF, JSON.stringify({ schema: "axo-v17-pointer-trace/1", text: TEXT, browser: "playwright chromium", results }, null, 1));
