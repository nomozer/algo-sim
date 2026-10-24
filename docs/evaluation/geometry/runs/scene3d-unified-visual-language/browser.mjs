import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync, readdirSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const run = dirname(fileURLToPath(import.meta.url));
const root = resolve(run, '../../../../..');
const front = join(root, 'frontend');
const stage = process.argv[2] ?? 'baseline';
const proposal = process.argv[3] ?? stage;
const baselineCommit = 'f95596716912e5550ed079287221274b2d70f24c';
const baselineSource = proposal === 'baseline';
const fixtureName = 'scenes-complete.json';
const out = join(run, stage);
if (existsSync(join(out, 'receipt.json'))) throw new Error('Refuse to overwrite completed evidence');
mkdirSync(out, { recursive: true });
const sha = x => createHash('sha256').update(x).digest('hex');
const { build } = await import(pathToFileURL(join(front, 'node_modules/vite/dist/node/index.js')));
const { default: react } = await import(pathToFileURL(join(front, 'node_modules/@vitejs/plugin-react/dist/index.js')));
const { chromium } = await import(pathToFileURL(join(front, 'node_modules/playwright/index.mjs')));
const referencePath = join(run, '../geometric-visual-correctness-framing/measure-visuals.mjs');
const reference = readFileSync(referencePath, 'utf8');
// Reuse the existing independent wall probe and screen-bounds measurement verbatim.
const helpers = reference.slice(reference.indexOf('w.depthProbe ='), reference.indexOf('function App()'));
const html = join(front, 'scripts/_unified_visual.html');
const tsx = join(front, 'scripts/_unified_visual.tsx');
const dist = join(root, '.superpowers/unified-visual-build', stage);
// B is overridden too (identical values to product): all three survey arms take the same build path.
const survey = ['A', 'B', 'C'].includes(proposal) ?JSON.parse(readFileSync(join(run, 'proposals.json')))[proposal] : null;
let appliedOverrides = 0;
const appliedBaseline = new Map();
let baselineCssChecks = [];
const sourceHashes = {};
for (const name of readdirSync(join(front,'src/simulations/domains/geometry'))) {
  const path=join(front,'src/simulations/domains/geometry',name);
  if(/\.(ts|tsx|json)$/.test(name)) sourceHashes['frontend/src/simulations/domains/geometry/'+name]=sha(readFileSync(path));
}
sourceHashes['frontend/src/styles/tokens.css']=sha(readFileSync(join(front,'src/styles/tokens.css')));
const priorSources = new Map();
if(baselineSource) {
  for(const path of ['frontend/src/simulations/domains/geometry/scene3d-roles.ts','frontend/src/simulations/domains/geometry/scene3d-view.tsx','frontend/src/styles/tokens.css']) {
    const source=execFileSync('git',['show',baselineCommit+':'+path],{cwd:root,encoding:'utf8'});
    priorSources.set(join(root,path).replaceAll('\\','/'),source); sourceHashes[path]=sha(source);
  }
}
writeFileSync(html, '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><div id="root"></div><script type="module" src="./_unified_visual.tsx"></script></body></html>');
writeFileSync(tsx, `
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as THREE from 'three';
import { Scene3DExplorer } from '../src/simulations/domains/geometry/Scene3DExplorer';
import { UnsupportedNotice } from '../src/components/SimulationWorkspace';
import { buildObject3D } from '../src/simulations/domains/geometry/scene3d-view';
import { tapKetQuaCuoi } from '../src/simulations/domains/geometry/scene3d-model';
import * as roles from '../src/simulations/domains/geometry/scene3d-roles';
import rows from '../../docs/evaluation/geometry/runs/scene3d-unified-visual-language/${fixtureName}';
import '../src/styles/global.css';
const w = window as any;
w.rows = rows; w.THREE = THREE; w.buildObject3D = buildObject3D;
w.finalIds = (i: number) => [...tapKetQuaCuoi(rows[i].scene as any)];
// Read-only runtime probe: the live module constant the renderer imports (null at the pre-token baseline).
w.tokenProbe = () => JSON.stringify((roles as any).PHONG_CACH_SCENE3D ?? null);
THREE.Scene.prototype.onAfterRender = function(renderer: any, scene: any, camera: any) {
  if (scene.children.some((n: any) => n.isGroup)) w.gpu = {renderer, scene, camera};
};
// Distinct encountered styles held by every owner's span pool: allocations beyond its growth are re-allocations.
w.poolSize = () => { let n = 0; w.gpu.scene.traverse((o: any) => { n += o.userData.spanMaterialPool?.size ?? 0; }); return n; };
w.materialTick = () => { const m = new THREE.Material(); const id = m.id; m.dispose(); return id; };
w.readGpu = () => {
  const {renderer, scene} = w.gpu;
  const materials: any[] = [];
  scene.traverse((n: any) => {
    for (const m of Array.isArray(n.material) ? n.material : n.material ? [n.material] : []) {
      if (!m.color || m.colorWrite === false) continue;
      materials.push({name: n.name, color: m.color.getHexString(), opacity: m.opacity, type: m.type,
        forceSinglePass: m.forceSinglePass, depthTest: m.depthTest, depthWrite: m.depthWrite,
        renderOrder: n.renderOrder, width: m.linewidth, dash: m.dashSize, gap: m.gapSize});
    }
  });
  return {materials, programs: renderer.info.programs.length, memory: {...renderer.info.memory},
    outputColorSpace: renderer.outputColorSpace, colorManagement: THREE.ColorManagement.enabled,
    render: {...renderer.info.render}};
};
w.shells = () => {
  const result: any = {};
  const solids=(rows[w.rowIndex] as any).scene.objects.filter((o: any)=>o.type==='solid'||o.type==='curved_solid');
  for(const o of solids) {
    w.gpu.scene.traverse((n: any)=> {
      if(n.name!=='solid:'+o.id && n.name!=='curved:'+o.id+':'+o.curved_kind) return;
      const mesh=n.children.find((c: any)=>c.isMesh&&c.material.colorWrite!==false);
      if(mesh) result[o.id]={color:mesh.material.color.getHexString(),opacity:mesh.material.opacity};
    });
  }
  return result;
};
w.labelMetrics = () => {
  const labels=[...document.querySelectorAll('.geo3d-label,.geo3d-nhan-mp,.geo3d-so-do')].filter((el: any)=>getComputedStyle(el).opacity!=='0');
  return labels.map((el: any)=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {text:el.textContent,color:s.color,background:s.backgroundColor,
    opacity:s.opacity,fontSize:parseFloat(s.fontSize),rect:{x:r.x,y:r.y,w:r.width,h:r.height}};});
};
w.ownPixels = () => {
  const {renderer, scene, camera} = w.gpu;
  const targets: any[] = [];
  scene.traverse((n: any) => { if (/^(section_fill|polygon_fill):/.test(n.name) && n.visible) targets.push(n); });
  const gl = renderer.getContext(); const width = gl.drawingBufferWidth, height = gl.drawingBufferHeight;
  const read = () => { renderer.render(scene, camera); const p = new Uint8Array(width*height*4); gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,p); return p; };
  const normal = read(); const results: any[] = [];
  for (const target of targets) {
    target.visible = false; const without = read(); target.visible = true;
    let pixels = 0, delta = 0;
    for (let i=0;i<normal.length;i+=4) {
      const d=Math.abs(normal[i]-without[i])+Math.abs(normal[i+1]-without[i+1])+Math.abs(normal[i+2]-without[i+2]);
      if(d>8) pixels++; delta+=d;
    }
    results.push({name:target.name, pixels, fraction:pixels/(width*height), meanRgbDelta:delta/(width*height*3)});
  }
  renderer.render(scene,camera);
  return results;
};
${helpers}
function App() {
  const [index, setIndex] = useState(0); const [epoch, setEpoch] = useState(0);
  const [reversed, setReversed] = useState(false);
  w.openRow = (i: number, reverse = false) => { w.gpu = null; w.rowIndex=i; setIndex(i); setReversed(reverse); setEpoch(n=>n+1); };
  const row = rows[index] as any;
  const scene = reversed && row.scene ? {...row.scene,objects:[...row.scene.objects].reverse()} : row.scene;
  return row.served ? <Scene3DExplorer key={epoch+':'+index} scene={scene} de={row.problem_text} tieuDe={row.category} routeDSimulation={row.route_d} />
    : <UnsupportedNotice unsupported={{reason:row.reason,error_code:row.code,failure_category:'postcondition_violated',refusal_cause:'SOURCE',stage_reached:'verification'}} />;
}
createRoot(document.getElementById('root')!).render(<App />);
`);
try {
  await build({root:front, configFile:false, plugins:[react(), {
    name:'research-token-proposal', enforce:'pre', transform(code,id) {
      if(baselineSource && priorSources.has(id)) { appliedBaseline.set(id,(appliedBaseline.get(id)??0)+1); return priorSources.get(id); }
      // CSS @import is inlined by Vite without plugin transforms: substitute baseline tokens at the importer.
      if(baselineSource && id.endsWith('/src/styles/global.css')) {
        const tokens=join(root,'frontend/src/styles/tokens.css').replaceAll('\\','/');
        if(!code.includes('@import "./tokens.css";')) throw new Error('Baseline tokens import did not match');
        appliedBaseline.set(tokens,(appliedBaseline.get(tokens)??0)+1);
        return code.replace('@import "./tokens.css";', priorSources.get(tokens));
      }
      if (!survey || !id.endsWith('/scene3d-roles.ts')) return;
      if(!/export const PHONG_CACH_SCENE3D = \{[\s\S]*?\n\} satisfies PhongCachScene3D;/.test(code)) throw new Error('Survey token override did not match source');
      appliedOverrides++;
      return code.replace(/export const PHONG_CACH_SCENE3D = \{[\s\S]*?\n\} satisfies PhongCachScene3D;/,
        'export const PHONG_CACH_SCENE3D = '+JSON.stringify(survey)+' satisfies PhongCachScene3D;');
    }
  }], logLevel:'error', build:{outDir:dist, emptyOutDir:true, rollupOptions:{input:html}}});
  if(survey && appliedOverrides!==1) throw new Error('Survey override count must be exactly one');
  if(baselineSource) {
    for(const path of priorSources.keys()) if(appliedBaseline.get(path)!==1) throw new Error('Baseline substitution not applied once: '+path);
    // Built output, not the transform count: every changed custom property must carry its baseline value.
    const builtCss=readdirSync(join(dist,'assets')).filter(f=>f.endsWith('.css')).map(f=>readFileSync(join(dist,'assets',f),'utf8')).join('\n');
    // Whitespace-normalized (working copy is CRLF, git show is LF): only genuinely changed declarations remain.
    const decls=t=>new Set((t.match(/--[\w-]+:\s*[^;]+;/g)??[]).map(d=>d.replace(/\s+/g,'')));
    const current=decls(readFileSync(join(front,'src/styles/tokens.css'),'utf8'));
    baselineCssChecks=[...decls(priorSources.get(join(root,'frontend/src/styles/tokens.css').replaceAll('\\','/')))].filter(d=>!current.has(d));
    for(const d of baselineCssChecks) if(!builtCss.replace(/\s+/g,'').includes(d.replace(/\s+/g,''))) throw new Error('Built CSS lacks baseline '+d);
  }
} finally { unlinkSync(html); unlinkSync(tsx); }
console.log(stage+': BUILD_SNAPSHOT_COMPLETE');

