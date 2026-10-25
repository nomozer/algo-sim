import assert from 'node:assert/strict';
import { test } from 'node:test';
import { assessSectionRole } from './section-role-oracle.mjs';
import { assessSectionRoleV2, sectionBoundaryWorldV2, otherSectionBoundariesWorldV2 } from './section-role-oracle-v2.mjs';

const BG = [248,246,241,255], BLUE = [37,99,235,255], FILL = [200,90,50,255];
const W=240, H=200;
function frame({ missing=false }={}) {
  const rgba = new Uint8Array(W*H*4);
  const put=(x,y,c)=>rgba.set(c,(y*W+x)*4);
  for(let y=0;y<H;y++) for(let x=0;x<W;x++) put(x,y,BG);
  const points=Array.from({length:193},(_,k)=>({x:120+80*Math.cos(k*2*Math.PI/192),y:100+80*Math.sin(k*2*Math.PI/192)}));
  const edges=points.slice(0,-1).map((a,i)=>({a,b:points[i+1],hidden:a.x<120,curve:true}));
  for(let y=21;y<180;y++) for(let x=41;x<200;x++) if(Math.hypot(x-120,y-100)<78) put(x,y,FILL);
  for(let k=0;k<12000;k++) {
    const theta=k*2*Math.PI/12000, hidden=Math.cos(theta)<0;
    // Independent synthetic cadence. Remove 20% of the hidden semicircle away from either transition.
    if(hidden && (theta*80%12>5 || (missing && theta>Math.PI*0.85 && theta<Math.PI*1.05))) continue;
    const x=Math.round(120+80*Math.cos(theta)),y=Math.round(100+80*Math.sin(theta));
    for(let d=-1;d<=1;d++) { put(x+d,y,BLUE); put(x,y+d,BLUE); }
  }
  return {img:{w:W,h:H,rgba},input:{scale:1,box:{w:W,h:H},edges}};
}
test('intact independent synthetic conic passes',()=>{
  const {img,input}=frame();
  assert.equal(assessSectionRoleV2(img,input).verdict,'PASS');
});
test('local loss of 20% of the hidden arc cannot pass through aggregate coverage',()=>{
  const {img,input}=frame({missing:true});
  assert.equal(assessSectionRole(img,input).verdict,'PASS','reproduces V1 false certification');
  assert.equal(assessSectionRoleV2(img,input).verdict,'FAIL');
});
test('a label covering only part of a boundary makes the frame uncertifiable',()=>{
  const {img,input}=frame();
  input.overlays=[{x:192,y:90,w:20,h:20}];
  // Long polygon edges remain scored under V1 even when part of one is masked.
  input.edges=[{a:{x:40,y:20},b:{x:200,y:20}},{a:{x:200,y:20},b:{x:200,y:180}},
    {a:{x:200,y:180},b:{x:40,y:180}},{a:{x:40,y:180},b:{x:40,y:20}}];
  for(let y=20;y<=180;y++) for(let x=40;x<=200;x++) img.rgba.set(x===40||x===200||y===20||y===180?BLUE:FILL,(y*W+x)*4);
  assert.equal(assessSectionRole(img,input).verdict,'PASS');
  assert.equal(assessSectionRoleV2(img,input).verdict,'UNCERTIFIABLE');
});
test('conic sampling is independent of the 96-chord renderer and lies on the source plane',()=>{
  const scene={objects:[{id:'ball',type:'curved_solid',curved_kind:'ball',anchor:['0','0','0'],radius_sq:'25'},
    {id:'cut',type:'circle3',center:['0','0','3'],normal:['0','0','1'],radius_sq:'16',depends:['ball']}]};
  const edges=sectionBoundaryWorldV2(scene,'cut',[10,5,8]);
  assert.notEqual(edges.length,96);
  for(const e of edges) { assert.ok(Math.abs(e.a[2]-3)<1e-12); assert.ok(Math.abs(Math.hypot(...e.a)-5)<1e-10); }
});

