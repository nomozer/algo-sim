/**
 * Live browser acceptance for the local-only route: drives the REAL Axo UI (vite preview of frontend/dist, /api proxied
 * to a running backend in HYBRID_ROUTE_MODE=local-only-scoped with the real GGUF) through Playwright Chromium.
 * No mocks, no route interception, no fixtures: every scene comes from POST /api/analyze answered by the backend.
 *
 * Per case: type the problem, submit, record the network response, wait for the 3D canvas or the refusal surface,
 * time the first WebGL draw after the response (first visible scene) and the first draw after a pointer drag
 * (first interactive frame), screenshot, check DOM vertex labels against the gold vertex set, orbit / zoom / step,
 * verify 0 extra /api/analyze calls during interaction, collect console errors and every non-loopback request.
 *
 * usage: node live_browser_acceptance.mjs --manifest <json> --out <dir> --base http://127.0.0.1:4173
 *        [--ids V01,V02] [--viewport 1366x768] [--tag main]
 */
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync, appendFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const FE = resolve(arg("frontend", join(import.meta.dirname, "../../../../../../frontend")));
const { chromium } = createRequire(join(FE, "package.json"))("playwright");
const { docPNG } = await import(pathToFileURL(join(FE, "scripts/png-pixels.mjs")).href);

const BASE = arg("base", "http://127.0.0.1:4173");
const OUT = resolve(arg("out"));
const TAG = arg("tag", "main");
const [VW, VH] = arg("viewport", "1366x768").split("x").map(Number);
const man = JSON.parse(readFileSync(arg("manifest"), "utf8"));
const ALL = [...man.valid_cases, ...man.negative_cases];
const ids = arg("ids") ? new Set(arg("ids").split(",")) : null;
const CASES = ALL.filter((c) => !ids || ids.has(c.case_id));
mkdirSync(join(OUT, "screenshots"), { recursive: true });
const REC = join(OUT, `browser_records_${TAG}.jsonl`);
const BODIES = join(OUT, `responses_${TAG}.jsonl`);
if (existsSync(REC)) throw new Error(`refusing to overwrite ${REC}`);

const pid = (t) => t.replace("'", "_prime");
const sha = (b) => createHash("sha256").update(b).digest("hex");
const LEAK = /\b(?:[A-Z]{2,}_[A-Z_]{3,}|kq_\w+|td_\w+|Traceback|reason_code|simulation_id)\b/;

/* WebGL draw timestamps, installed before any page script (product code untouched). */
const HOOK = `(() => {
  const D = { draws: [], ptr: [] }; window.__ACC__ = D;
  const wrap = (p) => { for (const f of ["drawElements", "drawArrays"]) { const o = p[f]; if (!o) continue;
    p[f] = function () { if (D.draws.length < 20000) D.draws.push(performance.now()); return o.apply(this, arguments); }; } };
  if (window.WebGL2RenderingContext) wrap(WebGL2RenderingContext.prototype);
  if (window.WebGLRenderingContext) wrap(WebGLRenderingContext.prototype);
  addEventListener("pointerdown", () => D.ptr.push(performance.now()), true);
  addEventListener("click", (e) => { if (e.target.closest && e.target.closest("#btn-composer-send")) D.tSubmit = performance.now(); }, true);
})();`;

function canvasStats(png) {
  const { w, h, rgba: data } = docPNG(png);
  const ch = 4;
  const bg = [data[0], data[1], data[2]];
  let ink = 0;
  for (let i = 0; i < w * h; i++) {
    const o = i * ch;
    if (Math.abs(data[o] - bg[0]) + Math.abs(data[o + 1] - bg[1]) + Math.abs(data[o + 2] - bg[2]) > 30) ink++;
  }
  return { width: w, height: h, ink_fraction: +(ink / (w * h)).toFixed(4) };
}

async function labels(page) {
  return page.evaluate(() => {
    const cv = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect();
    return [...document.querySelectorAll(".geo3d-label")].map((e) => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      return { id: e.dataset.id, text: e.textContent, x: Math.round(cx), y: Math.round(cy),
        visible: cs.display !== "none" && cs.visibility !== "hidden" && +cs.opacity > 0 && r.width > 0,
        inside: !!cv && cx >= cv.x && cx <= cv.x + cv.width && cy >= cv.y && cy <= cv.y + cv.height };
    });
  });
}

const firstAfter = (arr, t) => arr.find((x) => x > t);

async function newSession(browser) {
  const ctx = await browser.newContext({ viewport: { width: VW, height: VH } });
  await ctx.addInitScript(HOOK);
  const tag = `${Date.now()}${Math.random().toString(16).slice(2, 6)}`;
  const r = await ctx.request.post(`${BASE}/api/auth/register`, { data: {
    email: `live-browser-${tag}@example.com`, displayName: `Live ${tag}`, password: "LiveAcceptance!2026" } });
  if (!r.ok()) throw new Error(`register HTTP ${r.status()}`);
  return ctx;
}

