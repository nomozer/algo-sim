/**
 * Real-Browser Playwright Visual & Interactive Audit Runner for Scene3D.
 *
 * Builds a minimal static bundle from the current worktree's frontend using Vite,
 * serves it locally on 127.0.0.1, and runs headless Chromium (SwiftShader WebGL)
 * to measure:
 *   - WebGL canvas rendering & ink bounding box
 *   - Own pixel contribution of each primary solid / curved_solid / section / circle3 / ellipse3
 *   - Sub-entity extraction (faces, edges, vertices) & semanticTree categories
 *   - Timeline step count, dependency ordering, and step 0 vs final step progression
 *   - Camera orbit, zoom, pan, and reset framing
 *   - Selection/highlight, isolate, and explode (face + curved objects)
 *   - DOM label legibility and bounding-box collision count
 *   - Full Scene3DExplorer product UI rendering
 *   - 0 console / page / WebGL errors
 */
import { existsSync, mkdirSync, readFileSync, rmSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../../../..");
const frontendRoot = join(repoRoot, "frontend");

const { build, preview } = await import(pathToFileURL(join(frontendRoot, "node_modules/vite/dist/node/index.js")).href);
const reactPluginMod = await import(pathToFileURL(join(frontendRoot, "node_modules/@vitejs/plugin-react/dist/index.js")).href);
const react = reactPluginMod.default ?? reactPluginMod;
const { chromium } = await import(pathToFileURL(join(frontendRoot, "node_modules/playwright/index.mjs")).href);
const { docPNG } = await import(pathToFileURL(join(frontendRoot, "scripts/png-pixels.mjs")).href);

const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const scenesPath = resolve(arg("--scenes", join(__dirname, "browser-audit/baseline_scenes.json")));
const outDir = resolve(arg("--out", join(__dirname, "browser-audit/screenshots-baseline")));
const receiptPath = resolve(arg("--receipt", join(__dirname, "browser-audit/baseline_audit_receipt.json")));
const port = Number(arg("--port", "3111"));

mkdirSync(outDir, { recursive: true });
mkdirSync(dirname(receiptPath), { recursive: true });

const HUE = { section: 38, line: 174, highlight: 221 };
function hue(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  if (d === 0) return { h: 0, s: 0 };
  const h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return { h: (h * 60 + 360) % 360, s: mx === 0 ? 0 : d / mx };
}

function measure(png) {
  const { w, h, rgba } = docPNG(png);
  const n = { section: 0, line: 0, highlight: 0, inkPixels: 0 };
  const counts = new Map();
  for (let i = 0; i < rgba.length; i += 16) {
    const k = `${rgba[i]},${rgba[i + 1]},${rgba[i + 2]}`;
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  const bg = [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0].split(",").map((v) => Number(v));
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4, r = rgba[i], g = rgba[i + 1], b = rgba[i + 2];
      if (Math.abs(r - bg[0]) + Math.abs(g - bg[1]) + Math.abs(b - bg[2]) > 18) {
        n.inkPixels++;
        x0 = Math.min(x0, x); y0 = Math.min(y0, y);
        x1 = Math.max(x1, x); y1 = Math.max(y1, y);
      }
      const { h: hh, s } = hue(r, g, b);
      if (s < 0.25) continue;
      for (const k of Object.keys(HUE)) {
        if (Math.min(Math.abs(hh - HUE[k]), 360 - Math.abs(hh - HUE[k])) < 14) n[k]++;
      }
    }
  }
  return { ...n, ink: x1 < 0 ? null : [x0, y0, x1, y1], width: w, height: h };
}

function diffPixels(a, b) {
  const A = docPNG(a), B = docPNG(b);
  if (A.w !== B.w || A.h !== B.h) return A.w * A.h;
  let d = 0;
  for (let i = 0; i < A.rgba.length; i += 4) {
    if (
      Math.abs(A.rgba[i] - B.rgba[i]) +
      Math.abs(A.rgba[i + 1] - B.rgba[i + 1]) +
      Math.abs(A.rgba[i + 2] - B.rgba[i + 2]) > 30
    ) {
      d++;
    }
  }
  return d;
}

const tmpHtml = join(frontendRoot, "scripts/_tmp_sim_audit.html");
const tmpTsx = join(frontendRoot, "scripts/_tmp_sim_audit.tsx");
const tmpScenesJson = join(frontendRoot, "scripts/_tmp_sim_audit_scenes.json");
const distDir = join(tmpdir(), `algosim-sim-audit-dist-${process.pid}`);

