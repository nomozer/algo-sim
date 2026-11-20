import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { inflateSync } from "node:zlib";
import { HARNESS_VERSION, freshOutDir, loadPlaywright, parseArgs, required } from "./harness_paths.mjs";

const { chromium } = loadPlaywright();

// Inputs: the frozen manifest and the browser checks of the SAME run (read-only). Output: a fresh `--out-dir`
// holding ui_scenarios.json + screenshots/.
const ARGS = parseArgs(process.argv.slice(2), ["base", "manifest", "browser-checks", "out-dir"]);
const BASE = ARGS.values.base || "http://127.0.0.1:4173";
const MANIFEST_PATH = required(ARGS.values, "manifest");
const BROWSER_CHECKS_PATH = required(ARGS.values, "browser-checks");
const OUT_DIR = freshOutDir(ARGS.values["out-dir"]);
const OUT_SCENARIOS = join(OUT_DIR, "ui_scenarios.json");
const SHOT_DIR = join(OUT_DIR, "screenshots");

function normLabel(s) {
  return String(s || "").trim().replace(/[′’`]/g, "'");
}

function pngPixels(buf) {
  if (!buf || buf.length < 33 || buf.readUInt32BE(0) !== 0x89504e47) return null;
  let pos = 8, w = 0, h = 0, bitDepth = 0, colorType = 0;
  const idat = [];
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.subarray(pos + 4, pos + 8).toString("ascii");
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") { w = data.readUInt32BE(0); h = data.readUInt32BE(4); bitDepth = data[8]; colorType = data[9]; }
    else if (type === "IDAT") idat.push(data);
    else if (type === "IEND") break;
    pos += 12 + len;
  }
  if (!w || !h || bitDepth !== 8 || (colorType !== 2 && colorType !== 6)) return null;
  const bpp = colorType === 6 ? 4 : 3;
  const stride = w * bpp;
  const raw = inflateSync(Buffer.concat(idat));
  const recon = Buffer.alloc(h * stride);
  const paeth = (a, b, c) => {
    const p = a + b - c;
    const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
    return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
  };
  let src = 0;
  for (let y = 0; y < h; y++) {
    const f = raw[src++];
    const rowOff = y * stride;
    for (let x = 0; x < stride; x++) {
      const cur = raw[src++];
      const a = x >= bpp ? recon[rowOff + x - bpp] : 0;
      const b = y > 0 ? recon[rowOff - stride + x] : 0;
      const c = x >= bpp && y > 0 ? recon[rowOff - stride + x - bpp] : 0;
      let val = cur;
      if (f === 1) val = (cur + a) & 0xff;
      else if (f === 2) val = (cur + b) & 0xff;
      else if (f === 3) val = (cur + ((a + b) >> 1)) & 0xff;
      else if (f === 4) val = (cur + paeth(a, b, c)) & 0xff;
      recon[rowOff + x] = val;
    }
  }
  return { w, h, bpp, recon };
}

function pngDiff(b1, b2) {
  const p1 = pngPixels(b1), p2 = pngPixels(b2);
  if (!p1 || !p2 || p1.recon.length !== p2.recon.length) return 0;
  let changed = 0;
  const total = p1.w * p1.h;
  for (let i = 0; i < total; i++) {
    const o = i * p1.bpp;
    if (
      Math.abs(p1.recon[o] - p2.recon[o]) +
      Math.abs(p1.recon[o + 1] - p2.recon[o + 1]) +
      Math.abs(p1.recon[o + 2] - p2.recon[o + 2]) > 15
    ) changed++;
  }
  return +(changed / total).toFixed(5);
}

async function openSession(browser, idx, w = 1366, h = 860, externalRequests = []) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  page.__errors = [];
  page.__analyze = [];
  page.on("pageerror", (e) => page.__errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") page.__errors.push(`console.error: ${m.text()}`); });
  page.on("request", (req) => {
    const u = req.url();
    if (!u.startsWith("http://127.0.0.1") && !u.startsWith("http://localhost") && !u.startsWith("data:") && !u.startsWith("blob:") && u !== "about:blank") {
      externalRequests.push({ idx, url: u });
    }
    if (u.includes("/api/analyze") && req.method() === "POST") page.__analyze.push(Date.now());
  });
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 30000 });
  const email = `ui_${idx}_${Date.now()}@algosim.test`;
  await page.evaluate(async ({ email }) => {
    await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, displayName: "UI Tester", password: ["Axo", "Eval", "Pass!", "2026"].join("") }),
    });
  }, { email });
  await page.reload({ waitUntil: "domcontentloaded", timeout: 30000 });
  await page.locator(".composer-text").first().waitFor({ state: "visible", timeout: 15000 });
  return { ctx, page };
}

async function ensureComposer(page) {
  const comp = page.locator(".composer-text").first();
  if (await comp.isVisible().catch(() => false)) return;
  const nav = page.locator("#nav-home").first();
  if (await nav.isVisible().catch(() => false)) {
    await nav.click();
    if (await comp.waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false)) return;
  }
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 30000 });
  await comp.waitFor({ state: "visible", timeout: 15000 });
}

async function submitPrompt(page, text, { wait = true } = {}) {
  await ensureComposer(page);
  const p = page.waitForResponse((r) => r.url().includes("/api/analyze") && r.request().method() === "POST", { timeout: 180000 });
  await page.locator(".composer-text").first().fill(text);
  await page.locator("#btn-composer-send").first().click();
  if (!wait) return { pending: p };
  const r = await p;
  const http = r.status();
  const body = await r.json().catch(() => null);
  const status = body?.route_d?.status || null;
  if (status === "SERVED") {
    await page.locator(".geo3d-canvas canvas").first().waitFor({ state: "visible", timeout: 15000 }).catch(() => null);
    const fullBtn = page.getByRole("button", { name: "Xem mô hình đầy đủ" });
    if (await fullBtn.isVisible().catch(() => false)) await fullBtn.click();
    await page.waitForTimeout(550);
    return { surface: "SCENE", http, body };
  }
  await page.waitForTimeout(500);
  return { surface: "TOAST", http, body };
}

async function labelPos(page) {
  return page.evaluate(() => {
    const out = {};
    for (const el of document.querySelectorAll(".geo3d-label")) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        const k = String(el.textContent || "").trim().replace(/[′’`]/g, "'");
        out[k] = [+(r.left + r.width / 2).toFixed(1), +(r.top + r.height / 2).toFixed(1)];
      }
    }
    return out;
  });
}

