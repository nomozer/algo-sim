/** LOCAL Playwright CLI acceptance of real fact-route fixtures in the existing Scene3DWorkspace harness. */
import { chromium } from 'playwright';
import { mkdirSync,existsSync,readFileSync,writeFileSync } from 'node:fs';
import { resolve,join } from 'node:path';
import { createHash } from 'node:crypto';
import { docPNG } from './png-pixels.mjs';

const arg=(key,fallback)=>process.argv.includes(key)?process.argv[process.argv.indexOf(key)+1]:fallback;
const out=resolve(arg('--out',''));
if(!arg('--out') || existsSync(out)) throw new Error('--out must name a new task-owned directory');
const host=arg('--host','127.0.0.1'),port=arg('--port','3101');
const gpu=process.argv.includes('--gpu');
// --src function-discovery: same checks on the run `goal-directed-function-discovery` fixtures ("target" born before "foot").
const src=arg('--src','result-binding');
const SOURCES={'result-binding':'source-bound-result-planning','function-discovery':'goal-directed-function-discovery'};
if(!SOURCES[src]) throw new Error(`unknown --src ${src}`);
const sourceBytes=readFileSync(new URL(`../../docs/evaluation/geometry/runs/${SOURCES[src]}/visual/scenes.json`,import.meta.url));
const rows=JSON.parse(sourceBytes);
mkdirSync(out,{recursive:true});
function different(a,b){
  const x=docPNG(a),y=docPNG(b);let changed=0;
  for(let i=0;i<x.rgba.length;i+=4)
    if(Math.abs(x.rgba[i]-y.rgba[i])+Math.abs(x.rgba[i+1]-y.rgba[i+1])+Math.abs(x.rgba[i+2]-y.rgba[i+2])>30)changed++;
  return changed;
}
const server=await chromium.launchServer({args:gpu?['--use-angle=d3d11','--enable-gpu','--ignore-gpu-blocklist']:
  ['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const browser=await chromium.connect(server.wsEndpoint());
const results=[],errors=[],networkRetries=[];
try{
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  async function load(i,extra=''){
    const url=`http://${host}:${port}/scripts/hybrid-section-visual.html?src=${src}&i=${i}${extra}`;
    for(let attempt=0;;attempt++){
      try{await page.goto(url);await page.waitForSelector(rows[i].served?'canvas':'[data-testid="refusal"]');return;}
      catch(e){if(attempt>=2 || !/ERR_NETWORK_ACCESS_DENIED|ERR_CONNECTION_REFUSED/.test(String(e)))throw e;
        networkRetries.push({i,attempt:attempt+1});await page.waitForTimeout(1000);}
    }
  }
  async function shot(name){const bytes=await page.getByTestId('khung').screenshot();writeFileSync(join(out,name),bytes);return bytes;}
  for(let i=0;i<rows.length;i++){
    const row=rows[i];await load(i);
    if(!row.served){
      const text=await page.getByTestId('refusal').textContent();
      results.push({id:row.id,refusalVisible:text.includes(row.code),canvasAbsent:await page.locator('canvas').count()===0});
      await page.screenshot({path:join(out,`${row.id}-refusal.png`)});continue;
    }
    const model=await page.evaluate(()=>({n:window.__hybrid.stepCount,objects:window.__hybrid.objects,timeline:window.__hybrid.timeline}));
    const frames=[];
    for(let k=0;k<model.n;k++){
      await page.getByRole('slider',{name:'Bước dựng'}).fill(String(k));
      await page.waitForTimeout(100);
      const present=await page.evaluate(()=>window.__hybrid.presentAt(window.__hybrid.step));
      const violations=model.objects.filter(o=>present.includes(o.id)).flatMap(o=>(o.depends||[]).filter(d=>!present.includes(d)).map(d=>`${o.id}->${d}`));
      if(violations.length)throw new Error(`${row.id} step${k} dependencies ${violations}`);
      frames.push({step:k,present});
      await shot(`${row.id}-step-${String(k).padStart(2,'0')}.png`);
    }
    const lineBorn=frames.find(f=>f.present.includes(row.target))?.step;
    const footBorn=frames.find(f=>f.present.includes(row.foot))?.step;
    if(lineBorn===undefined || footBorn===undefined || lineBorn>=footBorn)throw new Error('line/foot order');
    const finalState=await page.evaluate(()=>({
      rendered:window.__geo3d_rendered_object_ids||[],
      auxHidden:window.__geo3d_auxiliary_hidden_ids||[]
    }));
    if(!finalState.rendered.includes(row.target)||!finalState.rendered.includes(row.foot)){
      throw new Error(`${row.id}: target line or foot missing from rendered objects under default aux=0`);
    }
    const final=await shot(`${row.id}-final.png`);
    await page.getByRole('checkbox',{name:'Hình phụ'}).check();
    await page.waitForTimeout(150);
    const auxShownHidden=await page.evaluate(()=>window.__geo3d_auxiliary_hidden_ids||[]);
    if(auxShownHidden.length!==0)throw new Error(`${row.id}: auxiliary toggle did not reveal hidden auxiliaries`);
    await shot(`${row.id}-final-aux1.png`);
    await page.getByRole('checkbox',{name:'Hình phụ'}).uncheck();
    await page.waitForTimeout(150);
    await page.getByRole('combobox',{name:'Chọn đối tượng'}).selectOption(row.foot);
    const selected=await page.evaluate(()=>window.__hybrid.selected_id);
    if(selected!==row.foot)throw new Error('foot selection failed');
    await shot(`${row.id}-selected-foot.png`);
    await page.getByRole('combobox',{name:'Chọn đối tượng'}).selectOption('');
    await page.getByRole('slider',{name:'Bước dựng'}).fill(String(lineBorn));
    const past=await page.evaluate(()=>window.__hybrid.presentAt(window.__hybrid.step));
    if(past.includes(row.foot))throw new Error('backward playback leaks foot');
    await page.getByRole('slider',{name:'Bước dựng'}).fill(String(model.n-1));
    const canvas=page.locator('canvas');const box=await canvas.boundingBox();
    await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
    await page.mouse.down();await page.mouse.move(box.x+box.width/2+90,box.y+box.height/2+35,{steps:10});await page.mouse.up();
    await page.waitForTimeout(1200);
    const orbit=await shot(`${row.id}-orbit.png`);
    const orbitChanged=different(final,orbit)>0;
    await page.mouse.wheel(0,-240);await page.waitForTimeout(600);
    const zoom=await shot(`${row.id}-zoom.png`);
    await page.getByRole('button',{name:'Đặt lại khung nhìn'}).click();await page.waitForTimeout(1000);
    const reset=await shot(`${row.id}-reset.png`);
    await load(i,`&hide=${row.target}`);await page.waitForTimeout(300);
    const hidden=await shot(`${row.id}-without-line.png`);
    const ownPixels=different(final,hidden);
    if(ownPixels===0)throw new Error(`${row.id}: line draws zero own pixels`);
    results.push({id:row.id,frames,lineBorn,footBorn,selected,ownPixels,
                  defaultAuxHidden:finalState.auxHidden,
                  orbit:orbitChanged?'OBSERVED_CHANGE_NOT_SETTLE_GATE':'UNRESOLVED_EXISTING_ORBIT_ISSUE',
                  zoomChanged:different(orbit,zoom)>0,resetDifferencePixels:different(final,reset)});
  }
  const renderer=await page.evaluate(()=>{const c=document.createElement('canvas');const g=c.getContext('webgl');
    const d=g?.getExtension('WEBGL_debug_renderer_info');return d?g.getParameter(d.UNMASKED_RENDERER_WEBGL):'UNKNOWN';});
  const receipt={scope:'Scene3DWorkspace harness only; real Hybrid fact route; no API/product E2E',src,
                 backendSceneSha256:createHash('sha256').update(sourceBytes).digest('hex'),
                 gpuRequested:gpu?'D3D11 hardware':'SwiftShader',renderer,browserPid:server.process().pid,
                 results,errors,networkRetries,mathAuthority:'separate exact oracle, not screenshots',
                 orbitGate:'UNRESOLVED; gesture observation does not certify stability',
                 verdict:errors.length?'FAIL':'PASS_CORE_CAUSAL_RENDERING'};
  writeFileSync(join(out,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  if(errors.length)throw new Error(`console/page errors ${errors.length}`);
  console.log(JSON.stringify({verdict:receipt.verdict,scenes:results.length,errors:errors.length,renderer}));
}finally{await browser.close();await server.close();}