const receipt = {stage, proposal, source_commit:baselineSource?baselineCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),
  checkout_commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(), baseline_source_overrides:[...priorSources.keys()], baseline_substitutions_applied:Object.fromEntries(appliedBaseline),
  baseline_built_css_declarations_verified:baselineCssChecks,
  source_hashes:sourceHashes, source_tree_sha256:sha(JSON.stringify(sourceHashes)), harness_sha256:sha(readFileSync(fileURLToPath(import.meta.url))),
  fixture_sha256:sha(readFileSync(join(run,fixtureName))), helper_sha256:sha(reference),
  proposal_override:survey, applied_token_overrides:appliedOverrides, environment:'Playwright Chromium / SwiftShader / DPR1 / offline assets only',
  human_visual_approval:'NOT_GRANTED', errors:[], scenes:[], compact:[], transitions:[], depth:[], xrayDepth:[], screenshots:[]};
const browser = await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const page = await browser.newPage({viewport:{width:1440,height:900}, deviceScaleFactor:1});
page.setDefaultTimeout(15000);
page.on('pageerror', e=>receipt.errors.push({type:'pageerror',message:e.message}));
page.on('console', msg=> {if(msg.type()==='error') receipt.errors.push({type:'console',message:msg.text()});});
await page.route('**/*', route=> {
  const u=new URL(route.request().url());
  if(u.hostname!=='unified.local') return route.abort();
  const file=join(dist,u.pathname);
  return route.fulfill({status:existsSync(file)?200:404, contentType:file.endsWith('.js')?'application/javascript':file.endsWith('.css')?'text/css':'text/html', body:existsSync(file)?readFileSync(file):'missing'});
});
async function screenshot(name) {
  await page.mouse.move(1439,899);
  const path=join(out,name+'.png'); await page.screenshot({path});
  receipt.screenshots.push({file:name+'.png',sha256:sha(readFileSync(path))});
}
async function state(index) {
  return page.evaluate(i=>({camera:window.__geo3d_camera_snapshot, bounds:window.measureSceneScreenBounds(i),
    edges:window.__geo3d_edge_spans, dash:window.__geo3d_edge_dash_signature,
    duplicateOwners:window.__geo3d_duplicate_visual_owner_ids, ownPixels:window.ownPixels(), gpu:window.readGpu(),
    selected:window.__geo3d_selected_id, rendered:window.__geo3d_rendered_object_ids,
    highlighted:window.__geo3d_highlighted_ids,
    labels:window.labelMetrics(), shells:window.shells(),
    annotationUnplaced:window.__geo3d_annotation_unplaced}),index);
}
async function finish(index, reversed=false) {
  await page.evaluate(({i,reversed})=>window.openRow(i,reversed),{i:index,reversed});
  await page.waitForFunction(()=>window.gpu && window.__geo3d_camera_snapshot);
  const full=page.getByRole('button',{name:'Xem mô hình đầy đủ',exact:true});
  if(await full.count()) await full.click();
  await page.waitForTimeout(180);
}
async function xray() {
  const menu=page.getByRole('button',{name:'Hiển thị',exact:true}); await menu.click();
  await page.getByRole('menuitemcheckbox',{name:'Nhìn xuyên khối',exact:true}).click();
  await menu.click(); await page.waitForTimeout(120);
}
try {
  await page.goto('http://unified.local/scripts/_unified_visual.html');
  await page.waitForFunction(()=>window.openRow);
  const live=await page.evaluate(()=>window.tokenProbe());
  receipt.runtime_token_probe={sha256:sha(live), value:JSON.parse(live),
    matches_override:survey?live===JSON.stringify(survey):null};
  if(survey && live!==JSON.stringify(survey)) throw new Error('Runtime token probe does not equal the survey override');
  const rows=JSON.parse(readFileSync(join(run,fixtureName),'utf8'));
  // B/final have the full interaction matrix; A/C are same-state desktop palette surveys.
  const fullMatrix=stage.startsWith('final');
  for(let i=0;i<rows.length;i++) {
    const row=rows[i]; console.log(stage+': '+(i+1)+'/'+rows.length+' '+row.id);
    await page.setViewportSize({width:1440,height:900});
    if(!row.served) {
      await page.evaluate(i=>window.openRow(i),i); await page.waitForTimeout(100);
      await screenshot(row.id+'-refusal'); receipt.scenes.push({id:row.id,refusalText:await page.locator('#root').innerText()}); continue;
    }
    await finish(i);
    const entry = {id:row.id, normal:await state(i)};
    await screenshot(row.id+'-normal');
    // Mode A does not start with the answer panel open or answer badges visible.
    entry.modeA=await page.evaluate(i=>({panelCount:document.querySelectorAll('[data-math-analysis-panel]').length,
      visibleFinalIds:[...document.querySelectorAll('[data-ann-id]')].map(el=>el.getAttribute('data-ann-id')).filter(id=>window.finalIds(i).includes(id))}),i);
    if(fullMatrix) {
      await page.locator('[data-mode-b-toggle]').click(); await page.waitForTimeout(140);
      entry.analysis=await state(i); await screenshot(row.id+'-analysis');
      const buttons=page.locator('[data-math-analysis-panel] button');
      if(await buttons.count()) {
        await buttons.first().click(); await page.waitForTimeout(140);
        entry.selected=await state(i); await screenshot(row.id+'-selected');
        await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click(); await page.waitForTimeout(80);
      }
      await page.locator('[data-mode-b-toggle]').click(); await page.waitForTimeout(140);
      const canvas=await page.locator('.geo3d-canvas canvas').boundingBox();
      await page.evaluate(()=>window.__geo3d_reset_occlusion_performance?.());
      const beforeMaterial=await page.evaluate(()=>window.materialTick()); const t=Date.now();
      await page.mouse.move(canvas.x+canvas.width*.5,canvas.y+canvas.height*.5); await page.mouse.down();
      await page.mouse.move(canvas.x+canvas.width*.68,canvas.y+canvas.height*.58,{steps:18}); await page.mouse.up();
      await page.waitForTimeout(220);
      entry.orbitPerformance={elapsedMs:Date.now()-t,materialAllocations:await page.evaluate(()=>window.materialTick())-beforeMaterial-1,
        occlusion:await page.evaluate(()=>window.__geo3d_occlusion_performance)};
      entry.orbit=await state(i); await screenshot(row.id+'-orbit');
      // Keep the SAME owners: the product reset button rebuilds them, so it cannot warm this cache.
      const repeatOrbits=[], poolGrowth=[];
      for(let pass=0;pass<3;pass++) {
        const pool=await page.evaluate(()=>window.poolSize());
        const mark=await page.evaluate(()=>window.materialTick());
        for(const direction of [-1,1]) {
          await page.mouse.move(canvas.x+canvas.width*.5,canvas.y+canvas.height*.5); await page.mouse.down();
          await page.mouse.move(canvas.x+canvas.width*(.5+direction*.18),canvas.y+canvas.height*(.5+direction*.08),{steps:18}); await page.mouse.up();
          await page.waitForTimeout(220);
        }
        repeatOrbits.push(await page.evaluate(()=>window.materialTick())-mark-1);
        poolGrowth.push(await page.evaluate(()=>window.poolSize())-pool);
      }
      entry.orbitPerformance.warmupPoolGrowth=poolGrowth[0];
      entry.orbitPerformance.repeatPoolGrowth=poolGrowth.slice(1);
      entry.orbitPerformance.warmupMaterialAllocations=repeatOrbits[0];
      entry.orbitPerformance.repeatMaterialAllocations=repeatOrbits.slice(1);
      await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click(); await page.waitForTimeout(140);
      entry.reset=await state(i);
      await xray(); entry.xray=await state(i); await screenshot(row.id+'-xray');
      for(let n=0;n<3;n++){await xray();await xray();}
      entry.xrayRepeated=await state(i); await xray();
      entry.normalRestored=await state(i);
      // Repeated same state pixels are reproducible within one browser/hardware execution.
      await screenshot(row.id+'-repeat');
    }
    receipt.scenes.push(entry);
    writeFileSync(join(out,'progress.json'),JSON.stringify(receipt,null,2));
  }
  if(fullMatrix) {
    // Actual hide/isolate/timeline controls on multi-solid and representative non-polyhedral scenes.
    for(const id of ['family07_multi_solid_composition','family10_cone_frustum_cut','family05_prism']) {
      const index=rows.findIndex(r=>r.id===id); await finish(index);
      const before=await state(index);
      await page.getByRole('button',{name:'Khám phá',exact:true}).click();
      await page.getByRole('menuitemcheckbox',{name:'Thành phần',exact:true}).click();
      const ids=Object.keys(before.shells);
      const target=ids.at(-1);
      await page.locator('[data-tree-id]').evaluateAll((buttons,target)=>{
        const button=buttons.find(b=>b.getAttribute('data-tree-id')===target); if(!button)throw new Error('missing solid tree button');
        for(let p=button.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
      },target);
      await page.locator('[data-tree-id]').evaluateAll((buttons,target)=>buttons.find(b=>b.getAttribute('data-tree-id')===target).click(),target);
      await page.getByRole('button',{name:'Chỉ xem phần này',exact:true}).click();
      await page.getByRole('button',{name:'Bỏ chọn',exact:true}).click(); await page.waitForTimeout(120);
      const isolated=await state(index); await screenshot(id+'-isolated');
      await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click();
      await page.locator('[data-tree-id]').evaluateAll((buttons,target)=>buttons.find(b=>b.getAttribute('data-tree-id')===target).click(),ids[0]);
      await page.getByRole('button',{name:'Ẩn',exact:true}).click(); await page.waitForTimeout(120);
      const hidden=await state(index); await screenshot(id+'-hidden');
      await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click();
      const previous=page.getByRole('button',{name:'Bước trước',exact:true});
      const steps=[];
      for(let n=0;n<3 && !(await previous.isDisabled());n++) { await previous.click(); await page.waitForTimeout(100); steps.push(await state(index)); }
      await finish(index,true); const reordered=await state(index);
      receipt.transitions.push({id,before,isolated,hidden,steps,reordered});
    }
    for(const viewport of [{width:1024,height:768},{width:820,height:640}]) {
      await page.setViewportSize(viewport);
      for(let i=0;i<rows.length;i++) {
        if(!rows[i].served) continue;
        await finish(i); const closed=await state(i);
        await page.locator('[data-mode-b-toggle]').click(); await page.waitForTimeout(160);
        const open=await state(i);
        await screenshot(rows[i].id+'-'+viewport.width+'-analysis');
        receipt.compact.push({id:rows[i].id,viewport,closed,open});
      }
    }
    await page.setViewportSize({width:1440,height:900}); await finish(0);
    receipt.depth=await page.evaluate(()=>window.depthProbe(false));
    receipt.xrayDepth=await page.evaluate(()=>window.depthProbe(true));
  }
  receipt.finished=true;
} catch(e) {
  receipt.errors.push({type:'HARNESS_OR_PRODUCT_ASSERTION',message:e.message});
  await screenshot('failure'); process.exitCode=1;
} finally {
  await browser.close();
  writeFileSync(join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(stage+': receipt scenes='+receipt.scenes.length+' errors='+receipt.errors.length);
}
