/**
 * UI scenarios U01–U10, U16 on the real app (vite preview of dist + live local-only backend). In-app navigation only
 * ("Đổi đề toán"), so stale-scene leakage between problems is observable. Problems come from the frozen manifest.
 * usage: node ui_runtime_scenarios.mjs --manifest <json> --out <dir> [--base http://127.0.0.1:4173]
 */
import { createRequire } from "node:module";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const FE = resolve(join(import.meta.dirname, "../../../../../../frontend"));
const { chromium } = createRequire(join(FE, "package.json"))("playwright");
const BASE = arg("base", "http://127.0.0.1:4173");
const OUT = resolve(arg("out"));
const man = JSON.parse(readFileSync(arg("manifest"), "utf8"));
const byId = Object.fromEntries([...man.valid_cases, ...man.negative_cases].map((c) => [c.case_id, c]));
mkdirSync(join(OUT, "screenshots"), { recursive: true });
const OUTF = join(OUT, "ui_scenarios.json");
if (existsSync(OUTF)) throw new Error(`refusing to overwrite ${OUTF}`);
const sha = (b) => createHash("sha256").update(b).digest("hex");
const results = [];
const rec = (id, ok, detail) => { results.push({ scenario_id: id, pass: ok, ...detail }); console.log(id, ok ? "PASS" : "FAIL", JSON.stringify(detail).slice(0, 240)); };

const labelIds = (page) => page.evaluate(() => [...document.querySelectorAll(".geo3d-label")]
  .filter((e) => e.checkVisibility({ opacityProperty: true, visibilityProperty: true })).map((e) => e.dataset.id).sort());
const { docPNG } = await import(new URL(`file:///${join(FE, "scripts/png-pixels.mjs").replace(/\\/g, "/")}`).href);
/** fraction of canvas pixels that differ (> 24 summed RGB) between two PNG screenshots — robust to sub-pixel AA */
function pixelDiff(a, b) {
  const A = docPNG(a), B = docPNG(b);
  if (A.w !== B.w || A.h !== B.h) return 1;
  let d = 0;
  for (let i = 0; i < A.w * A.h * 4; i += 4) if (Math.abs(A.rgba[i] - B.rgba[i]) + Math.abs(A.rgba[i + 1] - B.rgba[i + 1]) + Math.abs(A.rgba[i + 2] - B.rgba[i + 2]) > 24) d++;
  return +(d / (A.w * A.h)).toFixed(5);
}
const rawShot = async (page) => { await page.mouse.move(2, 2); await page.waitForTimeout(200); return page.locator(".geo3d-canvas canvas").first().screenshot(); };
const labelPos = (page) => page.evaluate(() => Object.fromEntries([...document.querySelectorAll(".geo3d-label")]
  .map((e) => { const r = e.getBoundingClientRect(); return [e.dataset.id, [Math.round(r.x), Math.round(r.y)]]; })));

async function session(browser, vw = 1366, vh = 768) {
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh } });
  const tag = `${Date.now()}${Math.random().toString(16).slice(2, 6)}`;
  const r = await ctx.request.post(`${BASE}/api/auth/register`, { data: { email: `ui-${tag}@example.com`, displayName: `UI ${tag}`, password: "LiveAcceptance!2026" } });
  if (!r.ok()) throw new Error(`register ${r.status()}`);
  const page = await ctx.newPage();
  page.__errors = []; page.__analyze = 0;
  page.on("console", (m) => { if (m.type() === "error") page.__errors.push(m.text().slice(0, 200)); });
  page.on("pageerror", (e) => page.__errors.push(String(e).slice(0, 200)));
  page.on("request", (q) => { if (q.url().includes("/api/analyze")) page.__analyze += 1; });
  await page.goto(BASE, { waitUntil: "networkidle" });
  return { ctx, page };
}

