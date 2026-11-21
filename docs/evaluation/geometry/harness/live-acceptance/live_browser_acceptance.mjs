import { createWriteStream, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { inflateSync } from "node:zlib";
import { HARNESS_VERSION, freshOutDir, loadPlaywright, parseArgs as parseHarnessArgs, required } from "./harness_paths.mjs";

const { chromium } = loadPlaywright();

// Inputs are read-only paths; every output goes into a fresh `--out-dir` (responses.jsonl, browser_checks.json,
// screenshots/). `--label` names the evaluator account (default "accept").
const ARGS = parseHarnessArgs(process.argv.slice(2), ["base", "manifest", "out-dir", "filter", "batch-size", "label"]);
const BASE = ARGS.values.base || "http://127.0.0.1:4173";
const MANIFEST_PATH = required(ARGS.values, "manifest");
const OUT_DIR = freshOutDir(ARGS.values["out-dir"]);
const LABEL = ARGS.values.label || "accept";
const OUT_JSONL = join(OUT_DIR, "responses.jsonl");
const OUT_CHECKS = join(OUT_DIR, "browser_checks.json");
const SHOT_DIR = join(OUT_DIR, "screenshots");

function parseArgs() {
  return { filter: ARGS.values.filter || "all", batchSize: Math.max(1, Number(ARGS.values["batch-size"]) || 10) };
}

function pngInkFraction(buf) {
  // Pure-Node PNG decoder for 8-bit RGB/RGBA buffers from locator.screenshot()
  if (!buf || buf.length < 33 || buf.readUInt32BE(0) !== 0x89504e47) return 0;
  let pos = 8;
  let w = 0, h = 0, bitDepth = 0, colorType = 0;
  const idat = [];
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.subarray(pos + 4, pos + 8).toString("ascii");
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (type === "IHDR") {
      w = data.readUInt32BE(0);
      h = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
    } else if (type === "IDAT") {
      idat.push(data);
    } else if (type === "IEND") {
      break;
    }
    pos += 12 + len;
  }
  if (!w || !h || bitDepth !== 8 || (colorType !== 2 && colorType !== 6)) return 0;
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
  const r0 = recon[0], g0 = recon[1], b0 = recon[2];
  let nonBg = 0;
  const total = w * h;
  for (let i = 0; i < total; i++) {
    const o = i * bpp;
    const diff = Math.abs(recon[o] - r0) + Math.abs(recon[o + 1] - g0) + Math.abs(recon[o + 2] - b0);
    if (diff > 15) nonBg++;
  }
  return +(nonBg / total).toFixed(5);
}

function isLocalUrl(u) {
  return (
    u.startsWith("http://127.0.0.1") ||
    u.startsWith("http://localhost") ||
    u.startsWith("data:") ||
    u.startsWith("blob:") ||
    u === "about:blank"
  );
}