async function runCase(page, c, net) {
  const rec = { case_id: c.case_id, tag: TAG, viewport: `${VW}x${VH}`, intent: c.simulation_intent, expected: c.expected_behavior };
  await page.goto(BASE, { waitUntil: "networkidle" });
  const composer = page.locator(".composer-text");
  await composer.waitFor({ state: "visible", timeout: 15000 });
  rec.readiness_text = await page.evaluate(() => [...document.querySelectorAll(".composer-sr-only")].map((e) => e.textContent).join(" | "));
  await composer.fill(c.original_input);
  const analyzeBefore = net.analyze;
  const respP = page.waitForResponse((r) => r.url().includes("/api/analyze") && r.request().method() === "POST", { timeout: 150000 });
  respP.catch(() => {});
  await page.locator("#btn-composer-send").click({ timeout: 10000 });
  const resp = await respP;
  const raw = await resp.text();
  let body = {};
  try { body = JSON.parse(raw); } catch { /* recorded as non-JSON */ }
  appendFileSync(BODIES, JSON.stringify({ case_id: c.case_id, tag: TAG, http: resp.status(), body }) + "\n");
  const rd = body.route_d || {};
  Object.assign(rec, { http: resp.status(), route_status: rd.status ?? null, extraction_mode: rd.extraction_mode ?? null,
    chosen_route: rd.adaptive_telemetry?.chosen_route ?? null, fallback_reason: rd.adaptive_telemetry?.fallback_reason ?? null,
    provider_calls: rd.adaptive_telemetry?.total_provider_calls ?? null, backend_total_ms: rd.adaptive_telemetry?.total_ms ?? null,
    refusal_code: rd.refusal?.code ?? body.envelope?.reason_code ?? body.reason_code ?? null,
    failure_category: body.envelope?.failure_category ?? null, ux_state: body.local_ai_ux?.ux_state ?? null,
    response_sha256: sha(raw) });

  const served = resp.status() === 200 && rd.status === "SERVED";
  // which surface the learner sees
  const surface = await Promise.race([
    page.locator(".geo3d-canvas canvas").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "SCENE"),
    page.locator(".refusal-facts, [data-clarification-question], section.card .eyebrow").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "REFUSAL"),
    page.locator(".axo-composer-toast").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "TOAST"),
  ]).catch(() => "NONE");
  rec.surface = surface;
  const timing = await page.evaluate(() => {
    const e = performance.getEntriesByType("resource").filter((x) => x.name.includes("/api/analyze")).pop();
    return { tSubmit: window.__ACC__.tSubmit, reqStart: e?.requestStart, respEnd: e?.responseEnd };
  });
  rec.http_round_trip_ms = timing.respEnd && timing.tSubmit ? +(timing.respEnd - timing.tSubmit).toFixed(1) : null;

  if (surface === "SCENE") {
    await page.waitForTimeout(300);
    const draws = await page.evaluate(() => window.__ACC__.draws.slice());
    const fv = firstAfter(draws, timing.respEnd);
    rec.first_visible_scene_ms = fv ? +(fv - timing.tSubmit).toFixed(1) : null;
    // first interactive frame: drag as soon as the scene is up, first draw after the pointer goes down
    const cv = page.locator(".geo3d-canvas canvas").first();
    const box = await cv.boundingBox();
    rec.canvas_box = box && { w: Math.round(box.width), h: Math.round(box.height) };
    const before = await labels(page);
    const shot0 = await cv.screenshot();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 140, box.y + box.height / 2 + 50, { steps: 8 });
    await page.mouse.up();
    await page.waitForTimeout(250);
    const acc = await page.evaluate(() => ({ draws: window.__ACC__.draws.slice(), ptr: window.__ACC__.ptr.slice() }));
    const pdown = acc.ptr[acc.ptr.length - 1];
    const fi = firstAfter(acc.draws, pdown);
    rec.first_interactive_frame_ms = fi && rec.first_visible_scene_ms ? +(fi - timing.tSubmit).toFixed(1) : null;
    const shot1 = await cv.screenshot();
    const after = await labels(page);
    const moved = before.filter((l) => { const a = after.find((x) => x.id === l.id); return a && (Math.abs(a.x - l.x) + Math.abs(a.y - l.y)) > 3; }).length;
    rec.orbit = { frame_changed: sha(shot0) !== sha(shot1), labels_moved: moved, labels_before: before.length,
      label_ids_stable: JSON.stringify(before.map((l) => l.id).sort()) === JSON.stringify(after.map((l) => l.id).sort()) };
    // zoom
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.wheel(0, -300); await page.waitForTimeout(250);
    const shotZ = await cv.screenshot();
    await page.mouse.wheel(0, 300); await page.waitForTimeout(250);
    rec.zoom = { frame_changed: sha(shot1) !== sha(shotZ) };
    // steps (opens at step 1 by product design), then full model
    const stepLbl = page.locator(".geo3d-progress").first();
    rec.step = { initial: (await stepLbl.textContent().catch(() => null))?.trim() ?? null };
    const prev = page.locator('button[aria-label="Bước trước"]').first();
    if (await prev.isEnabled().catch(() => false)) {
      await prev.click(); await page.waitForTimeout(150); rec.step.after_prev = (await stepLbl.textContent())?.trim();
      rec.step.labels_at_prev = (await labels(page)).filter((l) => l.visible).length;
      await page.locator('button[aria-label="Bước sau"]').first().click(); await page.waitForTimeout(150);
      rec.step.after_next = (await stepLbl.textContent())?.trim();
    }
    const full = page.getByRole("button", { name: "Xem mô hình đầy đủ" });
    if (await full.count()) await full.first().click();
    await page.waitForTimeout(400);
    rec.step.final = (await stepLbl.textContent().catch(() => null))?.trim() ?? null;
    const L = await labels(page);
    const gold = [...c.gold_entities.solid_vertices, ...c.gold_entities.auxiliary_points].map(pid);
    const shown = new Set(L.filter((l) => l.visible).map((l) => l.id));
    rec.labels = { gold_missing: gold.filter((g) => !shown.has(g)), outside_canvas: L.filter((l) => l.visible && !l.inside).map((l) => l.id),
      shown: [...shown].sort(), label_text_mismatch: L.filter((l) => /^[A-Z]/.test(l.id) && !l.id.includes("_") && l.text && !l.text.startsWith(l.id[0])).map((l) => l.id) };
    const png = await cv.screenshot();
    rec.canvas_pixels = canvasStats(png);
    const shotPath = join("screenshots", `${TAG}_${c.case_id}.png`);
    writeFileSync(join(OUT, shotPath), await page.screenshot());
    rec.screenshot = shotPath; rec.screenshot_sha256 = sha(readFileSync(join(OUT, shotPath)));
    rec.analyze_calls_during_interaction = net.analyze - analyzeBefore - 1;
  } else {
    rec.learner_text = await page.evaluate(() => {
      const t = document.querySelector(".axo-composer-toast");
      const card = document.querySelector(".refusal-facts")?.closest("section");
      return ((t?.innerText || "") + (card ? `\n${card.innerText}` : "")).trim().slice(0, 1500) || null;
    });
    rec.canvas_present = await page.locator(".geo3d-canvas canvas").count();
    const shotPath = join("screenshots", `${TAG}_${c.case_id}.png`);
    writeFileSync(join(OUT, shotPath), await page.screenshot());
    rec.screenshot = shotPath;
  }
  const visibleText = await page.evaluate(() => document.body.innerText);
  rec.ui_token_leak = (visibleText.match(LEAK) || [null])[0];
  rec.cloud_key_text = /khóa AI|API key|Gemini/i.test(visibleText);
  return { rec, served };
}