async function submit(page, id) {
  const box = page.locator(".composer-text");
  await box.waitFor({ state: "visible", timeout: 15000 });
  await box.fill(byId[id].original_input);
  const resp = page.waitForResponse((r) => r.url().includes("/api/analyze") && r.request().method() === "POST", { timeout: 150000 });
  await page.locator("#btn-composer-send").click();
  const r = await resp; const body = await r.json().catch(() => ({}));
  const surface = await Promise.race([
    page.locator(".geo3d-canvas canvas").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "SCENE"),
    page.locator(".axo-composer-toast").first().waitFor({ state: "visible", timeout: 30000 }).then(() => "TOAST"),
  ]).catch(() => "NONE");
  if (surface === "SCENE") {
    const full = page.getByRole("button", { name: "Xem mô hình đầy đủ" });
    if (await full.count()) await full.first().click();
    await page.waitForTimeout(400);
  }
  return { http: r.status(), route: body.route_d?.status ?? null, surface };
}

async function backToComposer(page) {
  const b = page.getByRole("button", { name: "Đổi đề toán" });
  if (await b.count()) { await b.first().click(); } else { await page.locator(".geo3d-quay-lai").first().click(); }
  await page.locator(".composer-text").waitFor({ state: "visible", timeout: 10000 });
}

const goldIds = (id) => [...byId[id].gold_entities.solid_vertices, ...byId[id].gold_entities.auxiliary_points].map((t) => t.replace("'", "_prime")).sort();
const canvasShot = async (page) => sha(await page.locator(".geo3d-canvas canvas").first().screenshot());
async function emptyPoint(page) {  // a canvas point far from any label / chip, for a real orbit start
  return page.evaluate(() => {
    const c = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect();
    const blocks = [...document.querySelectorAll(".geo3d-canvas *")].filter((e) => e.tagName !== "CANVAS" && getComputedStyle(e).pointerEvents !== "none")
      .map((e) => e.getBoundingClientRect()).filter((r) => r.width > 0);
    for (const fx of [0.15, 0.85, 0.5, 0.3, 0.7]) for (const fy of [0.2, 0.8, 0.5]) {
      const x = c.x + c.width * fx, y = c.y + c.height * fy;
      if (!blocks.some((r) => x >= r.x - 8 && x <= r.right + 8 && y >= r.y - 8 && y <= r.bottom + 8)
          && document.elementFromPoint(x, y)?.tagName === "CANVAS") return { x, y };
    }
    return { x: c.x + 20, y: c.y + 20 };
  });
}

