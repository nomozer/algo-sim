/**
 * /11 UI scenarios I01–I08 on the real app (vite preview of dist + live local-only backend). No mocks, no route
 * interception: every scene and refusal is a real POST /api/analyze answered by the backend. Problems come from the
 * frozen /11 manifest (ids passed in), plus the /10 V17 text for I01 (exposed regression text, named as such).
 * I06 needs a backend started with a short deadline (HYBRID_LIVE_TIMEOUT_SECONDS) — run it alone with --only I06.
 * usage: node v11_ui_scenarios.mjs --manifest <json> --out <dir> --scenes S01,C09,C13 --clarify N17 --slm Q04 --fast C09
 *        [--only I01,I02] [--base http://127.0.0.1:4173] [--tag main]
 */
import { createRequire } from "node:module";
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const FE = resolve(join(import.meta.dirname, "../../../../../../frontend"));
const { chromium } = createRequire(join(FE, "package.json"))("playwright");
const { docPNG } = await import(pathToFileURL(join(FE, "scripts/png-pixels.mjs")).href);
const BASE = arg("base", "http://127.0.0.1:4173");
const OUT = resolve(arg("out")); mkdirSync(join(OUT, "screenshots"), { recursive: true });
const TAG = arg("tag", "main");
const OUTF = join(OUT, `ui_scenarios_${TAG}.json`);
if (existsSync(OUTF)) throw new Error(`refusing to overwrite ${OUTF}`);
const man = JSON.parse(readFileSync(arg("manifest"), "utf8"));
const byId = Object.fromEntries([...man.valid_cases, ...man.negative_cases].map((c) => [c.case_id, c]));
byId.V17_10 = { case_id: "V17_10", original_input: "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SB vuông góc với (ABC), SB = a. Hãy mô phỏng hình chóp.",
  gold_entities: { solid_vertices: ["S", "A", "B", "C"], auxiliary_points: [] } };
const SCENES = arg("scenes").split(","), CLARIFY = arg("clarify"), SLM = arg("slm"), FAST = arg("fast");
const only = arg("only") ? new Set(arg("only").split(",")) : null;
const want = (id) => !only || only.has(id);
const results = [];
const rec = (id, ok, detail) => { results.push({ scenario_id: id, pass: ok, ...detail }); console.log(id, ok ? "PASS" : "FAIL", JSON.stringify(detail).slice(0, 300)); };

function pixelDiff(a, b) {
  const A = docPNG(a), B = docPNG(b);
  if (A.w !== B.w || A.h !== B.h) return 1;
  let d = 0;
  for (let i = 0; i < A.w * A.h * 4; i += 4) if (Math.abs(A.rgba[i] - B.rgba[i]) + Math.abs(A.rgba[i + 1] - B.rgba[i + 1]) + Math.abs(A.rgba[i + 2] - B.rgba[i + 2]) > 24) d++;
  return +(d / (A.w * A.h)).toFixed(5);
}
const shot = async (page) => { await page.mouse.move(2, 2); await page.waitForTimeout(200); return page.locator(".geo3d-canvas canvas").first().screenshot(); };
const labelPos = (page) => page.evaluate(() => Object.fromEntries([...document.querySelectorAll(".geo3d-label")]
  .map((e) => { const r = e.getBoundingClientRect(); return [e.dataset.id, [Math.round(r.x), Math.round(r.y)]]; })));
const labelIds = (page) => page.evaluate(() => [...document.querySelectorAll(".geo3d-label")]
  .filter((e) => e.checkVisibility({ opacityProperty: true, visibilityProperty: true })).map((e) => e.dataset.id).sort());
const goldIds = (id) => [...byId[id].gold_entities.solid_vertices, ...byId[id].gold_entities.auxiliary_points].map((t) => t.replace("'", "_prime")).sort();
const maxDrift = (a, b) => Math.max(0, ...Object.keys(a).map((k) => b[k] ? Math.abs(b[k][0] - a[k][0]) + Math.abs(b[k][1] - a[k][1]) : 999));

