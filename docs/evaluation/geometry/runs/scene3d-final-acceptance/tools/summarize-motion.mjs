import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {project} from '../../../../../../frontend/scripts/section-role-oracle.mjs';
const run='docs/evaluation/geometry/runs/scene3d-final-acceptance';
const read=p=>JSON.parse(readFileSync(p,'utf8'));
const motion=read(`${run}/motion/receipt.json`),controls=read(`${run}/label-controls/receipt.json`);
const scenes=new Map();
for(const id of ['cross_section','triangular_prism','cuboid']) scenes.set(id,read(`docs/evaluation/geometry/runs/visual-closure-hybrid-readiness/visual/final-inputs/fixtures/${id}_positive.json`).envelope.scene3d);
for(const s of read('frontend/src/data/geometry-samples.json').samples) scenes.set(s.id,s.envelope.scene3d);
for(const s of read('docs/evaluation/geometry/runs/geometric-visual-correctness-framing/demos/audit_scenes.json')) scenes.set(s.id,s.scene);
const num=s=>{const [a,b='1']=String(s).split('/');return Number(a)/Number(b);};
const rows=motion.rows.map(row=>{
 const scene=scenes.get(row.id),points=new Map(scene.objects.filter(o=>o.type==='point3').map(o=>[o.id,o]));
 const jumps=[],sourceErrors=[];let previous=new Map(),compared=0;
 for(const frame of row.motion.snapshots) {
  const current=new Map(),camera=frame.camera;
  for(const label of frame.labels) {
   const object=points.get(label.id);
   if(!object) {sourceErrors.push({id:label.id,reason:'NO_SOURCE_POINT'});continue;}
   if(object.notation&&!label.text.split(' ≡ ').map(s=>s.trim()).includes(object.notation.trim())) sourceErrors.push({id:label.id,reason:'NAME_MISMATCH'});
   if(!object.xyz) continue;
   const a=project(object.xyz.map(num),camera,{w:camera.viewport_width,h:camera.viewport_height});
   const value={...label,ax:a.x,ay:a.y,t:frame.t};current.set(label.id,value);
   const prior=previous.get(label.id);if(!prior||frame.t-prior.t>100) continue;
   compared++;
   const anchorMove=Math.hypot(a.x-prior.ax,a.y-prior.ay);
   const offsetJump=Math.hypot(label.x-a.x-(prior.x-prior.ax),label.y-a.y-(prior.y-prior.ay));
   if(anchorMove<5&&offsetJump>20) jumps.push({id:label.id,t:frame.t,anchor_move_css:anchorMove,offset_jump_css:offsetJump});
  }
  previous=current;
 }
 const ctrl=controls.rows.find(x=>x.id===row.id&&x.width===row.width);
 return {id:row.id,width:row.width,source_errors:sourceErrors,compared_frames:compared,suspected_layout_jumps:jumps,
   cpu_frame_ms:row.cpu_frame_ms,frame_interval_ms:row.frame_interval_ms,gpu_creations_in_mixed_sequence:row.motion.gpu,
   geometry_unchanged:row.geometry_unchanged,duplicate_free:row.no_duplicate_owners,
   source_labels_control_pass:ctrl?.pass===true&&ctrl.wrong_label_control_detected===true&&ctrl.selection_changed===true,
   distinct_visibility_states:new Set(row.frames.map(f=>JSON.stringify([f.visible,f.hidden,f.mixed]))).size};
});
const output=`${run}/motion-summary.json`;
if(existsSync(output)) throw Error('Fresh output required');
const result={schema:'scene3d-motion-summary/1',classification:'OBSERVATIONS_NOT_CONTINUITY_OR_PERFORMANCE_CERTIFICATION',
  original_label_negative_controls:'INVALID: substring comparator accidentally accepted letters present in the control string; original rows.pass is not a complete acceptance verdict',
  corrected_label_controls_passed:rows.filter(r=>r.source_labels_control_pass).length,
  jump_heuristic:'offset jump >20 CSSpx while projected source anchor moves <5 CSSpx in <=100ms; review flags, not a mathematical error oracle',
  rows};
writeFileSync(output,JSON.stringify(result,null,2));
console.log(JSON.stringify({rows:rows.length,corrected_controls:result.corrected_label_controls_passed,jump_flags:rows.reduce((s,r)=>s+r.suspected_layout_jumps.length,0),source_errors:rows.reduce((s,r)=>s+r.source_errors.length,0)}));