const browser = await chromium.launch();
try {
  // U01 readiness, keyless
  {
    const { ctx, page } = await session(browser);
    const h = await (await page.request.get(`${BASE}/api/health`)).json();
    const txt = await page.evaluate(() => document.body.innerText + [...document.querySelectorAll(".composer-sr-only")].map((e) => e.textContent).join(" "));
    rec("U01", h.aiAvailable === true && h.hasKey === false && h.localOnlyMode === true && !/khóa AI|API key|Gemini/i.test(txt),
      { hasKey: h.hasKey, aiAvailable: h.aiAvailable, localOnlyMode: h.localOnlyMode, localSlmReady: h.localSlmReady, ux_state: h.local_ai_ux?.ux_state, cloud_key_text: /khóa AI|API key|Gemini/i.test(txt) });

    // U02 consecutive inputs: pyramid quad -> tetrahedron OABC (different vertex sets), in-app
    const a = await submit(page, "V03"); const la = await labelIds(page);
    await backToComposer(page);
    const b = await submit(page, "V07"); const lb = await labelIds(page);
    await page.screenshot({ path: join(OUT, "screenshots", "U02_second_scene.png") });
    rec("U02", a.surface === "SCENE" && b.surface === "SCENE" && JSON.stringify(la) === JSON.stringify(goldIds("V03")) && JSON.stringify(lb) === JSON.stringify(goldIds("V07")),
      { first: la, second: lb, gold_second: goldIds("V07") });

    // U05 orbit from an empty canvas point (V17 scene, whose centre holds a measurement chip) + chip-start control
    await backToComposer(page);
    await submit(page, "V17");
    const callsBefore = page.__analyze;
    const p = await emptyPoint(page); const s0 = await canvasShot(page); const pos0 = await labelPos(page);
    await page.mouse.move(p.x, p.y); await page.mouse.down(); await page.mouse.move(p.x + 150, p.y + 40, { steps: 8 }); await page.mouse.up(); await page.waitForTimeout(250);
    const s1 = await canvasShot(page); const pos1 = await labelPos(page);
    const moved = Object.keys(pos0).filter((k) => pos1[k] && Math.abs(pos1[k][0] - pos0[k][0]) + Math.abs(pos1[k][1] - pos0[k][1]) > 3).length;
    const chip = await page.evaluate(() => { const e = [...document.querySelectorAll(".geo3d-canvas *")].find((x) => /AB = 2a/.test(x.textContent || "") && x.children.length === 0);
      if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2, cls: e.className, pe: getComputedStyle(e).pointerEvents }; });
    let chipStart = null;
    if (chip) { const c0 = await canvasShot(page); await page.mouse.move(chip.x, chip.y); await page.mouse.down(); await page.mouse.move(chip.x + 150, chip.y + 40, { steps: 8 }); await page.mouse.up(); await page.waitForTimeout(250);
      chipStart = { ...chip, frame_changed: c0 !== await canvasShot(page) }; }
    rec("U05", s0 !== s1 && moved > 0 && JSON.stringify(Object.keys(pos0).sort()) === JSON.stringify(Object.keys(pos1).sort()) && page.__analyze === callsBefore,
      { start: p, frame_changed: s0 !== s1, labels_moved: moved, analyze_calls: page.__analyze - callsBefore, drag_started_on_measurement_chip: chipStart });

    // U06 zoom
    const z0 = await canvasShot(page); await page.mouse.move(p.x, p.y); await page.mouse.wheel(0, -400); await page.waitForTimeout(300);
    const z1 = await canvasShot(page); await page.mouse.wheel(0, 400); await page.waitForTimeout(300);
    rec("U06", z0 !== z1, { frame_changed: z0 !== z1 });

    // U07 steps
    const prog = page.locator(".geo3d-progress").first();
    const st0 = (await prog.textContent()).trim();
    await page.locator('button[aria-label="Bước trước"]').first().click(); await page.waitForTimeout(200); const st1 = (await prog.textContent()).trim();
    await page.locator('button[aria-label="Bước sau"]').first().click(); await page.waitForTimeout(200); const st2 = (await prog.textContent()).trim();
    rec("U07", st0 !== st1 && st2 === st0, { start: st0, after_prev: st1, after_next: st2 });

    // U08 reset view: the rotated frame (U05/U06) must come back to the default camera
    const reset = page.locator('button[aria-label="Đặt lại góc nhìn 3D"]').first();
    const resetInfo = { exposed: await reset.count() > 0 };
    if (resetInfo.exposed) {
      const r0 = await rawShot(page); await reset.click(); await page.waitForTimeout(1800); const r1 = await rawShot(page); const p1 = await labelPos(page);
      await reset.click(); await page.waitForTimeout(1800); const r2 = await rawShot(page); const p2 = await labelPos(page);
      const drift = Math.max(0, ...Object.keys(p1).map((k) => p2[k] ? Math.abs(p2[k][0] - p1[k][0]) + Math.abs(p2[k][1] - p1[k][1]) : 999));
      Object.assign(resetInfo, { change_vs_rotated: pixelDiff(r0, r1), second_reset_pixel_diff: pixelDiff(r1, r2), second_reset_label_drift_px: drift });
    }
    rec("U08", resetInfo.exposed && resetInfo.change_vs_rotated > 0.01 && resetInfo.second_reset_label_drift_px <= 2, resetInfo);

    // U09 display toggles: X-ray button changes the frame and back; the display-options menu is inventoried
    const xray = page.locator('button[aria-label="Chế độ X-ray (nhìn xuyên khối)"]').first();
    const X0 = await rawShot(page); await xray.click(); await page.waitForTimeout(1500); const X1 = await rawShot(page);
    await xray.click(); await page.waitForTimeout(1500); const X2 = await rawShot(page);
    const xrayOn = pixelDiff(X0, X1), xrayBack = pixelDiff(X0, X2);
    const [x0, x1, x2] = [0, xrayOn > 0.001 ? 1 : 0, xrayBack <= 0.002 ? 0 : 2];  // frame-equality by pixel fraction
    await page.locator('button[aria-label="Tùy chọn hiển thị"]').first().click(); await page.waitForTimeout(300);
    const options = await page.evaluate(() => [...document.querySelectorAll("[role^=menuitem],[role=checkbox],label")]
      .filter((e) => e.getBoundingClientRect().width > 0).map((e) => (e.textContent || "").trim()).filter(Boolean).slice(0, 20));
    const labelToggle = options.some((o) => /^nhãn$/i.test(o));
    let labelsToggled = null;
    if (labelToggle) {  // "Nhãn" off hides the vertex labels, on brings the same set back
      const item = () => page.locator("label, [role^=menuitem], [role=checkbox]", { hasText: /^Nhãn$/ }).first();
      const before = await labelIds(page);
      await item().click(); await page.waitForTimeout(400); const off = await labelIds(page);
      await item().click(); await page.waitForTimeout(400); const on = await labelIds(page);
      labelsToggled = { before, off, on, hides: off.length < before.length, restores: JSON.stringify(on) === JSON.stringify(before) };
    }
    await page.keyboard.press("Escape").catch(() => {});
    rec("U09", x0 !== x1 && x2 === x0 && (!labelsToggled || (labelsToggled.hides && labelsToggled.restores)),
      { xray_changes_frame: x0 !== x1, xray_restores_frame: x2 === x0, xray_on_pixel_diff: xrayOn, xray_off_vs_before_pixel_diff: xrayBack, display_options: options,
        label_toggle: labelToggle ? "PRESENT" : "NOT_IN_PRODUCT", labels_toggled: labelsToggled });

    // U10 select an object via its entity chip -> its label is highlighted on the canvas
    const chipS = page.locator(".dock-entity-chip", { hasText: /^S$/ }).first();
    let sel = null;
    if (await chipS.count()) { await chipS.click(); await page.waitForTimeout(250); sel = await page.evaluate(() => document.querySelector('.geo3d-label[data-id="S"]')?.className); }
    rec("U10", !!sel && sel.includes("la-chon"), { selected_label_class: sel, ids_after: await labelIds(page) });

    // U03 served -> refusal: no canvas left behind
    await backToComposer(page);
    const n = await submit(page, "N03");
    const canvasLeft = await page.locator(".geo3d-canvas canvas").count();
    const toast = await page.locator(".axo-composer-toast").first().innerText().catch(() => null);
    await page.screenshot({ path: join(OUT, "screenshots", "U03_refusal_after_scene.png") });
    rec("U03", n.surface === "TOAST" && canvasLeft === 0, { route: n.route, canvas_left: canvasLeft, toast: toast?.slice(0, 200) });

    // U04 refusal -> served recovery
    const s = await submit(page, "C13"); const ls = await labelIds(page);
    rec("U04", s.surface === "SCENE" && JSON.stringify(ls) === JSON.stringify(goldIds("C13")), { labels: ls });
    rec("U00_console", page.__errors.length === 0, { console_errors: page.__errors });
    await ctx.close();
  }
  // U16 responsive
  for (const [w, h] of [[1920, 1080], [1366, 768], [768, 1024], [390, 844]]) {
    const { ctx, page } = await session(browser, w, h);
    const composer = await page.locator(".composer-text").isVisible();
    const s = await submit(page, "C09");
    const m = await page.evaluate(() => {
      const c = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect();
      return { canvas: c && { w: Math.round(c.width), h: Math.round(c.height), x: Math.round(c.x), y: Math.round(c.y) },
        overflow_x: document.documentElement.scrollWidth > innerWidth + 1,
        labels_inside: [...document.querySelectorAll(".geo3d-label")].every((e) => { const r = e.getBoundingClientRect(); return !c || (r.x >= c.x - 2 && r.right <= c.right + 2 && r.y >= c.y - 2 && r.bottom <= c.bottom + 2); }) };
    });
    const shot = join("screenshots", `U16_${w}x${h}.png`);
    await page.screenshot({ path: join(OUT, shot) });
    const share = m.canvas ? +(m.canvas.w * m.canvas.h / (w * h)).toFixed(3) : 0;
    rec(`U16_${w}x${h}`, composer && s.surface === "SCENE" && !m.overflow_x && m.labels_inside && share >= 0.3, { composer_visible: composer, ...m, canvas_viewport_share: share, screenshot: shot });
    await ctx.close();
  }
} finally {
  writeFileSync(OUTF, JSON.stringify({ schema: "axo-ui-scenarios/1", browser: browser.version(), base: BASE, results }, null, 1));
  await browser.close();
}
