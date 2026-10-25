/** Proposed V2 only. No product or official gate imports this file.
 * Reuses V1 color measurements, adds local completeness and strict boundary observability.
 * Curve expectations come from the source conic, not renderer buffers/quaternion/96-chord phase.
 * The declared 2-on/2-off in 96 dash slots is a presentation convention, not a geometry oracle.
 */
import { Matrix4, Vector3 } from 'three';
import { assessSectionRole, sectionBoundaryWorld, distanceToComposite, NGUONG_VAI_THIET_DIEN as N } from './section-role-oracle.mjs';

const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const unit=a=>{ const len=Math.hypot(...a); return len>0 ? a.map(x=>x/len) : null; };
const number=s=>{ const [a,b='1']=String(s).split('/'); return Number(a)/Number(b); };
const vector=v=>Array.isArray(v)&&v.length===3 ? v.map(number) : [NaN,NaN,NaN];

export function otherSectionBoundariesWorldV2(scene,selected,camera) {
  const boundaries=[],unsupported=[];
  for(const o of scene.objects??[]) {
    if(o.id===selected||!['section','polygon3','circle3','ellipse3'].includes(o.type)) continue;
    const boundary=sectionBoundaryWorldV2(scene,o.id,camera);
    if(boundary) boundaries.push({id:o.id,edges:boundary}); else unsupported.push(o.id);
  }
  return {boundaries,unsupported};
}

export function sectionBoundaryWorldV2(scene,id,camera) {
  const o=scene.objects?.find(x=>x.id===id);
  if(!o) return null;
  if(o.type==='section'||o.type==='polygon3') {
    const parent=scene.objects.find(x=>x.id===o.parent&&x.type==='solid');
    const points=(o.polygon??o.vertices??[]).map(vector);
    const vertices=(parent?.vertices??parent?.vertex_ids?.map(vid=>scene.objects.find(x=>x.id===vid)?.xyz)??[]).map(vector);
    if(!parent||points.length<3||!vertices.length||[...points,...vertices].some(v=>!v.every(Number.isFinite))) return null;
    if(!(parent.faces?.length)||parent.faces.some(face=>!Array.isArray(face)||face.length<3
      ||face.some(k=>!Number.isInteger(k)||k<0||!vertices[k])
      ||!unit(cross(sub(vertices[face[1]],vertices[face[0]]),sub(vertices[face[2]],vertices[face[0]]))))) return null;
    for(let i=0;i<points.length;i++) {
      const onFace=(parent.faces??[]).some(face=>{
        if(face.length<3||face.some(k=>!vertices[k])) return false;
        const normal=unit(cross(sub(vertices[face[1]],vertices[face[0]]),sub(vertices[face[2]],vertices[face[0]])));
        return normal&&[points[i],points[(i+1)%points.length]].every(p=>Math.abs(dot(normal,sub(p,vertices[face[0]])))<1e-6);
      });
      if(!onFace) return null;
    }
    return sectionBoundaryWorld(scene,id,camera);
  }
  if(!['circle3','ellipse3'].includes(o.type)) return null;
  const solid=scene.objects.find(x=>x.type==='curved_solid'&&(o.depends??[]).includes(x.id));
  if(!solid||!['ball','cylinder','cone'].includes(solid.curved_kind)) return null;
  const p=new Vector3(...(Array.isArray(camera)?camera:camera.position));
  if(camera.model_matrix_column_major) p.applyMatrix4(new Matrix4().fromArray(camera.model_matrix_column_major).invert());
  const eye=p.toArray(), center=vector(o.center), normal=unit(vector(o.normal));
  if(!normal||!center.every(Number.isFinite)) return null;
  let u,v,ru,rv;
  if(o.type==='circle3') {
    // Pick the least aligned Cartesian axis. This frame intentionally differs from the renderer's quaternion frame.
    const axis=[0,0,0]; axis[normal.map(Math.abs).indexOf(Math.min(...normal.map(Math.abs)))]=1;
    u=unit(cross(normal,axis)); v=cross(normal,u); ru=rv=Math.sqrt(number(o.radius_sq));
  } else {
    u=unit(vector(o.major_dir)); v=unit(vector(o.minor_dir));
    ru=Math.sqrt(number(o.semi_major_sq)); rv=Math.sqrt(number(o.semi_minor_sq));
    if(!u||!v||Math.abs(dot(u,v))>1e-8||Math.abs(dot(u,normal))>1e-8||Math.abs(dot(v,normal))>1e-8) return null;
  }
  if(![...u,...v,ru,rv].every(Number.isFinite)||ru<=0||rv<=0) return null;
  const anchor=vector(solid.anchor);
  const top=solid.apex_or_top?vector(solid.apex_or_top):null;
  const axis=unit(top?sub(top,anchor):vector(solid.axis));
  if(!anchor.every(Number.isFinite)|| (solid.curved_kind!=='ball'&&!axis)) return null;
  const height=top?Math.hypot(...sub(top,anchor)):number(solid.height);
  if(solid.curved_kind!=='ball'&&!(height>0)) return null;
  const point=t=>center.map((x,i)=>x+ru*Math.cos(t)*u[i]+rv*Math.sin(t)*v[i]);
  const count=257, phase=Math.PI/701;
  return Array.from({length:count},(_,i)=>{
    const t=phase+i*2*Math.PI/count, mid=point(t+Math.PI/count);
    let outward=sub(mid,anchor);
    if(solid.curved_kind!=='ball') {
      outward=sub(outward,axis.map(x=>x*dot(outward,axis)));
      if(solid.curved_kind==='cone') {
        const radial=Math.hypot(...outward), slope=Math.sqrt(number(solid.radius_sq))/height;
        outward=outward.map((x,k)=>x+axis[k]*radial*slope);
      }
    }
    return {a:point(t),b:point(t+2*Math.PI/count),hidden:dot(outward,sub(eye,mid))<0,curve:true};
  });
}