writeFileSync(tmpScenesJson, readFileSync(scenesPath, "utf-8"), "utf-8");
writeFileSync(
  tmpHtml,
  `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Scene3D Audit Harness</title></head><body><div id="root"></div><script type="module" src="./_tmp_sim_audit.tsx"></script></body></html>`,
  "utf-8"
);

writeFileSync(
  tmpTsx,
  `import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Scene3DWorkspace } from "../src/simulations/domains/geometry/scene3d-view";
import { Scene3DExplorer } from "../src/simulations/domains/geometry/Scene3DExplorer";
import { TRANG_THAI_DAU, select, isolate, explode, semanticTree } from "../src/simulations/domains/geometry/interaction-state";
import { diemHuuHan, geometryTimeline, objectsAt, stepCount } from "../src/simulations/domains/geometry/scene3d-model";
import { veKhongGian } from "../src/simulations/domains/geometry/scene3d-chart";
import { withSubEntities } from "../src/simulations/domains/geometry/scene3d-subentities";
import rows from "./_tmp_sim_audit_scenes.json";
import "../src/styles/global.css";

interface AuditParams {
  i: number;
  mode?: "workspace" | "explorer";
  step?: number | null;
  hide?: string;
  select?: string | null;
  isolate?: string | null;
  explode?: string | null;
  aux?: boolean;
}

function SceneView({ params }: { params: AuditParams }) {
  const row = (rows as any[])[params.i];
  const rawScene = row?.scene ?? row?.scene3d;
  const hide = new Set((params.hide ?? "").split(",").filter(Boolean));
  const khung = rawScene && {
    ...rawScene,
    objects: rawScene.objects.filter((o: any) => !hide.has(o.id)),
  } as any;
  const daVe = khung && veKhongGian(khung);
  const scene = daVe && withSubEntities(daVe, objectsAt);
  const n = scene ? stepCount(scene) : 0;
  const timeline = scene ? geometryTimeline(scene) : [];
  const initialStep = params.step != null ? params.step : Math.max(0, n - 1);

  let initInteraction = { ...TRANG_THAI_DAU, current_step: initialStep };
  if (params.select) initInteraction = select(initInteraction, params.select);
  if (params.isolate) initInteraction = isolate(initInteraction, [params.isolate]);
  if (params.explode) initInteraction = explode(initInteraction, params.explode);

  const [fit, setFit] = useState(0);
  const [step, setStep] = useState(initialStep);
  const [aux, setAux] = useState(Boolean(params.aux));
  const [interaction, setInteraction] = useState(initInteraction);

  useEffect(() => {
    setStep(initialStep);
    setAux(Boolean(params.aux));
    setInteraction(initInteraction);
  }, [params]);

  const tree = scene ? semanticTree(scene) : [];
  const finitePts = scene ? diemHuuHan(objectsAt(scene, step)) : [];
  let bbox = null;
  if (finitePts.length > 0) {
    const xs = finitePts.map((p) => p[0]), ys = finitePts.map((p) => p[1]), zs = finitePts.map((p) => p[2]);
    bbox = {
      min: [Math.min(...xs), Math.min(...ys), Math.min(...zs)],
      max: [Math.max(...xs), Math.max(...ys), Math.max(...zs)],
      count: finitePts.length,
    };
  }

  (window as any).__audit = {
    id: row?.id,
    category: row?.category,
    served: row?.served,
    stepCount: n,
    step,
    bbox,
    treeCategories: tree.map((cat: any) => ({
      id: cat.id,
      label: cat.label,
      count: cat.children.length,
      childIds: cat.children.map((c: any) => c.id),
    })),
    subEntityCounts: scene ? {
      total: scene.objects.length,
      topLevel: scene.objects.filter((o: any) => !o.parent).length,
      faces: scene.objects.filter((o: any) => o.type === "face").length,
      segments: scene.objects.filter((o: any) => o.type === "segment3").length,
      points: scene.objects.filter((o: any) => o.type === "point3").length,
    } : null,
    objects: scene ? scene.objects.filter((o: any) => !o.parent).map((o: any) => ({
      id: o.id,
      type: o.type,
      render: o.render,
      curved_kind: o.curved_kind ?? null,
      label: o.label,
      depends: o.depends ?? [],
    })) : [],
    events: scene ? (scene.events ?? []).map((e: any) => ({
      id: e.id,
      step_index: e.step_index,
      action: e.action,
      semantic_kind: e.semantic_kind,
      object: e.object,
      learner_text: e.learner_text,
    })) : [],
    presentAt: (k: number) => scene ? objectsAt(scene, k).map((o: any) => o.id) : [],
    timeline: timeline.map(({ index: idx, start, end, anchor }: any) => ({ index: idx, start, end, anchor })),
  };

  if (!row?.served || !scene) {
    return <main style={{ padding: 16 }}>
      <h1 data-testid="refusal-title">{row?.id}</h1>
      <p data-testid="refusal">{row?.code ?? row?.refusal?.code ?? "REFUSED"}: {row?.reason ?? row?.refusal?.reason ?? "Từ chối an toàn"}</p>
    </main>;
  }

  if (params.mode === "explorer") {
    return <div data-testid="explorer-root" style={{ width: "100vw", height: "100vh" }}>
      <Scene3DExplorer scene={rawScene} de={row.problem_text ?? row.category} tieuDe={row.category} />
    </div>;
  }

  return <main style={{ padding: 16, height: "100vh" }}>
    <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 8 }}>
      <button data-testid="reset-cam" onClick={() => setFit((x) => x + 1)}>Đặt lại khung nhìn</button>
      <input data-testid="step-slider" aria-label="Bước dựng" type="range" min={0} max={Math.max(0, n - 1)} value={step}
        onChange={(e) => setStep(Number(e.target.value))} />
      <label><input data-testid="aux-toggle" type="checkbox" checked={aux} onChange={(e) => setAux(e.target.checked)} /> Hình phụ</label>
    </div>
    <div data-testid="khung" style={{ height: "80vh", minHeight: 520 }}>
      <Scene3DWorkspace
        scene={scene}
        step={step}
        interaction={{ ...interaction, current_step: step }}
        onSelect={(id) => setInteraction((s) => select(s, id))}
        fitToken={fit}
        auxiliaryShown={aux}
      />
    </div>
  </main>;
}

function RootApp() {
  const [params, setParams] = useState<AuditParams>({ i: 0, mode: "workspace" });
  (window as any).__setAuditParams = (next: AuditParams) => {
    setParams({ mode: "workspace", ...next });
  };
  const key = JSON.stringify(params);
  return <SceneView key={key} params={params} />;
}

createRoot(document.getElementById("root")!).render(<RootApp />);
`,
  "utf-8"
);

