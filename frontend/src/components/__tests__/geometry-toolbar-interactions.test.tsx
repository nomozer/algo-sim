import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import esbuild from "esbuild";
import { chromium } from "playwright";
import { renderToString } from "react-dom/server";
import * as THREE from "three";
import { afterEach, describe, expect, it } from "vitest";
import { publicCatalog } from "../../data/offline-catalog";
import { dongBoNetDayManHinh } from "../../simulations/domains/geometry/scene3d-edge-visibility";
import type { Scene3D } from "../../simulations/domains/geometry/scene3d-model";
import { useAppStore } from "../../state/store";
import { AxoWorkspaceV62 } from "../SimulationWorkspace";

const globalCss = readFileSync(resolve(__dirname, "../../styles/global.css"), "utf8");

describe("Geometry Toolbar Interactions & X-Ray Rendering (AXO V9.4.20)", () => {
  afterEach(() => {
    useAppStore.setState({
      active: null,
      activeSampleId: null,
      activeHistoryId: null,
      unsupported: null,
    });
  });

  it("wires dongBoNetDayManHinh xray option while preserving dashed hidden edges and xray=false parity", () => {
    const geom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(2, 0, 0),
    ]);
    const hiddenMat = new THREE.LineDashedMaterial({
      color: 0x374151,
      dashSize: 0.14,
      gapSize: 0.1,
      transparent: true,
      opacity: 0.56,
      depthTest: true,
    });
    const hiddenLine = new THREE.Line(geom, hiddenMat);
    hiddenLine.name = "edge:SA:khuat";
    hiddenLine.userData.hidden = true;
    hiddenLine.computeLineDistances();

    const root = new THREE.Group();
    root.add(hiddenLine);

    const fatOff = new THREE.Group();
    dongBoNetDayManHinh([root], fatOff, 800, 600, false, 0, 1, false);
    expect(fatOff.children.filter((c) => c.visible)).toHaveLength(0);
    expect((fatOff.userData.pools as Map<unknown, unknown> | undefined)?.size ?? 0).toBe(0);

    const fatDefault = new THREE.Group();
    dongBoNetDayManHinh([root], fatDefault, 800, 600, true, 0, 1, false);
    const poolDefault = fatDefault.userData.pools as Map<number, { material: THREE.Material & { depthTest: boolean; opacity: number; dashed: boolean } }[]>;
    const matDefault = poolDefault.get(2)![0]!.material;
    expect(matDefault.depthTest).toBe(true);
    expect(matDefault.opacity).toBeCloseTo(0.56, 3);
    expect(matDefault.dashed).toBe(true);

    const fatXray = new THREE.Group();
    const summaryXray = dongBoNetDayManHinh([root], fatXray, 800, 600, false, 0, 1, true);
    expect(summaryXray.totalLines).toBe(1);
    const poolXray = fatXray.userData.pools as Map<number, { material: THREE.Material & { depthTest: boolean; opacity: number; dashed: boolean } }[]>;
    const matXray = poolXray.get(2)![0]!.material;
    expect(matXray.depthTest).toBe(false);
    expect(matXray.opacity).toBeGreaterThanOrEqual(0.85);
    expect(matXray.dashed).toBe(true);
  });

  it("renders clean toolbar icons, renamed Geo Custom copy, and removes dead Kernel-locked sliders", () => {
    const sample = publicCatalog().find((s) => s.id === "thiet-dien-chop") ?? publicCatalog()[0]!;
    const scene = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;
    const html = renderToString(
      <AxoWorkspaceV62
        scene={scene}
        de={sample.envelope.description}
        tieuDe={sample.title}
        initialGeoCustomOpen={true}
      />,
    );

    expect(html).not.toContain('fill="#FFF"');
    expect(html).toContain('fill="var(--surface, #ffffff)"');
    expect(html).toContain('title="Độ đậm vỏ khối &amp; mặt phẳng"');
    expect(html).toContain('data-tooltip="Độ đậm khối &amp; mặt"');
    expect(html).toContain("<span>Độ đậm khối &amp; mặt</span>");
    expect(html).toContain('<polygon points="12 3 21 8 12 13 3 8 12 3"');
    expect(html).toContain('id="slider-shell-opacity"');
    expect(html).toContain('id="slider-plane-opacity"');
    expect(html).toContain('id="btn-reset-geo-custom"');
    expect(html).not.toContain('id="geo-custom-experiment-group"');
    expect(html).not.toContain('id="slider-sphere-radius"');
    expect(html).not.toContain('id="slider-plane-height"');
    expect(html).not.toContain('id="geo-custom-kernel-note"');
  });

  it(
    "verifies real Chromium toolbar interactions: Eye xray pixels at Step 0 and final step, reset-view preserving selection & relations, display popover, and collapse/expand",
    async () => {
      const sample = publicCatalog().find((s) => s.id === "thiet-dien-chop") ?? publicCatalog()[0]!;
      const scene = (sample.envelope as unknown as { scene3d: Scene3D }).scene3d;

      const bundled = await esbuild.build({
        stdin: {
          contents: `
            import React from "react";
            import { createRoot } from "react-dom/client";
            import { AxoWorkspaceV62 } from "./SimulationWorkspace";
            import { useAppStore } from "../state/store";

            const SCENE = ${JSON.stringify(scene)};
            const DESC = ${JSON.stringify(sample.envelope.description ?? "")};
            const TITLE = ${JSON.stringify(sample.title)};

            useAppStore.setState({ activeSampleId: ${JSON.stringify(sample.id)} });
            const host = document.createElement("div");
            host.id = "app-shell";
            host.style.width = "1280px";
            host.style.height = "800px";
            host.style.display = "flex";
            document.body.appendChild(host);
            createRoot(host).render(
              React.createElement(AxoWorkspaceV62, {
                scene: SCENE,
                de: DESC,
                tieuDe: TITLE,
              }),
            );
          `,
          resolveDir: resolve(__dirname, ".."),
          sourcefile: "toolbar-browser-harness.tsx",
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
        await page.setContent("<!doctype html><html><body style='margin:0'></body></html>");
        await page.addStyleTag({ content: globalCss });
        await page.addScriptTag({ content: bundled.outputFiles[0]!.text });

        await page.waitForSelector(".geo3d-canvas canvas", { timeout: 5000 });
        await page.waitForTimeout(250);

        const canvasBox = page.locator(".geo3d-canvas");

        // Jump to Step 0 and verify Eye (#btn-xray) produces real WebGL pixel delta + preserves dashed hidden edges
        await page.locator("#dock-steps-ul .step-row[data-step='0']").click();
        await page.waitForTimeout(220);
        const step0OffPng = await canvasBox.screenshot();

        await page.locator("#btn-xray").click();
        await page.waitForFunction(() => (window as unknown as { __geo3d_xray_active?: boolean }).__geo3d_xray_active === true);
        await page.waitForTimeout(220);
        expect(await page.locator("#btn-xray").getAttribute("aria-pressed")).toBe("true");
        expect(await page.locator("#p-dot-xray.is-on").count()).toBe(1);
        const step0OnPng = await canvasBox.screenshot();
        expect(Buffer.compare(step0OffPng, step0OnPng)).not.toBe(0);

        // Turn Eye back off before final step comparison
        await page.locator("#btn-xray").click();
        await page.waitForFunction(() => (window as unknown as { __geo3d_xray_active?: boolean }).__geo3d_xray_active === false);

        // Jump to final step and verify Eye (#btn-xray) produces real pixel delta while keeping dashed signature
        await page.locator("#dock-steps-ul .step-row").last().click();
        await page.waitForTimeout(220);
        const finalOffPng = await canvasBox.screenshot();

        await page.locator("#btn-xray").click();
        await page.waitForFunction(() => (window as unknown as { __geo3d_xray_active?: boolean }).__geo3d_xray_active === true);
        await page.waitForTimeout(220);
        const finalOnPng = await canvasBox.screenshot();
        expect(Buffer.compare(finalOffPng, finalOnPng)).not.toBe(0);
        const hasDashSignature = await page.evaluate(() => {
          const sig = (window as unknown as { __geo3d_edge_dash_signature?: Record<string, string[]> }).__geo3d_edge_dash_signature;
          if (!sig || typeof sig !== "object") return false;
          const allTokens = Object.values(sig).flat();
          return allTokens.includes("HIDDEN_DASHED") && allTokens.includes("VISIBLE_SOLID");
        });
        expect(hasDashSignature).toBe(true);

        // Select an entity and toggle Xem quan he, then click #btn-reset-view -> selection + relation stay intact
        await page.locator(".dock-entity-chip").first().click();
        await page.waitForTimeout(120);
        const selectedBeforeReset = await page.evaluate(
          () => (window as unknown as { __geo3d_selected_id?: string | null }).__geo3d_selected_id ?? null,
        );
        expect(selectedBeforeReset).not.toBeNull();
        const relBtn = page.locator('[data-context-action="relations"]');
        if ((await relBtn.count()) > 0) {
          await relBtn.click();
          await page.waitForTimeout(100);
          expect(await relBtn.getAttribute("aria-pressed")).toBe("true");
        }

        await page.locator("#btn-reset-pos").click();
        await page.waitForTimeout(180);
        const selectedAfterReset = await page.evaluate(
          () => (window as unknown as { __geo3d_selected_id?: string | null }).__geo3d_selected_id ?? null,
        );
        expect(selectedAfterReset).toBe(selectedBeforeReset);
        if ((await relBtn.count()) > 0) {
          expect(await relBtn.getAttribute("aria-pressed")).toBe("true");
        }

        // Open #btn-display-pop, toggle #chk-axes & #chk-shell, then reset display opts
        await page.locator("#btn-display-pop").click();
        expect(await page.locator("#tb-display-pop.is-open").count()).toBe(1);
        const axesBefore = await page.evaluate(
          () => (window as unknown as { __geo3d_axes_visible?: boolean }).__geo3d_axes_visible,
        );
        await page.locator("#chk-axes").click();
        await page.waitForTimeout(120);
        const axesAfter = await page.evaluate(
          () => (window as unknown as { __geo3d_axes_visible?: boolean }).__geo3d_axes_visible,
        );
        expect(axesAfter).not.toBe(axesBefore);

        await page.locator("#chk-shell").click();
        await page.waitForTimeout(100);
        expect(await page.evaluate(() => (window as unknown as { __geo3d_shell_visible?: boolean }).__geo3d_shell_visible)).toBe(false);
        await page.locator("#btn-reset-display-opts").click();
        await page.waitForTimeout(120);
        expect(await page.evaluate(() => (window as unknown as { __geo3d_shell_visible?: boolean }).__geo3d_shell_visible)).toBe(true);
        expect(await page.evaluate(() => (window as unknown as { __geo3d_axes_visible?: boolean }).__geo3d_axes_visible)).toBe(axesBefore);

        // Toggle #btn-geo-custom-pop -> change sliders -> reset -> verify zero disabled sliders
        await page.locator("#btn-geo-custom-pop").click();
        expect(await page.locator("#tb-geo-custom-pop.open").count()).toBe(1);
        expect(await page.locator("#tb-geo-custom-pop input[disabled]").count()).toBe(0);
        await page.locator("#slider-shell-opacity").fill("24");
        await page.waitForTimeout(80);
        expect(await page.locator("#val-shell-opacity").innerText()).toBe("24%");
        await page.locator("#btn-reset-geo-custom").click();
        expect(await page.locator("#val-shell-opacity").innerText()).toBe("12%");

        // Collapse & expand floating toolbar
        await page.locator("#btn-tb-collapse").click();
        expect(await page.locator("#toolbar-3d-collapsed.is-visible").count()).toBe(1);
        await page.locator("#btn-tb-expand").click();
        expect(await page.locator("#toolbar-3d-collapsed.is-visible").count()).toBe(0);

        expect(pageErrors).toEqual([]);
      } finally {
        await browser.close();
      }
    },
    45_000,
  );
});