const browser = await chromium.launch();
const env = { browser_version: browser.version(), base: BASE, viewport: `${VW}x${VH}`, started_utc: new Date().toISOString() };
writeFileSync(join(OUT, `browser_env_${TAG}.json`), JSON.stringify(env, null, 1));
let ctx = null, page = null, used = 0;
const net = { analyze: 0, external: [] };
for (const c of CASES) {
  if (!ctx || used >= 14) {
    if (ctx) await ctx.close();
    ctx = await newSession(browser); page = await ctx.newPage(); used = 0;
    page.on("request", (r) => {
      const u = new URL(r.url());
      if (u.pathname.startsWith("/api/analyze")) net.analyze += 1;
      if (!["127.0.0.1", "localhost"].includes(u.hostname) && !u.protocol.startsWith("data") && !u.protocol.startsWith("blob")) net.external.push(r.url());
    });
    page.on("console", (m) => { if (m.type() === "error") page.__err?.push(m.text().slice(0, 300)); });
    page.on("pageerror", (e) => page.__err?.push(`pageerror: ${String(e).slice(0, 300)}`));
  }
  page.__err = [];
  const extBefore = net.external.length;
  let out;
  try { out = await runCase(page, c, net); } catch (e) { out = { rec: { case_id: c.case_id, tag: TAG, harness_error: String(e).slice(0, 500) } }; }
  used += 1;
  out.rec.console_errors = page.__err.slice();
  out.rec.external_requests = net.external.slice(extBefore);
  appendFileSync(REC, JSON.stringify(out.rec) + "\n");
  console.log(JSON.stringify({ id: c.case_id, http: out.rec.http, rs: out.rec.route_status, surface: out.rec.surface,
    fv: out.rec.first_visible_scene_ms, fi: out.rec.first_interactive_frame_ms, ink: out.rec.canvas_pixels?.ink_fraction,
    miss: out.rec.labels?.gold_missing, err: out.rec.harness_error }));
}
await browser.close();
