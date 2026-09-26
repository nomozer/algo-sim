/**
 * AUTOMATED BROWSER REPLAY FOR CUBOID, CUBE & SQUARE PRISM — VISUAL INTEGRITY
 *
 * Task: CUBOID_CUBE_PRISM_SPECIALIZATION_VERTICAL_SLICE
 * Viewports: Desktop 1440x900, Mobile 390x844
 * Targets:
 *   - Cuboid (AB=3, AD=4, AA'=5 => V=60)
 *   - Cube (edge=4 => V=64)
 *   - Square Prism Control (base=3, h=7 => V=63 != Cube)
 *   - Negative refusal case (fail-closed, Vietnamese explanation, no scene)
 */
import { createServer } from "node:http";
import { execSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync, copyFileSync, mkdirSync, statSync, readdirSync, rmSync } from "node:fs";
import { join, resolve, extname } from "node:path";
import crypto from "node:crypto";
import { chromium } from "playwright";

const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const FE_DIR = join(REPO_ROOT, "frontend");
const DIST_DIR = join(FE_DIR, "dist");
const OUT_DIR = resolve(process.env.CUBOID_EVIDENCE_DIR ?? join(
  REPO_ROOT, "docs", "evaluation", "geometry", "cuboid-cube-visual-integrity",
));
const FIXTURE_DIR = resolve(process.env.CUBOID_FIXTURE_DIR ?? OUT_DIR);

mkdirSync(OUT_DIR, { recursive: true });

const RUN_ID = "run_" + Date.now() + "_" + crypto.randomBytes(4).toString("hex");
const TEMP_DIR = join(REPO_ROOT, "docs", "evaluation", "geometry", "temp_" + RUN_ID);
mkdirSync(TEMP_DIR, { recursive: true });

const CUBOID_ENV = JSON.parse(readFileSync(join(FIXTURE_DIR, "cuboid_envelope.json"), "utf8"));
const CUBE_ENV = JSON.parse(readFileSync(join(FIXTURE_DIR, "cube_envelope.json"), "utf8"));
const SQUARE_PRISM_ENV = JSON.parse(readFileSync(join(FIXTURE_DIR, "square_prism_envelope.json"), "utf8"));

const NEGATIVE_ENV = {
  status: "unsupported",
  reason: "Đề bài mâu thuẫn hoặc thiếu dữ kiện hình học cho khối hộp / lập phương.",
  learner_reason: "Đề thuộc hình học không gian nhưng chưa đủ dữ kiện để dựng và kiểm chứng mô phỏng.",
  failure_category: "not_simulation_suitable",
  error_code: "GATE_NOT_SIMULATION_SUITABLE",
  stage_reached: "scope",
  representation_plan: {},
  analysis: {},
};

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

function startServer(directory) {
  return new Promise((res, reject) => {
    const sv = createServer((rq, rp) => {
      let p = decodeURIComponent(rq.url.split("?")[0]);
      if (p.includes("favicon")) {
        rp.writeHead(204);
        rp.end();
        return;
      }
      if (p === "/") p = "/index.html";
      let f = join(directory, p);
      if (!existsSync(f) || statSync(f).isDirectory()) {
        if (extname(p) !== "") {
          rp.writeHead(404);
          rp.end("Not Found");
          return;
        }
        f = join(directory, "index.html");
      }
      rp.writeHead(200, { "Content-Type": MIME[extname(f)] ?? "application/octet-stream" });
      rp.end(readFileSync(f));
    });
    sv.once("error", reject);
    const requestedPort = Number(process.env.BROWSER_REPLAY_PORT ?? 0);
    sv.listen(requestedPort, "127.0.0.1", () => {
      sv.removeListener("error", reject);
      res({ sv, port: sv.address().port });
    });
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function safeGoto(page, url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      await page.goto(url, { waitUntil: "networkidle" });
      await page.waitForFunction(() => {
        const root = document.querySelector("#root");
        return document.styleSheets.length > 0 && root &&
          getComputedStyle(root).display === "flex";
      }, undefined, { timeout: 5000 });
      return;
    } catch (e) {
      if (i < retries - 1 && (
        e.message.includes("ERR_NETWORK_ACCESS_DENIED") ||
        e.message.includes("ERR_CONNECTION_REFUSED") ||
        e.message.includes("ERR_FAILED") ||
        e.message.includes("Timeout")
      )) {
        console.warn(`[safeGoto] Transient navigation error (${e.message}), retrying in 500ms...`);
        await sleep(500);
        continue;
      }
      throw e;
    }
  }
}

async function orbitCanvas(page, canvasSelector, dx = 180, dy = 40) {
  const canvas = page.locator(canvasSelector);
  const box = await canvas.boundingBox();
  if (!box) return false;
  const startX = box.x + box.width * 0.5;
  const startY = box.y + box.height * 0.5;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + dx, startY + dy, { steps: 15 });
  await page.mouse.up();
  await sleep(400); // allow OrbitControls damping to settle
  return true;
}