function normLabel(s) {
  return String(s || "").trim().replace(/[′’`]/g, "'");
}

async function openAuthenticatedSession(browser, batchIdx, externalRequests) {
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 860 } });
  const page = await ctx.newPage();
  const errors = [];
  const analyzeEvents = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`console.error: ${msg.text()}`);
  });
  page.on("request", (req) => {
    const u = req.url();
    if (!isLocalUrl(u)) externalRequests.push({ batch: batchIdx, url: u, method: req.method() });
    if (u.includes("/api/analyze") && req.method() === "POST") analyzeEvents.push(Date.now());
  });

  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 30000 });
  const email = `${LABEL}_${batchIdx}_${Date.now()}@algosim.test`;
  const regRes = await page.evaluate(async ({ email }) => {
    const r = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        displayName: "Acceptance Evaluator",
        password: ["Axo", "Eval", "Pass!", "2026"].join(""),
      }),
    });
    return { status: r.status, text: await r.text() };
  }, { email });
  if (regRes.status >= 400) {
    throw new Error(`Auth register failed batch=${batchIdx}: ${regRes.status} ${regRes.text}`);
  }
  await page.reload({ waitUntil: "domcontentloaded", timeout: 30000 });
  await page.locator(".composer-text").waitFor({ state: "visible", timeout: 15000 });
  return { ctx, page, errors, analyzeEvents };
}

async function ensureComposer(page) {
  const composer = page.locator(".composer-text").first();
  if (await composer.isVisible().catch(() => false)) return;
  const homeBtn = page.locator("#nav-home").first();
  if (await homeBtn.isVisible().catch(() => false)) {
    await homeBtn.click();
    if (await composer.waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false)) return;
  }
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 30000 });
  await composer.waitFor({ state: "visible", timeout: 15000 });
}

async function measureInitialScene(page, goldVertices) {
  const metrics = await page.evaluate((gold) => {
    const canvas = document.querySelector(".geo3d-canvas canvas");
    if (!canvas) return { has_canvas: false };
    const cv = canvas.getBoundingClientRect();
    const norm = (s) => String(s || "").trim().replace(/[′’`]/g, "'");
    const labels = [...document.querySelectorAll(".geo3d-label")]
      .map((el) => {
        const r = el.getBoundingClientRect();
        return {
          text: norm(el.textContent),
          left: r.left,
          right: r.right,
          top: r.top,
          bottom: r.bottom,
          width: r.width,
          height: r.height,
        };
      })
      .filter((x) => x.width > 0 && x.height > 0);
    const outsideLabels = labels.filter(
      (r) => r.left < cv.left - 1 || r.right > cv.right + 1 || r.top < cv.top - 1 || r.bottom > cv.bottom + 1
    );
    const seenTexts = new Set(labels.map((l) => l.text));
    const missingGold = (gold || []).map(norm).filter((g) => !seenTexts.has(g));

    const snap = window.__geo3d_camera_snapshot || null;
    const markers = window.__geo3d_vertex_markers || [];
    const outsideNdc = [];
    if (snap && snap.view_matrix_column_major && snap.projection_matrix_column_major && markers.length > 0) {
      const mul4 = (m, v) => [
        m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12] * v[3],
        m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13] * v[3],
        m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14] * v[3],
        m[3] * v[0] + m[7] * v[1] + m[11] * v[2] + m[15] * v[3],
      ];
      for (const mk of markers) {
        if (!Array.isArray(mk.center) || mk.center.length < 3) continue;
        const viewPos = mul4(snap.view_matrix_column_major, [mk.center[0], mk.center[1], mk.center[2], 1]);
        const clip = mul4(snap.projection_matrix_column_major, viewPos);
        if (!clip[3] || Math.abs(clip[3]) < 1e-9) continue;
        const ndcX = clip[0] / clip[3];
        const ndcY = clip[1] / clip[3];
        const ndcZ = clip[2] / clip[3];
        if (Math.abs(ndcX) > 1.02 || Math.abs(ndcY) > 1.02 || Math.abs(ndcZ) > 1.02) {
          outsideNdc.push({ id: mk.id, ndc: [+ndcX.toFixed(3), +ndcY.toFixed(3), +ndcZ.toFixed(3)] });
        }
      }
    }

    return {
      has_canvas: true,
      canvas_rect: { w: Math.round(cv.width), h: Math.round(cv.height) },
      label_texts: labels.map((l) => l.text),
      label_positions: Object.fromEntries(labels.map((l) => [l.text, [Math.round(l.left), Math.round(l.top)]])),
      outside_initial_labels: outsideLabels.map((l) => l.text),
      missing_gold_labels: missingGold,
      vertex_marker_count: markers.length,
      outside_initial_ndc_vertices: outsideNdc,
      camera_position: snap ? snap.position : null,
      progress_text: document.querySelector(".geo3d-progress")?.textContent?.trim() || null,
    };
  }, goldVertices);

  let ink = 0;
  if (metrics.has_canvas) {
    const shotBuf = await page.locator(".geo3d-canvas canvas").first().screenshot();
    ink = pngInkFraction(shotBuf);
  }
  return { ...metrics, canvas_ink_fraction: ink };
}

