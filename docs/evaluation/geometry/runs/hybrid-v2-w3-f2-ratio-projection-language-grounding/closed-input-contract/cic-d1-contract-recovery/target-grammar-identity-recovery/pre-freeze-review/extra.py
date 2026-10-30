import json, sys, socket, os
from copy import deepcopy
os.environ['ALLOW_LIVE_AI']='0'; sys.dont_write_bytecode=True
socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('OFFLINE'))
sys.path.insert(0, sys.argv[1])
from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.function_route import run_typed_fact_next_planner_route
P=json.load(open('probes.json',encoding='utf-8'))
out={}
q=deepcopy(P['F2.pyr.pyr1D_vs_pyr2D'])
for pr in q['premises']:
    if pr['kind']=='segment_length' and pr['args']['segment']==['pyr2::D','pyr2::A']: pr['args']['value']='3a'; pr['quote']='DA = 3a'
q['problem_text']=q['problem_text'].replace('DA = a.','DA = 3a.').replace('DA = a','DA = 3a')
r=run_typed_fact_next_route(q); out['pyr1D_vs_pyr2D_DA3a']=(r.status,r.code,(r.answer_exact or {}).get('rv'),(r.reason or '')[:120])
base=deepcopy(P['F2.bind.distinct_ctrl_scoped']); base['solids'][0].pop('vertex_bindings',None)
for gt in ('radius','lateral_area','area'):
    p=deepcopy(base); p['math_goals'][-1].update(goal_type=gt,target={'solid':'pr'}); p['math_goals'][-1].pop('solid_id',None)
    for name,f in (('a3',run_typed_fact_next_route),('pl',run_typed_fact_next_planner_route)):
        r=f(deepcopy(p)); out[f'prism.{gt}.{name}']=(r.status,r.code,bool(r.scene3d),bool(r.answers))
print(json.dumps(out,ensure_ascii=False,indent=1))