let browser = null;

try {
  await build({
    root: frontendRoot,
    configFile: false,
    plugins: [react()],
    logLevel: "error",
    build: {
      outDir: distDir,
      emptyOutDir: true,
      rollupOptions: { input: tmpHtml },
    },
  });
} finally {
  if (existsSync(tmpHtml)) unlinkSync(tmpHtml);
  if (existsSync(tmpTsx)) unlinkSync(tmpTsx);
  if (existsSync(tmpScenesJson)) unlinkSync(tmpScenesJson);
}

try {
  browser = await chromium.launch({
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 860 } });

  // Serve Vite static build directly from distDir via Playwright route interception (0 TCP sockets, 0 EACCES/ERR_NETWORK_ACCESS_DENIED)
  await page.route("http://algosim.local/**", async (route) => {
    const u = new URL(route.request().url());
    const rel = u.pathname.replace(/^\/+/, "");
    const filePath = join(distDir, rel);
    if (!existsSync(filePath)) {
      await route.fulfill({ status: 404, body: "Not found" });
      return;
    }
    const contentType = filePath.endsWith(".html")
      ? "text/html; charset=utf-8"
      : filePath.endsWith(".js")
        ? "application/javascript; charset=utf-8"
        : filePath.endsWith(".css")
          ? "text/css; charset=utf-8"
          : "application/octet-stream";
    await route.fulfill({
      status: 200,
      contentType,
      body: readFileSync(filePath),
    });
  });

  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => pageErrors.push(String(e)));

  const baseUrl = `http://algosim.local/scripts/_tmp_sim_audit.html`;
  await page.goto(baseUrl);
  await page.waitForFunction(() => typeof (window).__setAuditParams === "function", null, { timeout: 15000 });

  const rows = JSON.parse(readFileSync(scenesPath, "utf-8"));

  const shot = async (testId = "khung") => page.getByTestId(testId).screenshot();
  const settle = async (testId = "khung") => {
    let a = await shot(testId);
    for (let i = 0; i < 25; i++) {
      await page.waitForTimeout(120);
      const b = await shot(testId);
      if (diffPixels(a, b) === 0) return { settled: true, buf: b };
      a = b;
    }
    return { settled: false, buf: a };
  };

  const switchParams = async (params, refused = false, testId = "khung") => {
    await page.evaluate((p) => (window).__setAuditParams(p), params);
    if (refused) {
      await page.waitForSelector('[data-testid="refusal"]', { state: "attached", timeout: 15000 });
      return null;
    }
    await page.waitForSelector("canvas", { state: "attached", timeout: 15000 });
    return await settle(testId);
  };

  const auditResults = [];

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const errStart = consoleErrors.length + pageErrors.length;
    if (!row.served) {
      await switchParams({ i }, true);
      const refusalText = await page.getByTestId("refusal").textContent();
      const refusalShot = await page.screenshot();
      const shotFile = `${row.id}_refused.png`;
      writeFileSync(join(outDir, shotFile), refusalShot);
      auditResults.push({
        id: row.id,
        category: row.category,
        served: false,
        refusalText,
        screenshot: shotFile,
        consoleErrors: consoleErrors.length + pageErrors.length - errStart,
      });
      continue;
    }

    // 1. Default view at final step
    const defFrame = await switchParams({ i });
    const defFile = `${row.id}_default.png`;
    writeFileSync(join(outDir, defFile), defFrame.buf);
    const defMetrics = measure(defFrame.buf);

    const meta = await page.evaluate(() => {
      const a = (window).__audit;
      const labels = [...document.querySelectorAll(".geo3d-label, [data-label-id]")].map((el) => {
        const r = el.getBoundingClientRect();
        return { text: (el.textContent ?? "").trim(), x: r.x, y: r.y, w: r.width, h: r.height };
      }).filter((l) => l.w > 0 && l.h > 0);
      let labelCollisions = 0;
      for (let p = 0; p < labels.length; p++) {
        for (let q = p + 1; q < labels.length; q++) {
          const A = labels[p], B = labels[q];
          const overlapX = Math.max(0, Math.min(A.x + A.w, B.x + B.w) - Math.max(A.x, B.x));
          const overlapY = Math.max(0, Math.min(A.y + A.h, B.y + B.h) - Math.max(A.y, B.y));
          if (overlapX * overlapY > 0.25 * Math.min(A.w * A.h, B.w * B.h)) {
            labelCollisions++;
          }
        }
      }
      const firstStepOf = {};
      for (let s = 0; s < a.stepCount; s++) {
        for (const id of a.presentAt(s)) {
          if (firstStepOf[id] === undefined) firstStepOf[id] = s;
        }
      }
      const depViolations = [];
      for (const o of a.objects) {
        const sO = firstStepOf[o.id];
        if (sO === undefined) continue;
        for (const dep of o.depends ?? []) {
          const sD = firstStepOf[dep];
          if (sD !== undefined && sD > sO) {
            depViolations.push({ object: o.id, step: sO, dep, depStep: sD });
          }
        }
      }
      const uniqueLabelCoords = new Set(labels.map((l) => `${Math.round(l.x / 4)},${Math.round(l.y / 4)}`)).size;
      return {
        ...a,
        labelCount: labels.length,
        labels: labels.map((l) => l.text),
        labelCollisions,
        uniqueLabelCoords,
        labelsNotCollapsed: labels.length <= 1 || uniqueLabelCoords > 1,
        depViolations,
      };
    });

    // 2. Orbit, zoom, pan, reset
    const box = await page.getByTestId("khung").boundingBox();
    const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    await page.mouse.move(cx + box.height * 0.35, cy + 40, { steps: 10 });
    await page.mouse.up();
    const orbitFrame = await settle();
    const orbitFile = `${row.id}_orbit.png`;
    writeFileSync(join(outDir, orbitFile), orbitFrame.buf);
    const orbitDiffPixels = diffPixels(defFrame.buf, orbitFrame.buf);

    // Zoom (wheel)
    await page.mouse.move(cx, cy);
    await page.mouse.wheel(0, -240);
    const zoomFrame = await settle();
    const zoomDiffPixels = diffPixels(orbitFrame.buf, zoomFrame.buf);

    // Pan (right mouse drag)
    await page.mouse.move(cx, cy);
    await page.mouse.down({ button: "right" });
    await page.mouse.move(cx + 80, cy + 50, { steps: 8 });
    await page.mouse.up({ button: "right" });
    const panFrame = await settle();
    const panDiffPixels = diffPixels(zoomFrame.buf, panFrame.buf);

    // Reset camera
    await page.getByTestId("reset-cam").click();
    const resetFrame = await settle();
    const resetDiffFromDefault = diffPixels(defFrame.buf, resetFrame.buf);

    // 3. Measure own-pixel contributions of primary geometric objects (solid, curved_solid, section, polygon3, circle3, ellipse3)
    const primaryObjs = meta.objects.filter((o) =>
      ["solid", "curved_solid", "section", "polygon3", "circle3", "ellipse3"].includes(o.type)
    );
    const ownPixelMap = {};
    for (const o of primaryObjs) {
      const withoutObj = await switchParams({ i, hide: o.id });
      ownPixelMap[o.id] = {
        type: o.type,
        render: o.render,
        curved_kind: o.curved_kind,
        ownPixels: diffPixels(defFrame.buf, withoutObj.buf),
      };
    }

    // 4. Selection & highlight check
    const selectTarget = primaryObjs[0]?.id ?? meta.objects[0]?.id;
    let selectionDiffPixels = 0;
    let selectedFile = null;
    if (selectTarget) {
      const selFrame = await switchParams({ i, select: selectTarget });
      selectedFile = `${row.id}_selected.png`;
      writeFileSync(join(outDir, selectedFile), selFrame.buf);
      selectionDiffPixels = diffPixels(defFrame.buf, selFrame.buf);
    }

    // 5. Explode check
    const expFrame = await switchParams({ i, explode: "face" });
    const explodedFile = `${row.id}_exploded.png`;
    writeFileSync(join(outDir, explodedFile), expFrame.buf);
    const explodeDiffPixels = diffPixels(defFrame.buf, expFrame.buf);

    // 6. Step 0 vs Final step check
    let step0DiffPixels = 0;
    let step0File = null;
    if (meta.stepCount > 1) {
      const step0Frame = await switchParams({ i, step: 0 });
      step0File = `${row.id}_step0.png`;
      writeFileSync(join(outDir, step0File), step0Frame.buf);
      step0DiffPixels = diffPixels(defFrame.buf, step0Frame.buf);
    }

    // 7. Full Scene3DExplorer UI check
    const expUiFrame = await switchParams({ i, mode: "explorer" }, false, "explorer-root");
    const explorerFile = `${row.id}_explorer.png`;
    writeFileSync(join(outDir, explorerFile), expUiFrame.buf);

    auditResults.push({
      id: row.id,
      category: row.category,
      served: true,
      stepCount: meta.stepCount,
      bbox: meta.bbox,
      subEntityCounts: meta.subEntityCounts,
      treeCategories: meta.treeCategories,
      objects: meta.objects,
      events: meta.events,
      ownPixelMap,
      ink: defMetrics.ink,
      inkPixels: defMetrics.inkPixels,
      hues: {
        section: defMetrics.section,
        line: defMetrics.line,
        highlight: defMetrics.highlight,
      },
      cameraChecks: {
        initialSettled: defFrame.settled,
        orbitSettled: orbitFrame.settled,
        orbitDiffPixels,
        zoomDiffPixels,
        panDiffPixels,
        resetDiffFromDefault,
      },
      interactionChecks: {
        selectTarget,
        selectionDiffPixels,
        explodeDiffPixels,
        step0DiffPixels,
      },
      labelChecks: {
        labelCount: meta.labelCount,
        labels: meta.labels,
        labelCollisions: meta.labelCollisions,
        uniqueLabelCoords: meta.uniqueLabelCoords,
        labelsNotCollapsed: meta.labelsNotCollapsed,
      },
      depViolations: meta.depViolations,
      screenshots: {
        default: defFile,
        orbit: orbitFile,
        selected: selectedFile,
        exploded: explodedFile,
        step0: step0File,
        explorer: explorerFile,
      },
      consoleErrors: consoleErrors.length + pageErrors.length - errStart,
    });
  }

  const receipt = {
    schema: "scene3d-browser-audit-receipt/1",
    scenesFile: scenesPath.startsWith(repoRoot) ? scenesPath.slice(repoRoot.length + 1).replace(/\\/g, "/") : scenesPath,
    totalScenes: rows.length,
    totalConsoleErrors: consoleErrors.length,
    totalPageErrors: pageErrors.length,
    consoleErrorMessages: consoleErrors,
    pageErrorMessages: pageErrors,
    results: auditResults,
  };

  writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + "\n", "utf-8");
  console.log(`Browser audit complete: ${rows.length} scenes -> ${receiptPath}`);
} finally {
  if (browser) await browser.close().catch(() => {});
  if (existsSync(distDir)) rmSync(distDir, { recursive: true, force: true });
}
