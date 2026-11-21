import path from "node:path";
import { fileURLToPath } from "node:url";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import esbuild from "esbuild";
import { chromium } from "playwright";
import { AxoWorkspaceV62 } from "../../../components/SimulationWorkspace";
import { ErrorBoundary } from "../../../components/ErrorBoundary";
import { publicCatalog } from "../../../data/offline-catalog";
import { useAppStore } from "../../../state/store";
import { hybridViewCua } from "./hybrid-preview-adapter";
import type { Scene3D } from "./scene3d-model";
import {
  classifySimulationError,
  ensureMutableSceneForAttachment,
  shouldOmitDockConstructionSteps,
} from "./simulation-error-classifier";

describe("Simulation Error Classification & Bounded Recovery (AXO Reliability)", () => {
  afterEach(() => {
    vi.useRealTimers();
    useAppStore.setState({
      active: null,
      activeSampleId: null,
      activeHistoryId: null,
      unsupported: null,
    });
  });

  it("classifies data errors as non-recoverable (omit Steps) and renderer faults as recoverable (preserve Steps)", () => {
    const schemaErr = classifySimulationError({ invalidSceneReason: "Điểm A thiếu tọa độ." });
    expect(schemaErr).toEqual({
      code: "SCENE_INVALID_SCHEMA",
      category: "invalid_scene_data",
      recoverable: false,
      omitConstructionSteps: true,
      suppressStageNavigationActions: true,
    });
    expect(shouldOmitDockConstructionSteps(schemaErr)).toBe(true);

    const mathErr = classifySimulationError({
      mathValid: false,
      contradictionId: "PLANE_NOT_UNIQUE",
    });
    expect(mathErr).toEqual({
      code: "PLANE_NOT_UNIQUE",
      category: "geometry_contradiction",
      recoverable: false,
      omitConstructionSteps: true,
      suppressStageNavigationActions: true,
    });
    expect(shouldOmitDockConstructionSteps(mathErr)).toBe(true);

    const webglErr = classifySimulationError({ webglPhase: "recovering", webglAttempt: 1 });
    expect(webglErr).toEqual({
      code: "WEBGL_CONTEXT_LOST",
      category: "renderer_runtime_failure",
      recoverable: true,
      omitConstructionSteps: false,
      suppressStageNavigationActions: true,
    });
    expect(shouldOmitDockConstructionSteps(webglErr)).toBe(false);

    const boundaryErr = classifySimulationError({ viewerBoundaryCrashed: true });
    expect(boundaryErr?.recoverable).toBe(true);
    expect(shouldOmitDockConstructionSteps(boundaryErr)).toBe(false);
    expect(classifySimulationError({})).toBeNull();
  });

  it("safely shallow-clones frozen Scene3D objects without throwing during workspace metadata attachment", () => {
    const sample = publicCatalog()[0]!;
    const rawScene = structuredClone(
      (sample.envelope as unknown as { scene3d: Scene3D }).scene3d,
    );
    const frozenScene = Object.freeze({ ...rawScene });
    expect(Object.isFrozen(frozenScene)).toBe(true);

    const cloned = ensureMutableSceneForAttachment(frozenScene);
    expect(cloned).not.toBe(frozenScene);
    expect(Object.isFrozen(cloned)).toBe(false);

    const html = renderToString(
      <AxoWorkspaceV62
        scene={frozenScene}
        de={sample.envelope.description}
        tieuDe={sample.envelope.title}
        hybrid={hybridViewCua(sample.envelope)}
      />,
    );
    expect(html).toContain('id="stage-3d-box"');
    expect(html).toContain('id="dock-steps-ul"');
    expect(html).not.toContain('id="ws-scene3d-unavailable-card"');
  });

  it("enforces bounded ErrorBoundary auto-retry cap, rapid error coalescing, resetKey guard, and unmount timer cleanup", () => {
    vi.useFakeTimers();
    const boundary = new ErrorBoundary({
      mien: "scene3d-viewer",
      resetKey: "sample:a|0",
      autoRetryMax: 2,
      autoRetryDelayMs: 180,
      fallback: () => null,
      children: null,
    });

    (boundary as unknown as { _mounted: boolean })._mounted = true;
    const setStateSpy = vi.fn((updater: unknown, cb?: () => void) => {
      const patch =
        typeof updater === "function"
          ? (updater as (s: typeof boundary.state) => Partial<typeof boundary.state>)(boundary.state)
          : (updater as Partial<typeof boundary.state>);
      boundary.state = { ...boundary.state, ...patch };
      cb?.();
    });
    boundary.setState = setStateSpy as typeof boundary.setState;
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    try {
      // Throw #1 + duplicate rapid catch while timer pending -> coalesced into 1 timer
      boundary.state = { hong: true, khoa: "sample:a|0", soLanThuLai: 0, hmrEpoch: 0 };
      boundary.componentDidCatch(new Error("Crash 1"), { componentStack: "" } as never);
      boundary.componentDidCatch(new Error("Crash 1 dup"), { componentStack: "" } as never);
      expect(boundary.render() || true).toBeTruthy();

      vi.advanceTimersByTime(180);
      expect(setStateSpy).toHaveBeenCalledTimes(1);
      expect(boundary.state.soLanThuLai).toBe(1);

      // Throw #2 -> retry #2 scheduled
      boundary.state = { ...boundary.state, hong: true };
      boundary.componentDidCatch(new Error("Crash 2"), { componentStack: "" } as never);
      vi.advanceTimersByTime(180);
      expect(setStateSpy).toHaveBeenCalledTimes(2);
      expect(boundary.state.soLanThuLai).toBe(2);

      // Throw #3 -> cap reached (soLanThuLai === 2 >= autoRetryMax), no further retry scheduled
      boundary.state = { ...boundary.state, hong: true };
      boundary.componentDidCatch(new Error("Crash 3"), { componentStack: "" } as never);
      vi.advanceTimersByTime(2000);
      expect(setStateSpy).toHaveBeenCalledTimes(2);

      // Tab/resetKey switch cancels pending timer before it fires
      boundary.state = { hong: true, khoa: "sample:b|0", soLanThuLai: 0, hmrEpoch: 0 };
      (boundary as { props: ErrorBoundary["props"] }).props = {
        ...boundary.props,
        resetKey: "sample:b|0",
      };
      boundary.componentDidCatch(new Error("Crash B"), { componentStack: "" } as never);
      (boundary as { props: ErrorBoundary["props"] }).props = {
        ...boundary.props,
        resetKey: "sample:c|0",
      };
      boundary.componentDidUpdate({ ...boundary.props, resetKey: "sample:b|0" });
      vi.advanceTimersByTime(500);
      expect(setStateSpy).toHaveBeenCalledTimes(2);

      // Unmount cancels pending timer cleanly
      boundary.state = { hong: true, khoa: "sample:c|0", soLanThuLai: 0, hmrEpoch: 0 };
      boundary.componentDidCatch(new Error("Crash C"), { componentStack: "" } as never);
      boundary.componentWillUnmount();
      vi.advanceTimersByTime(500);
      expect(setStateSpy).toHaveBeenCalledTimes(2);
    } finally {
      consoleSpy.mockRestore();
    }
  });

  it(
    "verifies real Chromium WebGL init retry, context loss/restore, cap, unmount/tab-switch cancellation, single RAF loop, and state preservation",
    async () => {
      const sampleA = publicCatalog()[0]!;
      const sampleB = publicCatalog()[1] ?? publicCatalog()[0]!;
      const sceneA = (sampleA.envelope as unknown as { scene3d: Scene3D }).scene3d;
      const sceneB = (sampleB.envelope as unknown as { scene3d: Scene3D }).scene3d;

      const bundled = await esbuild.build({
        stdin: {
          contents: `
            import React, { useState } from "react";
            import { flushSync } from "react-dom";
            import { createRoot } from "react-dom/client";
            import * as THREE from "three";
            import { AxoWorkspaceV62 } from "./components/SimulationWorkspace";
            import { setWebGLRendererFactoryForTest } from "./simulations/domains/geometry/scene3d-view";
            import { useAppStore } from "./state/store";

            const SCENE_A = ${JSON.stringify(sceneA)};
            const SCENE_B = ${JSON.stringify(sceneB)};
            const DESC_A = ${JSON.stringify(sampleA.envelope.description ?? "")};
            const TITLE_A = ${JSON.stringify(sampleA.envelope.title ?? "Sample A")};
            const DESC_B = ${JSON.stringify(sampleB.envelope.description ?? "")};
            const TITLE_B = ${JSON.stringify(sampleB.envelope.title ?? "Sample B")};

            const metrics = {
              initCalls: 0,
              disposeCalls: 0,
              activeRafCallbacks: 0,
              postUnmountCalls: 0,
            };
            window.__recoveryMetrics = metrics;

            const origRAF = window.requestAnimationFrame.bind(window);
            const pendingRafIds = new Set();
            window.requestAnimationFrame = (cb) => {
              const id = origRAF((ts) => {
                pendingRafIds.delete(id);
                metrics.activeRafCallbacks = pendingRafIds.size;
                cb(ts);
              });
              pendingRafIds.add(id);
              metrics.activeRafCallbacks = pendingRafIds.size;
              return id;
            };
            const origCancelRAF = window.cancelAnimationFrame.bind(window);
            window.cancelAnimationFrame = (id) => {
              pendingRafIds.delete(id);
              metrics.activeRafCallbacks = pendingRafIds.size;
              return origCancelRAF(id);
            };

            let mounted = false;
            window.__setFailInitCount = (count) => {
              let remaining = count;
              metrics.initCalls = 0;
              metrics.disposeCalls = 0;
              setWebGLRendererFactoryForTest(() => {
                metrics.initCalls += 1;
                if (!mounted) metrics.postUnmountCalls += 1;
                if (remaining > 0) {
                  remaining -= 1;
                  return null;
                }
                const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                const origDispose = renderer.dispose.bind(renderer);
                renderer.dispose = () => {
                  metrics.disposeCalls += 1;
                  origDispose();
                };
                return renderer;
              });
            };

            const host = document.createElement("div");
            host.id = "root";
            document.body.appendChild(host);
            const root = createRoot(host);

            let setSceneKey = null;
            function Harness({ initialKey }) {
              const [k, setK] = useState(initialKey);
              setSceneKey = setK;
              const isB = k === "B";
              return React.createElement(AxoWorkspaceV62, {
                scene: isB ? SCENE_B : SCENE_A,
                de: isB ? DESC_B : DESC_A,
                tieuDe: isB ? TITLE_B : TITLE_A,
              });
            }

            window.__mount = (key = "A") => {
              mounted = true;
              flushSync(() => {
                useAppStore.setState({ activeSampleId: key === "B" ? "b" : "a" });
                root.render(React.createElement(Harness, { initialKey: key }));
              });
            };
            window.__switchToB = () => {
              flushSync(() => {
                useAppStore.setState({ activeSampleId: "b" });
                setSceneKey?.("B");
              });
            };
            window.__unmount = () => {
              mounted = false;
              flushSync(() => {
                root.render(null);
              });
            };
          `,
          // This checkout's `frontend/src`, never a fixed path to another clone (it resolved the harness against
          // whatever that clone held, or failed when it had no node_modules).
          resolveDir: path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../.."),
          sourcefile: "recovery-browser-harness.tsx",
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
        const pageErrors: string[] = [];
        page.on("pageerror", (e) => pageErrors.push(e.message));
        await page.clock.install();
        await page.setContent("<!doctype html><html><body></body></html>");
        await page.addScriptTag({ content: bundled.outputFiles[0]!.text });

        // 1) Transient init failure (fails once -> recovers automatically on attempt #1, preserves step selected during outage)
        await page.evaluate(() => {
          const w = window as unknown as {
            __setFailInitCount: (n: number) => void;
            __mount: (k?: string) => void;
          };
          w.__setFailInitCount(1);
          w.__mount("A");
        });
        await page.waitForSelector('[data-viewer-recovery-phase="recovering"]', { timeout: 3000 });
        expect(await page.locator(".axo-viewer-recovery-retry").count()).toBe(0);

        // Learner changes step in #dock-steps-ul while renderer is recovering
        await page.evaluate(() => {
          const rows = document.querySelectorAll<HTMLElement>("#dock-steps-ul .step-row");
          if (rows.length > 1) rows[1]!.click();
        });
        await page.clock.fastForward(300);
        await page.waitForSelector(".geo3d-canvas canvas", { timeout: 3000 });
        expect(await page.locator('[data-viewer-recovery-phase]').count()).toBe(0);
        expect(await page.locator(".geo3d-canvas canvas").count()).toBe(1);
        expect(await page.locator("#dock-steps-counter").innerText()).toContain("Bước 2/");

        // Select an object and activate Xem quan he, then simulate real WebGL context lost + restored
        const selectedLabel = await page.evaluate(() => {
          const btn = document.querySelector<HTMLElement>(".dock-entity-chip");
          if (!btn) return "";
          const label = (btn.innerText || "").trim();
          btn.click();
          return label;
        });
        await page.evaluate(() => {
          const canvas = document.querySelector(".geo3d-canvas canvas");
          if (!canvas) throw new Error("Missing canvas");
          const ev = new Event("webglcontextlost", { cancelable: true });
          canvas.dispatchEvent(ev);
        });
        await page.waitForSelector('[data-viewer-recovery-phase="recovering"]', { timeout: 3000 });
        await page.evaluate(() => {
          const canvas = document.querySelector(".geo3d-canvas canvas");
          canvas?.dispatchEvent(new Event("webglcontextrestored"));
        });
        await page.clock.fastForward(150);
        expect(await page.locator('[data-viewer-recovery-phase]').count()).toBe(0);
        expect(await page.locator("#dock-steps-counter").innerText()).toContain("Bước 2/");
        if (selectedLabel) {
          expect(await page.locator("#dock-context-object-mount").innerText()).toContain(selectedLabel);
        }

        // Single animation loop / no duplicate RAF leak check
        const loopCountAfterRestore = await page.evaluate(
          () => (window as unknown as { __recoveryMetrics: { activeRafCallbacks: number } }).__recoveryMetrics.activeRafCallbacks,
        );
        expect(loopCountAfterRestore).toBeLessThanOrEqual(2);

        // 2) Persistent init failure -> capped at initial + 2 retries (total 3 initCalls), settles cleanly at "failed" without retry button
        await page.evaluate(() => {
          const w = window as unknown as {
            __unmount: () => void;
            __setFailInitCount: (n: number) => void;
            __mount: (k?: string) => void;
          };
          w.__unmount();
          w.__setFailInitCount(99);
          w.__mount("A");
        });
        await page.clock.fastForward(1200);
        await page.waitForSelector('[data-viewer-recovery-phase="failed"]', { timeout: 3000 });
        expect(await page.locator(".axo-viewer-recovery-retry").count()).toBe(0);
        const initCallsWhenCapped = await page.evaluate(
          () => (window as unknown as { __recoveryMetrics: { initCalls: number } }).__recoveryMetrics.initCalls,
        );
        expect(initCallsWhenCapped).toBe(3);

        // 3) Tab / scene switch mid-retry cancels old timer and succeeds cleanly on scene B
        await page.evaluate(() => {
          const w = window as unknown as {
            __unmount: () => void;
            __setFailInitCount: (n: number) => void;
            __mount: (k?: string) => void;
            __switchToB: () => void;
          };
          w.__unmount();
          w.__setFailInitCount(1);
          w.__mount("A");
          w.__switchToB();
        });
        await page.clock.fastForward(400);
        await page.waitForSelector(".geo3d-canvas canvas", { timeout: 3000 });

        // 4) Unmount during pending retry -> zero post-unmount retries, disposes cleanly
        await page.evaluate(() => {
          const w = window as unknown as {
            __unmount: () => void;
            __setFailInitCount: (n: number) => void;
            __mount: (k?: string) => void;
          };
          w.__unmount();
          w.__setFailInitCount(1);
          w.__mount("A");
          w.__unmount();
        });
        await page.clock.fastForward(1000);
        const finalMetrics = await page.evaluate(
          () =>
            (
              window as unknown as {
                __recoveryMetrics: { postUnmountCalls: number };
              }
            ).__recoveryMetrics,
        );
        expect(finalMetrics.postUnmountCalls).toBe(0);
        expect(pageErrors).toEqual([]);
      } finally {
        await browser.close();
      }
    },
    25_000,
  );
});
