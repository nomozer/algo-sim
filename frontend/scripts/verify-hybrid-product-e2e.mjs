/**
 * verify-hybrid-product-e2e.mjs — Real Frontend + Backend + Headless Chromium E2E Verification (§IX & §X).
 *
 * Spawns real FastAPI `uvicorn` backend processes and serves the compiled `frontend/dist` production bundle
 * behind a local `/api` reverse-proxy gateway (mirroring production Nginx -> FastAPI topology).
 * Executes all 6 required end-to-end user flows through actual browser DOM interactions and network requests,
 * plus runtime health/diagnostics and rollback checks. Makes 0 live provider calls (`ALLOW_LIVE_AI=0`).
 */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import { extname, join, normalize, resolve } from "node:path";
import { chromium } from "playwright";
import { repoRootOf, resolvePython } from "./full-gate.mjs";

const REPO = repoRootOf(import.meta.url);
const RUN_DIR = join(REPO, "docs/evaluation/geometry/runs/hybrid-master-backend-replacement");
const CORPUS_PATH = join(RUN_DIR, "product-integration-staging-corpus.json");
const VERIFICATION_PATH = join(RUN_DIR, "product-integration-16-classes-verification.json");
const DIST_DIR = join(REPO, "frontend/dist");
const RECEIPT_OUT = join(RUN_DIR, "product-e2e-browser-receipt.json");
const SECRET_CANARY = "SECRET_DO_NOT_LEAK_E2E_999";

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

function assert(cond, msg) {
  if (!cond) throw new Error(`E2E_ASSERTION_FAILED: ${msg}`);
}

function getFreePort() {
  return new Promise((res, rej) => {
    const srv = net.createServer();
    srv.unref();
    srv.on("error", rej);
    srv.listen(0, "127.0.0.1", () => {
      const addr = srv.address();
      const port = typeof addr === "object" && addr ? addr.port : 0;
      srv.close(() => res(port));
    });
  });
}

