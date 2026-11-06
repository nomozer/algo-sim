import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { chromium } from "playwright";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import * as ts from "typescript";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App, { AppRoot } from "../App";
import { publicCatalog } from "../data/offline-catalog";
import { AxoClientError, analyzeViaServer } from "../llm/client";
import { registerAllSimulations } from "../simulations";
import type { Scene3D } from "../simulations/domains/geometry/scene3d-model";
import { disposeScene3DObject } from "../simulations/domains/geometry/scene3d-view";
import {
  clearLearnerRecoverySnapshot,
  loadLearnerRecoverySnapshot,
  saveLearnerRecoverySnapshot,
} from "../state/learner-recovery-snapshot";
import { useAppStore } from "../state/store";
import { ErrorBoundary } from "./ErrorBoundary";
import {
  AxoViewerRecoverySurface,
  AxoWorkspaceV62,
  SimulationWorkspace,
} from "./SimulationWorkspace";

registerAllSimulations();

const requireFromFrontend = createRequire(import.meta.url);

function syncStoreForSSR() {
  Object.assign(useAppStore.getInitialState(), useAppStore.getState());
}

describe("AXO Master Continuation §4–§6: Root-Cause Runtime Recovery, Fault Isolation & Learner State Preservation", () => {
  beforeEach(() => {
    registerAllSimulations();
    clearLearnerRecoverySnapshot();
    useAppStore.getState().reset();
    syncStoreForSSR();
  });

  afterEach(() => {
    clearLearnerRecoverySnapshot();
    vi.restoreAllMocks();
  });

  it("1. Category A (Transient Network / Gateway Failure): retries bounded times with backoff, sanitizes NaN policies, pauses if tab hides before or during backoff, and never retries 4xx/refusal errors", async () => {
    let attempts = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      attempts += 1;
      if (attempts < 3) {
        return new Response(JSON.stringify({ detail: "Bad Gateway" }), { status: 502 });
      }
      return new Response(
        JSON.stringify({
          status: "unsupported",
          reason: "Đề thiếu kích thước.",
          failure_category: "insufficient_specification",
        }),
        { status: 200 },
      );
    });

    const recovered = await analyzeViaServer(
      { type: "text", content: "Cho hình chóp S.ABC" },
      undefined,
      { maxRetries: 2, baseDelayMs: 5 },
    );
    expect(attempts).toBe(3);
    expect(recovered.status).toBe("unsupported");

    // NaN policy values are sanitized to safe bounded defaults rather than producing NaN delays/caps
    let nanAttempts = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      nanAttempts += 1;
      return new Response(JSON.stringify({ detail: "Gateway Timeout" }), { status: 504 });
    });
    await expect(
      analyzeViaServer(
        { type: "text", content: "Cho hình nón" },
        undefined,
        { maxRetries: Number.NaN, baseDelayMs: 5 },
      ),
    ).rejects.toBeInstanceOf(AxoClientError);
    expect(nanAttempts).toBe(3); // default maxRetries = 2 -> 1 initial + 2 retries

    // Counterfactual 1: 400/422/429 deterministic client/quota error MUST NOT auto-retry
    let badInputAttempts = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      badInputAttempts += 1;
      return new Response(JSON.stringify({ code: "INVALID_INPUT", error: "Đầu vào rỗng." }), {
        status: 400,
      });
    });
    await expect(
      analyzeViaServer(
        { type: "text", content: "" },
        undefined,
        { maxRetries: 2, baseDelayMs: 5 },
      ),
    ).rejects.toBeInstanceOf(AxoClientError);
    expect(badInputAttempts).toBe(1);

    // Counterfactual 2: Tab becoming hidden DURING backoff wait cancels the next attempt immediately
    let hiddenMidBackoffAttempts = 0;
    let hiddenFlag = false;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      hiddenMidBackoffAttempts += 1;
      setTimeout(() => {
        hiddenFlag = true;
      }, 1);
      throw new TypeError("Failed to fetch");
    });
    await expect(
      analyzeViaServer(
        { type: "text", content: "Cho hình chóp" },
        undefined,
        { maxRetries: 2, baseDelayMs: 12, isDocumentHidden: () => hiddenFlag },
      ),
    ).rejects.toBeInstanceOf(AxoClientError);
    expect(hiddenMidBackoffAttempts).toBe(1);
  });

  it(
    "2. Category C (Viewer-Scoped React Crash Isolation in Real Chromium DOM): mounts real React 18 createRoot(<AxoWorkspaceV62 />), catches viewer crash inside #stage-3d-box while keeping #ws-dock intact, recovers on manual retry, and resyncs stage controls when problemSnapshotKey changes with identical scene ref",
    async () => {
      const wsPath = join(__dirname, "SimulationWorkspace.tsx");
      const wsSrc = readFileSync(wsPath, "utf8");
      const wsAst = ts.createSourceFile(wsPath, wsSrc, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

      // Zero test-backdoor bypass props in production workspace code
      expect(wsSrc).not.toContain("viewerOverrideForTest");
      expect(wsSrc).not.toContain("initialViewerRecoveryStateForTest");
      expect(wsSrc).not.toContain("ViewerTestOverrideMount");

      // Verify AST topology: `<ErrorBoundary mien="scene3d-viewer">` wraps `<Scene3DWorkspace>` inside `#stage-3d-box`, while `#ws-dock` sits outside it
      let foundViewerBoundaryWrappingScene3D = false;
      let viewerBoundaryEnd = -1;
      let studyDockStart = -1;
      const visitWs = (node: ts.Node) => {
        if (ts.isJsxElement(node)) {
          const tag = node.openingElement.tagName.getText(wsAst);
          if (tag === "ErrorBoundary") {
            const isViewerMien = node.openingElement.attributes.properties.some(
              (attr) =>
                ts.isJsxAttribute(attr)
                && attr.name.getText(wsAst) === "mien"
                && attr.initializer?.getText(wsAst) === '"scene3d-viewer"',
            );
            if (isViewerMien) {
              const innerText = node.getText(wsAst);
              if (innerText.includes("<Scene3DWorkspace") && !innerText.includes('id="ws-dock"')) {
                foundViewerBoundaryWrappingScene3D = true;
                viewerBoundaryEnd = node.getEnd();
              }
            }
          }
          if (tag === "aside") {
            const isStudyDock = node.openingElement.attributes.properties.some(
              (attr) =>
                ts.isJsxAttribute(attr)
                && attr.name.getText(wsAst) === "id"
                && attr.initializer?.getText(wsAst) === '"ws-dock"',
            );
            if (isStudyDock) {
              studyDockStart = node.getStart(wsAst);
            }
          }
        }
        ts.forEachChild(node, visitWs);
      };
      visitWs(wsAst);
      expect(foundViewerBoundaryWrappingScene3D).toBe(true);
      expect(studyDockStart).toBeGreaterThan(viewerBoundaryEnd);

      // Bundle real `AxoWorkspaceV62` + `createRoot` + `flushSync` in memory via esbuild and execute inside real headless Chromium
      const esbuild = requireFromFrontend("esbuild") as {
        build: (opts: Record<string, unknown>) => Promise<{ outputFiles: { text: string }[] }>;
      };
      const sample = publicCatalog().find((s) => s.id === "thiet-dien-chop") ?? publicCatalog()[0]!;
      const sceneJson = JSON.stringify((sample.envelope as unknown as { scene3d: Scene3D }).scene3d);
      const descJson = JSON.stringify(sample.envelope.description);
      const titleJson = JSON.stringify(sample.title);

      const bundled = await esbuild.build({
        stdin: {
          contents: `
            import React from "react";
            import { flushSync } from "react-dom";
            import { createRoot } from "react-dom/client";
            import * as THREE from "three";
            import { useAppStore } from "../state/store";
            import { AxoWorkspaceV62 } from "./SimulationWorkspace";

            const SHARED_SCENE = ${sceneJson};
            const PROBLEM_DESC = ${descJson};
            const PROBLEM_TITLE = ${titleJson};

            const origObjAdd = THREE.Object3D.prototype.add;
            window.__armViewerCrash = false;
            THREE.Object3D.prototype.add = function(...objs) {
              if (window.__armViewerCrash) {
                throw new Error("Controlled crash inside Scene3DWorkspace");
              }
              return origObjAdd.apply(this, objs);
            };

            const host = document.createElement("div");
            host.id = "root";
            document.body.appendChild(host);
            const root = createRoot(host);

            window.__resetHarnessRoot = () => {
              flushSync(() => {
                root.render(null);
              });
            };

            window.__mountWorkspace = (sampleId, armCrash) => {
              window.__armViewerCrash = Boolean(armCrash);
              flushSync(() => {
                useAppStore.setState({ activeSampleId: sampleId });
                root.render(
                  React.createElement(AxoWorkspaceV62, {
                    scene: SHARED_SCENE,
                    de: PROBLEM_DESC,
                    tieuDe: PROBLEM_TITLE,
                  })
                );
              });
            };
          `,
          resolveDir: __dirname,
          sourcefile: "viewer-boundary-harness.tsx",
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
        const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
        await page.setContent("<!doctype html><html><body></body></html>");
        await page.addScriptTag({ content: bundled.outputFiles[0]!.text });

        // 1) Mount real AxoWorkspaceV62 with armed fault inside Scene3DWorkspace -> caught by real <ErrorBoundary mien="scene3d-viewer">
        await page.evaluate(() => {
          (window as unknown as { __mountWorkspace: (k: string, t: boolean) => void }).__mountWorkspace(
            "sample:thiet-dien-chop:a",
            true,
          );
        });
        await page.waitForSelector('[data-viewer-fault="render_crash"]', { timeout: 3000 });

        const afterCrash = await page.evaluate(() => ({
          hasViewerFault: Boolean(document.querySelector('[data-viewer-fault="render_crash"]')),
          hasNotFound: Boolean(document.querySelector('[data-error-kind="not_found"]')),
          leaksStack: (document.body.innerText || "").includes("Controlled crash"),
          hasStudyDock: Boolean(document.getElementById("ws-dock")),
          hasProblemStatement: Boolean(document.getElementById("dock-prob-statement")),
          hasStepsList: Boolean(document.getElementById("dock-steps-ul")),
          hasPlaybackBar: Boolean(document.getElementById("playback-pa-box")),
          hasFloatingToolbar: Boolean(document.getElementById("floating-toolbar-3d")),
          hasRetryBtn: Boolean(document.querySelector(".axo-viewer-recovery-retry")),
        }));
        expect(afterCrash).toEqual({
          hasViewerFault: true,
          hasNotFound: false,
          leaksStack: false,
          hasStudyDock: true,
          hasProblemStatement: true,
          hasStepsList: true,
          hasPlaybackBar: false,
          hasFloatingToolbar: false,
          hasRetryBtn: true,
        });

        // 2) Disarm fault and click real `.axo-viewer-recovery-retry` button -> runs ErrorBoundary.setState + onRecover, restoring viewer & stage controls
        await page.evaluate(() => {
          (window as unknown as { __armViewerCrash: boolean }).__armViewerCrash = false;
        });
        await page.click(".axo-viewer-recovery-retry");
        await page.waitForSelector("#playback-pa-box", { timeout: 3000 });
        const afterManualRetry = await page.evaluate(() => ({
          hasViewerFault: Boolean(document.querySelector('[data-viewer-fault="render_crash"]')),
          hasPlaybackBar: Boolean(document.getElementById("playback-pa-box")),
          hasFloatingToolbar: Boolean(document.getElementById("floating-toolbar-3d")),
          hasStudyDock: Boolean(document.getElementById("ws-dock")),
          canvasCount: document.querySelectorAll(".geo3d-canvas canvas").length,
        }));
        expect(afterManualRetry).toEqual({
          hasViewerFault: false,
          hasPlaybackBar: true,
          hasFloatingToolbar: true,
          hasStudyDock: true,
          canvasCount: 1,
        });

        // 3) Crash again on problem key B, then switch to problem key C WITH THE EXACT SAME `SHARED_SCENE` REFERENCE (`MINOR-R2-2`)
        await page.evaluate(() => {
          const w = window as unknown as {
            __resetHarnessRoot: () => void;
            __mountWorkspace: (k: string, t: boolean) => void;
          };
          w.__resetHarnessRoot();
          w.__mountWorkspace("sample:thiet-dien-chop:b", true);
        });
        await page.waitForSelector('[data-viewer-fault="render_crash"]', { timeout: 3000 });
        expect(await page.locator("#playback-pa-box").count()).toBe(0);

        await page.evaluate(() => {
          (window as unknown as { __mountWorkspace: (k: string, t: boolean) => void }).__mountWorkspace(
            "sample:thiet-dien-chop:c",
            false,
          );
        });
        await page.waitForSelector("#playback-pa-box", { timeout: 3000 });
        const afterSameSceneKeySwitch = await page.evaluate(() => ({
          hasViewerFault: Boolean(document.querySelector('[data-viewer-fault="render_crash"]')),
          hasPlaybackBar: Boolean(document.getElementById("playback-pa-box")),
          hasFloatingToolbar: Boolean(document.getElementById("floating-toolbar-3d")),
          canvasCount: document.querySelectorAll(".geo3d-canvas canvas").length,
        }));
        expect(afterSameSceneKeySwitch).toEqual({
          hasViewerFault: false,
          hasPlaybackBar: true,
          hasFloatingToolbar: true,
          canvasCount: 1,
        });
      } finally {
        await browser.close();
      }
    },
    20_000,
  );

  it("3. Category B, §6.1, GPU/Window Hygiene & Responsive Stacking: renders minimalist 'Đang khôi phục mô phỏng', enforces WebGL/RAF/window cleanup in AST, disposes Sprite CanvasTextures, and stacks stage controls cleanly across <= 860px & <= 480px", () => {
    const recoveringHtml = renderToString(
      <AxoViewerRecoverySurface
        state={{
          phase: "recovering",
          reason: "webgl_context_lost",
          attempt: 1,
          maxAttempts: 2,
        }}
      />,
    );
    expect(recoveringHtml).toContain("Đang khôi phục mô phỏng");
    expect(recoveringHtml).toContain('aria-live="polite"');
    expect(recoveringHtml).toContain('data-viewer-recovery-phase="recovering"');
    expect(recoveringHtml).not.toContain('data-error-kind="not_found"');
    const visibleTextOnly = recoveringHtml.replace(/<svg[\s\S]*?<\/svg>/gu, "");
    expect(visibleTextOnly).not.toContain("404");

    const sample = publicCatalog().find((s) => s.id === "cau-cat-mat-phang") ?? publicCatalog()[0]!;
    const scene = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const healthyWsHtml = renderToString(
      <AxoWorkspaceV62 scene={scene} de={sample.envelope.description} tieuDe={sample.title} />,
    );
    expect(healthyWsHtml).toContain('id="ws-dock"');
    expect(healthyWsHtml).toContain('id="dock-prob-statement"');
    expect(healthyWsHtml).toContain('id="dock-given-params"');
    expect(healthyWsHtml).toContain("R = 5");
    expect(healthyWsHtml).toContain('id="dock-steps-ul"');

    // Lock BLOCKER-1 & MINOR-R2-1 via TypeScript AST on scene3d-view.tsx:
    // - WebGL lifecycle useEffect depends on `[webglEpoch, webglFailed]` and latches `webglTerminalLatchedRef`
    // - Cancels pending `rafId` via `cancelAnimationFrame`
    // - Deletes `__geo3d_reset_occlusion_performance` (releasing `goc` closure) & all `__geo3d_*` keys
    // - Uses `disposeScene3DObject` on `nhanChungRef` children
    const viewPath = join(__dirname, "../simulations/domains/geometry/scene3d-view.tsx");
    const viewSrc = readFileSync(viewPath, "utf8");
    const viewAst = ts.createSourceFile(viewPath, viewSrc, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    let foundWebglEffectDeps = false;
    let foundTerminalLatchGuard = false;
    let foundRafCancelAndGlobalCleanup = false;
    const visitView = (node: ts.Node) => {
      if (
        ts.isCallExpression(node)
        && ts.isIdentifier(node.expression)
        && node.expression.text === "useEffect"
        && node.arguments.length === 2
        && ts.isArrayLiteralExpression(node.arguments[1])
      ) {
        const depNames = node.arguments[1].elements.map((e) => e.getText(viewAst));
        if (depNames.includes("webglEpoch") && depNames.includes("webglFailed")) {
          foundWebglEffectDeps = true;
          const bodyText = node.arguments[0].getText(viewAst);
          if (
            bodyText.includes("if (webglFailed || webglTerminalLatchedRef.current) return;")
            && bodyText.includes("webglTerminalLatchedRef.current = true;")
          ) {
            foundTerminalLatchGuard = true;
          }
          if (
            bodyText.includes("cancelAnimationFrame(rafId)")
            && bodyText.includes('"__geo3d_reset_occlusion_performance"')
            && bodyText.includes('"__geo3d_occlusion_performance"')
          ) {
            foundRafCancelAndGlobalCleanup = true;
          }
        }
      }
      ts.forEachChild(node, visitView);
    };
    visitView(viewAst);
    expect(foundWebglEffectDeps).toBe(true);
    expect(foundTerminalLatchGuard).toBe(true);
    expect(foundRafCancelAndGlobalCleanup).toBe(true);
    expect(viewSrc).toMatch(/const nhom = nhanChungRef\.current;[\s\S]{0,160}?disposeScene3DObject\(con\)/);

    // Lock MAJOR-5: disposeScene3DObject disposes SpriteMaterial.map & alphaMap textures (e.g., Oxyz axis CanvasTextures)
    const mapTex = new THREE.Texture();
    const alphaTex = new THREE.Texture();
    const mapDisposeSpy = vi.spyOn(mapTex, "dispose");
    const alphaDisposeSpy = vi.spyOn(alphaTex, "dispose");
    const spriteMat = new THREE.SpriteMaterial({ map: mapTex, alphaMap: alphaTex });
    const matDisposeSpy = vi.spyOn(spriteMat, "dispose");
    const axisGroup = new THREE.Group();
    axisGroup.add(new THREE.Sprite(spriteMat));
    disposeScene3DObject(axisGroup);
    expect(mapDisposeSpy).toHaveBeenCalledTimes(1);
    expect(alphaDisposeSpy).toHaveBeenCalledTimes(1);
    expect(matDisposeSpy).toHaveBeenCalledTimes(1);

    // Lock MAJOR-2, MAJOR-R2-2 & §6.1 in CSS:
    // - Flat stage error surface
    // - `.toolbar-3d-floating` elevated to `bottom: 58px` across `<= 860px` (above `.playback-pa-wrap` at `bottom: 12px; max-width: calc(100% - 24px)`)
    // - `.toolbar-3d-floating` adjusted to `bottom: 48px; right: 8px` across `<= 480px`
    const css = readFileSync(new URL("../styles/global.css", import.meta.url), "utf8");
    expect(css).toContain(".axo-viewer-recovery");
    expect(css).toMatch(/\.axo-error-experience\.is-stage\s+\.axo-error-surface\s*\{[\s\S]*?background:\s*transparent/);
    const media860Blocks = [...css.matchAll(/@media\s*\(max-width:\s*860px\)\s*\{([\s\S]*?)\r?\n\}/g)].map(
      (m) => m[1]!,
    );
    expect(media860Blocks.some((b) => /\.toolbar-3d-floating\s*\{[\s\S]*?bottom:\s*58px;/.test(b))).toBe(true);
    expect(
      media860Blocks.some((b) => /\.playback-pa-wrap\s*\{[\s\S]*?max-width:\s*calc\(100%\s*-\s*24px\);/.test(b)),
    ).toBe(true);
    const media480Blocks = [...css.matchAll(/@media\s*\(max-width:\s*480px\)\s*\{([\s\S]*?)\r?\n\}/g)].map(
      (m) => m[1]!,
    );
    expect(media480Blocks.length).toBeGreaterThanOrEqual(1);
    expect(media480Blocks.some((b) => /\.toolbar-3d-floating\s*\{\s*bottom:\s*48px;/.test(b))).toBe(true);
    expect(media480Blocks.some((b) => /\.toolbar-3d-floating\s*\{\s*bottom:\s*8px;/.test(b))).toBe(false);
  });

  it("4. Category D & Math Contradiction Isolation: suppresses stage overlays & 2D footer while keeping #ws-dock, #dock-prob-statement, #dock-steps-ul & '—' badge intact across inner-malformed, outer-malformed, and contradictory Scene3D", () => {
    const sample = publicCatalog()[0]!;
    const malformedInnerScene = {
      free_objects: ["A"],
      objects: [
        { id: "A", type: "point3", label: "A", origin: "free", render: "point_marker", xyz: "not_a_tuple_crash" },
      ],
      events: [{ step_index: 0, action: "INIT" }],
    } as unknown as Scene3D;

    const innerHtml = renderToString(
      <AxoWorkspaceV62
        scene={malformedInnerScene}
        de="Cho hình chóp S.ABC có SA vuông góc với (ABC), AB = 2a, SA = 4a."
        tieuDe="Bài toán kiểm thử dữ liệu Scene3D hỏng"
      />,
    );

    expect(innerHtml).toContain('id="stage-3d-box"');
    expect(innerHtml).toContain('id="ws-scene3d-unavailable-card"');
    expect(innerHtml).toContain('data-stage-fault="invalid_scene_data"');
    expect(innerHtml).toContain('id="ws-dock"');
    expect(innerHtml).toContain('id="dock-prob-statement"');
    expect(innerHtml).toContain("SA = 4a");
    expect(innerHtml).toContain('id="dock-steps-ul"');
    expect(innerHtml).toContain("Tạm gián đoạn");
    expect(innerHtml).not.toContain("Bước 1/1");
    expect(innerHtml).not.toContain('id="playback-pa-box"');
    expect(innerHtml).not.toContain('id="floating-toolbar-3d"');
    expect(innerHtml).not.toContain("Chưa đủ kết quả mục tiêu");
    expect(innerHtml).not.toContain('data-error-action="secondary-retry"');
    expect(innerHtml).not.toContain("<canvas");

    // Outer-malformed geometry envelope WITH empty problem text AND rendered inside full `<App />` shell:
    // - Keeps `#ws-dock`, `#dock-prob-statement`, and `#dock-steps-ul`
    // - Does NOT leak the 2D `<footer class="panel-controls">` shell controls!
    useAppStore.setState({
      view: "workspace",
      returnView: "library",
      hasInAppNavigation: true,
      problemText: "",
      active: {
        moduleId: "generic.semantic_program",
        envelope: {
          ...sample.envelope,
          domain: "geometry",
          title: "",
          description: undefined,
          scene3d: { malformed: true },
        } as unknown as typeof sample.envelope,
        config: { ...(sample.envelope.config as Record<string, unknown>), __unmatched_broken: true },
        state: {},
      },
    });
    syncStoreForSSR();
    const outerWsHtml = renderToString(<SimulationWorkspace />);
    expect(outerWsHtml).toContain('id="ws-scene3d-unavailable-card"');
    expect(outerWsHtml).toContain('id="ws-dock"');
    expect(outerWsHtml).toContain('id="dock-prob-statement"');
    expect(outerWsHtml).toContain('id="dock-steps-ul"');
    expect(outerWsHtml).not.toContain('id="playback-pa-box"');
    expect(outerWsHtml).not.toContain('id="floating-toolbar-3d"');

    const fullAppHtml = renderToString(<App />);
    expect(fullAppHtml).toContain('id="ws-scene3d-unavailable-card"');
    expect(fullAppHtml).not.toContain('class="panel-controls"');

    // Mathematically contradictory Scene3D (`!mathVerification.valid`, `MINOR-R2-3`):
    // - Keeps `#ws-dock`, `#dock-prob-statement`, `<ul id="dock-steps-ul">`, and `#dock-trigger-badge` `"—"`
    // - Suppresses `#playback-pa-box` and `#floating-toolbar-3d`
    const chopSample = publicCatalog().find((s) => s.id === "thiet-dien-chop") ?? publicCatalog()[0]!;
    const contradictoryScene = structuredClone(
      (chopSample.envelope as unknown as { scene3d: Scene3D }).scene3d,
    );
    const secObj = contradictoryScene.objects.find((o) => o.type === "section")!;
    if (Array.isArray(secObj.polygon) && secObj.polygon.length >= 3) {
      secObj.polygon = [...secObj.polygon];
      secObj.polygon[0] = ["99", "88", "77"];
    }
    const contradictionHtml = renderToString(
      <AxoWorkspaceV62
        scene={contradictoryScene}
        de={chopSample.envelope.description}
        tieuDe="Bài toán kiểm thử mâu thuẫn hình học"
      />,
    );
    expect(contradictionHtml).toContain("data-math-contradiction");
    expect(contradictionHtml).toContain('id="ws-dock"');
    expect(contradictionHtml).toContain('id="dock-prob-statement"');
    expect(contradictionHtml).toContain('id="dock-steps-ul"');
    expect(contradictionHtml).toContain('<span class="dock-trigger-badge" id="dock-trigger-badge">—</span>');
    expect(contradictionHtml).not.toContain('id="playback-pa-box"');
    expect(contradictionHtml).not.toContain('id="floating-toolbar-3d"');
  });

  it("5. Condition-Based ErrorBoundary Pure State Machine (resetKey, HMR / Code Update Signal & Bounded Cap): recovers on verified code/route signal without infinite retry loops, including AppRoot", () => {
    expect(ErrorBoundary.getDerivedStateFromError()).toEqual({ hong: true });

    // `getDerivedStateFromProps` resets `hong`, `soLanThuLai`, and `hmrEpoch` when `resetKey` changes
    const resetPatch = ErrorBoundary.getDerivedStateFromProps(
      {
        mien: "scene3d-viewer",
        resetKey: "sample:cau-cat-mat-phang|0",
        fallback: () => null,
        children: null,
      },
      {
        hong: true,
        khoa: "sample:thiet-dien-chop|0",
        soLanThuLai: 1,
        hmrEpoch: 2,
      },
    );
    expect(resetPatch).toEqual({
      hong: false,
      khoa: "sample:cau-cat-mat-phang|0",
      soLanThuLai: 0,
      hmrEpoch: 0,
    });
    expect(
      ErrorBoundary.getDerivedStateFromProps(
        {
          mien: "scene3d-viewer",
          resetKey: "sample:cau-cat-mat-phang|0",
          fallback: () => null,
          children: null,
        },
        {
          hong: true,
          khoa: "sample:cau-cat-mat-phang|0",
          soLanThuLai: 1,
          hmrEpoch: 1,
        },
      ),
    ).toBeNull();

    const initialCrashedState = {
      hong: true,
      khoa: "/simulation/thiet-dien-chop",
      soLanThuLai: 0,
      hmrEpoch: 0,
    };
    const nextAfterHmr1 = ErrorBoundary.deriveRecoveryFromSignal(initialCrashedState, {
      kind: "hmr_update",
      isDocumentHidden: false,
    });
    expect(nextAfterHmr1).not.toBeNull();
    expect(nextAfterHmr1?.hong).toBe(false);

    const blockedWhenHidden = ErrorBoundary.deriveRecoveryFromSignal(initialCrashedState, {
      kind: "hmr_update",
      isDocumentHidden: true,
    });
    expect(blockedWhenHidden).toBeNull();

    let rollingState: ReturnType<typeof ErrorBoundary.deriveRecoveryFromSignal> = initialCrashedState;
    let autoRecoveries = 0;
    for (let i = 0; i < 6; i += 1) {
      const recovered = ErrorBoundary.deriveRecoveryFromSignal(rollingState!, {
        kind: "hmr_update",
        isDocumentHidden: false,
      });
      if (!recovered) break;
      autoRecoveries += 1;
      rollingState = { ...recovered, hong: true };
    }
    expect(autoRecoveries).toBeGreaterThanOrEqual(1);
    expect(autoRecoveries).toBeLessThanOrEqual(2);

    const rootHtml = renderToString(<AppRoot />);
    expect(rootHtml).not.toContain("Ứng dụng gặp lỗi hiển thị. Hãy tải lại trang.");
  });

  it("6. §5.3 Learner State Snapshot Preservation & Sub-Entity / Future-Step Selection Hygiene: preserves valid ::face:/::edge: sub-entities while blocking future-step & pending_step selections", () => {
    const storageMap = new Map<string, string>();
    const memStorage: Pick<Storage, "getItem" | "setItem" | "removeItem"> = {
      getItem: (k) => storageMap.get(k) ?? null,
      setItem: (k, v) => {
        storageMap.set(k, v);
      },
      removeItem: (k) => {
        storageMap.delete(k);
      },
    };

    saveLearnerRecoverySnapshot(
      {
        problemKey: "sample:thiet-dien-chop",
        stepIndex: 7,
        selectedId: "mp",
        dockCollapsed: true,
        mobileViewMode: "stage_expanded",
        display: {
          showShell: true,
          showVertexLabels: true,
          showPlane: false,
          showSection: true,
          showAxes: true,
          showDimensionLabels: true,
          showRightAngles: false,
          showDashedHidden: true,
          auxiliaryShown: true,
          gridShown: false,
          xray: true,
          shellOpacityPct: 24,
          planeOpacityPct: 16,
        },
        camera: {
          position: [6.5, -4.2, 5.1],
          target: [0, 0, 1.5],
        },
      },
      { storage: memStorage, nowMs: 1_000_000 },
    );

    const restored = loadLearnerRecoverySnapshot("sample:thiet-dien-chop", {
      storage: memStorage,
      nowMs: 1_005_000,
    });
    expect(restored).not.toBeNull();
    expect(restored?.stepIndex).toBe(7);
    expect(restored?.selectedId).toBe("mp");
    expect(restored?.dockCollapsed).toBe(true);
    expect(restored?.mobileViewMode).toBe("stage_expanded");
    expect(restored?.display.showPlane).toBe(false);
    expect(restored?.display.shellOpacityPct).toBe(24);
    expect(restored?.camera).toEqual({
      position: [6.5, -4.2, 5.1],
      target: [0, 0, 1.5],
    });

    expect(
      loadLearnerRecoverySnapshot("sample:cau-cat-mat-phang", {
        storage: memStorage,
        nowMs: 1_005_000,
      }),
    ).toBeNull();

    expect(
      loadLearnerRecoverySnapshot("sample:thiet-dien-chop", {
        storage: memStorage,
        nowMs: 1_000_000 + 1000 * 60 * 60 * 2,
      }),
    ).toBeNull();

    saveLearnerRecoverySnapshot(
      {
        problemKey: "sample:thiet-dien-chop",
        stepIndex: 3,
        selectedId: null,
        dockCollapsed: false,
        mobileViewMode: "dock_open",
        display: {
          showShell: true,
          showVertexLabels: true,
          showPlane: true,
          showSection: true,
          showAxes: false,
          showDimensionLabels: true,
          showRightAngles: true,
          showDashedHidden: true,
          auxiliaryShown: false,
          gridShown: true,
          xray: false,
          shellOpacityPct: 12,
          planeOpacityPct: 8,
        },
        camera: {
          position: [1, 1, 1],
          target: [1, 1, 1],
        },
      },
      { storage: memStorage, nowMs: 2_000_000 },
    );
    const sanitizedCam = loadLearnerRecoverySnapshot("sample:thiet-dien-chop", {
      storage: memStorage,
      nowMs: 2_000_100,
    });
    expect(sanitizedCam?.stepIndex).toBe(3);
    expect(sanitizedCam?.camera).toBeNull();

    // Future-step selectedId (`thiet_dien`, only created at final step) MUST NOT mount at step 0 (`MINOR-1`)
    const sample = publicCatalog().find((s) => s.id === "thiet-dien-chop") ?? publicCatalog()[0]!;
    const scene = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const step0Html = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialStep={0}
        initialSelectedId="thiet_dien"
      />,
    );
    expect(step0Html).not.toContain('data-context-object="thiet_dien"');

    // Valid synthesized sub-entity (`chop::face:0`) MUST be preserved at the final step (`MAJOR-R2-3`)!
    const subEntityHtml = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialSelectedId="chop::face:0"
      />,
    );
    expect(subEntityHtml).toContain('data-context-object="chop::face:0"');

    // Pending-step given quantity pill MUST render `disabled` and reject `initialSelectedId` at step 0 (`MAJOR-R2-3`)
    const pendingQtyScene: Scene3D = {
      free_objects: ["A", "B", "S", "q_sa_future"],
      objects: [
        { id: "A", type: "point3", label: "A", notation: "A", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "0"] },
        { id: "B", type: "point3", label: "B", notation: "B", origin: "free", render: "point_marker", depends: [], xyz: ["2", "0", "0"] },
        { id: "S", type: "point3", label: "S", notation: "S", origin: "free", render: "point_marker", depends: [], xyz: ["0", "0", "4"] },
        {
          id: "seg_ab",
          type: "segment3",
          label: "Cạnh AB",
          notation: "AB",
          origin: "derived",
          render: "segment",
          depends: ["A", "B"],
          endpoint_ids: ["A", "B"],
          point_a: ["0", "0", "0"],
          point_b: ["2", "0", "0"],
        },
        {
          id: "seg_sa",
          type: "segment3",
          label: "Cạnh bên SA",
          notation: "SA",
          origin: "derived",
          render: "segment",
          depends: ["S", "A"],
          endpoint_ids: ["S", "A"],
          point_a: ["0", "0", "4"],
          point_b: ["0", "0", "0"],
        },
        {
          id: "q_sa_future",
          type: "quantity",
          label: "Chiều cao SA",
          notation: "SA",
          origin: "free",
          render: "readout",
          depends: ["S", "A"],
          value: "4",
          source: { fact_id: "f_sa", provenance: "GIVEN", is_given: true },
          annotation: { kind: "length", category: "measurement", role: "given", anchor: "segment", subject_ids: ["S", "A"] },
        },
      ] as unknown as Scene3D["objects"],
      events: [
        { step_index: 0, action: "CREATE", object: "seg_ab", depends: ["A", "B"], explanation: "" },
        { step_index: 1, action: "CREATE", object: "seg_sa", depends: ["S", "A"], explanation: "" },
      ],
    };
    const pendingStep0Html = renderToString(
      <AxoWorkspaceV62
        scene={pendingQtyScene}
        de="Cho AB = 2, SA = 4."
        tieuDe="Kiểm thử dữ kiện chờ bước sau"
        initialStep={0}
        initialSelectedId="q_sa_future"
      />,
    );
    expect(pendingStep0Html).not.toContain('data-context-object="q_sa_future"');
    expect(pendingStep0Html).toMatch(
      /class="dock-given-param-pill"[^>]*data-given-param-id="q_sa_future"[^>]*data-given-param-status="pending_step"[^>]*disabled/,
    );

    memStorage.setItem(
      "axo:learner-recovery:v1",
      JSON.stringify({ schemaVersion: 999, problemKey: "sample:thiet-dien-chop", stepIndex: 2 }),
    );
    expect(
      loadLearnerRecoverySnapshot("sample:thiet-dien-chop", {
        storage: memStorage,
        nowMs: 2_000_200,
      }),
    ).toBeNull();
    memStorage.setItem("axo:learner-recovery:v1", "{corrupted_json");
    expect(
      loadLearnerRecoverySnapshot("sample:thiet-dien-chop", {
        storage: memStorage,
        nowMs: 2_000_200,
      }),
    ).toBeNull();
  });
});