async function session(browser, vw = 1366, vh = 768) {
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh } });
  const tag = `${Date.now()}${Math.random().toString(16).slice(2, 6)}`;
  const r = await ctx.request.post(`${BASE}/api/auth/register`, { data: { email: `v11ui-${tag}@example.com`, displayName: `UI ${tag}`, password: "LiveAcceptance!2026" } });
  if (!r.ok()) throw new Error(`register ${r.status()}`);
  const page = await ctx.newPage();
  page.__errors = []; page.__analyze = [];
  page.on("console", (m) => { if (m.type() === "error") page.__errors.push(m.text().slice(0, 200)); });
  page.on("pageerror", (e) => page.__errors.push(String(e).slice(0, 200)));
  page.on("request", (q) => { if (q.url().includes("/api/analyze")) page.__analyze.push(Date.now()); });
  await page.goto(BASE, { waitUntil: "networkidle" });
  return { ctx, page };
}
async function submit(page, id, { wait = true } = {}) {
  const box = page.locator(".composer-text");
  await box.waitFor({ state: "visible", timeout: 15000 });
  await box.fill(byId[id].original_input);
  const resp = page.waitForResponse((r) => r.url().includes("/api/analyze") && r.request().method() === "POST", { timeout: 150000 });
  await page.locator("#btn-composer-send").click();
  if (!wait) return { pending: resp };
  const r = await resp; const body = await r.json().catch(() => ({}));
  const surface = await Promise.race([
    page.locator(".geo3d-canvas canvas").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "SCENE"),
    page.locator(".axo-composer-toast").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "TOAST"),
  ]).catch(() => "NONE");
  if (surface === "SCENE") {
    const full = page.getByRole("button", { name: "Xem mô hình đầy đủ" });
    if (await full.count()) await full.first().click();
    await page.waitForTimeout(600);
  }
  return { http: r.status(), route: body.route_d?.status ?? null, mode: body.route_d?.extraction_mode ?? null, surface };
}
async function backToComposer(page) {
  const b = page.getByRole("button", { name: "Đổi đề toán" });
  if (await b.count()) await b.first().click(); else await page.locator(".geo3d-quay-lai").first().click();
  await page.locator(".composer-text").waitFor({ state: "visible", timeout: 10000 });
}
/** drag from p by (140, 50); rotated = frame changed AND some label moved AND label set unchanged AND 0 re-analysis */
async function drag(page, p) {
  const calls = page.__analyze.length; const s0 = await shot(page); const l0 = await labelPos(page);
  const under = await page.evaluate(({ x, y }) => { const e = document.elementFromPoint(x, y); return e && { tag: e.tagName, cls: String(e.className || "").slice(0, 60) }; }, p);
  await page.mouse.move(p.x, p.y); await page.mouse.down(); await page.mouse.move(p.x + 140, p.y + 50, { steps: 8 }); await page.mouse.up();
  await page.waitForTimeout(300);
  const s1 = await shot(page); const l1 = await labelPos(page);
  const moved = Object.keys(l0).filter((k) => l1[k] && Math.abs(l1[k][0] - l0[k][0]) + Math.abs(l1[k][1] - l0[k][1]) > 3).length;
  const diff = pixelDiff(s0, s1);
  return { start: { x: Math.round(p.x), y: Math.round(p.y) }, under, frame_pixel_diff: diff, labels_moved: moved,
    rotated: diff > 0.002 && moved > 0 && JSON.stringify(Object.keys(l0).sort()) === JSON.stringify(Object.keys(l1).sort()) && page.__analyze.length === calls };
}
const centre = (page) => page.evaluate(() => { const c = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect(); return { x: c.x + c.width / 2, y: c.y + c.height / 2 }; });
const resetBtn = (page) => page.locator('button[aria-label="Đặt lại góc nhìn 3D"]').first();