async function exerciseInteractions(page, initialMetrics, analyzeEvents) {
  const beforeAnalyze = analyzeEvents.length;
  const cxInfo = await page.evaluate(() => {
    const c = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect();
    return c ? { x: c.left + c.width / 2, y: c.top + c.height / 2, w: c.width, h: c.height } : null;
  });
  if (!cxInfo) return { ok: false, reason: "no_canvas" };

  // 1. Orbit drag
  const cam0 = initialMetrics.camera_position;
  const pos0 = initialMetrics.label_positions;
  await page.mouse.move(cxInfo.x, cxInfo.y);
  await page.mouse.down();
  await page.mouse.move(cxInfo.x + 115, cxInfo.y + 45, { steps: 6 });
  await page.mouse.up();
  await page.waitForTimeout(260);
  const afterOrbit = await page.evaluate(() => {
    const snap = window.__geo3d_camera_snapshot || null;
    const norm = (s) => String(s || "").trim().replace(/[′’`]/g, "'");
    const pos = {};
    for (const el of document.querySelectorAll(".geo3d-label")) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) pos[norm(el.textContent)] = [Math.round(r.left), Math.round(r.top)];
    }
    return { cam: snap ? snap.position : null, pos };
  });
  let maxMove = 0;
  for (const [k, [x, y]] of Object.entries(pos0)) {
    if (afterOrbit.pos[k]) {
      maxMove = Math.max(maxMove, Math.hypot(afterOrbit.pos[k][0] - x, afterOrbit.pos[k][1] - y));
    }
  }
  const camDist =
    cam0 && afterOrbit.cam
      ? Math.hypot(afterOrbit.cam[0] - cam0[0], afterOrbit.cam[1] - cam0[1], afterOrbit.cam[2] - cam0[2])
      : 0;
  const orbitOk = maxMove > 2 || camDist > 0.05;

  // 2. Zoom wheel
  await page.mouse.move(cxInfo.x, cxInfo.y);
  await page.mouse.wheel(0, -180);
  await page.waitForTimeout(200);
  const afterZoomCam = await page.evaluate(() => window.__geo3d_camera_snapshot?.position || null);
  const zoomDist =
    afterOrbit.cam && afterZoomCam
      ? Math.hypot(
          afterZoomCam[0] - afterOrbit.cam[0],
          afterZoomCam[1] - afterOrbit.cam[1],
          afterZoomCam[2] - afterOrbit.cam[2]
        )
      : 0;
  const zoomOk = zoomDist > 0.01;

  // 3. Step prev / next
  let stepStatus = "not_applicable";
  const prevBtn = page.locator('button[aria-label="Bước trước"]').first();
  const nextBtn = page.locator('button[aria-label="Bước sau"]').first();
  if ((await prevBtn.count()) > 0 && (await prevBtn.isEnabled().catch(() => false))) {
    const pBefore = await page.locator(".geo3d-progress").first().textContent().catch(() => "");
    await prevBtn.click();
    await page.waitForTimeout(180);
    const pAfterPrev = await page.locator(".geo3d-progress").first().textContent().catch(() => "");
    if (await nextBtn.isEnabled().catch(() => false)) {
      await nextBtn.click();
      await page.waitForTimeout(180);
    }
    const fullBtn = page.getByRole("button", { name: "Xem mô hình đầy đủ" });
    if (await fullBtn.isVisible().catch(() => false)) {
      await fullBtn.click();
      await page.waitForTimeout(250);
    }
    stepStatus = pAfterPrev !== pBefore ? "ok" : "unchanged";
  }

  // 4. Reset camera
  let resetOk = false;
  let outsideAfterReset = [];
  const resetBtn = page.locator('button[aria-label="Đặt lại góc nhìn 3D"]').first();
  if ((await resetBtn.count()) > 0 && (await resetBtn.isVisible().catch(() => false))) {
    await resetBtn.click();
    await page.waitForTimeout(420);
    const resReset = await page.evaluate(() => {
      const c = document.querySelector(".geo3d-canvas canvas")?.getBoundingClientRect();
      const out = [];
      if (c) {
        for (const el of document.querySelectorAll(".geo3d-label")) {
          const r = el.getBoundingClientRect();
          if (r.width <= 0 || r.height <= 0) continue;
          if (r.left < c.left - 1 || r.right > c.right + 1 || r.top < c.top - 1 || r.bottom > c.bottom + 1) {
            out.push(el.textContent?.trim() || "");
          }
        }
      }
      return { out, cam: window.__geo3d_camera_snapshot?.position || null };
    });
    outsideAfterReset = resReset.out;
    resetOk = outsideAfterReset.length === 0 && resReset.cam !== null;
  }

  const afterAnalyze = analyzeEvents.length;
  const zeroExtraAnalyze = afterAnalyze === beforeAnalyze;
  return {
    ok: orbitOk && zoomOk && (stepStatus === "ok" || stepStatus === "not_applicable") && resetOk && zeroExtraAnalyze,
    orbit_ok: orbitOk,
    orbit_label_shift_px: +maxMove.toFixed(1),
    orbit_cam_delta: +camDist.toFixed(3),
    zoom_ok: zoomOk,
    zoom_cam_delta: +zoomDist.toFixed(3),
    step_status: stepStatus,
    reset_ok: resetOk,
    outside_after_reset: outsideAfterReset,
    extra_analyze_requests: afterAnalyze - beforeAnalyze,
  };
}

async function main() {
  const opts = parseArgs();
  const manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf-8"));
  const queue = [];
  if (opts.filter === "all" || opts.filter === "valid") {
    for (const c of manifest.valid_cases) queue.push({ ...c, _group: "valid" });
  }
  if (opts.filter === "all" || opts.filter === "negative") {
    for (const c of manifest.negative_cases) queue.push({ ...c, _group: "negative" });
  }

  const stream = createWriteStream(OUT_JSONL, { flags: "w", encoding: "utf-8" });
  const browser = await chromium.launch({ headless: true });
  const externalRequests = [];
  const results = [];
  let session = null;
  let batchUsed = 0;
  let batchIdx = 0;
  let prevServedLabels = null;
  let prevServedCaseId = null;

  try {
    for (let i = 0; i < queue.length; i++) {
      const c = queue[i];
      if (!session || batchUsed >= opts.batchSize) {
        if (session) await session.ctx.close();
        batchIdx++;
        session = await openAuthenticatedSession(browser, batchIdx, externalRequests);
        batchUsed = 0;
        prevServedLabels = null;
        prevServedCaseId = null;
      }
      const { page, errors, analyzeEvents } = session;
      const errStart = errors.length;

      await ensureComposer(page);
      const t0 = Date.now();
      const respPromise = page.waitForResponse(
        (r) => r.url().includes("/api/analyze") && r.request().method() === "POST",
        { timeout: 180000 }
      );
      await page.locator(".composer-text").first().fill(c.original_input);
      await page.locator("#btn-composer-send").first().click();
      const resp = await respPromise;
      const ms = Date.now() - t0;
      const http = resp.status();
      const body = await resp.json().catch(() => null);
      batchUsed++;

      stream.write(
        JSON.stringify({
          case_id: c.case_id,
          group: c._group,
          expected_behavior: c.expected_behavior,
          http,
          ms,
          body,
        }) + "\n"
      );

      const routeStatus = body?.route_d?.status || null;
      const extMode = body?.route_d?.extraction_mode || null;
      let uiInfo = { route_status: routeStatus, extraction_mode: extMode, http, ms };

      if (routeStatus === "SERVED") {
        // Wait for Scene3D workspace canvas or full-model button
        await page
          .locator(".geo3d-canvas canvas")
          .first()
          .waitFor({ state: "visible", timeout: 15000 })
          .catch(() => null);

        const fullBtn = page.getByRole("button", { name: "Xem mô hình đầy đủ" });
        if (await fullBtn.isVisible().catch(() => false)) {
          await fullBtn.click();
        }
        await page.waitForTimeout(550);

        const goldV = c.gold_entities?.solid_vertices || [];
        const initM = await measureInitialScene(page, goldV);

        const staleVsPrev =
          prevServedLabels !== null &&
          prevServedCaseId !== c.case_id &&
          JSON.stringify([...(c.gold_entities?.solid_vertices || [])].sort()) !==
            JSON.stringify([...prevServedLabels].sort()) &&
          JSON.stringify([...initM.label_texts].sort()) === JSON.stringify([...prevServedLabels].sort());
        prevServedLabels = initM.label_texts;
        prevServedCaseId = c.case_id;

        const inter = await exerciseInteractions(page, initM, analyzeEvents);
        const caseErrors = errors.slice(errStart);
        const initialVisualOk =
          initM.has_canvas &&
          initM.canvas_ink_fraction >= 0.01 &&
          initM.outside_initial_labels.length === 0 &&
          initM.missing_gold_labels.length === 0 &&
          initM.outside_initial_ndc_vertices.length === 0 &&
          !staleVsPrev &&
          caseErrors.length === 0;

        if (!initialVisualOk || !inter.ok || (extMode && extMode.startsWith("LOCAL_SLM")) || i % 15 === 0) {
          await page.screenshot({ path: join(SHOT_DIR, `${c.case_id}.png`) }).catch(() => null);
        }

        uiInfo = {
          ...uiInfo,
          surface: "SCENE",
          initial_visual_ok: initialVisualOk,
          stale_vs_previous: staleVsPrev,
          ...initM,
          interactions: inter,
          console_errors: caseErrors,
        };
      } else {
        await page.waitForTimeout(500);
        const canvasCount = await page.locator(".geo3d-canvas canvas").count();
        const toastTitle = await page.locator(".axo-composer-toast-title").first().innerText().catch(() => "");
        const toastDesc = await page.locator(".axo-composer-toast-desc").first().innerText().catch(() => "");
        const caseErrors = errors.slice(errStart);
        uiInfo = {
          ...uiInfo,
          surface: "NO_SCENE",
          reason_code: body?.route_d?.reason_code || body?.detail || body?.error_code || null,
          canvas_count: canvasCount,
          toast: `${toastTitle} | ${toastDesc}`.trim(),
          console_errors: caseErrors,
        };
      }

      results.push({
        case_id: c.case_id,
        group: c._group,
        expected_behavior: c.expected_behavior,
        ...uiInfo,
      });

      if ((i + 1) % 10 === 0 || i + 1 === queue.length) {
        console.log(`[${i + 1}/${queue.length}] ${c.case_id} http=${http} route=${routeStatus} mode=${extMode} ms=${ms}`);
      }
    }
  } finally {
    if (session) await session.ctx.close();
    await browser.close();
    await new Promise((r) => stream.end(r));
  }

  const served = results.filter((r) => r.route_status === "SERVED");
  const summary = {
    schema: "axo-browser-checks/1",
    harness_version: HARNESS_VERSION,
    base: BASE,
    total_cases: results.length,
    served_count: served.length,
    initial_visual_pass: served.filter((r) => r.initial_visual_ok).length,
    interaction_pass: served.filter((r) => r.interactions?.ok).length,
    external_requests_count: externalRequests.length,
    external_requests: externalRequests,
    console_error_cases: results.filter((r) => (r.console_errors || []).length > 0).map((r) => r.case_id),
    results,
  };
  writeFileSync(OUT_CHECKS, JSON.stringify(summary, null, 2) + "\n", "utf-8");
  console.log(
    JSON.stringify({
      total: summary.total_cases,
      served: summary.served_count,
      initial_visual_pass: summary.initial_visual_pass,
      interaction_pass: summary.interaction_pass,
      external_requests: summary.external_requests_count,
    })
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