function maxDrift(a, b) {
  let m = 0;
  for (const k of Object.keys(a)) {
    if (b[k]) m = Math.max(m, Math.hypot(a[k][0] - b[k][0], a[k][1] - b[k][1]));
  }
  return +m.toFixed(2);
}

async function dragAt(page, pt) {
  const calls = page.__analyze.length;
  const s0 = await page.locator(".geo3d-canvas canvas").first().screenshot();
  const l0 = await labelPos(page);
  const under = await page.evaluate(({ x, y }) => {
    const e = document.elementFromPoint(x, y);
    return e ? { tag: e.tagName, cls: String(e.className || "").slice(0, 60) } : null;
  }, pt);
  await page.mouse.move(pt.x, pt.y);
  await page.mouse.down();
  await page.mouse.move(pt.x + 125, pt.y + 48, { steps: 8 });
  await page.mouse.up();
  await page.waitForTimeout(260);
  const s1 = await page.locator(".geo3d-canvas canvas").first().screenshot();
  const l1 = await labelPos(page);
  const moved = Object.keys(l0).filter((k) => l1[k] && Math.hypot(l1[k][0] - l0[k][0], l1[k][1] - l0[k][1]) > 2).length;
  const diff = pngDiff(s0, s1);
  return {
    start: { x: Math.round(pt.x), y: Math.round(pt.y) },
    under,
    frame_pixel_diff: diff,
    labels_moved: moved,
    rotated: diff > 0.0015 && moved > 0 && page.__analyze.length === calls,
  };
}