const browser = await chromium.launch();
try {
  if (want("I01") || want("I02") || want("I03") || want("I04")) {
    const { ctx, page } = await session(browser);
    if (want("I01")) {
      const per = [];
      for (const id of ["V17_10", ...SCENES]) {
        const s = await submit(page, id);
        const d = s.surface === "SCENE" ? await drag(page, await centre(page)) : null;
        per.push({ case_id: id, surface: s.surface, ...(d || {}) });
        await page.screenshot({ path: join(OUT, "screenshots", `I01_${id}.png`) });
        await backToComposer(page);
      }
      rec("I01", per.every((x) => x.rotated), { scenes: per });
    }
    if (want("I02") || want("I03") || want("I04")) {
      const s = await submit(page, SCENES[0]);
      if (want("I02")) {
        const pts = await page.evaluate(() => {
          const c = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect();
          const L = [...document.querySelectorAll(".geo3d-label")].map((e) => e.getBoundingClientRect());
          const chip = [...document.querySelectorAll(".geo3d-so-do, [data-ann-id]")].map((e) => e.getBoundingClientRect()).find((r) => r.width > 0);
          const a = L[0], b = L[1];
          // a point on the segment between two vertex anchors (an edge, in projection) and one 10 px beside a label
          return { edge: a && b && { x: (a.x + a.width / 2 + b.x + b.width / 2) / 2, y: (a.y + a.height / 2 + b.y + b.height / 2) / 2 },
            chip: chip && { x: chip.x + chip.width / 2, y: chip.y + chip.height / 2 },
            near_label: a && { x: Math.min(c.right - 4, a.right + 10), y: a.y + a.height / 2 } };
        });
        const out = {};
        for (const [k, p] of Object.entries(pts)) out[k] = p ? await drag(page, p) : { absent: true };
        rec("I02", Object.values(out).every((x) => x.absent || x.rotated) && !out.edge.absent, { scene: SCENES[0], surface: s.surface, ...out });
      }
      if (want("I04")) {   // U08 root cause: label positions sampled over time after each reset
        const series = async () => { const t0 = Date.now(); const xs = [];
          for (const t of [100, 300, 600, 1000, 1800, 3000, 4500]) { await page.waitForTimeout(Math.max(0, t - (Date.now() - t0))); xs.push({ t, pos: await labelPos(page) }); }
          return xs; };
        await drag(page, await centre(page));
        await resetBtn(page).click(); const first = await series();
        await resetBtn(page).click(); const second = await series();
        const settled1 = first.at(-1).pos;
        const drift = second.map(({ t, pos }) => ({ t, max_drift_px: maxDrift(settled1, pos) }));
        const firstSelf = first.map(({ t, pos }) => ({ t, max_drift_px_vs_settled: maxDrift(settled1, pos) }));
        rec("I04", drift.at(-1).max_drift_px <= 2, { scene: SCENES[0], second_reset_drift_vs_first_settled: drift, first_reset_convergence: firstSelf,
          settled_first: settled1, settled_second: second.at(-1).pos });
      }
      if (want("I03")) {
        await resetBtn(page).click(); await page.waitForTimeout(1800);
        const afterReset = await drag(page, await centre(page));
        await backToComposer(page);
        const s2 = await submit(page, SCENES[1]);
        const afterChange = await drag(page, await centre(page));
        const ids = await labelIds(page);
        rec("I03", afterReset.rotated && afterChange.rotated && JSON.stringify(ids) === JSON.stringify(goldIds(SCENES[1])),
          { after_reset: afterReset, after_problem_change: { surface: s2.surface, ...afterChange }, labels_after_change: ids, gold: goldIds(SCENES[1]) });
      }
    }
    rec(`I00_console_${TAG}`, page.__errors.length === 0, { console_errors: page.__errors });
    await ctx.close();
  }
  if (want("I05")) {   // first id = the registered I05 case; the rest record what the learner reads (D-cases etc.)
    const per = [];
    for (const id of CLARIFY.split(",")) {
      const { ctx, page } = await session(browser);
      const s = await submit(page, id);
      const toast = await page.locator(".axo-composer-toast").first().innerText().catch(() => "");
      await page.screenshot({ path: join(OUT, "screenshots", `I05_${id}.png`) });
      per.push({ case_id: id, ...s, toast: toast.slice(0, 400), not_supported_text: /chưa (được )?hỗ trợ|ngoài phạm vi/i.test(toast),
        question_surfaced: /bạn hãy|bổ sung|viết rõ|\?/i.test(toast) });
      await ctx.close();
    }
    const p = per[0];
    rec("I05", p.surface === "TOAST" && !p.not_supported_text && p.question_surfaced, { registered: p, learner_text_by_case: per });
  }
  if (want("I06")) {   // backend started with a short deadline: the classified timeout must not be retried
    const { ctx, page } = await session(browser);
    const t0 = Date.now();
    const s = await submit(page, SLM);
    const shown = Date.now() - t0;
    await page.waitForTimeout(8000);   // a retry would show up here
    const toast = await page.locator(".axo-composer-toast").first().innerText().catch(() => "");
    rec("I06", page.__analyze.length === 1 && s.http === 504 && shown < 30000, { case_id: SLM, ...s, analyze_calls: page.__analyze.length, ms_to_message: shown, toast: toast.slice(0, 300) });
    await ctx.close();
  }
  if (want("I07")) {   // cancel a slow (SLM) request, submit a fast one; the late first response must never replace it
    const { ctx, page } = await session(browser);
    const slow = await submit(page, SLM, { wait: false });
    await page.waitForTimeout(800);
    const cancel = page.locator("#btn-composer-cancel");
    const hadCancel = await cancel.count() > 0;
    if (hadCancel) await cancel.first().click();
    await slow.pending.catch(() => null);
    const f = await submit(page, FAST);
    const ids0 = await labelIds(page);
    await page.waitForTimeout(15000);   // longer than the SLM path, so a stale write would have landed
    const ids1 = await labelIds(page);
    rec("I07", hadCancel && f.surface === "SCENE" && JSON.stringify(ids0) === JSON.stringify(goldIds(FAST)) && JSON.stringify(ids1) === JSON.stringify(ids0),
      { slow: SLM, fast: FAST, cancel_button: hadCancel, fast_surface: f.surface, labels_at_render: ids0, labels_after_15s: ids1, gold: goldIds(FAST), console_errors: page.__errors });
    await ctx.close();
  }
  if (want("I08")) {
    for (const [w, h] of [[1920, 1080], [1366, 768], [768, 1024], [390, 844]]) {
      const { ctx, page } = await session(browser, w, h);
      const composer = await page.locator(".composer-text").isVisible();
      const s = await submit(page, FAST);
      const m = await page.evaluate(() => {
        const c = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect();
        return { canvas: c && { w: Math.round(c.width), h: Math.round(c.height) }, overflow_x: document.documentElement.scrollWidth > innerWidth + 1,
          labels_inside: [...document.querySelectorAll(".geo3d-label")].every((e) => { const r = e.getBoundingClientRect(); return !c || (r.x >= c.x - 2 && r.right <= c.right + 2 && r.y >= c.y - 2 && r.bottom <= c.bottom + 2); }) };
      });
      const d = s.surface === "SCENE" ? await drag(page, await centre(page)) : null;
      const file = join("screenshots", `I08_${w}x${h}.png`); await page.screenshot({ path: join(OUT, file) });
      const share = m.canvas ? +(m.canvas.w * m.canvas.h / (w * h)).toFixed(3) : 0;
      rec(`I08_${w}x${h}`, composer && s.surface === "SCENE" && !m.overflow_x && m.labels_inside && share >= 0.3 && d?.rotated,
        { composer_visible: composer, ...m, canvas_viewport_share: share, centre_drag_rotated: d?.rotated, screenshot: file });
      await ctx.close();
    }
  }
} finally {
  writeFileSync(OUTF, JSON.stringify({ schema: "axo-v11-ui-scenarios/1", browser: browser.version(), base: BASE, tag: TAG, results }, null, 1));
  await browser.close();
}