async function waitForHealth(port, timeoutMs = 25_000) {
  const deadline = Date.now() + timeoutMs;
  let lastErr = "not_started";
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/api/health`);
      if (r.ok) return await r.json();
      lastErr = `HTTP ${r.status}`;
    } catch (e) {
      lastErr = e instanceof Error ? e.message : String(e);
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error(`Backend on port ${port} did not become healthy: ${lastErr}`);
}

function spawnBackend(pythonPath, port, extraEnv) {
  const logs = [];
  const child = spawn(
    pythonPath,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(port), "--log-level", "warning"],
    {
      cwd: join(REPO, "backend"),
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        GEMINI_API_KEY: "",
        ALLOW_LIVE_AI: "0",
        HYBRID_V2_LOCAL_ANALYZE: "0",
        ...extraEnv,
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  child.stdout.on("data", (d) => logs.push(d.toString("utf8")));
  child.stderr.on("data", (d) => logs.push(d.toString("utf8")));
  return { child, logs };
}

function startGatewayServer(distDir, getTargetPort) {
  return new Promise((resolveServer, rejectServer) => {
    const srv = http.createServer((req, res) => {
      const urlPath = (req.url || "/").split("?")[0];
      if (urlPath.startsWith("/api/") || urlPath === "/api") {
        const proxyReq = http.request(
          {
            hostname: "127.0.0.1",
            port: getTargetPort(),
            path: req.url,
            method: req.method,
            headers: { ...req.headers, host: `127.0.0.1:${getTargetPort()}` },
          },
          (proxyRes) => {
            res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
            proxyRes.pipe(res);
          },
        );
        proxyReq.on("error", (err) => {
          if (!res.headersSent) {
            res.writeHead(502, { "content-type": "application/json; charset=utf-8" });
            res.end(JSON.stringify({ error: `Gateway proxy error: ${err.message}` }));
          } else {
            res.destroy();
          }
        });
        req.on("aborted", () => proxyReq.destroy());
        req.pipe(proxyReq);
        return;
      }

      const safeRel = normalize(urlPath === "/" ? "index.html" : urlPath.replace(/^\/+/, ""));
      let filePath = resolve(distDir, safeRel);
      if (!filePath.startsWith(resolve(distDir)) || !existsSync(filePath) || statSync(filePath).isDirectory()) {
        filePath = join(distDir, "index.html");
      }
      const ext = extname(filePath).toLowerCase();
      res.writeHead(200, { "content-type": MIME[ext] || "application/octet-stream" });
      res.end(readFileSync(filePath));
    });
    srv.on("error", rejectServer);
    srv.listen(0, "127.0.0.1", () => {
      const addr = srv.address();
      resolveServer({ server: srv, port: typeof addr === "object" && addr ? addr.port : 0 });
    });
  });
}

function loadProblemTexts() {
  const ver = JSON.parse(readFileSync(VERIFICATION_PATH, "utf8"));
  const byId = new Map();
  for (const cat of ver.categories) {
    for (const c of cat.cases) {
      byId.set(c.case_id, c.problem_text);
    }
  }
  return byId;
}

async function submitProblemAndCapture(page, text) {
  const composer = page.locator(".composer-text");
  await composer.waitFor({ state: "visible", timeout: 10_000 });
  await composer.fill(text);
  const responsePromise = page.waitForResponse(
    (r) => r.url().includes("/api/analyze") && r.request().method() === "POST",
    { timeout: 20_000 },
  );
  await page.locator(".composer-send").click();
  const netRes = await responsePromise;
  const status = netRes.status();
  const rawBody = await netRes.text();
  return { status, rawBody, json: JSON.parse(rawBody) };
}

async function verifyServedWorkspace(page, expectedAnswers, checkStepping = false) {
  await page.locator(".geo3d-xuong").waitFor({ state: "visible", timeout: 10_000 });
  const canvas = page.locator(".geo3d-canvas canvas");
  await canvas.waitFor({ state: "visible", timeout: 10_000 });
  const box = await canvas.boundingBox();
  assert(box && box.width >= 200 && box.height >= 150, `Canvas bounding box too small: ${JSON.stringify(box)}`);

  let stepProgression = null;
  if (checkStepping) {
    const stepLabel = page.locator(".geo3d-buoc-so");
    const beforeStep = (await stepLabel.textContent())?.trim() || "";
    const nextBtn = page.locator('button[aria-label="Bước sau"]');
    if (await nextBtn.isEnabled()) {
      await nextBtn.click();
      const afterStep = (await stepLabel.textContent())?.trim() || "";
      assert(afterStep !== beforeStep, `Expected step label to advance from ${beforeStep}, got ${afterStep}`);
      stepProgression = { before: beforeStep, after: afterStep };
    }
  }

  const analysisBtn = page.locator('[data-mo-bang="phan-tich"]');
  await analysisBtn.waitFor({ state: "visible", timeout: 10_000 });
  await analysisBtn.click();
  const analysisPanel = page.locator("#geo3d-bang-phan-tich");
  await analysisPanel.waitFor({ state: "visible", timeout: 10_000 });
  const panelText = (await analysisPanel.textContent()) || "";
  for (const ans of expectedAnswers) {
    assert(panelText.includes(ans), `Expected answer "${ans}" inside #geo3d-bang-phan-tich, got: ${panelText}`);
  }
  assert(!/\b(?:kq_|td_|mp_td_)[A-Za-z0-9_]+|section:td_/.test(panelText), `Leaked machine ID in UI: ${panelText}`);

  const bodyText = (await page.locator("body").textContent()) || "";
  assert(!/\b(?:kq_|td_|mp_td_)[A-Za-z0-9_]+|section:td_/.test(bodyText), "Leaked machine ID in body");

  await page.locator(".geo3d-quay-lai").click();
  await page.locator(".composer-text").waitFor({ state: "visible", timeout: 10_000 });
  return { canvasBox: { width: Math.round(box.width), height: Math.round(box.height) }, stepProgression };
}

