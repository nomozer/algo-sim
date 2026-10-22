import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const runDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(runDir, '../../../../..');
const frontDir = join(repoRoot, 'frontend');
const stage = process.argv[2] ?? 'before';
const outDir = join(runDir, stage);
mkdirSync(outDir, { recursive: true });

const { build } = await import(pathToFileURL(join(frontDir, 'node_modules/vite/dist/node/index.js')));
const { default: react } = await import(pathToFileURL(join(frontDir, 'node_modules/@vitejs/plugin-react/dist/index.js')));
const { chromium } = await import(pathToFileURL(join(frontDir, 'node_modules/playwright/index.mjs')));

const htmlPath = join(frontDir, 'scripts/_framing_audit.html');
const tsxPath = join(frontDir, 'scripts/_framing_audit.tsx');
const distDir = join(repoRoot, '.superpowers/framing-browser', stage);

writeFileSync(
  htmlPath,
  '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><div id="root"></div><script type="module" src="./_framing_audit.tsx"></script></body></html>',
);

writeFileSync(
  tsxPath,
  `
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as THREE from 'three';
import { Scene3DExplorer } from '../src/simulations/domains/geometry/Scene3DExplorer';
import { UnsupportedNotice, SimulationWorkspace } from '../src/components/SimulationWorkspace';
import { useAppStore } from '../src/state/store';
import { registerSemanticDomain } from '../src/simulations/domains/semantic';
import { buildObject3D } from '../src/simulations/domains/geometry/scene3d-view';
import { phanTichToanHocCuaCanh } from '../src/simulations/domains/geometry/scene3d-model';
import rows from '../../docs/evaluation/geometry/runs/${stage === "before" ? "simulation-visual-consistency-learning-ux" : "geometric-visual-correctness-framing"}/demos/audit_scenes.json';
import '../src/styles/global.css';

const w = window as any;
registerSemanticDomain();
w.rows = rows;
w.THREE = THREE;
w.buildObject3D = buildObject3D;

w.depthProbe = (xray = false) => {
  const results: any[] = [];
  for (const row of rows.filter((r: any) => r.served)) {
    for (const o of (row as any).scene.objects.filter((o: any) =>
      o.surface_role === 'SECTION_REGION' ||
      o.type === 'section' ||
      (o.render === 'polygon' && o.surface_role === 'AUXILIARY_SURFACE')
    )) {
      const built = buildObject3D(o, false, undefined, undefined, undefined, undefined, undefined, xray);
      if (!built) continue;
      built.updateMatrixWorld(true);
      let fill: any;
      built.traverse((n: any) => {
        if (/^(section_fill|polygon_fill):/.test(n.name)) fill = n;
      });
      if (!fill) continue;
      const mesh = new THREE.Mesh(fill.geometry.clone(), fill.material.clone());
      mesh.applyMatrix4(fill.matrixWorld);
      mesh.renderOrder = fill.renderOrder;
      const box = new THREE.Box3().setFromObject(mesh);
      const center = box.getCenter(new THREE.Vector3());
      const size = Math.max(box.getSize(new THREE.Vector3()).length(), 1);
      const positions = mesh.geometry.getAttribute('position');
      let normal = new THREE.Vector3();
      const rayTarget = center.clone();
      const index = mesh.geometry.getIndex();
      const count = index ? index.count : positions.count;
      const vertex = (i: number) =>
        new THREE.Vector3().fromBufferAttribute(positions, index ? index.getX(i) : i).applyMatrix4(mesh.matrix);
      for (let i = 0; i + 2 < count; i += 3) {
        const a = vertex(i), b = vertex(i + 1), c = vertex(i + 2);
        normal.crossVectors(b.clone().sub(a), c.clone().sub(a));
        if (normal.lengthSq() > 1e-8) {
          normal.normalize();
          rayTarget.copy(a).add(b).add(c).multiplyScalar(1 / 3);
          break;
        }
      }
      if (!normal.lengthSq()) continue;
      const scene = new THREE.Scene();
      scene.background = new THREE.Color('white');
      scene.add(new THREE.AmbientLight(0xffffff, 3));
      scene.add(mesh);
      const wall = new THREE.Mesh(
        new THREE.PlaneGeometry(size * 2, size * 2),
        new THREE.MeshBasicMaterial({ color: 0x647a96, side: THREE.DoubleSide }),
      );
      wall.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      wall.position.copy(rayTarget).addScaledVector(normal, size * 0.2);
      scene.add(wall);
      scene.updateMatrixWorld(true);
      const renderer = new THREE.WebGLRenderer({ preserveDrawingBuffer: true });
      renderer.setSize(96, 96);
      const camera = new THREE.PerspectiveCamera(40, 1, 0.01, size * 20);
      const samples: any[] = [];
      for (const side of [1, -1]) {
        camera.position.copy(rayTarget).addScaledVector(normal, size * side * 2);
        camera.up.set(Math.abs(normal.y) > 0.9 ? 1 : 0, Math.abs(normal.y) > 0.9 ? 0 : 1, 0);
        camera.lookAt(rayTarget);
        camera.updateMatrixWorld();
        const ray = new THREE.Raycaster(camera.position, rayTarget.clone().sub(camera.position).normalize());
        const hits = ray.intersectObjects([wall, mesh]);
        const firstHit = hits[0]?.object === wall ? 'opaque_wall' : 'section';
        const pixels = () => {
          renderer.render(scene, camera);
          const p = new Uint8Array(96 * 96 * 4);
          renderer.getContext().readPixels(0, 0, 96, 96, renderer.getContext().RGBA, renderer.getContext().UNSIGNED_BYTE, p);
          return p;
        };
        mesh.visible = true;
        const on = pixels();
        mesh.visible = false;
        const off = pixels();
        mesh.visible = true;
        let changed = 0;
        for (let i = 0; i < on.length; i += 4) {
          if (Math.abs(on[i] - off[i]) + Math.abs(on[i + 1] - off[i + 1]) + Math.abs(on[i + 2] - off[i + 2]) > 8) {
            changed++;
          }
        }
        samples.push({
          side,
          firstHit,
          changed,
          pass: xray && !mesh.material.depthTest ? changed > 0 : firstHit === 'opaque_wall' ? changed === 0 : changed > 0,
        });
      }
      results.push({
        family: row.id,
        id: o.id,
        depthTest: mesh.material.depthTest,
        depthFunc: mesh.material.depthFunc,
        depthWrite: mesh.material.depthWrite,
        renderOrder: mesh.renderOrder,
        samples,
      });
      renderer.dispose();
      renderer.forceContextLoss();
      mesh.geometry.dispose();
      mesh.material.dispose();
      wall.geometry.dispose();
      wall.material.dispose();
    }
  }
  return results;
};

w.measureSceneScreenBounds = (rowIndex: number) => {
  const row = rows[rowIndex] as any;
  const canvasEl = document.querySelector('.geo3d-canvas canvas') as HTMLCanvasElement | null;
  if (!canvasEl || !row?.scene) return null;
  const cRect = canvasEl.getBoundingClientRect();
  const snap = w.__geo3d_camera_snapshot;
  if (!snap) return null;

  const viewMat = new THREE.Matrix4().fromArray(snap.view_matrix_column_major);
  const projMat = new THREE.Matrix4().fromArray(snap.projection_matrix_column_major);
  const vpMat = new THREE.Matrix4().multiplyMatrices(projMat, viewMat);

  const projectPoint = (pt: number[]) => {
    const v = new THREE.Vector3(pt[0], pt[1], pt[2]).applyMatrix4(vpMat);
    return {
      x: ((v.x + 1) / 2) * cRect.width,
      y: ((1 - v.y) / 2) * cRect.height,
      z: v.z,
    };
  };

  const makeBox = () => ({ minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity, count: 0 });
  const addPt = (b: any, x: number, y: number) => {
    if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    b.minX = Math.min(b.minX, x);
    b.minY = Math.min(b.minY, y);
    b.maxX = Math.max(b.maxX, x);
    b.maxY = Math.max(b.maxY, y);
    b.count++;
  };
  const finalizeBox = (b: any) =>
    b.count > 0
      ? {
          x: Math.round(b.minX * 10) / 10,
          y: Math.round(b.minY * 10) / 10,
          w: Math.round((b.maxX - b.minX) * 10) / 10,
          h: Math.round((b.maxY - b.minY) * 10) / 10,
          maxX: Math.round(b.maxX * 10) / 10,
          maxY: Math.round(b.maxY * 10) / 10,
        }
      : null;

  const geoBox = makeBox();
  const secBox = makeBox();
  const renderedIds = new Set<string>(
    (w.__geo3d_rendered_object_ids || []).map((id: string) => id.split('#')[0]),
  );

  for (const o of row.scene.objects) {
    if (!renderedIds.has(o.id) && o.type !== 'point3') continue;
    if (o.type === 'plane3' || o.type === 'line3') continue;
    const isSec =
      o.type === 'section' ||
      o.surface_role === 'SECTION_REGION' ||
      (o.render === 'polygon' && o.surface_role === 'AUXILIARY_SURFACE');
    const sample3D: number[][] = [];
    if (o.xyz) sample3D.push(o.xyz);
    if (o.points) sample3D.push(...o.points);
    if (o.vertices) sample3D.push(...o.vertices);
    if (o.polygon) sample3D.push(...o.polygon);
    const built = o.type === 'point3' ? null : buildObject3D(o, false);
    if (built) {
      built.updateMatrixWorld(true);
      built.traverse((node: any) => {
        if (node.name === 'pick-proxy' || node.userData?.dauDinh || node.userData?.vungBam) return;
        const pos = node.geometry?.getAttribute?.('position');
        if (!pos) return;
        const step = Math.max(1, Math.floor(pos.count / 96));
        const v = new THREE.Vector3();
        for (let i = 0; i < pos.count; i += step) {
          v.fromBufferAttribute(pos, i).applyMatrix4(node.matrixWorld);
          if (Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z)) {
            sample3D.push([v.x, v.y, v.z]);
          }
        }
      });
    }
    for (const p of sample3D) {
      const sp = projectPoint(p);
      addPt(geoBox, sp.x, sp.y);
      if (isSec) addPt(secBox, sp.x, sp.y);
    }
  }

  const labelBox = makeBox();
  const ptBoxes = w.__geo3d_point_label_boxes || [];
  const plBoxes = w.__geo3d_plane_label_boxes || [];
  const annBoxes = w.__geo3d_annotation_boxes || [];
  for (const lb of [...ptBoxes, ...plBoxes.map((x: any) => x.box), ...annBoxes.map((x: any) => x.box)]) {
    if (!lb) continue;
    addPt(labelBox, lb.x, lb.y);
    addPt(labelBox, lb.x + lb.w, lb.y + lb.h);
  }

  const combinedBox = makeBox();
  for (const b of [geoBox, labelBox]) {
    if (b.count > 0) {
      addPt(combinedBox, b.minX, b.minY);
      addPt(combinedBox, b.maxX, b.maxY);
    }
  }

  const overlays: any[] = [];
  for (const sel of ['.geo3d-noi', '#geo3d-bang-phan-tich', '.geo3d-soi', '.geo3d-ngan', '.geo3d-buoc-hop']) {
    for (const el of Array.from(document.querySelectorAll(sel))) {
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) continue;
      overlays.push({
        selector: sel,
        x: Math.round((r.left - cRect.left) * 10) / 10,
        y: Math.round((r.top - cRect.top) * 10) / 10,
        w: Math.round(r.width * 10) / 10,
        h: Math.round(r.height * 10) / 10,
      });
    }
  }

  // Safe viewport inside canvas excluding right-side open panels and left floating controls
  let safeLeft = 16;
  let safeRight = cRect.width - 16;
  let safeTop = 16;
  let safeBottom = cRect.height - 16;
  for (const ov of overlays) {
    if (ov.selector === '#geo3d-bang-phan-tich' || ov.selector === '.geo3d-ngan' || ov.selector === '.geo3d-soi') {
      if (ov.x > cRect.width * 0.35) {
        safeRight = Math.min(safeRight, ov.x - 12);
      }
    }
  }
  const safeViewport = {
    x: Math.round(safeLeft * 10) / 10,
    y: Math.round(safeTop * 10) / 10,
    w: Math.round(Math.max(1, safeRight - safeLeft) * 10) / 10,
    h: Math.round(Math.max(1, safeBottom - safeTop) * 10) / 10,
  };

  const gFinal = finalizeBox(geoBox);
  const lFinal = finalizeBox(labelBox);
  const cFinal = finalizeBox(combinedBox);
  const sFinal = finalizeBox(secBox);

  const panelOv = overlays.find((o) => o.selector === '#geo3d-bang-phan-tich');
  let panelOverlapPx = 0;
  if (panelOv && cFinal) {
    const ox = Math.max(0, Math.min(cFinal.maxX, panelOv.x + panelOv.w) - Math.max(cFinal.x, panelOv.x));
    const oy = Math.max(0, Math.min(cFinal.maxY, panelOv.y + panelOv.h) - Math.max(cFinal.y, panelOv.y));
    panelOverlapPx = Math.round(ox * oy);
  }

  return {
    canvas: { w: Math.round(cRect.width), h: Math.round(cRect.height) },
    safeViewport,
    geometryBounds: gFinal,
    labelBounds: lFinal,
    combinedBounds: cFinal,
    sectionBounds: sFinal,
    overlays,
    metrics: gFinal && cFinal ? {
      geometryHeightRatioCanvas: Number((gFinal.h / cRect.height).toFixed(3)),
      geometryHeightRatioSafe: Number((gFinal.h / safeViewport.h).toFixed(3)),
      combinedHeightRatioCanvas: Number((cFinal.h / cRect.height).toFixed(3)),
      combinedHeightRatioSafe: Number((cFinal.h / safeViewport.h).toFixed(3)),
      geometryWidthRatioSafe: Number((gFinal.w / safeViewport.w).toFixed(3)),
      combinedWidthRatioSafe: Number((cFinal.w / safeViewport.w).toFixed(3)),
      topMarginPx: Number(cFinal.y.toFixed(1)),
      bottomMarginPx: Number((cRect.height - cFinal.maxY).toFixed(1)),
      leftMarginPx: Number(cFinal.x.toFixed(1)),
      rightMarginSafePx: Number((safeLeft + safeViewport.w - cFinal.maxX).toFixed(1)),
      panelOverlapPx,
    } : null,
    pointLabelsText: Array.from(document.querySelectorAll('.geo3d-label'))
      .filter((el: any) => el.style.opacity !== '0')
      .map((el: any) => el.textContent?.trim()),
    titleText: document.querySelector('.geo3d-ten-bai')?.textContent?.trim() ?? null,
    guidanceStepText: document.querySelector('[data-guidance-step]')?.textContent?.trim() ?? null,
    guidanceHintText: document.querySelector('[data-guidance-hint]')?.textContent?.trim() ?? null,
  };
};

function App() {
  const [index, setIndex] = useState(0);
  const [actual, setActual] = useState(false);
  w.openRow = (i: number, real = false) => {
    const row = rows[i] as any;
    useAppStore.setState(
      row.served
        ? ({
            unsupported: null,
            active: {
              moduleId: 'generic.semantic_program',
              envelope: { title: row.category, description: row.problem_text, scene3d: row.scene },
            },
          } as any)
        : {
            active: null,
            unsupported: {
              reason: row.reason,
              error_code: row.code,
              failure_category: 'postcondition_violated',
              refusal_cause: 'SOURCE',
              stage_reached: 'verification',
            },
          },
    );
    setActual(real);
    setIndex(i);
  };
  const row = rows[index] as any;
  w.analysis = row.scene ? phanTichToanHocCuaCanh(row.scene, null, row.route_d) : null;
  return actual ? (
    <SimulationWorkspace key={'actual' + index} />
  ) : row.served ? (
    <Scene3DExplorer key={index} scene={row.scene} de={row.problem_text} tieuDe={row.category} routeDSimulation={row.route_d} />
  ) : (
    <UnsupportedNotice
      unsupported={{
        reason: row.reason,
        error_code: row.code,
        failure_category: 'postcondition_violated',
        refusal_cause: 'SOURCE',
        stage_reached: 'verification',
      }}
    />
  );
}
createRoot(document.getElementById('root')!).render(<App />);
`,
);

