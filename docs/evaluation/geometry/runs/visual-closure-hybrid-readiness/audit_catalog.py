"""Read the Owner HTML as reference data, inventory every catalog entry, bind inspected code by hashes."""
import hashlib,html,json,re
from collections import Counter
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/"backend/app").is_dir())
source=Path(__file__).resolve().parent/"reference/matphang.html"
raw=source.read_bytes(); text=raw.decode('utf-8')
catalog=text.split('const SHAPES_DB = [',1)[1].split('\n        ];',1)[0]
entries=re.findall(r"id:\s*'([^']+)'\s*,\s*name:\s*'([^']+)'",catalog)
assert len(entries)==18 and len({i for i,_ in entries})==18
P='PARTIAL'; O='OFFLINE_GEOMETRY_VERIFIED'; R='RENDER_ONLY'; U='UNSUPPORTED'; Q='UNKNOWN'
# Nine separate layers: facts, source, registry, planner, exact engine, /4, frontend, browser, new authored problem.
layers={
'quan_he_dt_mp':([P,P,O,P,O,P,R,P,Q],P,'Named/polyhedral instances only; three-perpendicular theorem discovery and full standalone source family not certified.'),
'hai_dt_cheo_nhau':([P,P,O,P,O,P,R,P,Q],P,'Exact line relations exist on Route B/kernel; canonical V2 measurement bridge does not expose general distance/angle goals.'),
'chop_sa_vuong_day_vuong':([P,O,O,O,O,O,R,P,Q],P,'Pyramid construction/volume/sections have offline paths; requested circumsphere combination is not canonical Hybrid.'),
'chop_tu_giac_deu':([P,O,O,O,O,O,R,P,Q],P,'Regular-square-pyramid subset; inscribed/circumscribed spheres are absent from the canonical bridge.'),
'chop_tam_giac_deu':([P,O,O,O,O,O,R,P,Q],P,'Regular-triangular-pyramid subset; full incircle/circumsphere program not certified.'),
'chop_sa_vuong_abc':([P,O,O,O,O,O,R,P,Q],P,'Determined triangular bases only; no blanket arbitrary-triangle/in- or circumsphere claim.'),
'to_hop_chop_non':([P,U,U,U,P,U,R,Q,Q],R,'Curved solid declaration parses; bridge rejects cone before Source Gate/Planner.'),
'to_hop_lang_tru_tru_cau':([P,U,U,U,P,U,R,Q,Q],R,'Renderer can compose supplied meshes; canonical cylinder/sphere bridge is refused.'),
'to_hop_non_cau':([P,U,U,U,P,U,R,Q,Q],R,'Curved primitives in legacy kernel do not establish canonical inscribed/circumscribed composite solving.'),
'chop_cut_deu':([U,U,U,U,P,U,Q,Q,Q],U,'Square-pyramid frustum is not the cone_frustum schema enum; no canonical frustum topology/goal contract.'),
'hinh_hop_chu_nhat':([P,O,O,O,O,O,R,P,Q],P,'Cuboid/cube metric subset served; optional sphere combination is not canonical Hybrid.'),
'lang_tru_tam_giac_deu':([P,O,O,O,O,O,R,P,O],P,'New right-triangular-prism volume probes pass; full arbitrary-base/circumsphere catalog behavior not certified.'),
'lang_tru_xien':([P,O,O,O,O,O,R,P,O],P,'New oblique-prism volume probes pass with one lateral vector; general perpendicular sections and arbitrary bases remain bounded.'),
'mat_cau':([P,U,U,U,O,U,R,P,Q],R,'Kernel distinguishes proper circle/tangent/no cut exactly; canonical bridge rejects sphere. Legacy screenshots are render evidence.'),
'hinh_non':([P,U,U,U,P,U,R,P,Q],R,'Legacy cone/generator/axial cuts exist; canonical bridge has no cone function or goal contracts.'),
'hinh_tru':([P,U,U,U,P,U,R,P,Q],R,'Legacy cylinder sections are bounded; arbitrary axis-parallel sections and canonical routing are not certified here.'),
'he_truc_oxyz':([P,U,U,U,P,U,R,Q,Q],U,'A root frame marker is not source-grounded arbitrary point coordinates; bridge lacks general coordinate inputs/goals.'),
'oxyz_dt_mp_cau':([P,U,U,U,P,U,R,Q,Q],R,'Legacy coordinates/plane/sphere rendering is not source-gated canonical Hybrid solving.'),
}
layer_names=['typedfacts_v2','source_gate','registry','planner','exact_engine','adapter4','frontend','browser','new_authored_problem']
rows=[]
for identifier,name in entries:
    statuses,overall,limit=layers[identifier]
    rows.append({'id':identifier,'name':html.unescape(name),'html_line':text[:text.index("id: '"+identifier+"'")].count('\n')+1,
                 'overall':overall,'layers':dict(zip(layer_names,statuses)),'limitation':limit})
paths=['backend/app/simulation/geometry_functions/typed_fact_next.py','backend/app/simulation/geometry_functions/typed_fact_next_bridge.py',
       'backend/app/simulation/geometry_functions/registry.py','backend/app/simulation/geometry_functions/planner.py',
       'backend/app/simulation/geometry_functions/engine.py','backend/app/simulation/geometry/curved.py',
       'backend/app/ai/adapter4_route.py','backend/app/ai/hybrid_offline.py',
       'frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx','frontend/src/simulations/domains/geometry/scene3d-view.tsx']
hashes={p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in paths}
registry=(ROOT/paths[2]).read_text(encoding='utf-8')
result={'schema':'html-geometry-capability-audit/1','reference':{'path':str(source),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'catalog_entries':len(rows)},
        'scope':'All 18 full HTML configurations, including optional composite/inscription goals; authored numerical subsets are narrower.',
        'provider_calls':0,'independent_holdout':'NOT_RUN','nl_extraction_quality':'UNKNOWN',
        'counts':dict(Counter(r['overall'] for r in rows)),'full_e2e_verified':0,
        'registry_declarations':re.findall(r'_F\("([^"]+)"',registry),'inspected_source_sha256_lf':hashes,'families':rows}
(Path(__import__("tempfile").mkdtemp(prefix="algosim-catalog-"))/"receipt.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reference':result['reference'],'counts':result['counts'],'registry_declarations':len(result['registry_declarations'])},ensure_ascii=False))
