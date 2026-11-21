/**
 * Backend-to-Frontend Dynamic Contract Test
 *
 * Exercises the real local FastAPI Python pipeline (`POST /api/analyze`) under
 * `ALLOW_LIVE_AI=0`, `HYBRID_ROUTE_MODE=staging-replay`, `GEMINI_API_KEY=""`
 * (zero network / zero mocked backend responses), validates the returned
 * Scene3D contract across polyhedral, section, sphere, cylinder, cone, and
 * auxiliary primitives, loads envelopes dynamically into `useAppStore`, mounts
 * `<SimulationWorkspace />` in headless Chromium (WebGL via SwiftShader),
 * verifies stepping, object selection, `Xem quan hệ` (0 raw IDs, <= 4 visible
 * items initially), `Định vị` (0 crashes / 0 `NaN`), and verifies fail-closed
 * `REFUSED` payloads (`gate_out_of_scope`, `MISSING_DIMENSION`, `PLANE_NOT_UNIQUE`).
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import type { AnalysisUnsupported } from "../../../core/types";
import { docPhanHoiPhanTich } from "../../../llm/client";
import { registerAllSimulations } from "../../index";
import type { SimulationEnvelope } from "../../types";
import { __resetHistoryForTest } from "../../../state/history";
import { useAppStore } from "../../../state/store";
import { hybridViewCua, kiemHybridView } from "./hybrid-preview-adapter";
import { hopLeScene3D, type Scene3D, type SceneObject } from "./scene3d-model";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FRONTEND_DIR = path.resolve(HERE, "../../../..");
const WORKTREE_ROOT = path.resolve(FRONTEND_DIR, "..");
const BACKEND_DIR = path.join(WORKTREE_ROOT, "backend");
const CORPUS_PATH = path.join(
  WORKTREE_ROOT,
  "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-staging-corpus.json",
);
const VERIFICATION_INDEX_PATH = path.join(
  WORKTREE_ROOT,
  "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/product-integration-16-classes-verification.json",
);

const requireFromFrontend = createRequire(path.join(FRONTEND_DIR, "package.json"));

interface DynamicBackendCaseResult {
  case_id: string;
  prompt: string;
  http_status: number;
  body: Record<string, unknown>;
}

interface VerificationIndexFile {
  categories: Array<{
    cases: Array<{
      case_id: string;
      problem_text: string;
    }>;
  }>;
}

const OUT_OF_SCOPE_PROMPT = "Tính tích phân xác định sin(x) dx";
const SERVED_CASE_IDS = [
  "R1-C02",
  "cr.cube_section_plus_inscribed_sphere",
  "cyl.Stp",
  "cone.par.S",
] as const;
const REFUSED_CORPUS_CASE_IDS = ["n.missing_height", "K-B01"] as const;

const RAW_MACHINE_LEAK_RE =
  /::|@[a-zA-Z0-9_]+|_prime\b|Traceback|\b(?:kq|td|mp_td|khoi|derived|tam_cau|tx_cau|mp_tx|mp_day|day_k)_[a-zA-Z0-9_]+\b/i;

function resolveGitCommonRepoRoot(): string | null {
  try {
    const commonDirRaw = execFileSync("git", ["rev-parse", "--git-common-dir"], {
      cwd: WORKTREE_ROOT,
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
    if (!commonDirRaw) return null;
    const commonDir = path.resolve(WORKTREE_ROOT, commonDirRaw);
    return path.resolve(commonDir, "..");
  } catch {
    return null;
  }
}

function resolveBackendPython(): string {
  const candidates: string[] = [];
  const envPython = process.env.BACKEND_PYTHON?.trim();
  if (envPython) {
    candidates.push(envPython);
  }
  candidates.push(
    path.join(BACKEND_DIR, ".venv/Scripts/python.exe"),
    path.join(BACKEND_DIR, ".venv/bin/python"),
  );
  const commonRepoRoot = resolveGitCommonRepoRoot();
  if (commonRepoRoot && path.resolve(commonRepoRoot) !== path.resolve(WORKTREE_ROOT)) {
    candidates.push(
      path.join(commonRepoRoot, "backend/.venv/Scripts/python.exe"),
      path.join(commonRepoRoot, "backend/.venv/bin/python"),
    );
  }
  candidates.push(
    path.resolve(WORKTREE_ROOT, "../algo-sim/backend/.venv/Scripts/python.exe"),
    path.resolve(WORKTREE_ROOT, "../algo-sim/backend/.venv/bin/python"),
  );
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  throw new Error(`No backend Python virtualenv found in candidates: ${candidates.join(", ")}`);
}

function loadVerificationPrompts(): Map<string, string> {
  const index = JSON.parse(
    fs.readFileSync(VERIFICATION_INDEX_PATH, "utf-8"),
  ) as VerificationIndexFile;
  const map = new Map<string, string>();
  for (const cat of index.categories) {
    for (const c of cat.cases) {
      if (c.case_id && typeof c.problem_text === "string") {
        map.set(c.case_id, c.problem_text);
      }
    }
  }
  return map;
}

function invokeRealBackendAnalyze(
  requests: Array<{ case_id: string; prompt: string }>,
): DynamicBackendCaseResult[] {
  const pythonBin = resolveBackendPython();
  const pythonScript = `
import json, os, pathlib, sys, tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.persistence import db as db_module
import app.main as main_module
import app.accounts.router as router_module
from tests.route_client import route_client

assert os.environ.get("ALLOW_LIVE_AI") == "0", "ALLOW_LIVE_AI must be 0"
assert os.environ.get("HYBRID_ROUTE_MODE") == "staging-replay", "HYBRID_ROUTE_MODE must be staging-replay"
assert os.environ.get("GEMINI_API_KEY", "") == "", "GEMINI_API_KEY must be empty"

reqs = json.loads(sys.stdin.read())
out = []
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    db_file = pathlib.Path(tmp) / "dynamic_contract.db"
    eng = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False}, future=True)
    db_module.Base.metadata.create_all(bind=eng)
    SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    db_module.engine = eng
    db_module.SessionLocal = SessionLocal
    main_module.SessionLocal = SessionLocal
    router_module.SessionLocal = SessionLocal
    client = route_client(main_module.app)
    for item in reqs:
        resp = client.post("/api/analyze", json={"input": {"type": "text", "content": item["prompt"]}})
        out.append({
            "case_id": item["case_id"],
            "prompt": item["prompt"],
            "http_status": resp.status_code,
            "body": resp.json(),
        })
    eng.dispose()
sys.stdout.write(json.dumps(out, ensure_ascii=False))
`;

  const stdout = execFileSync(pythonBin, ["-c", pythonScript], {
    cwd: BACKEND_DIR,
    env: {
      ...process.env,
      ALLOW_LIVE_AI: "0",
      HYBRID_ROUTE_MODE: "staging-replay",
      GEMINI_API_KEY: "",
      HYBRID_REPLAY_CORPUS: CORPUS_PATH,
      PYTHONIOENCODING: "utf-8",
    },
    input: JSON.stringify(requests),
    encoding: "utf-8",
    maxBuffer: 25 * 1024 * 1024,
  });

  return JSON.parse(stdout) as DynamicBackendCaseResult[];
}

function assertNoNonFiniteNumbers(value: unknown, pathLabel: string): void {
  if (typeof value === "number") {
    expect(Number.isFinite(value), `Non-finite number at ${pathLabel}: ${value}`).toBe(true);
    return;
  }
  if (typeof value === "string") {
    expect(value === "NaN" || value === "Infinity" || value === "-Infinity", `Bad numeric string at ${pathLabel}`).toBe(
      false,
    );
    return;
  }
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i += 1) {
      assertNoNonFiniteNumbers(value[i], `${pathLabel}[${i}]`);
    }
    return;
  }
  if (value && typeof value === "object") {
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      assertNoNonFiniteNumbers(v, `${pathLabel}.${k}`);
    }
  }
}

describe("Backend-to-Frontend dynamic /api/analyze -> Scene3D -> SimulationWorkspace contract", () => {
  const resultsByCase = new Map<string, DynamicBackendCaseResult>();

  beforeAll(() => {
    registerAllSimulations();
    const prompts = loadVerificationPrompts();
    const requests: Array<{ case_id: string; prompt: string }> = [
      ...SERVED_CASE_IDS.map((cid) => {
        const prompt = prompts.get(cid);
        if (!prompt) {
          throw new Error(`Missing problem_text in verification index for SERVED case ${cid}`);
        }
        return { case_id: cid, prompt };
      }),
      ...REFUSED_CORPUS_CASE_IDS.map((cid) => {
        const prompt = prompts.get(cid);
        if (!prompt) {
          throw new Error(`Missing problem_text in verification index for REFUSED case ${cid}`);
        }
        return { case_id: cid, prompt };
      }),
      { case_id: "OOS_INTEGRAL", prompt: OUT_OF_SCOPE_PROMPT },
    ];

    const responses = invokeRealBackendAnalyze(requests);
    for (const r of responses) {
      resultsByCase.set(r.case_id, r);
    }
  }, 30_000);

  afterEach(() => {
    __resetHistoryForTest();
    useAppStore.getState().reset();
  });

  it("validates SERVED Scene3D contract across points, segments, polygons, planes, spheres, cylinders, cones, and auxiliary objects", () => {
    const observedObjectTypes = new Set<string>();
    const observedCurvedKinds = new Set<string>();
    let auxiliaryCount = 0;

    for (const cid of SERVED_CASE_IDS) {
      const res = resultsByCase.get(cid);
      expect(res, `Missing backend response for ${cid}`).toBeDefined();
      expect(res!.http_status).toBe(200);

      const routeD = res!.body.route_d as Record<string, unknown> | undefined;
      expect(routeD?.status).toBe("SERVED");

      const parsed = docPhanHoiPhanTich(res!.body);
      expect((parsed as { status?: string }).status).not.toBe("unsupported");

      const env = parsed as SimulationEnvelope & { scene3d: Scene3D };
      const hybridView = hybridViewCua(env);
      expect(hybridView).not.toBeNull();
      expect(kiemHybridView(hybridView, env.scene3d)).toBeNull();
      expect(hopLeScene3D(env.scene3d)).toBe(true);
      assertNoNonFiniteNumbers(env.scene3d, cid);

      const objs = (env.scene3d.objects ?? []) as Array<
        SceneObject & { curved_kind?: string; radius_sq?: string; height_sq?: string }
      >;
      expect(objs.length).toBeGreaterThan(0);

      for (const obj of objs) {
        observedObjectTypes.add(obj.type);
        if (obj.type === "curved_solid" && obj.curved_kind) {
          observedCurvedKinds.add(obj.curved_kind);
          expect(obj.radius_sq).toBeTruthy();
        }
        if (obj.formation_roles?.includes("CONSTRUCT_AUXILIARY_GEOMETRY")) {
          auxiliaryCount += 1;
        }
      }

      // Dynamically load into Zustand app store and confirm clean workspace state
      __resetHistoryForTest();
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(env, undefined, res!.prompt);
      const st = useAppStore.getState();
      expect(st.view).toBe("workspace");
      expect(st.unsupported).toBeNull();
      expect(st.analysisError).toBeNull();
      expect(st.active).not.toBeNull();
      expect((st.active?.envelope as { scene3d?: Scene3D }).scene3d?.objects.length).toBe(objs.length);
    }

    // Required contract families across the real SERVED backend suite
    expect(observedObjectTypes.has("point3")).toBe(true);
    expect(observedObjectTypes.has("segment3")).toBe(true);
    expect(observedObjectTypes.has("polygon3")).toBe(true);
    expect(observedObjectTypes.has("section")).toBe(true);
    expect(observedObjectTypes.has("plane3")).toBe(true);
    expect(observedObjectTypes.has("curved_solid")).toBe(true);
    expect(observedCurvedKinds.has("ball")).toBe(true);
    expect(observedCurvedKinds.has("cylinder")).toBe(true);
    expect(observedCurvedKinds.has("cone")).toBe(true);
    expect(auxiliaryCount).toBeGreaterThan(0);
  });

  it("loads SERVED payloads into <SimulationWorkspace /> in Chromium, steps forward, selects objects, checks Xem quan hệ & Định vị with 0 raw IDs and 0 NaN", async () => {
    const esbuild = requireFromFrontend("esbuild") as {
      build: (opts: Record<string, unknown>) => Promise<{ outputFiles: { text: string }[] }>;
    };
    const { chromium } = requireFromFrontend("playwright") as {
      chromium: {
        launch: (opts: Record<string, unknown>) => Promise<{
          newPage: (opts?: Record<string, unknown>) => Promise<Record<string, any>>;
          close: () => Promise<void>;
        }>;
      };
    };

    const wsComponentPath = path.join(FRONTEND_DIR, "src/components/SimulationWorkspace.tsx");
    const bundled = await esbuild.build({
      stdin: {
        contents: `
          import React from "react";
          import { flushSync } from "react-dom";
          import { createRoot } from "react-dom/client";
          import { registerAllSimulations } from ${JSON.stringify(path.join(FRONTEND_DIR, "src/simulations/index.ts"))};
          import { docPhanHoiPhanTich } from ${JSON.stringify(path.join(FRONTEND_DIR, "src/llm/client.ts"))};
          import { useAppStore } from ${JSON.stringify(path.join(FRONTEND_DIR, "src/state/store.ts"))};
          import { __resetHistoryForTest } from ${JSON.stringify(path.join(FRONTEND_DIR, "src/state/history.ts"))};
          import { SimulationWorkspace } from ${JSON.stringify(wsComponentPath)};

          registerAllSimulations();

          const host = document.createElement("div");
          host.id = "root";
          document.body.appendChild(host);
          const root = createRoot(host);

          window.__axoDynamicMountServed = (rawBody, prompt) => {
            __resetHistoryForTest();
            useAppStore.getState().reset();
            const parsed = docPhanHoiPhanTich(rawBody);
            if ((parsed && parsed.status) === "unsupported") {
              throw new Error("Expected SERVED payload, got unsupported");
            }
            useAppStore.getState().loadEnvelope(parsed, undefined, prompt);
            flushSync(() => {
              root.render(React.createElement(SimulationWorkspace));
            });
            return {
              storeView: useAppStore.getState().view,
              hasActive: Boolean(useAppStore.getState().active),
              rawIds: ((parsed.scene3d && parsed.scene3d.objects) || [])
                .map((o) => o.id)
                .filter((id) => typeof id === "string" && id.includes("_")),
            };
          };

          window.__axoDynamicMountRefused = (rawBody, prompt, mode) => {
            __resetHistoryForTest();
            useAppStore.getState().reset();
            const parsed = docPhanHoiPhanTich(rawBody);
            if (!parsed || parsed.status !== "unsupported") {
              throw new Error("Expected REFUSED/unsupported payload");
            }
            if (mode === "envelope_guard") {
              useAppStore.getState().loadEnvelope(parsed, undefined, prompt);
            } else {
              useAppStore.getState().loadUnsupported(parsed, "contract-refusal-check", prompt);
            }
            flushSync(() => {
              root.render(React.createElement(SimulationWorkspace));
            });
            const st = useAppStore.getState();
            return {
              storeView: st.view,
              hasActive: Boolean(st.active),
              hasUnsupported: Boolean(st.unsupported),
              analysisError: st.analysisError,
            };
          };
        `,
        resolveDir: HERE,
        sourcefile: "dynamic-contract-harness.tsx",
        loader: "tsx",
      },
      bundle: true,
      write: false,
      jsx: "automatic",
      format: "iife",
      platform: "browser",
      target: "es2022",
      define: {
        "process.env.NODE_ENV": '"development"',
        "import.meta.hot": "undefined",
      },
    });

    const browser = await chromium.launch({
      headless: true,
      args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    });

    try {
      const page = await browser.newPage({ viewport: { width: 1280, height: 860 } });
      const pageErrors: string[] = [];
      page.on("pageerror", (err: Error) => {
        pageErrors.push(String(err));
      });

      await page.route("http://axo.local/**", async (route: { request: () => { url: () => string }; fulfill: (opts: Record<string, unknown>) => Promise<void> }) => {
        const url = route.request().url();
        if (url === "http://axo.local/" || url === "http://axo.local/index.html") {
          await route.fulfill({
            status: 200,
            contentType: "text/html; charset=utf-8",
            body: `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body, #root { margin: 0; padding: 0; width: 1280px; height: 860px; }
  .axo-workspace-v62 { display: flex; flex-direction: column; width: 1280px; height: 860px; }
  .axo-body { display: flex; flex: 1; min-height: 620px; }
  .stage-3d, .geo3d-khung, .geo3d-canvas { width: 780px; height: 560px; min-width: 780px; min-height: 560px; position: relative; display: block; }
  #ws-dock { width: 440px; min-width: 440px; display: block; overflow: auto; }
</style>
</head>
<body></body>
</html>`,
          });
          return;
        }
        await route.fulfill({ status: 404, body: "" });
      });

      await page.goto("http://axo.local/");
      await page.addScriptTag({ content: bundled.outputFiles[0]!.text });

      // Test interactive SERVED payloads in Chromium
      for (const cid of SERVED_CASE_IDS) {
        const res = resultsByCase.get(cid)!;
        const mountInfo = (await page.evaluate(
          ({ body, prompt }: { body: Record<string, unknown>; prompt: string }) =>
            (window as unknown as {
              __axoDynamicMountServed: (b: Record<string, unknown>, p: string) => {
                storeView: string;
                hasActive: boolean;
                rawIds: string[];
              };
            }).__axoDynamicMountServed(body, prompt),
          { body: res.body, prompt: res.prompt },
        )) as { storeView: string; hasActive: boolean; rawIds: string[] };

        expect(mountInfo.storeView).toBe("workspace");
        expect(mountInfo.hasActive).toBe(true);

        await page.waitForSelector("#ws-dock", { timeout: 5000 });
        await page.waitForSelector("#playback-pa-box", { timeout: 5000 });
        await page.waitForSelector(".geo3d-canvas canvas", { timeout: 5000 });

        const initialCounter = await page.locator("#pa-counter").innerText();
        const stepMatch = initialCounter.match(/Bước\s+(\d+)\/(\d+)/u);
        expect(stepMatch, `Unexpected counter format for ${cid}: ${initialCounter}`).not.toBeNull();
        const initialStepNum = Number(stepMatch![1]);
        const totalSteps = Number(stepMatch![2]);
        expect(totalSteps).toBeGreaterThanOrEqual(2);

        // Workspace opens at the completed construction by default; rewind to step 1 first so we can verify forward stepping
        if (initialStepNum > 1) {
          await page.locator("#pa-pips-mount button").first().click();
          const atStartCounter = await page.locator("#pa-counter").innerText();
          expect(atStartCounter).toBe(`Bước 1/${totalSteps}`);
        }

        // Step forward using the real `#pa-next` playback button
        const stepsToAdvance = Math.min(3, totalSteps - 1);
        for (let stepIdx = 0; stepIdx < stepsToAdvance; stepIdx += 1) {
          const prevCounter = await page.locator("#pa-counter").innerText();
          expect(await page.locator("#pa-next").isDisabled()).toBe(false);
          await page.click("#pa-next");
          const nextCounter = await page.locator("#pa-counter").innerText();
          expect(nextCounter).not.toBe(prevCounter);
        }

        // Advance to final step on multi-object polyhedral scenes so derived relations & sections are present
        if (cid === "R1-C02" || cid === "cr.cube_section_plus_inscribed_sphere") {
          for (let guard = 0; guard < 30; guard += 1) {
            if (await page.locator("#pa-next").isDisabled()) break;
            await page.click("#pa-next");
          }
        }

        // Select an object from `#dock-entities-pills` (expand background entities if needed)
        const moreEntitiesBtn = page.locator("#btn-dock-entities-more");
        if ((await moreEntitiesBtn.count()) > 0 && (await moreEntitiesBtn.getAttribute("aria-expanded")) !== "true") {
          await moreEntitiesBtn.click();
        }
        const chipsCount = await page.locator("#dock-entities-pills button.dock-entity-chip").count();
        expect(chipsCount, `Expected entity chips for ${cid}`).toBeGreaterThan(0);

        let inspectedWithRelations = false;
        const maxTryChips = Math.min(chipsCount, 8);
        for (let chipIdx = 0; chipIdx < maxTryChips; chipIdx += 1) {
          await page.locator("#dock-entities-pills button.dock-entity-chip").nth(chipIdx).click();
          await page.waitForSelector('#dock-context-object-mount .context-object-card button[data-context-action="relations"]', {
            timeout: 3000,
          });
          await page.click('#dock-context-object-mount button[data-context-action="relations"]');
          await page.waitForSelector('#dock-context-object-mount .context-card-relations-box', {
            timeout: 3000,
          });

          const relStats = (await page.evaluate((rawIds: string[]) => {
            const card = document.querySelector("#dock-context-object-mount .context-object-card");
            const relBox = document.querySelector("#dock-context-object-mount .context-card-relations-box");
            const items = Array.from(document.querySelectorAll("#dock-context-object-mount .context-card-relation-item"));
            const cardText = (card?.textContent ?? "").trim();
            const relText = (relBox?.textContent ?? "").trim();
            const leakedIds = rawIds.filter((id) => cardText.includes(id) || relText.includes(id));
            return {
              visibleRelationItems: items.length,
              leakedIds,
              cardText,
              relText,
            };
          }, mountInfo.rawIds)) as {
            visibleRelationItems: number;
            leakedIds: string[];
            cardText: string;
            relText: string;
          };

          expect(relStats.visibleRelationItems).toBeLessThanOrEqual(4);
          expect(relStats.leakedIds).toEqual([]);
          expect(RAW_MACHINE_LEAK_RE.test(relStats.cardText), `Raw ID leak in cardText (${cid}): ${relStats.cardText}`).toBe(
            false,
          );
          expect(RAW_MACHINE_LEAK_RE.test(relStats.relText), `Raw ID leak in relText (${cid}): ${relStats.relText}`).toBe(
            false,
          );

          // Test `Định vị` on the selected object
          await page.click('#dock-context-object-mount button[data-context-action="locate"]');
          await page.waitForTimeout(80);

          if (relStats.visibleRelationItems > 0) {
            inspectedWithRelations = true;
            break;
          }
        }

        if (cid === "R1-C02" || cid === "cr.cube_section_plus_inscribed_sphere") {
          expect(inspectedWithRelations, `Expected at least 1 verified relation row for ${cid}`).toBe(true);
        }

        const health = (await page.evaluate(() => ({
          canvasCount: document.querySelectorAll(".geo3d-canvas canvas").length,
          viewerFaultCount: document.querySelectorAll('[data-viewer-fault="render_crash"]').length,
          bodyHasNaN: /\bNaN\b/.test(document.body.innerText || ""),
        }))) as { canvasCount: number; viewerFaultCount: number; bodyHasNaN: boolean };

        expect(health).toEqual({
          canvasCount: 1,
          viewerFaultCount: 0,
          bodyHasNaN: false,
        });
      }

      // Test REFUSED payloads rendered fail-closed in Chromium
      const refusedIds = [...REFUSED_CORPUS_CASE_IDS, "OOS_INTEGRAL"] as const;
      for (const cid of refusedIds) {
        const res = resultsByCase.get(cid)!;
        const guardInfo = (await page.evaluate(
          ({ body, prompt }: { body: Record<string, unknown>; prompt: string }) =>
            (window as unknown as {
              __axoDynamicMountRefused: (b: Record<string, unknown>, p: string, m: string) => {
                storeView: string;
                hasActive: boolean;
                hasUnsupported: boolean;
                analysisError: string | null;
              };
            }).__axoDynamicMountRefused(body, prompt, "envelope_guard"),
          { body: res.body, prompt: res.prompt },
        )) as {
          storeView: string;
          hasActive: boolean;
          hasUnsupported: boolean;
          analysisError: string | null;
        };

        expect(guardInfo.storeView).toBe("home");
        expect(guardInfo.hasActive).toBe(false);
        expect(guardInfo.analysisError).toBeTruthy();

        const refusalInfo = (await page.evaluate(
          ({ body, prompt }: { body: Record<string, unknown>; prompt: string }) =>
            (window as unknown as {
              __axoDynamicMountRefused: (b: Record<string, unknown>, p: string, m: string) => {
                storeView: string;
                hasActive: boolean;
                hasUnsupported: boolean;
              };
            }).__axoDynamicMountRefused(body, prompt, "refusal"),
          { body: res.body, prompt: res.prompt },
        )) as { storeView: string; hasActive: boolean; hasUnsupported: boolean };

        expect(refusalInfo.storeView).toBe("home");
        expect(refusalInfo.hasActive).toBe(false);
        expect(refusalInfo.hasUnsupported).toBe(true);

        await page.waitForSelector('[data-error-kind="unsupported_simulation"]', { timeout: 3000 });
        const domCheck = (await page.evaluate(() => {
          const text = document.body.innerText || "";
          return {
            hasRefusalFacts: Boolean(document.querySelector(".refusal-facts")),
            canvasCount: document.querySelectorAll(".geo3d-canvas canvas").length,
            viewerFaultCount: document.querySelectorAll('[data-viewer-fault="render_crash"]').length,
            leaksInternalCode:
              text.includes("gate_out_of_scope") ||
              text.includes("MISSING_DIMENSION") ||
              text.includes("PLANE_NOT_UNIQUE") ||
              text.includes("Traceback"),
          };
        })) as {
          hasRefusalFacts: boolean;
          canvasCount: number;
          viewerFaultCount: number;
          leaksInternalCode: boolean;
        };

        expect(domCheck).toEqual({
          hasRefusalFacts: true,
          canvasCount: 0,
          viewerFaultCount: 0,
          leaksInternalCode: false,
        });
      }

      expect(pageErrors).toEqual([]);
    } finally {
      await browser.close();
    }
  }, 45_000);

  it("handles real backend REFUSED payloads cleanly through docPhanHoiPhanTich and Zustand store fail-closed guards", () => {
    const expectedChecks: Array<{
      case_id: string;
      expectedCode: string;
      checkTopLevelUnsupported: boolean;
    }> = [
      { case_id: "OOS_INTEGRAL", expectedCode: "gate_out_of_scope", checkTopLevelUnsupported: true },
      { case_id: "n.missing_height", expectedCode: "MISSING_DIMENSION", checkTopLevelUnsupported: false },
      { case_id: "K-B01", expectedCode: "PLANE_NOT_UNIQUE", checkTopLevelUnsupported: false },
    ];

    for (const cfg of expectedChecks) {
      const res = resultsByCase.get(cfg.case_id);
      expect(res, `Missing backend response for ${cfg.case_id}`).toBeDefined();
      expect(res!.http_status).toBe(200);

      if (cfg.checkTopLevelUnsupported) {
        expect(res!.body.status).toBe("unsupported");
        expect(res!.body.error_code).toBe(cfg.expectedCode);
      } else {
        const rd = res!.body.route_d as Record<string, unknown>;
        const env = res!.body.envelope as Record<string, unknown>;
        expect(rd?.status).toBe("REFUSED");
        expect(env?.status).toBe("unsupported");
        expect(env?.reason_code).toBe(cfg.expectedCode);
      }

      const parsed = docPhanHoiPhanTich(res!.body) as AnalysisUnsupported;
      expect(parsed.status).toBe("unsupported");

      // Passing an unsupported payload directly into loadEnvelope must fail closed without throwing or activating a scene
      __resetHistoryForTest();
      useAppStore.getState().reset();
      useAppStore.getState().loadEnvelope(parsed as unknown as SimulationEnvelope, undefined, res!.prompt);
      expect(useAppStore.getState().active).toBeNull();
      expect(useAppStore.getState().view).toBe("home");
      expect(useAppStore.getState().analysisError).toBeTruthy();

      // Passing via loadUnsupported records clean learner-safe refusal state
      const attemptId = `refusal-${cfg.case_id}`;
      useAppStore.getState().loadUnsupported(parsed, attemptId, res!.prompt);
      const st = useAppStore.getState();
      expect(st.active).toBeNull();
      expect(st.view).toBe("home");
      expect(st.unsupported).toEqual(parsed);
      expect(st.problemProcessingRecords[attemptId]?.status).toBe("needs_attention");
      expect(st.problemProcessingRecords[attemptId]?.failureKind).toBe("PROBLEM_ERROR");
    }
  });
});
