// Replay proposed V2 from hashed captures; never writes the original receipt or any official result.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname,join} from 'node:path';
import assert from 'node:assert/strict';
import {docPNG} from './png-pixels.mjs';
import {project} from './section-role-oracle.mjs';
import {assessSectionRoleV2,sectionBoundaryWorldV2,otherSectionBoundariesWorldV2} from './section-role-oracle-v2.mjs';
const arg=k=>process.argv[process.argv.indexOf(k)+1];
const source=arg('--receipt'),out=arg('--out'),cases=JSON.parse(readFileSync(arg('--cases'),'utf8'));
assert.ok(!existsSync(out),'Fresh output required');
const old=JSON.parse(readFileSync(source,'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const rows=[];
for(const row of old.rows) {
 assert.notEqual(row.verdict,'ERROR');
 const c=cases.find(c=>c.id===row.case),raw=JSON.parse(readFileSync(c.envelope_file,'utf8'));
 const envelope=c.pick?c.pick.split('.').reduce((v,k)=>v[k],raw):raw,scene=envelope.scene3d;
 const png=readFileSync(join(dirname(source),row.file));assert.equal(sha(png),row.sha256);
 const img=docPNG(png),cam=row.camera,box={w:cam.viewport_width,h:cam.viewport_height};
 const projection=boundary=>boundary.map(e=>({...e,a:project(e.a,cam,box),b:project(e.b,cam,box)}));
 const world=sectionBoundaryWorldV2(scene,c.section,cam),other=otherSectionBoundariesWorldV2(scene,c.section,cam);
 const edges=row.comparison.independentEdges??(world?projection(world):null);
 const result=world?assessSectionRoleV2(img,{scale:img.w/box.w,box,edges,overlays:row.comparison.overlays,
   otherBoundaries:other.boundaries.map(x=>projection(x.edges)),unsupportedOtherBoundaries:other.unsupported})
   :{verdict:'UNCERTIFIABLE',reasons:['SOURCE_GEOMETRY_UNSUPPORTED']};
 rows.push({case:row.case,width:row.width,camera:row.cameraName,fault:row.fault,file:row.file,sha256:row.sha256,
   identity_ok:row.identity_ok,locked_hue:row.comparison.locked_hue_predicate,v1:row.comparison.v1,
   initial_v2:{verdict:row.comparison.v2.verdict,reasons:row.comparison.v2.reasons},v2:result,
   verdict:row.identity_ok?result.verdict:'FAIL'});
}
const baseline=rows.filter(r=>r.fault==='none'),view=r=>`${r.case}|${r.width}|${r.camera}`;
const certified=new Set(baseline.filter(r=>r.verdict==='PASS').map(view));
const faults=rows.filter(r=>r.fault!=='none'&&certified.has(view(r)));
const counts=(rs,key)=>Object.fromEntries(['PASS','FAIL','UNCERTIFIABLE'].map(v=>[v,rs.filter(r=>key(r)===v).length]));
const result={schema:'section-role-v2-reassessment/1',official_score_changed:false,provider_calls:0,source_receipt:source,
 source_sha256:sha(readFileSync(source)),oracle_sha256:sha(readFileSync('scripts/section-role-oracle-v2.mjs')),
 summary:{baseline:counts(baseline,r=>r.verdict),v1:counts(baseline,r=>r.v1.verdict),locked_hue_pass:baseline.filter(r=>r.locked_hue.pass).length,
 faults_on_certified_views:faults.length,faults_detected:faults.filter(r=>r.verdict==='FAIL').length},rows};
writeFileSync(out,JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));