function buffersDiffer(b1, b2) {
  if (b1.length !== b2.length) return true;
  for (let i = 0; i < b1.length; i++) {
    if (b1[i] !== b2[i]) return true;
  }
  return false;
}

function solidTopology(scene3d) {
  const solid = (scene3d.objects ?? []).find((o) => o.type === "solid");
  if (!solid) return { vertices: 0, edges: 0, faces: 0, euler: null };
  const edges = new Set();
  for (const face of solid.faces ?? []) {
    for (let i = 0; i < face.length; i++) {
      const a = face[i];
      const b = face[(i + 1) % face.length];
      edges.add(a < b ? `${a}:${b}` : `${b}:${a}`);
    }
  }
  const vertices = (solid.vertex_ids ?? solid.vertices ?? []).length;
  const faces = (solid.faces ?? []).length;
  return { vertices, edges: edges.size, faces, euler: vertices - edges.size + faces };
}

function expectedHighlightClosure(scene3d, id) {
  const objects = new Map((scene3d.objects ?? []).map((o) => [o.id, o]));
  const visited = new Set();
  const queue = [...(objects.get(id)?.depends ?? [])];
  while (queue.length > 0) {
    const current = queue.shift();
    if (current === id || visited.has(current)) continue;
    visited.add(current);
    queue.push(...(objects.get(current)?.depends ?? []));
  }
  return [id, ...visited].sort();
}

async function mobileMetrics(page) {
  return page.evaluate(() => ({
    scroll_width: document.documentElement.scrollWidth,
    viewport_width: window.innerWidth,
    overflow_x: document.documentElement.scrollWidth > window.innerWidth,
  }));
}

