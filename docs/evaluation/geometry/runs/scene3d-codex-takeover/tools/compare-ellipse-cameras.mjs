import {readFileSync, writeFileSync} from 'node:fs';
import {sectionBoundaryWorldV2} from '../../../../../../frontend/scripts/section-role-oracle-v2.mjs';
import {project} from '../../../../../../frontend/scripts/section-role-oracle.mjs';
const run='docs/evaluation/geometry/runs/scene3d-codex-takeover';
const read=path=>JSON.parse(readFileSync(path,'utf8'));
const before=read(`${run}/ellipse-before/receipt.json`).rows;
const after=read(`${run}/role-aware/receipt.json`).rows;
const scene=read('docs/evaluation/geometry/runs/f2-role-aware-oracle/inputs/p6-ellipse-envelope.json').scene3d;
const rows=before.map(b=>{
  const a=after.find(r=>r.case===b.case&&r.width===b.width&&r.cameraName===b.cameraName);
  const edges=sectionBoundaryWorldV2(scene,'E',b.camera);
  if(!edges?.length) throw Error('Independent source conic unavailable');
  let maxCssDelta=0;
  for(const e of edges) for(const point of [e.a,e.b]) {
    const x=project(point,b.camera,{w:b.camera.viewport_width,h:b.camera.viewport_height});
    const y=project(point,a.camera,{w:a.camera.viewport_width,h:a.camera.viewport_height});
    maxCssDelta=Math.max(maxCssDelta,Math.hypot(x.x-y.x,x.y-y.y));
  }
  return {width:b.width,camera:b.cameraName,before:b.verdict,after:a.verdict,max_source_boundary_projection_delta_css_px:maxCssDelta,
    note:'Identical source conic and gesture; damping leaves slightly different camera floats. These are near-matched observations, not bit-identical camera captures; analytic regression is the exact mathematical check.'};
});
writeFileSync(`${run}/verification/ellipse-projection-comparison.json`,JSON.stringify({rows},null,2)+'\n');
console.log(JSON.stringify({rows}));
