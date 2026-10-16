/** Offline real-route scenes through Product store and shared harness; no provider calls. */
import { chromium } from 'playwright';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { createHash } from 'node:crypto';
import { BrowserSession } from './browser-runner.mjs';

const out=resolve(process.argv[2]??'');
if(!process.argv[2]||existsSync(out)) throw new Error('fresh output directory required');
mkdirSync(out,{recursive:true});
const rows=JSON.parse(readFileSync(new URL('../../docs/evaluation/geometry/runs/generalized-goal-entry/visual/scenes.json',import.meta.url)));
const session=new BrowserSession({url:'http://127.0.0.1:3101',viewport:1440,height:1000,webgl:true});
const results=[],errors=[]; let browser;
async function shot(page,name){
  const b=await page.screenshot(); writeFileSync(join(out,name),b);
  return {file:name,sha256:createHash('sha256').update(b).digest('hex')};
}
try{
  await session.open();
  browser=await chromium.connectOverCDP('http://'+new URL(session.ws.url).host);
  const page=browser.contexts()[0].pages()[0];
  page.setDefaultTimeout(20000);page.on('pageerror',e=>errors.push(e.message));
  for(let i=0;i<2;i++){
    const row=rows[i];
    await page.goto('http://127.0.0.1:3101/');
    await page.evaluate(async({store,env})=>{const s=await import(store);s.useAppStore.getState().loadEnvelope(env);},
      {store:session.mods.store,env:row.envelope});
    await page.locator('.geo3d-canvas canvas').waitFor();
    const slider=page.locator('.geo3d-scrub input[type=range]');
    const last=Number(await slider.getAttribute('max')); const frames=[];
    for(const step of [...new Set([0,Math.floor(last/2),last])]){
      await slider.fill(String(step)); await page.waitForTimeout(200);
      const rendered=await page.evaluate(()=>window.__geo3d_rendered_object_ids??[]);
      if(step===last&&!rendered.includes('M'))throw new Error(row.id+' missing midpoint');
      frames.push({step,rendered,image:await shot(page,`${row.id}-product-${step}.png`)});
    }
    await page.getByRole('button',{name:'Khám phá',exact:true}).click();
    await page.getByRole('menuitemcheckbox',{name:'Thành phần',exact:true}).click();
    await page.locator('[data-tree-id="M"]').evaluate(el=>{
      for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;
    });
    await page.locator('[data-tree-id="M"]').click();
    await page.waitForTimeout(150);
    if(await page.evaluate(()=>window.__geo3d_selected_id)!=='M')throw new Error('selection');
    const selected=await shot(page,`${row.id}-selected-M.png`);
    await page.goto(`http://127.0.0.1:3101/scripts/hybrid-section-visual.html?src=goal-entry&i=${i}`);
    await page.locator('canvas').waitFor();await page.waitForTimeout(200);
    const harness=await page.evaluate(()=>window.__geo3d_rendered_object_ids??[]);
    const product=frames.at(-1).rendered;
    const sameObjects=JSON.stringify([...harness].sort())===JSON.stringify([...product].sort());
    if(!sameObjects)throw new Error('Product-Harness object parity '+row.id);
    results.push({id:row.id,frames,selected,sameObjects,harness_image:await shot(page,`${row.id}-harness.png`)});
    console.log(row.id+' product timeline/selection and harness parity PASS');
  }
  // Existing perpendicular scene exercises the inherited interaction blocker on the Product inspector.
  const old=JSON.parse(readFileSync(new URL('../../docs/evaluation/geometry/runs/goal-directed-function-discovery/visual/scenes.json',import.meta.url)));
  const row=old.find(x=>x.id==='pyr-midpoint-to-named-line');
  const env={...rows[0].envelope,scene3d:row.scene};
  await page.goto('http://127.0.0.1:3101/');
  await page.evaluate(async({store,env})=>{const s=await import(store);s.useAppStore.getState().loadEnvelope(env);},{store:session.mods.store,env});
  const slider=page.locator('.geo3d-scrub input[type=range]');await slider.waitFor();
  await slider.fill(await slider.getAttribute('max'));await page.waitForTimeout(200);
  const before=await page.evaluate(()=>window.__geo3d_witness_ids??[]);
  if(!before.includes('perpendicular:H'))throw new Error('fixture witness missing');
  await page.getByRole('button',{name:'Khám phá',exact:true}).click();
  await page.getByRole('menuitemcheckbox',{name:'Thành phần',exact:true}).click();
  await page.locator('[data-tree-id="M"]').evaluate(el=>{for(let p=el.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;});
  await page.locator('[data-tree-id="M"]').click();
  await page.getByRole('button',{name:'Ẩn',exact:true}).click();await page.waitForTimeout(200);
  const after=await page.evaluate(()=>({witnesses:window.__geo3d_witness_ids??[],rendered:window.__geo3d_rendered_object_ids??[]}));
  if(after.witnesses.includes('perpendicular:H')||after.rendered.includes('M'))throw new Error('hidden source left witness');
  results.push({id:'hidden-source-witness',before,after,image:await shot(page,'hidden-source-witness.png')});
  if(errors.length)throw new Error('page errors '+errors.join('; '));
  writeFileSync(join(out,'receipt.json'),JSON.stringify({status:'PASS_PRODUCT_AND_HARNESS',model_calls:0,
    human_visual_acceptance:'NOT_APPROVED',api_extraction:'NOT_MEASURED',injection:'public store; minimal shell config, exact route Scene3D unchanged',results,errors},null,2)+'\n');
}catch(e){
  writeFileSync(join(out,'failure.json'),JSON.stringify({status:'FAIL',message:e.message,results,errors},null,2)+'\n');throw e;
}finally{await browser?.close();await session.close();}