async function main() {
  const manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf-8"));
  const checks = JSON.parse(readFileSync(BROWSER_CHECKS_PATH, "utf-8"));
  const validById = Object.fromEntries(manifest.valid_cases.map((c) => [c.case_id, c]));
  const servedChecks = checks.results.filter((r) => r.route_status === "SERVED" && validById[r.case_id]);

  // Pick representative served cases dynamically (strictly from completed run):
  const sampleIds = [
    servedChecks[0]?.case_id,
    servedChecks[Math.floor(servedChecks.length / 2)]?.case_id,
    servedChecks.find((r) => r.extraction_mode && r.extraction_mode.startsWith("LOCAL_SLM"))?.case_id || servedChecks[servedChecks.length - 1]?.case_id,
  ].filter(Boolean);
  const fastCase = [...servedChecks].sort((a, b) => a.ms - b.ms)[0];
  const slowCase = [...servedChecks].sort((a, b) => b.ms - a.ms)[0];
  const clarifyCandidate =
    checks.results.find((r) => r.route_status !== "SERVED" && (r.reason_code === "AMBIGUOUS_FACT" || r.reason_code === "FACT_INCOMPLETE")) ||
    manifest.valid_cases.find((c) => c.expected_behavior !== "SERVE") ||
    manifest.negative_cases[0];
  const clarifyText = clarifyCandidate.original_input || validById[clarifyCandidate.case_id]?.original_input;

  const browser = await chromium.launch({ headless: true });
  const externalRequests = [];
  const results = [];
  let sid = 0;

  try {
    // I01: Orbit from center across 3 distinct served scenes
    {
      const { ctx, page } = await openSession(browser, ++sid, 1366, 860, externalRequests);
      const per = [];
      for (const cid of sampleIds) {
        const c = validById[cid];
        const s = await submitPrompt(page, c.original_input);
        const centre = await page.evaluate(() => {
          const r = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect();
          return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
        });
        const d = s.surface === "SCENE" ? await dragAt(page, centre) : null;
        per.push({ case_id: cid, surface: s.surface, ...(d || {}) });
      }
      results.push({ scenario_id: "I01", pass: per.length >= 2 && per.every((x) => x.rotated) && page.__errors.length === 0, scenes: per, console_errors: page.__errors });
      await ctx.close();
    }

    // I02, I03, I04: drag from edge/chip/label, double-reset convergence, problem switch without stale scene
    if (sampleIds.length >= 2) {
      const { ctx, page } = await openSession(browser, ++sid, 1366, 860, externalRequests);
      const c0 = validById[sampleIds[0]];
      const c1 = validById[sampleIds[1]];
      await submitPrompt(page, c0.original_input);

      // I02: drag from edge midpoint, chip (if present), near label
      const pts = await page.evaluate(() => {
        const c = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect();
        const L = [...document.querySelectorAll(".geo3d-label")].map((e) => e.getBoundingClientRect()).filter((r) => r.width > 0);
        const chip = [...document.querySelectorAll(".geo3d-so-do, [data-ann-id]")].map((e) => e.getBoundingClientRect()).find((r) => r.width > 0);
        const a = L[0], b = L[1];
        return {
          edge: a && b ? { x: (a.left + a.width / 2 + b.left + b.width / 2) / 2, y: (a.top + a.height / 2 + b.top + b.height / 2) / 2 } : null,
          chip: chip ? { x: chip.left + chip.width / 2, y: chip.top + chip.height / 2 } : null,
          near_label: a ? { x: Math.min(c.right - 6, a.right + 12), y: a.top + a.height / 2 } : null,
        };
      });
      const i02 = {};
      for (const [k, pt] of Object.entries(pts)) i02[k] = pt ? await dragAt(page, pt) : { absent: true };
      results.push({ scenario_id: "I02", pass: Boolean(i02.edge?.rotated && (i02.chip?.absent || i02.chip?.rotated) && (i02.near_label?.absent || i02.near_label?.rotated)), scene: c0.case_id, ...i02 });

      // I04: double reset label stability
      const resetBtn = page.locator('button[aria-label="Đặt lại góc nhìn 3D"]').first();
      await resetBtn.click(); await page.waitForTimeout(800);
      const lFirst = await labelPos(page);
      await resetBtn.click(); await page.waitForTimeout(800);
      const lSecond = await labelPos(page);
      const driftPx = maxDrift(lFirst, lSecond);
      results.push({ scenario_id: "I04", pass: driftPx <= 2.0, scene: c0.case_id, double_reset_max_drift_px: driftPx });

      // I03: reset orbit + switch to second problem cleanly
      const centre = await page.evaluate(() => { const r = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
      const afterReset = await dragAt(page, centre);
      const s2 = await submitPrompt(page, c1.original_input);
      const labels2 = Object.keys(await labelPos(page)).sort();
      const gold2 = (c1.gold_entities?.solid_vertices || []).map(normLabel).sort();
      const missing2 = gold2.filter((g) => !labels2.includes(g));
      const centre2 = await page.evaluate(() => { const r = document.querySelector(".geo3d-canvas canvas").getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
      const afterChange = s2.surface === "SCENE" ? await dragAt(page, centre2) : { rotated: false };
      results.push({ scenario_id: "I03", pass: afterReset.rotated && s2.surface === "SCENE" && afterChange.rotated && missing2.length === 0, after_reset: afterReset, after_change: afterChange, missing_gold_after_change: missing2 });
      await ctx.close();
    }

    // I05: Clarification / underdetermined toast surfacing cleanly
    if (clarifyText) {
      const { ctx, page } = await openSession(browser, ++sid, 1366, 860, externalRequests);
      const s = await submitPrompt(page, clarifyText);
      const toast = await page.locator(".axo-composer-toast").first().innerText().catch(() => "");
      const hasCanvas = (await page.locator(".geo3d-canvas canvas").count()) > 0;
      const notSupportedWording = /chưa (được )?hỗ trợ|ngoài phạm vi/i.test(toast);
      await page.screenshot({ path: join(SHOT_DIR, `UI_I05_${clarifyCandidate.case_id}.png`) }).catch(() => null);
      results.push({
        scenario_id: "I05",
        pass: s.surface === "TOAST" && !hasCanvas && toast.length > 0 && !notSupportedWording,
        case_id: clarifyCandidate.case_id,
        reason_code: s.body?.route_d?.reason_code || null,
        toast: toast.slice(0, 400),
        console_errors: page.__errors,
      });
      await ctx.close();
    }

    // I07: Cancel slow request then submit fast request -> fast scene preserved after delay
    if (slowCase && fastCase && slowCase.case_id !== fastCase.case_id) {
      const slowText = (validById[slowCase.case_id] || {}).original_input;
      const fastText = (validById[fastCase.case_id] || {}).original_input;
      if (slowText && fastText) {
        const { ctx, page } = await openSession(browser, ++sid, 1366, 860, externalRequests);
        const slow = await submitPrompt(page, slowText, { wait: false });
        const cancelBtn = page.locator("#btn-composer-cancel").first();
        const hadCancel = await cancelBtn.waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false);
        if (hadCancel) await cancelBtn.click();
        await slow.pending.catch(() => null);
        const f = await submitPrompt(page, fastText);
        const ids0 = Object.keys(await labelPos(page)).sort();
        await page.waitForTimeout(4000);
        const ids1 = Object.keys(await labelPos(page)).sort();
        const goldF = (validById[fastCase.case_id].gold_entities?.solid_vertices || []).map(normLabel).sort();
        results.push({
          scenario_id: "I07",
          pass: f.surface === "SCENE" && JSON.stringify(ids0) === JSON.stringify(ids1) && goldF.every((g) => ids1.includes(g)) && page.__errors.length === 0,
          had_cancel_button: hadCancel,
          slow_case: slowCase.case_id,
          fast_case: fastCase.case_id,
          labels_at_render: ids0,
          labels_after_wait: ids1,
          console_errors: page.__errors,
        });
        await ctx.close();
      }
    }

    // I08: Responsive viewports initial framing BEFORE orbit/reset + drag orbit across all 4 viewports
    if (sampleIds.length > 0) {
      const vpCase = validById[sampleIds[sampleIds.length - 1]];
      for (const [w, h] of [[1920, 1080], [1366, 768], [768, 1024], [390, 844]]) {
        const { ctx, page } = await openSession(browser, ++sid, w, h, externalRequests);
        const s = await submitPrompt(page, vpCase.original_input);
        const metrics = await page.evaluate((gold) => {
          const c = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect();
          const norm = (x) => String(x || "").trim().replace(/[′’`]/g, "'");
          const labels = [...document.querySelectorAll(".geo3d-label")]
            .map((el) => ({ t: norm(el.textContent), r: el.getBoundingClientRect() }))
            .filter((x) => x.r.width > 0 && x.r.height > 0);
          const outside = c
            ? labels.filter((l) => l.r.left < c.left - 1 || l.r.right > c.right + 1 || l.r.top < c.top - 1 || l.r.bottom > c.bottom + 1).map((l) => l.t)
            : ["NO_CANVAS"];
          const seen = new Set(labels.map((l) => l.t));
          const missing = (gold || []).map(norm).filter((g) => !seen.has(g));
          return {
            overflow_x: document.documentElement.scrollWidth > window.innerWidth + 1,
            canvas: c ? { w: Math.round(c.width), h: Math.round(c.height) } : null,
            outside_initial_labels: outside,
            missing_gold_labels: missing,
          };
        }, vpCase.gold_entities?.solid_vertices || []);
        const centre = await page.evaluate(() => { const r = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect(); return r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : null; });
        const d = s.surface === "SCENE" && centre ? await dragAt(page, centre) : null;
        await page.screenshot({ path: join(SHOT_DIR, `UI_I08_${w}x${h}_${vpCase.case_id}.png`) }).catch(() => null);
        const share = metrics.canvas ? +(metrics.canvas.w * metrics.canvas.h / (w * h)).toFixed(3) : 0;
        results.push({
          scenario_id: `I08_${w}x${h}`,
          pass:
            s.surface === "SCENE" &&
            !metrics.overflow_x &&
            metrics.outside_initial_labels.length === 0 &&
            metrics.missing_gold_labels.length === 0 &&
            share >= 0.25 &&
            Boolean(d?.rotated) &&
            page.__errors.length === 0,
          case_id: vpCase.case_id,
          ...metrics,
          canvas_viewport_share: share,
          centre_drag_rotated: d?.rotated || false,
          console_errors: page.__errors,
        });
        await ctx.close();
      }
    }
  } finally {
    await browser.close();
  }

  writeFileSync(
    OUT_SCENARIOS,
    JSON.stringify(
      {
        schema: "axo-ui-scenarios/1",
        harness_version: HARNESS_VERSION,
        base: BASE,
        external_requests_count: externalRequests.length,
        external_requests: externalRequests,
        total_scenarios: results.length,
        passed_scenarios: results.filter((r) => r.pass).length,
        results,
      },
      null,
      2
    ) + "\n",
    "utf-8"
  );
  console.log(JSON.stringify({ total: results.length, passed: results.filter((r) => r.pass).length, external_requests: externalRequests.length }));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
