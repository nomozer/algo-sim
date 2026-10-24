import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const run = dirname(fileURLToPath(import.meta.url));
const repo = resolve(run, '../../../../..');
const front = join(repo, 'frontend');
const stage = process.argv[2] ?? 'before';
const depthOnly = process.argv.includes('--depth-only');
const out = join(run, stage);
mkdirSync(out, { recursive: true });
const { build } = await import(pathToFileURL(join(front, 'node_modules/vite/dist/node/index.js')));
const { default: react } = await import(pathToFileURL(join(front, 'node_modules/@vitejs/plugin-react/dist/index.js')));
const { chromium } = await import(pathToFileURL(join(front, 'node_modules/playwright/index.mjs')));
const html = join(front, 'scripts/_quality.html');
const tsx = join(front, 'scripts/_quality.tsx');
const dist = join(repo, '.superpowers/quality-browser', stage);
writeFileSync(html, '<html><head><meta charset="utf-8"></head><body><div id="root"></div><script type="module" src="./_quality.tsx"></script></body></html>');
writeFileSync(tsx, `
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as THREE from 'three';
import { Scene3DExplorer } from '../src/simulations/domains/geometry/Scene3DExplorer';
import { UnsupportedNotice, SimulationWorkspace } from '../src/components/SimulationWorkspace';
import { useAppStore } from '../src/state/store';
import { registerSemanticDomain } from '../src/simulations/domains/semantic';
import { buildObject3D } from '../src/simulations/domains/geometry/scene3d-view';
import { phanTichToanHocCuaCanh, stepCount } from '../src/simulations/domains/geometry/scene3d-model';
import rows from '../../docs/evaluation/geometry/runs/simulation-visual-consistency-learning-ux/demos/audit_scenes.json';
import '../src/styles/global.css';
const w = window as any;
registerSemanticDomain();
w.rows = rows;
w.depthProbe = (xray=false) => {
  const results: any[] = [];
  for (const row of rows.filter((r: any) => r.served)) {
    for (const o of (row as any).scene.objects.filter((o: any) => o.surface_role === 'SECTION_REGION' || o.type === 'section' || (o.render === 'polygon' && o.surface_role === 'AUXILIARY_SURFACE'))) {
      const built = buildObject3D(o, false, undefined, undefined, undefined, undefined, undefined, xray);
      if (!built) continue;
      built.updateMatrixWorld(true);
      let fill: any;
      built.traverse((n: any) => { if (/^(section_fill|polygon_fill):/.test(n.name)) fill = n; });
      if (!fill) continue;
      const mesh = new THREE.Mesh(fill.geometry.clone(), fill.material.clone());
      mesh.applyMatrix4(fill.matrixWorld);
      mesh.renderOrder = fill.renderOrder;
      const box = new THREE.Box3().setFromObject(mesh), center = box.getCenter(new THREE.Vector3());
      const size = Math.max(box.getSize(new THREE.Vector3()).length(), 1);
      const positions = mesh.geometry.getAttribute('position');
      let normal = new THREE.Vector3(), rayTarget = center.clone();
      const index = mesh.geometry.getIndex(), count = index ? index.count : positions.count;
      const vertex = (i: number) => new THREE.Vector3().fromBufferAttribute(positions,index ? index.getX(i):i).applyMatrix4(mesh.matrix);
      for (let i = 0; i + 2 < count; i+=3) {
        const a=vertex(i), b=vertex(i+1), c=vertex(i+2);
        normal.crossVectors(b.clone().sub(a),c.clone().sub(a));
        if(normal.lengthSq()>1e-8) { normal.normalize();rayTarget.copy(a).add(b).add(c).multiplyScalar(1/3);break; }
      }
      if (!normal.lengthSq()) continue;
      const scene = new THREE.Scene(); scene.background = new THREE.Color('white');
      scene.add(new THREE.AmbientLight(0xffffff, 3)); scene.add(mesh);
      const wall = new THREE.Mesh(new THREE.PlaneGeometry(size*2, size*2), new THREE.MeshBasicMaterial({ color: 0x647a96, side: THREE.DoubleSide }));
      wall.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), normal);
      wall.position.copy(rayTarget).addScaledVector(normal, size*.2);
      scene.add(wall); scene.updateMatrixWorld(true);
      const renderer = new THREE.WebGLRenderer({ preserveDrawingBuffer: true }); renderer.setSize(96,96);
      const camera = new THREE.PerspectiveCamera(40,1,.01,size*20);
      const samples: any[] = [];
      for (const side of [1,-1]) {
        camera.position.copy(rayTarget).addScaledVector(normal,size*side*2);
        camera.up.set(Math.abs(normal.y)>.9 ? 1:0, Math.abs(normal.y)>.9 ? 0:1, 0);
        camera.lookAt(rayTarget); camera.updateMatrixWorld();
        const ray = new THREE.Raycaster(camera.position, rayTarget.clone().sub(camera.position).normalize());
        const hits = ray.intersectObjects([wall, mesh]);
        const firstHit = hits[0]?.object === wall ? 'opaque_wall' : 'section';
        const pixels = () => { renderer.render(scene,camera); const p = new Uint8Array(96*96*4); renderer.getContext().readPixels(0,0,96,96,renderer.getContext().RGBA,renderer.getContext().UNSIGNED_BYTE,p); return p; };
        mesh.visible=true; const on=pixels(); mesh.visible=false; const off=pixels(); mesh.visible=true;
        let changed=0; for(let i=0;i<on.length;i+=4) if(Math.abs(on[i]-off[i])+Math.abs(on[i+1]-off[i+1])+Math.abs(on[i+2]-off[i+2])>8) changed++;
        samples.push({side, firstHit, changed, pass:xray && !mesh.material.depthTest ? changed>0 : firstHit==='opaque_wall' ? changed===0 : changed>0});
      }
      results.push({family:row.id, id:o.id, depthTest:mesh.material.depthTest, depthFunc:mesh.material.depthFunc, depthWrite:mesh.material.depthWrite, renderOrder:mesh.renderOrder, samples});
      renderer.dispose(); renderer.forceContextLoss(); mesh.geometry.dispose(); mesh.material.dispose(); wall.geometry.dispose(); wall.material.dispose();
    }
  }
  return results;
};
function App() {
  const [index,setIndex] = useState(0), [actual,setActual] = useState(false);
  w.openRow = (i: number, real=false) => {
    const row = rows[i] as any;
    useAppStore.setState(row.served ? {unsupported:null, active:{moduleId:'generic.semantic_program', envelope:{title:row.category, description:row.problem_text, scene3d:row.scene}} as any} : {active:null, unsupported:{reason:row.reason, error_code:row.code, failure_category:'postcondition_violated', refusal_cause:'SOURCE', stage_reached:'verification'}});
    setActual(real); setIndex(i);
  };
  const row = rows[index] as any;
  w.analysis = row.scene ? phanTichToanHocCuaCanh(row.scene,null,row.route_d) : null;
  return actual ? <SimulationWorkspace key={'actual'+index}/> : row.served ? <Scene3DExplorer key={index} scene={row.scene} de={row.problem_text} tieuDe={row.category} routeDSimulation={row.route_d}/> : <UnsupportedNotice unsupported={{reason:row.reason,error_code:row.code,failure_category:'postcondition_violated',refusal_cause:'SOURCE',stage_reached:'verification'}}/>;
}
createRoot(document.getElementById('root')!).render(<App/>);
`);
try {
  await build({ root: front, configFile: false, plugins:[react()], logLevel:'error', build:{ outDir:dist, emptyOutDir:true, rollupOptions:{input:html} } });
} finally { unlinkSync(html); unlinkSync(tsx); }
const browser = await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const receipt = {stage, environment:'Chromium SwiftShader WebGL; offline fixtures; no provider calls', errors:[], depth:[], scenes:[]};
try {
  const page = await browser.newPage({viewport:{width:1440,height:900}});
  page.on('pageerror', e => receipt.errors.push(String(e)));
  await page.route('http://quality.local/**', route => {
    const file = join(dist,new URL(route.request().url()).pathname);
    return route.fulfill({status:existsSync(file)?200:404, contentType:file.endsWith('.js')?'application/javascript':file.endsWith('.css')?'text/css':'text/html', body:existsSync(file)?readFileSync(file):'missing'});
  });
  await page.goto('http://quality.local/scripts/_quality.html');
  await page.waitForFunction(()=>window.openRow);
  receipt.depth = await page.evaluate(()=>window.depthProbe());
  if(stage!=='before') receipt.xrayDepth = await page.evaluate(()=>window.depthProbe(true));
  writeFileSync(join(out,'depth.json'),JSON.stringify({depth:receipt.depth,xrayDepth:receipt.xrayDepth},null,2));
  const ids = await page.evaluate(()=>window.rows.map(r=>r.id));
  const wanted = /family01_|family05_|family07_|family09_|family10_|family11_|family12_|family13_/;
  for(let i=0;i<ids.length;i++) {
    if(depthOnly) break;
    if(!wanted.test(ids[i])) continue;
    console.log(stage,ids[i]);
    await page.evaluate(i=>window.openRow(i),i);
    await page.waitForTimeout(650);
    const refused = ids[i].includes('family13');
    const item = {id:ids[i], firstGuidance:await page.locator('[data-learner-guidance]').textContent().catch(()=>null), analysisClosed:await page.locator('[data-math-analysis-panel]').count()===0};
    if(refused) {
      item.refusal=await page.locator('#root').innerText();
      item.mainRefusal=await page.locator('#root').evaluate(n=>{const c=n.cloneNode(true);c.querySelectorAll('details').forEach(d=>d.remove());return c.textContent;});
      await page.screenshot({path:join(out,ids[i]+'.png')}); receipt.scenes.push(item); continue;
    }
    await page.locator('.geo3d-canvas canvas').waitFor();
    item.firstRendered = await page.evaluate(()=>window.__geo3d_rendered_object_ids);
    item.firstBadges = await page.locator('[data-ann-id]').allTextContents();
    await page.screenshot({path:join(out,ids[i]+'-entry.png')});
    const preview=page.getByRole('button',{name:'Xem mô hình đầy đủ',exact:true});
    if(await preview.count()) await preview.click();
    else { const slider=page.locator('input[type=range]').first(); await slider.fill(await slider.getAttribute('max')); }
    await page.waitForTimeout(250);
    item.finalRendered=await page.evaluate(()=>window.__geo3d_rendered_object_ids);
    item.defaultCamera=await page.evaluate(()=>window.__geo3d_camera_snapshot.position);
    item.answerBadges=await page.locator('[data-ann-id]').allTextContents();
    await page.screenshot({path:join(out,ids[i]+'-complete.png')});
    await page.locator('[data-mode-b-toggle]').click();
    item.analysis=await page.locator('[data-math-analysis-panel]').innerText();
    const selectable=page.locator('[data-math-analysis-panel] button').first();
    if(await selectable.count()) {
      await selectable.click();
      item.selected=await page.evaluate(()=>window.__geo3d_selected_id);
      item.highlighted=await page.evaluate(()=>window.__geo3d_highlighted_ids);
      await page.screenshot({path:join(out,ids[i]+'-selected.png')});
      await page.getByRole('button',{name:'Chỉ xem phần này',exact:true}).click();
      item.isolated=await page.evaluate(()=>window.__geo3d_rendered_object_ids);
      await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click();
      item.resetSelected=await page.evaluate(()=>window.__geo3d_selected_id);
    }
    await page.screenshot({path:join(out,ids[i]+'-analysis.png')});
    await page.locator('[data-mode-b-toggle]').click();
    const canvas=page.locator('.geo3d-canvas canvas'), box=await canvas.boundingBox();
    await page.mouse.move(box.x+box.width*.5,box.y+box.height*.5);await page.mouse.down();await page.mouse.move(box.x+box.width*.7,box.y+box.height*.6,{steps:12});await page.mouse.up();
    await page.waitForTimeout(180);
    item.orbitCamera=await page.evaluate(()=>window.__geo3d_camera_snapshot.position);
    await page.screenshot({path:join(out,ids[i]+'-rotated.png')});
    await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click();
    await page.waitForTimeout(200);
    item.resetCamera=await page.evaluate(()=>window.__geo3d_camera_snapshot.position);
    const menu=page.getByRole('button',{name:'Hiển thị',exact:true}); await menu.click();
    const xray=page.getByRole('menuitemcheckbox',{name:'Nhìn xuyên khối',exact:true});
    item.xrayAvailable=await xray.count()>0;
    if(item.xrayAvailable){ await xray.click(); await menu.click(); item.xrayStatus=await page.getByRole('status').allTextContents(); await page.screenshot({path:join(out,ids[i]+'-xray.png')}); }
    else await menu.click();
    // Actual application entry uses SimulationWorkspace/store and no forced final step.
    await page.evaluate(i=>window.openRow(i,true),i);await page.waitForTimeout(250);
    item.actualEntryGuidance=await page.locator('[data-learner-guidance]').textContent().catch(()=>null);
    item.actualEntryRendered=await page.evaluate(()=>window.__geo3d_rendered_object_ids);
    item.actualAnalysisClosed=await page.locator('[data-math-analysis-panel]').count()===0;
    receipt.scenes.push(item);
    writeFileSync(join(out,'receipt.json'),JSON.stringify(receipt,null,2));
  }
  writeFileSync(join(out,'receipt.json'),JSON.stringify(receipt,null,2));
  if(stage!=='before') {
    assert.equal(receipt.errors.length,0);
    assert(receipt.depth.length>5);
    assert(receipt.depth.every(d=>d.samples.every(s=>s.pass)),'section occlusion disagrees with independent ray ordering');
    assert(receipt.xrayDepth.every(d=>d.samples.every(s=>s.pass)),'explicit x-ray did not reveal interior fill');
    assert(receipt.scenes.filter(s=>s.analysis).every(s=>! /cone_main|cone_upper|\^\d|<[^>]+>|\\(?:frac|sqrt)/.test(s.analysis)),'internal names or escaped math leaked');
    const refusal=receipt.scenes.find(s=>s.mainRefusal);
    if(!depthOnly) {
      assert(!refusal.mainRefusal.includes('CURVED_')&&!refusal.mainRefusal.includes('NGOÀI DANH MỤC'));
      assert(refusal.mainRefusal.includes('bán kính'));
    }
    assert(receipt.scenes.every(s=>s.analysisClosed));
    assert(receipt.scenes.filter(s=>s.analysis).every(s=>s.xrayAvailable));
    assert(receipt.scenes.filter(s=>s.analysis).every(s=>s.actualEntryGuidance?.includes('Bấm Phát')&&s.actualAnalysisClosed));
    assert(receipt.scenes.filter(s=>s.analysis).every(s=>s.selected && s.highlighted.length>0 && s.isolated.length>0 && s.resetSelected===null));
    assert(receipt.scenes.filter(s=>s.analysis).every(s=>s.defaultCamera.every((v,i)=>Math.abs(v-s.resetCamera[i])<1e-6)),'camera reset changed default framing');
  }
  console.log('receipt',join(out,'receipt.json'));
} finally { await browser.close(); }