try {
  await build({
    root: frontDir,
    configFile: false,
    plugins: [react()],
    logLevel: 'error',
    build: { outDir: distDir, emptyOutDir: true, rollupOptions: { input: htmlPath } },
  });
} finally {
  if (existsSync(htmlPath)) unlinkSync(htmlPath);
  if (existsSync(tsxPath)) unlinkSync(tsxPath);
}

const browser = await chromium.launch({
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});
const measurements = {
  stage,
  environment: 'Chromium SwiftShader WebGL; offline fixtures; 0 live provider calls',
  errors: [],
  depth: [],
  xrayDepth: [],
  scenes: [],
  multiViewport: [],
};

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on('pageerror', (e) => measurements.errors.push(String(e)));
  await page.route('http://framing.local/**', (route) => {
    const file = join(distDir, new URL(route.request().url()).pathname);
    return route.fulfill({
      status: existsSync(file) ? 200 : 404,
      contentType: file.endsWith('.js')
        ? 'application/javascript'
        : file.endsWith('.css')
          ? 'text/css'
          : 'text/html',
      body: existsSync(file) ? readFileSync(file) : 'missing',
    });
  });
  await page.goto('http://framing.local/scripts/_framing_audit.html');
  await page.waitForFunction(() => window.openRow);

  measurements.depth = await page.evaluate(() => window.depthProbe(false));
  measurements.xrayDepth = await page.evaluate(() => window.depthProbe(true));

  const ids = await page.evaluate(() => window.rows.map((r) => r.id));
  const mandatory = /family01_|family05_|family07_|family09_|family10_|family11_|family12_|family13_/;

  for (let i = 0; i < ids.length; i++) {
    if (!mandatory.test(ids[i])) continue;
    console.log(`[${stage}] auditing ${ids[i]}`);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.evaluate((idx) => window.openRow(idx, false), i);
    await page.waitForTimeout(500);

    if (ids[i].includes('family13')) {
      await page.screenshot({ path: join(outDir, `${ids[i]}.png`) });
      measurements.scenes.push({
        id: ids[i],
        refusalText: await page.locator('#root').innerText(),
      });
      continue;
    }

    await page.locator('.geo3d-canvas canvas').waitFor();
    const entryBounds = await page.evaluate((idx) => window.measureSceneScreenBounds(idx), i);
    await page.screenshot({ path: join(outDir, `${ids[i]}-entry.png`) });

    const previewBtn = page.getByRole('button', { name: 'Xem mô hình đầy đủ', exact: true });
    if (await previewBtn.count()) await previewBtn.click();
    await page.waitForTimeout(280);

    const completeBounds = await page.evaluate((idx) => window.measureSceneScreenBounds(idx), i);
    const defaultCamera = await page.evaluate(() => window.__geo3d_camera_snapshot.position);
    await page.screenshot({ path: join(outDir, `${ids[i]}-complete.png`) });

    // Open Math Analysis panel
    await page.locator('[data-mode-b-toggle]').click();
    await page.waitForTimeout(250);
    const analysisBounds = await page.evaluate((idx) => window.measureSceneScreenBounds(idx), i);
    await page.screenshot({ path: join(outDir, `${ids[i]}-analysis.png`) });

    // Select first item in analysis panel
    const selBtn = page.locator('[data-math-analysis-panel] button').first();
    let selectedBounds = null;
    if (await selBtn.count()) {
      await selBtn.click();
      await page.waitForTimeout(200);
      selectedBounds = await page.evaluate((idx) => window.measureSceneScreenBounds(idx), i);
      await page.screenshot({ path: join(outDir, `${ids[i]}-selected.png`) });
      await page.getByRole('button', { name: 'Xem lại toàn hình', exact: true }).click();
      await page.waitForTimeout(200);
    }

    // Close analysis panel
    await page.locator('[data-mode-b-toggle]').click();
    await page.waitForTimeout(200);

    // Orbit
    const canvas = page.locator('.geo3d-canvas canvas');
    const box = await canvas.boundingBox();
    await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.5);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width * 0.68, box.y + box.height * 0.58, { steps: 12 });
    await page.mouse.up();
    await page.waitForTimeout(200);
    const orbitBounds = await page.evaluate((idx) => window.measureSceneScreenBounds(idx), i);
    const orbitCamera = await page.evaluate(() => window.__geo3d_camera_snapshot.position);
    await page.screenshot({ path: join(outDir, `${ids[i]}-rotated.png`) });

    // Reset camera
    await page.getByRole('button', { name: 'Xem lại toàn hình', exact: true }).click();
    await page.waitForTimeout(220);
    const resetCamera = await page.evaluate(() => window.__geo3d_camera_snapshot.position);

    // X-ray mode
    const menu = page.getByRole('button', { name: 'Hiển thị', exact: true });
    await menu.click();
    const xray = page.getByRole('menuitemcheckbox', { name: 'Nhìn xuyên khối', exact: true });
    let xrayBounds = null;
    if (await xray.count()) {
      await xray.click();
      await menu.click();
      await page.waitForTimeout(200);
      xrayBounds = await page.evaluate((idx) => window.measureSceneScreenBounds(idx), i);
      await page.screenshot({ path: join(outDir, `${ids[i]}-xray.png`) });
    } else {
      await menu.click();
    }

    measurements.scenes.push({
      id: ids[i],
      defaultCamera,
      orbitCamera,
      resetCamera,
      entryBounds,
      completeBounds,
      analysisBounds,
      selectedBounds,
      orbitBounds,
      xrayBounds,
    });
  }

  // Multi-viewport audit on representative scenes (1024x768 and 820x640)
  for (const vp of [
    { width: 1024, height: 768 },
    { width: 820, height: 640 },
  ]) {
    await page.setViewportSize(vp);
    for (const targetId of ['family01_triangular_pyramid', 'family05_prism', 'family09_cylinder_and_sections', 'family11_sphere_plane_cut']) {
      const idx = ids.indexOf(targetId);
      if (idx < 0) continue;
      await page.evaluate((k) => window.openRow(k, false), idx);
      await page.waitForTimeout(350);
      const previewBtn = page.getByRole('button', { name: 'Xem mô hình đầy đủ', exact: true });
      if (await previewBtn.count()) await previewBtn.click();
      await page.waitForTimeout(250);
      const boundsClosed = await page.evaluate((k) => window.measureSceneScreenBounds(k), idx);
      await page.locator('[data-mode-b-toggle]').click();
      await page.waitForTimeout(220);
      const boundsOpen = await page.evaluate((k) => window.measureSceneScreenBounds(k), idx);
      await page.screenshot({ path: join(outDir, `${targetId}-${vp.width}x${vp.height}-analysis.png`) });
      measurements.multiViewport.push({
        id: targetId,
        viewport: `${vp.width}x${vp.height}`,
        boundsClosed,
        boundsOpen,
      });
    }
  }

  writeFileSync(join(outDir, 'measurements.json'), JSON.stringify(measurements, null, 2));
  console.log('Saved measurements to', join(outDir, 'measurements.json'));
} finally {
  await browser.close();
}
