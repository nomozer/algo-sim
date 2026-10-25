// Offline observations of the existing OrbitControls, labels and synchronous rAF callback CPU.
// Timings include instrument overhead and SwiftShader; they are observations, not device performance certification.
import {chromium} from 'playwright';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
const arg=(k,d)=>process.argv.includes(k)?process.argv[process.argv.indexOf(k)+1]:d;
const url=arg('--url','http://127.0.0.1:3156'),out=arg('--out');
const controlsOnly=process.argv.includes('--controls-only');
if(!out||existsSync(out)) throw Error('Fresh output directory required');
mkdirSync(out,{recursive:true});
const read=f=>JSON.parse(readFileSync(f,'utf8'));
const samples=read('src/data/geometry-samples.json').samples;
const fixtures=['cross_section','triangular_prism','cuboid'].map(id=>({id,envelope:read(`../docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${id}_positive.json`).envelope}));
for(const id of ['cau-cat-mat-phang','tru-truc-xien','non-duong-sinh','non-thiet-dien-truc']) fixtures.push({id,envelope:samples.find(x=>x.id===id).envelope});
const audit=read('../docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json');
for(const match of ['family07','family12']) {
  const a=audit.find(x=>x.id.startsWith(match));
  if(a) fixtures.push({id:a.id,envelope:{...samples[0].envelope,scene3d:a.scene}});
}
const receipt={schema:'scene3d-motion-observation/1',controls_only:controlsOnly,provider_calls:0,forbidden:[],errors:[],rows:[],human_visual_approved:'PENDING'};
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try {
for(const width of [1440,390]) {
 const ctx=await browser.newContext({viewport:{width,height:width===390?844:900},deviceScaleFactor:width===390?2:1});
 await ctx.route('**/*',r=>{
   const u=new URL(r.request().url());
   if(u.origin!==url) {receipt.forbidden.push(u.origin);return r.abort();}
   if(u.pathname.startsWith('/api/')) return r.fulfill({json:u.pathname==='/api/health'?{ok:true,hasKey:false}:{user:null}});
   return r.continue();
 });
 await ctx.addInitScript(()=>{
   window.__motion={active:false,cpu:[],intervals:[],snapshots:[],gpu:{},last:null};
   const raf=window.requestAnimationFrame.bind(window);
   window.requestAnimationFrame=fn=>raf(t=>{
     const m=window.__motion,active=m.active,start=performance.now();
     fn(t);
     if(!active) return;
     m.cpu.push({t,ms:performance.now()-start});
     if(m.last===t) return;
     if(m.last!==null) m.intervals.push(t-m.last); m.last=t;
     // Sampling runs after the measured callback, so DOM inspection is not part of its CPU time.
     const canvas=document.querySelector('.geo3d-canvas canvas'),r=canvas?.getBoundingClientRect();
     if(r&&m.snapshots.length<240) m.snapshots.push({t,camera:window.__geo3d_camera_snapshot,
       visible:window.__geo3d_visible_edge_ids,hidden:window.__geo3d_hidden_edge_ids,
       labels:[...document.querySelectorAll('.geo3d-label[data-id]')].filter(e=>getComputedStyle(e).opacity!=='0').map(e=>{
         const b=e.getBoundingClientRect();return {id:e.dataset.id,text:e.textContent,x:b.x-r.x,y:b.y-r.y,w:b.width,h:b.height};
       })});
   });
   for(const P of [WebGLRenderingContext.prototype,WebGL2RenderingContext.prototype]) for(const key of ['createBuffer','createTexture','createProgram','createShader']) {
     const original=P[key];P[key]=function(...args){if(window.__motion.active) window.__motion.gpu[key]=(window.__motion.gpu[key]??0)+1;return original.apply(this,args);};
   }
 });
 const page=await ctx.newPage();page.setDefaultTimeout(15000);
 page.on('pageerror',e=>receipt.errors.push(e.message.split('\n')[0]));
 for(const f of fixtures) {
   const row={id:f.id,width,frames:[]};receipt.rows.push(row);
   try {
    await page.goto(url);
    await page.evaluate(async e=>{const {useAppStore}=await import('/src/state/store.ts');useAppStore.getState().loadEnvelope(e);},f.envelope);
    const canvas=page.locator('.geo3d-canvas canvas');await canvas.waitFor();
    await page.locator('.geo3d-scrub input').evaluate(el=>{
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,el.max);
      el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));
    });
    await page.waitForTimeout(300);
    const original=await page.evaluate(()=>JSON.stringify(window.__ALGO_SIM_STORE__.getState().active.envelope.scene3d));
    const capture=async state=>{
      await page.mouse.move(0,0);await page.waitForTimeout(160);
      const file=`${f.id}-${width}-${state}.png`,png=await canvas.screenshot();writeFileSync(join(out,file),png);
      row.frames.push({state,file,sha256:createHash('sha256').update(png).digest('hex'),...await page.evaluate(()=>({camera:window.__geo3d_camera_snapshot,
        visible:window.__geo3d_visible_edge_ids,hidden:window.__geo3d_hidden_edge_ids,mixed:window.__geo3d_mixed_edge_ids,
        duplicates:window.__geo3d_duplicate_visual_owner_ids,witness_ids:window.__geo3d_witness_ids,
        final_canvas_labels:[...document.querySelectorAll('.geo3d-so-do.la-ket-qua')].map(el=>el.textContent),
        labels:[...document.querySelectorAll('.geo3d-label[data-id],.geo3d-nhan-mp')].filter(e=>getComputedStyle(e).opacity!=='0').map(e=>({id:e.dataset.id??e.dataset.planeId,text:e.textContent}))}))});
    };
    await capture('default-mode-a');
    const b=await canvas.boundingBox();
    if(!controlsOnly) await page.evaluate(()=>{window.__motion.active=true;window.__geo3d_reset_occlusion_performance?.();});
    for(const state of controlsOnly?[]:['quarter','back','high','low']) {
      if(state==='high'||state==='low') await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click();
      const dx=['quarter','back'].includes(state)?b.height*.25:0,dy=state==='high'?b.height*.16:state==='low'?-b.height*.16:0;
      await page.mouse.move(b.x+b.width*.25,b.y+b.height*.5);await page.mouse.down();
      await page.mouse.move(b.x+b.width*.25+dx,b.y+b.height*.5+dy,{steps:24});await page.mouse.up();
      await capture(state);
    }
    row.motion=await page.evaluate(()=>{window.__motion.active=false;return {...window.__motion,occlusion:window.__geo3d_occlusion_performance};});
    // Mode B selected followed by a genuine second selection from the analysis list.
    await page.getByRole('button',{name:'Xem lại toàn hình',exact:true}).click();
    await page.getByRole('button',{name:'Phân tích toán học',exact:true}).click();
    const items=page.locator('[data-analysis-item] button');
    if(await items.count()) {
      await items.first().click();await capture('selected-mode-b');
      row.first_selected=await page.evaluate(()=>window.__geo3d_selected_id);
      if(await items.count()>1) {await items.nth(1).click();row.next_selected=await page.evaluate(()=>window.__geo3d_selected_id);row.selection_changed=row.next_selected!==row.first_selected;}
    }
    const objects=f.envelope.scene3d.objects;
    const auditLabels=async()=>page.locator('.geo3d-label[data-id]').evaluateAll((els,objects)=>els.flatMap(el=>{
      const o=objects.find(o=>o.id===el.dataset.id),expected=o?.notation?.trim();
      return expected&&!el.textContent.split(' ≡ ').map(x=>x.trim()).includes(expected)?[{id:el.dataset.id,expected,actual:el.textContent}]:[];
    }),objects);
    row.label_source_errors=await auditLabels();
    const label=page.locator('.geo3d-label[data-id]').first();
    if(await label.count()) {
      const saved=await label.textContent();await label.evaluate(el=>el.textContent='__invalid_label__');
      row.wrong_label_control_detected=(await auditLabels()).length>0;await label.evaluate((el,text)=>el.textContent=text,saved);
    }
    row.geometry_unchanged=original===await page.evaluate(()=>JSON.stringify(window.__ALGO_SIM_STORE__.getState().active.envelope.scene3d));
    const stats=values=>{const a=[...values].sort((a,b)=>a-b);return {n:a.length,p50:a[Math.floor(a.length*.5)]??null,p95:a[Math.floor(a.length*.95)]??null,max:a.at(-1)??null};};
    const cpuFrames=new Map();for(const {t,ms} of row.motion.cpu) cpuFrames.set(t,(cpuFrames.get(t)??0)+ms);
    row.cpu_frame_ms=stats([...cpuFrames.values()]);row.frame_interval_ms=stats(row.motion.intervals);
    row.no_duplicate_owners=row.frames.every(f=>!f.duplicates?.length);
    row.mode_a_no_final_canvas_labels=row.frames.filter(f=>f.state!=='selected-mode-b').every(f=>f.final_canvas_labels.length===0);
    row.pass=row.geometry_unchanged&&row.no_duplicate_owners&&!row.label_source_errors.length&&row.mode_a_no_final_canvas_labels
      &&row.selection_changed!==false&&row.wrong_label_control_detected!==false;
   } catch(e) {row.error=e.message.split('\n')[0];row.pass=false;}
   writeFileSync(join(out,'receipt.json'),JSON.stringify(receipt,null,2));
   console.log(`${f.id} ${width}: ${row.pass?'PASS':'GAP'} CPU p95 ${row.cpu_frame_ms?.p95??'UNKNOWN'} ${row.error??''}`);
 }
 await ctx.close();
}
}finally{await browser.close();}
receipt.summary={rows:receipt.rows.length,passed:receipt.rows.filter(r=>r.pass).length};
writeFileSync(join(out,'receipt.json'),JSON.stringify(receipt,null,2));
process.exitCode=receipt.errors.length||receipt.forbidden.length||receipt.rows.some(r=>!r.pass)?1:0;