test('unknown polygon parent cannot certify visibility',()=>{
  const scene={objects:[{id:'cut',type:'polygon3',vertices:[['0','0','0'],['1','0','0'],['0','1','0']]}]};
  assert.equal(sectionBoundaryWorldV2(scene,'cut',[3,4,5]),null);
});
for(const badFace of [[0,1,99],[0,0,0]]) test(`malformed polygon face ${badFace} cannot crash or invent visibility`,()=>{
  const vertices=[['0','0','0'],['1','0','0'],['0','1','0'],['0','0','1']];
  const scene={objects:[{id:'parent',type:'solid',vertices,faces:[badFace,[0,1,2]]},
    {id:'cut',type:'section',parent:'parent',polygon:vertices.slice(0,3)}]};
  assert.equal(sectionBoundaryWorldV2(scene,'cut',[3,4,5]),null);
});
test('other polygon3 regions and unsupported conics are never silently omitted',()=>{
  const result=otherSectionBoundariesWorldV2({objects:[{id:'small',type:'polygon3'},{id:'unknown',type:'circle3'}]},'selected',[3,4,5]);
  assert.deepEqual(result.unsupported,['small','unknown']);
});
test('all pixels masked is uncertifiable rather than proof of missing cobalt',()=>{
  const {img,input}=frame();input.overlays=[{x:0,y:0,w:W,h:H}];
  assert.equal(assessSectionRoleV2(img,input).verdict,'UNCERTIFIABLE');
});
test('hidden polygon completeness without a dash bound cannot be certified',()=>{
  const {img,input}=frame();input.edges.forEach(e=>e.curve=false);
  assert.equal(assessSectionRoleV2(img,input).verdict,'UNCERTIFIABLE');
});
test('a hidden polygon with a declared dash bound detects local missing ink',()=>{
  const {img,input}=frame();
  const points=[{x:40,y:20},{x:200,y:20},{x:200,y:180},{x:40,y:180}];
  input.edges=points.map((a,i)=>({a,b:points[(i+1)%4],hidden:true,max_hidden_gap_css:20}));
  for(let y=0;y<H;y++) for(let x=0;x<W;x++) {
    const inside=x>=40&&x<=200&&y>=20&&y<=180;
    const edge=inside&&(x===40||x===200||y===20||y===180);
    img.rgba.set(edge?BLUE:inside?FILL:BG,(y*W+x)*4);
  }
  for(let x=90;x<146;x++) img.rgba.set(BG,(20*W+x)*4);
  assert.equal(assessSectionRole(img,input).verdict,'PASS');
  assert.equal(assessSectionRoleV2(img,input).verdict,'FAIL');
});

test('camera tilt preserves independent source visibility under inverse model rotation',()=>{
  const scene={objects:[{id:'ball',type:'curved_solid',curved_kind:'ball',anchor:['0','0','0'],radius_sq:'1'},
    {id:'cut',type:'circle3',center:['0','0','0'],normal:['0','0','1'],radius_sq:'1',depends:['ball']}]};
  const model=[1,0,0,0,0,0,1,0,0,-1,0,0,0,0,0,1];
  assert.deepEqual(sectionBoundaryWorldV2(scene,'cut',{position:[3,-5,4],model_matrix_column_major:model}),sectionBoundaryWorldV2(scene,'cut',[3,4,5]));
});

test('edge-on front and hidden arcs sharing the same pixels are uncertifiable',()=>{
  const {img,input}=frame();
  input.edges=input.edges.map(e=>({...e,a:{x:e.a.x,y:100+(e.a.y-100)*.001},b:{x:e.b.x,y:100+(e.b.y-100)*.001}}));
  for(let y=0;y<H;y++) for(let x=0;x<W;x++) img.rgba.set(y===100&&x>=40&&x<=200?BLUE:BG,(y*W+x)*4);
  assert.equal(assessSectionRoleV2(img,input).verdict,'UNCERTIFIABLE');
});

for(const [role,from,to] of [['boundary',BLUE,[0,117,222,255]],['boundary',BLUE,FILL],['fill',FILL,[251,146,60,255]],['fill',FILL,BLUE]]) {
 test(`V2 rejects wrong ${role} even when the other role remains correct: ${to.slice(0,3)}`,()=>{
  const {img,input}=frame();
  for(let q=0;q<img.rgba.length;q+=4) if(from.slice(0,3).every((c,i)=>img.rgba[q+i]===c)) img.rgba.set(to,q);
  assert.equal(assessSectionRoleV2(img,input).verdict,'FAIL');
 });
}
test('V2 rejects a tiny second selected boundary without relying on global blue area',()=>{
  const {img,input}=frame();
  const points=[{x:5,y:5},{x:15,y:5},{x:15,y:15},{x:5,y:15}];
  input.otherBoundaries=[points.map((a,i)=>({a,b:points[(i+1)%4]}))];
  for(let x=5;x<=15;x++) for(const y of [5,15]) img.rgba.set(BLUE,(y*W+x)*4);
  for(let y=5;y<=15;y++) for(const x of [5,15]) img.rgba.set(BLUE,(y*W+x)*4);
  assert.ok(assessSectionRoleV2(img,input).reasons.includes('UNSELECTED_BOUNDARY_COBALT'));
});