async function main() {
  console.log("Starting static preview server...");
  const { sv, port } = await startServer(DIST_DIR);
  const origin = `http://127.0.0.1:${port}`;
  console.log(`Server listening on ${origin}`);

  const report = {
    task_id: "CUBOID_CUBE_PRISM_SPECIALIZATION_VERTICAL_SLICE",
    run_id: RUN_ID,
    timestamp: new Date().toISOString(),
    origin,
    scenarios: {},
    all_passed: false,
  };

  const browser = await chromium.launch({ headless: true });

  try {
    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 1: Desktop 1440x900 — Cuboid (AB=3, AD=4, AA'=5 => V=60)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 1: Desktop 1440x900 (Cuboid V=60) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const txt = msg.text();
          if (!txt.includes("favicon") && !txt.includes("ERR_NETWORK_ACCESS_DENIED")) consoleErrors.push(txt.slice(0, 200));
        }
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          await sleep(150);
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CUBOID_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await safeGoto(page, origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.waitFor({ state: "visible" });
      await submitButton.click();

      // Wait for scene3d canvas
      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });
      const canvasBox = await canvasLocator.boundingBox();
      console.log(`Desktop Canvas size: ${canvasBox.width}x${canvasBox.height}`);

      // Scrub to end for default scene view
      const nextButton = page.locator('[aria-label="Bước sau"]');
      const prevButton = page.locator('[aria-label="Bước trước"]');
      for (let i = 0; i < 15; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      // Check readout 60 and tokens
      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const expectedTokens = ["AB", "AD", "AA′", "S(ABCD)", "60", "V"];
      const missingTokens = expectedTokens.filter((t) => !readoutText.includes(t));
      const answerCorrect = missingTokens.length === 0;
      console.log(`Cuboid Desktop Readout: ${readoutText}`);
      if (!answerCorrect) {
        console.error(`Missing expected tokens in Cuboid readout: ${missingTokens.join(", ")}`);
      }

      // Verify 8 distinct labels
      await sleep(300);
      const labelsLocator = page.locator(".geo3d-labels span");
      const labels = (await labelsLocator.allTextContents()).map((l) => l.trim());
      console.log(`Cuboid Desktop Labels: ${JSON.stringify(labels)}`);
      const requiredBase = ["A", "B", "C", "D"];
      const hasBase = requiredBase.every((l) => labels.includes(l));
      const hasTop = labels.some((l) => l.includes("A'") || l.includes("A′")) &&
                     labels.some((l) => l.includes("B'") || l.includes("B′")) &&
                     labels.some((l) => l.includes("C'") || l.includes("C′")) &&
                     labels.some((l) => l.includes("D'") || l.includes("D′"));
      const hasAll8Labels = hasBase && hasTop && labels.length >= 8;
      const projectedCenters = await labelsLocator.evaluateAll((nodes) => nodes.map((node) => {
        const r = node.getBoundingClientRect();
        return `${Math.round(r.x + r.width / 2)}:${Math.round(r.y + r.height / 2)}`;
      }));
      const distinctProjectedPositions = new Set(projectedCenters).size === labels.length;
      const topology = solidTopology(CUBOID_ENV.scene3d);
      const topologyPassed = topology.vertices === 8 && topology.edges === 12 &&
        topology.faces === 6 && topology.euler === 2;

      // 1. Capture cuboid_desktop_default.png
      const defaultBuf = await page.screenshot({ path: join(TEMP_DIR, "cuboid_desktop_default.png") });
      console.log("Captured: cuboid_desktop_default.png");

      // 2. Orbit scene & Capture cuboid_desktop_rotated.png
      await orbitCanvas(page, ".geo3d-canvas canvas", 220, 45);
      const rotatedBuf = await page.screenshot({ path: join(TEMP_DIR, "cuboid_desktop_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: cuboid_desktop_rotated.png (orbit changed: ${orbitChanged})`);

      // Reset view
      const resetBtn = page.locator('button:has-text("Xem lại toàn hình")');
      if (await resetBtn.isVisible()) {
        await resetBtn.click();
        await sleep(300);
      }

      // Helper to compute machine-readable frame evidence
      function extractFrameEvidence(scene3d, step, screenPoints) {
        const free = new Set(scene3d.free_objects || []);
        const visible = new Set(free);
        const events = scene3d.events || [];
        for (let s = 0; s <= step; s++) {
          const ev = events[s];
          if (!ev) continue;
          if (ev.objects && Array.isArray(ev.objects)) {
            for (const id of ev.objects) visible.add(id);
          } else if (ev.object) {
            visible.add(ev.object);
          }
        }

        const objMap = new Map((scene3d.objects || []).map((o) => [o.id, o]));
        const visible_object_ids = Array.from(visible);
        const object_kind = {};
        const endpoint_ids = {};
        const unexpected_unbounded_objects = [];

        for (const id of visible_object_ids) {
          const obj = objMap.get(id);
          if (!obj) continue;
          object_kind[id] = obj.render || obj.type;
          if (obj.endpoint_ids && Array.isArray(obj.endpoint_ids)) {
            endpoint_ids[id] = obj.endpoint_ids;
          }
          if (obj.render === "line" || obj.type === "line3") {
            const role = String(obj.role || "").toLowerCase();
            if (role.includes("cạnh") || role.includes("cao") || role.includes("edge") || role.includes("height")) {
              unexpected_unbounded_objects.push(id);
            }
          }
        }

        const screen_projected_endpoints = {};
        for (const [k, pt] of Object.entries(screenPoints)) {
          if (visible.has(k)) {
            screen_projected_endpoints[k] = pt;
          }
        }

        return {
          step_index: step,
          visible_object_ids,
          object_kind,
          endpoint_ids,
          screen_projected_endpoints,
          unexpected_unbounded_objects,
        };
      }

      // 3. Formation frames: all 9 formation frames (Step 0 to Step 8)
      for (let i = 0; i < 20; i++) {
        const canPrev = await prevButton.isEnabled().catch(() => false);
        if (!canPrev) break;
        await prevButton.click();
        await sleep(50);
      }
      await sleep(200);

      const formationStepsEvidence = [];
      const allUnexpectedUnbounded = [];

      for (let step = 0; step < 9; step++) {
        const stepFile = `formation_step_${step}.png`;
        await page.screenshot({ path: join(TEMP_DIR, stepFile) });
        console.log(`Captured: ${stepFile} (Bước ${step + 1}/9)`);

        const screenPoints = await page.evaluate(() => {
          const spans = Array.from(document.querySelectorAll(".geo3d-labels span"));
          const res = {};
          for (const sp of spans) {
            const text = sp.textContent ? sp.textContent.trim() : "";
            if (!text) continue;
            const r = sp.getBoundingClientRect();
            res[text] = { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
          }
          return res;
        });

        const frameEvidence = extractFrameEvidence(CUBOID_ENV.scene3d, step, screenPoints);
        formationStepsEvidence.push(frameEvidence);
        if (frameEvidence.unexpected_unbounded_objects.length > 0) {
          allUnexpectedUnbounded.push(...frameEvidence.unexpected_unbounded_objects);
        }

        if (step < 8) {
          const canNext = await nextButton.isEnabled().catch(() => false);
          if (canNext) {
            await nextButton.click();
            await sleep(150);
          }
        }
      }

      copyFileSync(join(TEMP_DIR, "formation_step_0.png"), join(TEMP_DIR, "formation_initial.png"));
      copyFileSync(join(TEMP_DIR, "formation_step_4.png"), join(TEMP_DIR, "formation_middle.png"));
      copyFileSync(join(TEMP_DIR, "formation_step_8.png"), join(TEMP_DIR, "formation_final.png"));

      // 4. Causal chain highlight: click readout V
      const vReadoutItem = page.locator('.geo3d-readout li').filter({
        has: page.locator('.geo3d-readout-ten', { hasText: /^V$/ })
      }).first();
      await vReadoutItem.waitFor({ state: "visible", timeout: 5000 });
      await vReadoutItem.click();
      await sleep(200);

      const thanhPhanBtn = page.locator('button:has-text("Thành phần")');
      if (await thanhPhanBtn.isVisible()) {
        await thanhPhanBtn.click();
        await sleep(200);
      }
      const chiTietBtn = page.locator('button:has-text("Chi tiết")');
      if (await chiTietBtn.isVisible()) {
        await chiTietBtn.click();
        await sleep(200);
      }
      const learnerText = await page.locator("body").innerText();
      const leakedInternalTokens = [
        "A_prime", "B_prime", "C_prime", "D_prime",
        "point3", "polygon3", "segment3", "construct_prism",
      ].filter((token) => learnerText.includes(token));
      await page.screenshot({ path: join(TEMP_DIR, "causal_chain_highlight.png") });
      console.log("Captured: causal_chain_highlight.png");

      const causalState = await page.evaluate(() => {
        return {
          selected_id: window.__geo3d_selected_id || null,
          highlighted_ids: window.__geo3d_highlighted_ids || [],
        };
      });
      console.log("Causal state in browser:", JSON.stringify(causalState));

      const expectedDeps = expectedHighlightClosure(CUBOID_ENV.scene3d, "V");
      const actualDeps = [...causalState.highlighted_ids].sort();
      const missingDeps = expectedDeps.filter((id) => !actualDeps.includes(id));
      const unexpectedDeps = actualDeps.filter((id) => !expectedDeps.includes(id));
      const causalPassed = causalState.selected_id === "V" &&
        missingDeps.length === 0 && unexpectedDeps.length === 0;
      if (!causalPassed) {
        console.error(`Causal chain check: selected_id=${causalState.selected_id}, missingDeps=${missingDeps.join(", ")}`);
      }

      report.causal_chain = {
        clicked_object_id: "V",
        selected_object_id: causalState.selected_id,
        expected_dependency_ids: expectedDeps,
        actual_highlighted_ids: causalState.highlighted_ids,
        missing_dependency_ids: missingDeps,
        unexpected_dependency_ids: unexpectedDeps,
        leaked_internal_tokens: leakedInternalTokens,
        causal_chain_passed: causalPassed,
      };

      report.formation_steps = formationStepsEvidence;
      report.unexpected_unbounded_objects = allUnexpectedUnbounded;

      report.scenarios.cuboid_desktop = {
        viewport: "1440x900",
        canvas_mounted: !!canvasBox && canvasBox.width > 100 && canvasBox.height > 100,
        labels_present: hasAll8Labels,
        labels,
        distinct_projected_positions: distinctProjectedPositions,
        topology,
        topology_passed: topologyPassed,
        answer_displayed: answerCorrect,
        answer_text: readoutText,
        orbit_changed: orbitChanged,
        unexpected_unbounded_objects_count: allUnexpectedUnbounded.length,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: hasAll8Labels && distinctProjectedPositions && topologyPassed &&
                leakedInternalTokens.length === 0 &&
                answerCorrect && orbitChanged &&
                consoleErrors.length === 0 && uncaughtExceptions.length === 0 &&
                allUnexpectedUnbounded.length === 0,
      };

      await context.close();
      await sleep(300);
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 2: Mobile 390x844 — Cuboid (V=60)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 2: Mobile 390x844 (Cuboid V=60) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
        isMobile: true,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const txt = msg.text();
          if (!txt.includes("favicon") && !txt.includes("ERR_NETWORK_ACCESS_DENIED")) consoleErrors.push(txt.slice(0, 200));
        }
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CUBOID_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await safeGoto(page, origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 15; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const answerCorrect = readoutText.includes("60");

      const defaultBuf = await page.screenshot({ path: join(TEMP_DIR, "cuboid_mobile_default.png") });
      console.log("Captured: cuboid_mobile_default.png");

      await orbitCanvas(page, ".geo3d-canvas canvas", 120, 30);
      const rotatedBuf = await page.screenshot({ path: join(TEMP_DIR, "cuboid_mobile_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: cuboid_mobile_rotated.png (orbit changed: ${orbitChanged})`);
      const layout = await mobileMetrics(page);

      report.scenarios.cuboid_mobile = {
        viewport: "390x844",
        answer_displayed: answerCorrect,
        orbit_changed: orbitChanged,
        layout,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: answerCorrect && orbitChanged && !layout.overflow_x &&
                consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
      await sleep(300);
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 3: Desktop 1440x900 — Cube (edge=4 => V=64)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 3: Desktop 1440x900 (Cube V=64) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const txt = msg.text();
          if (!txt.includes("favicon") && !txt.includes("ERR_NETWORK_ACCESS_DENIED")) consoleErrors.push(txt.slice(0, 200));
        }
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CUBE_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await safeGoto(page, origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Tính thể tích của hình lập phương đó.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 15; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const expectedTokens = ["AB", "S(ABCD)", "64", "V"];
      const missingTokens = expectedTokens.filter((t) => !readoutText.includes(t));
      const answerCorrect = missingTokens.length === 0;
      console.log(`Cube Desktop Readout: ${readoutText}`);

      await sleep(300);
      const labelsLocator = page.locator(".geo3d-labels span");
      const labels = (await labelsLocator.allTextContents()).map((l) => l.trim());
      console.log(`Cube Desktop Labels: ${JSON.stringify(labels)}`);
      const hasAll8Labels = ["A", "B", "C", "D"].every((l) => labels.includes(l)) && labels.length >= 8;
      const projectedCenters = await labelsLocator.evaluateAll((nodes) => nodes.map((node) => {
        const r = node.getBoundingClientRect();
        return `${Math.round(r.x + r.width / 2)}:${Math.round(r.y + r.height / 2)}`;
      }));
      const distinctProjectedPositions = new Set(projectedCenters).size === labels.length;
      const topology = solidTopology(CUBE_ENV.scene3d);
      const topologyPassed = topology.vertices === 8 && topology.edges === 12 &&
        topology.faces === 6 && topology.euler === 2;

      const defaultBuf = await page.screenshot({ path: join(TEMP_DIR, "cube_desktop_default.png") });
      console.log("Captured: cube_desktop_default.png");

      await orbitCanvas(page, ".geo3d-canvas canvas", 200, 45);
      const rotatedBuf = await page.screenshot({ path: join(TEMP_DIR, "cube_desktop_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      console.log(`Captured: cube_desktop_rotated.png (orbit changed: ${orbitChanged})`);

      report.scenarios.cube_desktop = {
        viewport: "1440x900",
        labels_present: hasAll8Labels,
        labels,
        distinct_projected_positions: distinctProjectedPositions,
        topology,
        topology_passed: topologyPassed,
        answer_displayed: answerCorrect,
        answer_text: readoutText,
        orbit_changed: orbitChanged,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: hasAll8Labels && distinctProjectedPositions && topologyPassed &&
                answerCorrect && orbitChanged && consoleErrors.length === 0 &&
                uncaughtExceptions.length === 0,
      };

      await context.close();
      await sleep(300);
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 4: Mobile 390x844 — Cube (edge=4 => V=64)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 4: Mobile 390x844 (Cube V=64) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
        isMobile: true,
      });
      const page = await context.newPage();
      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const txt = msg.text();
          if (!txt.includes("favicon") && !txt.includes("ERR_NETWORK_ACCESS_DENIED")) {
            consoleErrors.push(txt.slice(0, 200));
          }
        }
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));
      await page.route("**/api/**", async (route) => {
        const pathname = new URL(route.request().url()).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(CUBE_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await safeGoto(page, origin);
      await page.waitForSelector("textarea");
      await page.fill("textarea", "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. Tính thể tích của hình lập phương đó.");
      await page.locator('[aria-label="Phân tích đề bằng AI"]').click();
      await page.locator(".geo3d-canvas canvas").waitFor({ state: "visible", timeout: 15000 });
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 20; i++) {
        if (!await nextButton.isEnabled().catch(() => false)) break;
        await nextButton.click();
        await sleep(50);
      }
      const readoutText = await page.locator(".geo3d-readout").textContent();
      const answerCorrect = readoutText.includes("64");
      const defaultBuf = await page.screenshot({ path: join(TEMP_DIR, "cube_mobile_default.png") });
      await orbitCanvas(page, ".geo3d-canvas canvas", 120, 30);
      const rotatedBuf = await page.screenshot({ path: join(TEMP_DIR, "cube_mobile_rotated.png") });
      const orbitChanged = buffersDiffer(defaultBuf, rotatedBuf);
      const layout = await mobileMetrics(page);

      report.scenarios.cube_mobile = {
        viewport: "390x844",
        answer_displayed: answerCorrect,
        orbit_changed: orbitChanged,
        layout,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: answerCorrect && orbitChanged && !layout.overflow_x &&
                consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };
      await context.close();
      await sleep(300);
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 5: Desktop 1440x900 — Right Square Prism Control (V=63)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 5: Desktop 1440x900 (Square Prism Control V=63) ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 1,
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const txt = msg.text();
          if (!txt.includes("favicon") && !txt.includes("ERR_NETWORK_ACCESS_DENIED")) consoleErrors.push(txt.slice(0, 200));
        }
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SQUARE_PRISM_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await safeGoto(page, origin);
      await page.waitForSelector("textarea");

      const inputText = "Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao bằng 7. Tính thể tích khối lăng trụ đứng đó.";
      await page.fill("textarea", inputText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      const canvasLocator = page.locator(".geo3d-canvas canvas");
      await canvasLocator.waitFor({ state: "visible", timeout: 15000 });

      // Scrub to end
      const nextButton = page.locator('[aria-label="Bước sau"]');
      for (let i = 0; i < 15; i++) {
        const canNext = await nextButton.isEnabled().catch(() => false);
        if (!canNext) break;
        await nextButton.click();
        await sleep(50);
      }

      const readoutLocator = page.locator(".geo3d-readout");
      await readoutLocator.waitFor({ state: "visible" });
      const readoutText = await readoutLocator.textContent();
      const answerCorrect = readoutText.includes("63");
      const notCube = !readoutText.toLowerCase().includes("lập phương") && !readoutText.toLowerCase().includes("cube");
      const topology = solidTopology(SQUARE_PRISM_ENV.scene3d);
      const topologyPassed = topology.vertices === 8 && topology.edges === 12 &&
        topology.faces === 6 && topology.euler === 2;
      console.log(`Square Prism Readout: ${readoutText} (answerCorrect=${answerCorrect}, notCube=${notCube})`);

      await page.screenshot({ path: join(TEMP_DIR, "square_prism_control.png") });
      console.log("Captured: square_prism_control.png");

      report.scenarios.square_prism_control = {
        viewport: "1440x900",
        answer_displayed: answerCorrect,
        not_labeled_as_cube: notCube,
        topology,
        topology_passed: topologyPassed,
        answer_text: readoutText,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: answerCorrect && notCube && topologyPassed &&
                consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
      await sleep(300);
    }

    // ══════════════════════════════════════════════════════════════════════
    // SCENARIO 6: Negative Error Presentation (Fail-Closed)
    // ══════════════════════════════════════════════════════════════════════
    console.log("\n--- Scenario 6: Negative Error Presentation ---");
    {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
      });
      const page = await context.newPage();

      const consoleErrors = [];
      const uncaughtExceptions = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          const txt = msg.text();
          if (!txt.includes("favicon") && !txt.includes("ERR_NETWORK_ACCESS_DENIED")) consoleErrors.push(txt.slice(0, 200));
        }
      });
      page.on("pageerror", (err) => uncaughtExceptions.push(err.message.slice(0, 200)));

      await page.route("**/api/**", async (route) => {
        const u = route.request().url();
        const pathname = new URL(u).pathname;
        if (pathname === "/api/health") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true, hasKey: true, cachedProblems: 0 }) });
        }
        if (pathname === "/api/auth/me") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: null }) });
        }
        if (pathname === "/api/analyze") {
          return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(NEGATIVE_ENV) });
        }
        return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ error: "not mocked" }) });
      });

      await safeGoto(page, origin);
      await page.waitForSelector("textarea");

      const invalidText = "Cho hình hộp chữ nhật có cạnh bên xiên nhưng khai cuboid.";
      await page.fill("textarea", invalidText);

      const submitButton = page.locator('[aria-label="Phân tích đề bằng AI"]');
      await submitButton.click();

      await sleep(500);

      const canvasVisible = await page.locator(".geo3d-canvas canvas").isVisible();
      const bodyText = await page.locator("body").innerText();
      const errorDisplayed = bodyText.includes("chưa đủ dữ kiện") || bodyText.includes("mâu thuẫn") || bodyText.includes("không thể mô phỏng") || bodyText.includes("Từ chối");
      console.log(`Negative Case - Canvas visible: ${canvasVisible}, Error message observed: ${errorDisplayed}`);

      await page.screenshot({ path: join(TEMP_DIR, "negative_error.png") });
      console.log("Captured: negative_error.png");

      report.scenarios.negative_error = {
        viewport: "1440x900",
        canvas_absent: !canvasVisible,
        error_displayed: errorDisplayed,
        console_errors: consoleErrors,
        uncaught_exceptions: uncaughtExceptions,
        passed: !canvasVisible && errorDisplayed && consoleErrors.length === 0 && uncaughtExceptions.length === 0,
      };

      await context.close();
      await sleep(300);
    }

    report.all_passed =
      !!report.scenarios.cuboid_desktop?.passed &&
      !!report.scenarios.cuboid_mobile?.passed &&
      !!report.scenarios.cube_desktop?.passed &&
      !!report.scenarios.cube_mobile?.passed &&
      !!report.scenarios.square_prism_control?.passed &&
      !!report.scenarios.negative_error?.passed &&
      !!report.causal_chain?.causal_chain_passed;

    console.log(`\nALL BROWSER VISUAL CHECKS PASSED: ${report.all_passed}`);
    const reportPath = join(TEMP_DIR, "BROWSER_VISUAL_RESULT.json");
    writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
    console.log(`Wrote browser visual report: ${reportPath}`);

    // Generate contact sheet
    console.log("\nGenerating contact sheet...");
    const pythonExe = join(REPO_ROOT, "backend", ".venv", "Scripts", "python.exe");
    const sheetOutput = join(TEMP_DIR, "CUBOID_CUBE_VISUAL_CONTACT_SHEET.png");
    const tempPy = join(TEMP_DIR, "_generate_sheet.py");

    const pyCode = `
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def make_contact_sheet(img_dir, output_path):
    print(f"Generating contact sheet from {img_dir} to {output_path}...")
    panels = [
        ("cuboid_desktop_default.png", "Cuboid Desktop Default (V=60)"),
        ("cuboid_desktop_rotated.png", "Cuboid Desktop Rotated (Orbit View)"),
        ("cuboid_mobile_default.png", "Cuboid Mobile Default (V=60)"),
        ("cuboid_mobile_rotated.png", "Cuboid Mobile Rotated (Orbit View)"),
        ("cube_desktop_default.png", "Cube Desktop Default (V=64)"),
        ("cube_desktop_rotated.png", "Cube Desktop Rotated (Orbit View)"),
        ("cube_mobile_default.png", "Cube Mobile Default (V=64)"),
        ("cube_mobile_rotated.png", "Cube Mobile Rotated (Orbit View)"),
        ("square_prism_control.png", "Right Square Prism Control (V=63 != Cube)"),
        ("negative_error.png", "Negative Error Presentation (Fail-Closed Refusal)"),
        ("formation_step_0.png", "Formation Step 0: Given Quantities & 8 Vertices"),
        ("formation_step_1.png", "Formation Step 1: Base ABCD Polygon"),
        ("formation_step_2.png", "Formation Step 2: Top A'B'C'D' Polygon"),
        ("formation_step_3.png", "Formation Step 3: Lateral Edges AA', BB', CC', DD'"),
        ("formation_step_4.png", "Formation Step 4: Prism / Cuboid Solid ABCD.A'B'C'D'"),
        ("formation_step_5.png", "Formation Step 5: Base Area S(ABCD) = 12"),
        ("formation_step_6.png", "Formation Step 6: Height AA' = 5"),
        ("formation_step_7.png", "Formation Step 7: Volume V = 60"),
        ("formation_step_8.png", "Formation Step 8: Final Witness V = 60"),
        ("causal_chain_highlight.png", "Causal Chain & Provenance Closure")
    ]
    cell_w, cell_h = 480, 300
    cols, rows = 4, 5
    margin_top, margin_side, margin_bottom = 100, 30, 30
    pad, header_h = 20, 28
    total_w = margin_side * 2 + cols * cell_w + (cols - 1) * pad
    total_h = margin_top + margin_bottom + rows * (cell_h + header_h) + (rows - 1) * pad

    sheet = Image.new("RGB", (total_w, total_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    try:
        title_font = ImageFont.truetype("arial.ttf", 26)
        sub_font = ImageFont.truetype("arial.ttf", 15)
        label_font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        label_font = ImageFont.load_default()

    draw.rectangle([(0, 0), (total_w, 80)], fill=(20, 35, 60))
    draw.text((30, 15), "ALGO-SIM - CUBOID, CUBE & SQUARE PRISM VISUAL INTEGRITY ACCEPTANCE", fill=(255, 255, 255), font=title_font)
    draw.text((30, 48), "Specialization of construct_prism Primitive * 8 Vertices * 12 Edges * 6 Faces (V=60, V=64, V=63)", fill=(180, 205, 235), font=sub_font)

    for idx, (fname, label) in enumerate(panels):
        fpath = os.path.join(img_dir, fname)
        r = idx // cols
        c = idx % cols
        x = margin_side + c * (cell_w + pad)
        y = margin_top + r * (cell_h + header_h + pad)
        w = cell_w

        draw.rectangle([(x, y), (x + w, y + header_h)], fill=(45, 65, 95))
        draw.text((x + 10, y + 6), label, fill=(255, 255, 255), font=label_font)
        draw.rectangle([(x, y + header_h), (x + w, y + header_h + cell_h)], fill=(255, 255, 255), outline=(200, 210, 225), width=1)

        if os.path.exists(fpath):
            img = Image.open(fpath)
            img.thumbnail((w - 6, cell_h - 6), Image.Resampling.LANCZOS)
            offset_x = x + (w - img.width) // 2
            offset_y = y + header_h + (cell_h - img.height) // 2
            sheet.paste(img, (offset_x, offset_y))
        else:
            draw.text((x + 20, y + header_h + 100), f"MISSING: {fname}", fill=(200, 0, 0), font=label_font)

    sheet.save(output_path, "PNG", optimize=True)
    print(f"Contact sheet saved: {output_path} ({total_w}x{total_h})")

if __name__ == '__main__':
    make_contact_sheet(sys.argv[1], sys.argv[2])
`;
    writeFileSync(tempPy, pyCode, "utf8");
    try {
      execSync(`"${pythonExe}" "${tempPy}" "${TEMP_DIR}" "${sheetOutput}"`, { stdio: "inherit" });
    } finally {
      if (existsSync(tempPy)) {
        rmSync(tempPy, { force: true });
      }
    }
    console.log(`Contact sheet generated: ${sheetOutput}`);

    // Compute SHA-256 for all PNG files and generate EVIDENCE_MANIFEST.json
    const PANEL_FILES = [
      "cuboid_desktop_default.png",
      "cuboid_desktop_rotated.png",
      "cuboid_mobile_default.png",
      "cuboid_mobile_rotated.png",
      "cube_desktop_default.png",
      "cube_desktop_rotated.png",
      "cube_mobile_default.png",
      "cube_mobile_rotated.png",
      "square_prism_control.png",
      "formation_initial.png",
      "formation_middle.png",
      "formation_final.png",
      "formation_step_0.png",
      "formation_step_1.png",
      "formation_step_2.png",
      "formation_step_3.png",
      "formation_step_4.png",
      "formation_step_5.png",
      "formation_step_6.png",
      "formation_step_7.png",
      "formation_step_8.png",
      "causal_chain_highlight.png",
      "negative_error.png",
    ];

    const manifest = {
      task_id: "CUBOID_CUBE_PRISM_SPECIALIZATION_VERTICAL_SLICE",
      run_id: RUN_ID,
      timestamp: new Date().toISOString(),
      panel_count: PANEL_FILES.length,
      panels: {},
      all_pngs: {},
      inputs: {},
    };

    let allPanelsValid = true;
    for (const f of PANEL_FILES) {
      const p = join(TEMP_DIR, f);
      if (!existsSync(p) || statSync(p).size === 0) {
        allPanelsValid = false;
        console.error(`Missing or empty panel: ${f}`);
      } else {
        const hash = crypto.createHash("sha256").update(readFileSync(p)).digest("hex");
        manifest.panels[f] = hash;
      }
    }

    const allPngFiles = [
      ...PANEL_FILES,
      "CUBOID_CUBE_VISUAL_CONTACT_SHEET.png",
    ];

    for (const f of allPngFiles) {
      const p = join(TEMP_DIR, f);
      if (existsSync(p)) {
        manifest.all_pngs[f] = crypto.createHash("sha256").update(readFileSync(p)).digest("hex");
      }
    }

    for (const f of ["cuboid_envelope.json", "cube_envelope.json", "square_prism_envelope.json"]) {
      const p = join(FIXTURE_DIR, f);
      manifest.inputs[f] = crypto.createHash("sha256").update(readFileSync(p)).digest("hex");
    }

    const manifestPath = join(TEMP_DIR, "EVIDENCE_MANIFEST.json");
    writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");
    console.log(`Wrote evidence manifest: ${manifestPath}`);

    // Copy everything from TEMP_DIR to OUT_DIR atomically
    console.log(`\nCopying all artifacts from ${TEMP_DIR} to ${OUT_DIR}...`);
    for (const f of readdirSync(TEMP_DIR)) {
      copyFileSync(join(TEMP_DIR, f), join(OUT_DIR, f));
    }
    console.log("Atomic copy complete.");
    if (!allPanelsValid || !report.all_passed) {
      throw new Error("Browser visual gate failed; inspect BROWSER_VISUAL_RESULT.json");
    }
  } finally {
    await browser.close();
    sv.close();
    if (existsSync(TEMP_DIR)) {
      rmSync(TEMP_DIR, { recursive: true, force: true });
    }
  }
}

main().catch((err) => {
  console.error("FATAL ERROR in browser replay:", err);
  if (existsSync(TEMP_DIR)) {
    rmSync(TEMP_DIR, { recursive: true, force: true });
  }
  process.exit(1);
});