async function main() {
  assert(existsSync(join(DIST_DIR, "index.html")), "frontend/dist/index.html missing — run `npm run build` first");
  assert(existsSync(CORPUS_PATH), `Missing staging corpus: ${CORPUS_PATH}`);
  assert(existsSync(VERIFICATION_PATH), `Missing 16-class verification: ${VERIFICATION_PATH}`);

  const resolvedPy = resolvePython({ repo: REPO });
  const tmpDir = mkdtempSync(join(os.tmpdir(), "algosim-hybrid-e2e-"));
  const children = [];
  let gateway = null;
  let browser = null;

  try {
    const stagingPort = await getFreePort();
    const infraFailPort = await getFreePort();
    const rollbackPort = await getFreePort();

    const stagingDb = `sqlite:///${join(tmpDir, "staging.db").replace(/\\/g, "/")}`;
    const infraDb = `sqlite:///${join(tmpDir, "infra.db").replace(/\\/g, "/")}`;
    const rollbackDb = `sqlite:///${join(tmpDir, "rollback.db").replace(/\\/g, "/")}`;

    const stagingProc = spawnBackend(resolvedPy.path, stagingPort, {
      DATABASE_URL: stagingDb,
      HYBRID_ROUTE_MODE: "staging-replay",
      HYBRID_REPLAY_CORPUS: CORPUS_PATH,
    });
    children.push(stagingProc.child);

    const infraProc = spawnBackend(resolvedPy.path, infraFailPort, {
      DATABASE_URL: infraDb,
      HYBRID_ROUTE_MODE: "live",
      ALLOW_LIVE_AI: "0",
      GEMINI_API_KEY: SECRET_CANARY,
    });
    children.push(infraProc.child);

    const rollbackProc = spawnBackend(resolvedPy.path, rollbackPort, {
      DATABASE_URL: rollbackDb,
      HYBRID_ROUTE_MODE: "off",
    });
    children.push(rollbackProc.child);

    const [stagingHealth, infraHealth, rollbackHealth] = await Promise.all([
      waitForHealth(stagingPort),
      waitForHealth(infraPort_fix(infraFailPort)),
      waitForHealth(rollbackPort),
    ]);

    function infraPort_fix(p) {
      return p;
    }

    // §X Startup, health, diagnostics, secret hygiene & rollback checks
    assert(stagingHealth.ok === true, "staging health not ok");
    assert(stagingHealth.runtime.hybrid_route.mode === "staging-replay", "unexpected staging mode");
    assert(stagingHealth.runtime.hybrid_route.simulated === true, "staging must declare simulated=true");
    assert(
      stagingHealth.runtime.hybrid_route.extraction_mode === "REPLAY_STAGING_SIMULATED",
      "staging must declare REPLAY_STAGING_SIMULATED",
    );

    const infraDiag = await (await fetch(`http://127.0.0.1:${infraFailPort}/api/diagnostics/runtime`)).json();
    assert(!JSON.stringify(infraHealth).includes(SECRET_CANARY), "secret leaked in /api/health");
    assert(!JSON.stringify(infraDiag).includes(SECRET_CANARY), "secret leaked in /api/diagnostics/runtime");
    assert(infraDiag.hybrid_route.mode === "live", "infra backend must report mode=live");
    assert(infraDiag.hybrid_route.allow_live_ai === false, "infra backend must report allow_live_ai=false");

    assert(rollbackHealth.runtime.hybrid_route.mode === "off", "rollback mode must be off");
    assert(rollbackHealth.runtime.hybrid_route.enabled === false, "rollback enabled must be false");

    let activeBackendPort = stagingPort;
    gateway = await startGatewayServer(DIST_DIR, () => activeBackendPort);
    const uiBase = `http://127.0.0.1:${gateway.port}`;

    const texts = loadProblemTexts();
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (err) => pageErrors.push(err.message));

    await page.goto(uiBase, { waitUntil: "networkidle" });
    // Register a real student session through the gateway so unlimited E2E flows run under an authenticated cookie.
    const regStatus = await page.evaluate(async () => {
      const e2eCred = ["MatKhau", "AnToan!2026"].join("");
      const r = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: "hybrid.e2e@student.local",
          displayName: "Học sinh E2E",
          password: e2eCred,
        }),
      });
      return r.status;
    });
    assert(regStatus === 200, `Student registration failed with HTTP ${regStatus}`);
    await page.reload({ waitUntil: "networkidle" });

    const flows = [];

    // Flow 1: Supported polyhedral problem (`S2-B-I07_ve_va_tinh`)
    {
      const net = await submitProblemAndCapture(page, texts.get("S2-B-I07_ve_va_tinh"));
      assert(net.status === 200 && net.json.route_d?.status === "SERVED", `Flow 1 HTTP ${net.status}`);
      const ui = await verifyServedWorkspace(page, ["8/3"], true);
      flows.push({
        flow_id: "flow_1_supported_polyhedral",
        case_ids: ["S2-B-I07_ve_va_tinh"],
        http_status: net.status,
        answers_verified: ["8/3"],
        step_progression: ui.stepProgression,
        canvas_box: ui.canvasBox,
        passed: true,
      });
    }

    // Flow 2: Curved & composite multi-object geometry (`cr.shared_base_pyramids_plus_inscribed_sphere`, `cone.par.S`)
    {
      const net1 = await submitProblemAndCapture(
        page,
        texts.get("cr.shared_base_pyramids_plus_inscribed_sphere"),
      );
      assert(net1.status === 200 && net1.json.route_d?.status === "SERVED", `Flow 2a HTTP ${net1.status}`);
      const ui1 = await verifyServedWorkspace(page, ["72", "9π"], false);

      const net2 = await submitProblemAndCapture(page, texts.get("cone.par.S"));
      assert(net2.status === 200 && net2.json.route_d?.status === "SERVED", `Flow 2b HTTP ${net2.status}`);
      const ui2 = await verifyServedWorkspace(page, ["81π/16"], false);

      flows.push({
        flow_id: "flow_2_curved_and_composite_geometry",
        case_ids: ["cr.shared_base_pyramids_plus_inscribed_sphere", "cone.par.S"],
        http_status: 200,
        answers_verified: ["72", "9π", "81π/16"],
        canvas_boxes: [ui1.canvasBox, ui2.canvasBox],
        passed: true,
      });
    }

    // Flow 3: Registered multi-function composition (`S2-B-P07_shared_intermediate_two_goals`)
    {
      const net = await submitProblemAndCapture(
        page,
        texts.get("S2-B-P07_shared_intermediate_two_goals"),
      );
      assert(net.status === 200 && net.json.route_d?.status === "SERVED", `Flow 3 HTTP ${net.status}`);
      const ui = await verifyServedWorkspace(page, ["√3", "1"], true);
      flows.push({
        flow_id: "flow_3_multi_function_composition",
        case_ids: ["S2-B-P07_shared_intermediate_two_goals"],
        http_status: net.status,
        answers_verified: ["√3", "1"],
        step_progression: ui.stepProgression,
        canvas_box: ui.canvasBox,
        passed: true,
      });
    }

    // Flow 4: Constrained-plane (`K-A01`) AND defined-point orthocenter (`R1-B01`) with Category B section rendering
    {
      const net1 = await submitProblemAndCapture(page, texts.get("K-A01"));
      assert(net1.status === 200 && net1.json.route_d?.status === "SERVED", `Flow 4a HTTP ${net1.status}`);
      assert(
        net1.json.route_d.sections?.[0]?.certificate_category === "ENGINE_DERIVED_SECTION",
        "K-A01 must carry ENGINE_DERIVED_SECTION",
      );
      const ui1 = await verifyServedWorkspace(page, ["3√2/2"], false);

      const net2 = await submitProblemAndCapture(page, texts.get("R1-B01"));
      assert(net2.status === 200 && net2.json.route_d?.status === "SERVED", `Flow 4b HTTP ${net2.status}`);
      assert(
        net2.json.route_d.sections?.[0]?.certificate_category === "ENGINE_DERIVED_SECTION",
        "R1-B01 must carry ENGINE_DERIVED_SECTION",
      );
      const ui2 = await verifyServedWorkspace(page, ["2304/625"], false);

      flows.push({
        flow_id: "flow_4_constrained_plane_and_orthocenter",
        case_ids: ["K-A01", "R1-B01"],
        http_status: 200,
        section_certificate_category: "ENGINE_DERIVED_SECTION",
        answers_verified: ["3√2/2", "2304/625"],
        canvas_boxes: [ui1.canvasBox, ui2.canvasBox],
        passed: true,
      });
    }

    // Flow 5: Ambiguous (`S2-C-A01_goc_chieu`) AND contradictory (`S2-D-D03_contradictory_length`)
    {
      const netAmb = await submitProblemAndCapture(page, texts.get("S2-C-A01_goc_chieu"));
      assert(netAmb.status === 200 && netAmb.json.route_d?.status === "REFUSED", "Flow 5a expected 200 REFUSED");
      const clarLoc = page.locator("[data-clarification-question]");
      await clarLoc.waitFor({ state: "visible", timeout: 10_000 });
      const clarText = ((await clarLoc.textContent()) || "").trim();
      assert(
        clarText === netAmb.json.route_d.refusal.clarification.question,
        `Clarification mismatch: ${clarText}`,
      );
      assert((await page.locator(".geo3d-canvas").count()) === 0, "Refusal must not render 3D canvas");

      const netContra = await submitProblemAndCapture(page, texts.get("S2-D-D03_contradictory_length"));
      assert(
        netContra.status === 200 && netContra.json.route_d?.status === "REFUSED",
        "Flow 5b expected 200 REFUSED",
      );
      await page.locator("dl.refusal-facts").waitFor({ state: "visible", timeout: 10_000 });
      assert(
        (await page.locator("[data-clarification-question]").count()) === 0,
        "Contradictory refusal must clear prior clarification question",
      );
      assert((await page.locator(".geo3d-canvas").count()) === 0, "Contradictory refusal must not render 3D canvas");

      flows.push({
        flow_id: "flow_5_ambiguous_and_contradictory_refusal",
        case_ids: ["S2-C-A01_goc_chieu", "S2-D-D03_contradictory_length"],
        http_status: 200,
        clarification_question_rendered: clarText,
        contradictory_failure_category: netContra.json.envelope?.failure_category,
        zero_canvas_on_refusal: true,
        passed: true,
      });
    }

    // Flow 6: Controlled infrastructure failure (HTTP 503) + secret hygiene + clean recovery
    {
      activeBackendPort = infraFailPort;
      const netFail = await submitProblemAndCapture(page, texts.get("S2-B-I07_ve_va_tinh"));
      assert(netFail.status === 503, `Expected HTTP 503 on live-disabled backend, got ${netFail.status}`);
      assert(netFail.json.failure_kind === "INFRASTRUCTURE_FAILURE", "Expected INFRASTRUCTURE_FAILURE");
      assert(!netFail.rawBody.includes(SECRET_CANARY), "Secret leaked in 503 response");
      assert(!netFail.rawBody.includes("Traceback"), "Traceback leaked in 503 response");

      const errBanner = page.locator(".error-banner");
      await errBanner.waitFor({ state: "visible", timeout: 10_000 });
      const errText = ((await errBanner.textContent()) || "").trim();
      assert(errText.length > 0 && !errText.includes(SECRET_CANARY) && !errText.includes("Traceback"), "Bad error banner");
      // Prior UnsupportedNotice (`dl.refusal-facts`) must be cleared so infra failure is NOT mislabeled as math refusal!
      assert(
        (await page.locator("dl.refusal-facts").count()) === 0,
        "Infrastructure error must clear stale mathematical refusal card",
      );
      assert((await page.locator(".geo3d-canvas").count()) === 0, "Infrastructure error must not render 3D canvas");

      // Switch back to healthy staging-replay backend and confirm immediate user recovery without page reload!
      activeBackendPort = stagingPort;
      const netRecover = await submitProblemAndCapture(page, texts.get("S2-B-I07_ve_va_tinh"));
      assert(netRecover.status === 200 && netRecover.json.route_d?.status === "SERVED", "Recovery failed");
      const uiRecover = await verifyServedWorkspace(page, ["8/3"], false);

      flows.push({
        flow_id: "flow_6_infrastructure_failure_and_recovery",
        infra_http_status: netFail.status,
        infra_reason_code: netFail.json.reason_code,
        infra_banner_text: errText,
        secret_leaked: false,
        traceback_leaked: false,
        mislabeled_as_math_refusal: false,
        recovered_to_served_canvas: uiRecover.canvasBox,
        rollback_off_mode_verified: true,
        passed: true,
      });
    }

    assert(pageErrors.length === 0, `Uncaught browser page errors: ${pageErrors.join("; ")}`);

    const distIndexSha = createHash("sha256").update(readFileSync(join(DIST_DIR, "index.html"))).digest("hex");
    const receipt = {
      schema: "hybrid-product-e2e-browser-receipt/1",
      classification: "REAL_BROWSER_AND_UVICORN_NETWORK_E2E_STAGING_REPLAY",
      live_provider_calls: 0,
      browser: "Playwright Chromium (headless)",
      frontend_bundle: {
        served_from: "frontend/dist",
        index_html_sha256: distIndexSha,
      },
      runtime_modes_verified: {
        staging_replay: stagingHealth.runtime.hybrid_route,
        live_disabled_gate: infraDiag.hybrid_route,
        rollback_off: rollbackHealth.runtime.hybrid_route,
      },
      page_errors: pageErrors.length,
      flows_total: flows.length,
      flows_passed: flows.filter((f) => f.passed).length,
      flows,
    };
    writeFileSync(RECEIPT_OUT, JSON.stringify(receipt, null, 2) + "\n", "utf8");
    console.log(
      JSON.stringify({
        ok: true,
        flows_passed: `${receipt.flows_passed}/${receipt.flows_total}`,
        page_errors: receipt.page_errors,
        receipt: "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-e2e-browser-receipt.json",
      }),
    );
  } finally {
    if (browser) await browser.close().catch(() => {});
    if (gateway?.server) await new Promise((r) => gateway.server.close(() => r()));
    for (const c of children) {
      try {
        c.kill();
      } catch {}
    }
    await new Promise((r) => setTimeout(r, 300));
    try {
      rmSync(tmpDir, { recursive: true, force: true });
    } catch {}
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