function distance(x,y,e) {
  const dx=e.b.x-e.a.x,dy=e.b.y-e.a.y;
  const t=Math.max(0,Math.min(1,((x-e.a.x)*dx+(y-e.a.y)*dy)/(dx*dx+dy*dy||1)));
  return Math.hypot(x-e.a.x-t*dx,y-e.a.y-t*dy);
}

export function assessSectionRoleV2(img,input) {
  const base=assessSectionRole(img,input), {edges,scale,box,overlays=[]}=input;
  const reasons=[...base.reasons], local=[], r=Math.ceil(N.windowCss*scale);
  const lengths=edges.map(e=>Math.hypot(e.b.x-e.a.x,e.b.y-e.a.y));
  const perimeter=lengths.reduce((sum,x)=>sum+x,0), starts=[];
  lengths.reduce((sum,x,i)=>{starts[i]=sum; return sum+x;},0);
  // Max two absent dash slots at the largest projected angular speed, plus both search windows and raster rounding.
  const hiddenGapLimit=Math.max(...lengths)*edges.length/48+2*N.windowCss+2;
  const observations=[];
  let masked=0;
  for(let i=0;i<edges.length;i++) {
    const e=edges[i], steps=Math.max(1,Math.ceil(lengths[i]));
    for(let k=0;k<steps;k++) {
      const t=(k+0.5)/steps,x=e.a.x+(e.b.x-e.a.x)*t,y=e.a.y+(e.b.y-e.a.y)*t;
      const covered=overlays.some(b=>x>=b.x-3&&x<=b.x+b.w+3&&y>=b.y-3&&y<=b.y+b.h+3);
      const apart=edges.some((s,j)=>{
        const arcDistance=Math.abs(starts[i]+t*lengths[i]-starts[j]-lengths[j]/2);
        return Math.min(arcDistance,perimeter-arcDistance)>2*(N.separationCss+N.windowCss)
          &&Boolean(s.hidden)!==Boolean(e.hidden)&&distance(x,y,s)<N.separationCss;
      });
      const usable=!covered&&!apart&&x>=3&&x<box.w-3&&y>=3&&y<box.h-3;
      if(!usable) masked++;
      let blue=false;
      if(usable) for(let dy=-r;dy<=r&&!blue;dy++) for(let dx=-r;dx<=r;dx++) {
        const px=Math.round(x*scale)+dx,py=Math.round(y*scale)+dy;
        if(px<0||py<0||px>=img.w||py>=img.h) continue;
        const q=(py*img.w+px)*4;
        if(distanceToComposite([img.rgba[q],img.rgba[q+1],img.rgba[q+2]],[37,99,235],0.35)<=N.boundaryDeltaE) { blue=true; break; }
      }
      observations.push({usable,blue,hidden:Boolean(e.hidden),curve:e.curve,maxHiddenGap:e.max_hidden_gap_css,length:lengths[i]/steps,edge:i});
    }
  }
  // Repeat once to cover a missing interval across the closed curve's phase origin. Masks split intervals.
  let gap=0, previousHidden=null;
  for(const s of [...observations,...observations]) {
    if(!s.usable||s.blue||s.hidden!==previousHidden) gap=0;
    if(s.usable&&!s.blue) gap+=s.length;
    previousHidden=s.hidden;
    const limit=s.hidden?(s.curve?hiddenGapLimit:s.maxHiddenGap??null):2*N.windowCss+2;
    if(limit!==null&&gap>limit&&!local.some(row=>row.edge===s.edge)) local.push({edge:s.edge,hidden:s.hidden,gap_css:gap,limit_css:limit});
  }
  if(local.length) reasons.push('LOCAL_BOUNDARY_INK_MISSING');
  if(masked) reasons.push('BOUNDARY_PARTLY_UNOBSERVABLE');
  if(edges.some(e=>e.hidden&&!e.curve&&!Number.isFinite(e.max_hidden_gap_css))) reasons.push('HIDDEN_POLYGON_DASH_BOUND_UNKNOWN');
  if(input.unsupportedOtherBoundaries?.length) reasons.push('OTHER_BOUNDARY_SOURCE_UNSUPPORTED');
  const ownershipUnobservable=!base.blue.all&&observations.every(s=>!s.usable);
  const unique=[...new Set(reasons.filter(r=>!(ownershipUnobservable&&r==='COBALT_NOT_ON_SELECTED_BOUNDARY')))];
  const unobservable=new Set(['BOUNDARY_NOT_OBSERVABLE','BOUNDARY_NOT_FULLY_OBSERVABLE','FILL_NOT_OBSERVABLE','BOUNDARY_PARTLY_UNOBSERVABLE','HIDDEN_POLYGON_DASH_BOUND_UNKNOWN','OTHER_BOUNDARY_SOURCE_UNSUPPORTED']);
  const verdict=unique.some(x=>!unobservable.has(x))?'FAIL':unique.length?'UNCERTIFIABLE':'PASS';
  return {...base,pass:verdict==='PASS',verdict,reasons:unique,local_gaps:local,masked_boundary_samples:masked,hidden_gap_limit_css:hiddenGapLimit,
    scope:'PROPOSED_V2_PIXEL_PRESENTATION_CHECK_NOT_A_GEOMETRY_PROOF'};
}
